from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
import uuid
from loguru import logger

# Импорты конфигурации и логирования
from config_simple import settings
from logging_config import setup_logging, setup_sentry
from database import get_db, check_database_connection, init_database, close_database, AsyncSessionLocal
from models import User, WordGroup, Word, LLM, WordSerp, Company, BrandProject, Competitor, BrandMention
from schemas import (
    UserCreate, UserLogin, UserResponse, Token,
    WordGroupCreate, WordGroupUpdate, WordGroupResponse,
    WordCreate, WordUpdate, WordResponse,
    LLMCreate, LLMUpdate, LLMResponse,
    WordSerpResponse, CompanyResponse,
    WordAnalytics, GroupAnalytics,
    BrandProjectCreate, BrandProjectResponse, BrandProjectUpdate,
    CompetitorResponse, BrandMentionResponse, BrandAnalytics
)
from auth import hash_password, verify_password, create_access_token, get_current_user
from llm_service_modern import llm_service
import requests
import json
from datetime import datetime, timedelta

# === ФУНКЦИИ ПРЯМОГО ОБНОВЛЕНИЯ SERP ===

async def get_serp_from_openai_direct(word: str) -> str:
    """Прямое получение SERP данных от OpenAI"""
    try:
        prompt = f"""
        Представь, что ты поисковая система. Для запроса "{word}" выдай топ-10 результатов поиска в формате:
        1. Заголовок - краткое описание
        2. Заголовок - краткое описание
        ...
        
        Результаты должны быть релевантными и реалистичными.
        """
        
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            logger.error(f"Ошибка OpenAI API: {response.status_code}")
            return f"Моковые результаты для '{word}': 1. Результат 1 - описание, 2. Результат 2 - описание"
            
    except Exception as e:
        logger.error(f"Ошибка получения SERP от OpenAI: {e}")
        return f"Моковые результаты для '{word}': 1. Результат 1 - описание, 2. Результат 2 - описание"

async def extract_companies_from_serp_direct(serp_text: str) -> List[str]:
    """Прямое извлечение компаний из SERP текста"""
    try:
        prompt = f"""
        Проанализируй следующие результаты поиска и извлеки названия компаний, брендов и организаций.
        Верни только список названий через запятую, без дополнительного текста.
        
        Результаты поиска:
        {serp_text}
        """
        
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500,
            "temperature": 0.3
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            companies_text = result['choices'][0]['message']['content']
            companies = [c.strip() for c in companies_text.split(',') if c.strip()]
            return companies[:10]  # Максимум 10 компаний
        else:
            logger.error(f"Ошибка OpenAI API при извлечении компаний: {response.status_code}")
            return ["Компания 1", "Компания 2", "Компания 3"]
            
    except Exception as e:
        logger.error(f"Ошибка извлечения компаний: {e}")
        return ["Компания 1", "Компания 2", "Компания 3"]

async def update_serp_data_direct(db: AsyncSession, group_id: Optional[uuid.UUID] = None):
    """Прямое обновление SERP данных без воркера"""
    try:
        logger.info("🚀 Запуск прямого обновления SERP данных")
        
        # Получаем активные слова
        words_query = select(Word).where(Word.status == 1)
        if group_id:
            words_query = words_query.where(Word.group_id == group_id)
        
        words_result = await db.execute(words_query)
        words = list(words_result.scalars().all())
        
        # Получаем активные LLM
        llms_result = await db.execute(select(LLM).where(LLM.is_active == 1))
        llms = list(llms_result.scalars().all())
        
        logger.info(f"Найдено {len(words)} слов и {len(llms)} LLM для обработки")
        
        processed_count = 0
        
        for word in words:
            for llm in llms:
                try:
                    # Проверяем, нужно ли обновлять данные
                    existing_serp = await db.scalar(
                        select(WordSerp).where(
                            and_(
                                WordSerp.word_id == word.uuid,
                                WordSerp.llm_id == llm.uuid
                            )
                        )
                    )
                    
                    # Обновляем если данных нет или они старше 14 дней
                    should_update = False
                    if not existing_serp:
                        should_update = True
                    elif existing_serp.updated_at < datetime.utcnow() - timedelta(days=14):
                        should_update = True
                    
                    if should_update:
                        logger.info(f"Обновление SERP для слова '{word.name}' и LLM '{llm.name}'")
                        
                        # Получаем SERP данные
                        if llm.name.lower() == "openai":
                            serp_text = await get_serp_from_openai_direct(word.name)
                        else:
                            # Для других LLM используем моковые данные
                            serp_text = f"Моковые результаты для '{word.name}' от {llm.name}: 1. Результат 1, 2. Результат 2"
                        
                        # Сохраняем или обновляем SERP данные
                        if existing_serp:
                            existing_serp.serp_text = serp_text
                            existing_serp.updated_at = datetime.utcnow()
                        else:
                            new_serp = WordSerp(
                                word_id=word.uuid,
                                llm_id=llm.uuid,
                                serp_text=serp_text,
                                created_at=datetime.utcnow(),
                                updated_at=datetime.utcnow()
                            )
                            db.add(new_serp)
                        
                        # Извлекаем компании
                        companies = await extract_companies_from_serp_direct(serp_text)
                        
                        # Сохраняем компании
                        for company_name in companies:
                            existing_company = await db.scalar(
                                select(Company).where(Company.name == company_name)
                            )
                            if not existing_company:
                                new_company = Company(
                                    name=company_name,
                                    created_at=datetime.utcnow()
                                )
                                db.add(new_company)
                        
                        processed_count += 1
                        
                        # Коммитим каждые 10 обработанных пар
                        if processed_count % 10 == 0:
                            await db.commit()
                            logger.info(f"Обработано {processed_count} пар слово-LLM")
                    
                except Exception as e:
                    logger.error(f"Ошибка обработки слова '{word.name}' с LLM '{llm.name}': {e}")
                    continue
        
        # Финальный коммит
        await db.commit()
        logger.info(f"✅ Обновление SERP данных завершено. Обработано {processed_count} пар")
        
    except Exception as e:
        logger.error(f"Ошибка прямого обновления SERP данных: {e}")
        await db.rollback()
        raise

# Настройка логирования и мониторинга
setup_logging()
if settings.sentry_dsn:
    setup_sentry()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    logger.info(" Starting SEO Analyzer API...")
    
    # Проверяем соединение с базой данных
    if await check_database_connection():
        logger.info("Database connection established")
    else:
        logger.warning("Database connection failed - starting without DB")
        # Не останавливаем сервер, просто предупреждаем
    
    # Инициализируем базу данных (только если подключение успешно)
    try:
        await init_database()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}")
    
    # Инициализируем LLM сервис
    available_providers = llm_service.get_available_providers()
    logger.info(f"LLM Service initialized with providers: {available_providers}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down SEO Analyzer API...")
    await close_database()
    logger.info("Database connections closed")

app = FastAPI(
    title="SEO Analyzer API",
    description="API для анализа SEO ключевых слов с интеграцией LLM",
    version="1.0.0",
    lifespan=lifespan
)

# Добавляем middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=settings.allowed_hosts or ["*"]
)

# CORS настройки для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить все домены
    allow_credentials=False,  # Отключить credentials для безопасности при allow_origins=["*"]
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# === АВТОРИЗАЦИЯ ===

@app.post("/api/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Регистрация нового пользователя"""
    # Проверяем, существует ли пользователь
    existing_user = await db.scalar(select(User).where(User.email == user_data.email))
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует"
        )
    
    # Создаем нового пользователя
    hashed_password = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        password=hashed_password
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user

@app.post("/api/auth/login", response_model=Token)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Авторизация пользователя"""
    user = await db.scalar(select(User).where(User.email == user_data.email))
    
    if not user or not verify_password(user_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль"
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Получение информации о текущем пользователе"""
    return current_user

# === ГРУППЫ СЛОВ ===

@app.get("/api/word-groups", response_model=List[WordGroupResponse])
async def get_word_groups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение всех групп слов пользователя"""
    result = await db.execute(select(WordGroup).where(WordGroup.user_id == current_user.uuid))
    return result.scalars().all()

@app.post("/api/word-groups", response_model=WordGroupResponse)
async def create_word_group(
    group_data: WordGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Создание новой группы слов"""
    new_group = WordGroup(name=group_data.name, user_id=current_user.uuid)
    db.add(new_group)
    await db.commit()
    await db.refresh(new_group)
    return new_group

@app.put("/api/word-groups/{group_id}", response_model=WordGroupResponse)
async def update_word_group(
    group_id: uuid.UUID,
    group_data: WordGroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Обновление группы слов"""
    group = await db.scalar(select(WordGroup).where(
        WordGroup.uuid == group_id,
        WordGroup.user_id == current_user.uuid
    ))
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    
    group.name = group_data.name
    await db.commit()
    await db.refresh(group)
    return group

@app.delete("/api/word-groups/{group_id}")
async def delete_word_group(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Удаление группы слов"""
    group = await db.scalar(select(WordGroup).where(
        WordGroup.uuid == group_id,
        WordGroup.user_id == current_user.uuid
    ))
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    
    await db.delete(group)
    await db.commit()
    return {"message": "Группа удалена"}

# === СЛОВА ===

@app.get("/api/words", response_model=List[WordResponse])
async def get_words(
    group_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение всех слов или слов определенной группы"""
    query = select(Word).where(Word.status == 1)
    if group_id:
        query = query.where(Word.group_id == group_id)
    
    result = await db.execute(query)
    return result.scalars().all()

@app.post("/api/words", response_model=WordResponse)
async def create_word(
    word_data: WordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Создание нового слова"""
    new_word = Word(
        name=word_data.name,
        group_id=word_data.group_id
    )
    db.add(new_word)
    await db.commit()
    await db.refresh(new_word)
    return new_word

@app.put("/api/words/{word_id}", response_model=WordResponse)
async def update_word(
    word_id: uuid.UUID,
    word_data: WordUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Обновление слова"""
    word = await db.scalar(select(Word).where(Word.uuid == word_id))
    if not word:
        raise HTTPException(status_code=404, detail="Слово не найдено")
    
    if word_data.name is not None:
        word.name = word_data.name
    if word_data.group_id is not None:
        word.group_id = word_data.group_id
    if word_data.status is not None:
        word.status = word_data.status
    
    await db.commit()
    await db.refresh(word)
    return word

@app.delete("/api/words/{word_id}")
async def delete_word(
    word_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Мягкое удаление слова"""
    word = await db.scalar(select(Word).where(Word.uuid == word_id))
    if not word:
        raise HTTPException(status_code=404, detail="Слово не найдено")
    
    word.status = 0  # Мягкое удаление
    await db.commit()
    return {"message": "Слово удалено"}

# === LLM ПРОВАЙДЕРЫ ===

@app.get("/api/llm", response_model=List[LLMResponse])
async def get_llm_providers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение всех LLM провайдеров"""
    result = await db.execute(select(LLM))
    return result.scalars().all()

@app.post("/api/llm", response_model=LLMResponse)
async def create_llm_provider(
    llm_data: LLMCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Создание нового LLM провайдера"""
    new_llm = LLM(
        name=llm_data.name,
        api_url=llm_data.api_url,
        api_key=llm_data.api_key
    )
    db.add(new_llm)
    await db.commit()
    await db.refresh(new_llm)
    return new_llm

# === АНАЛИТИКА ===

async def _get_word_analytics_data(
    word_id: uuid.UUID,
    db: AsyncSession
) -> WordAnalytics:
    """Внутренняя функция для получения аналитики по слову"""
    try:
        word = await db.scalar(select(Word).where(Word.uuid == word_id))
        if not word:
            raise HTTPException(status_code=404, detail="Слово не найдено")
        
        # Получаем SERP результаты
        serp_results = await db.execute(
            select(WordSerp).where(WordSerp.word_id == word_id)
        )
        serp_list = list(serp_results.scalars().all())
        
        # Получаем компании (без JOIN для упрощения)
        companies_list = []
        if serp_list:
            for serp in serp_list:
                companies_result = await db.execute(
                    select(Company).where(Company.serp_id == serp.uuid)
                )
                companies_list.extend(companies_result.scalars().all())
        
        return WordAnalytics(
            word=word,
            serp_results=serp_list,
            companies=companies_list
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения аналитики по слову {word_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения аналитики: {str(e)}")

@app.get("/api/analytics/word/{word_id}")
async def get_word_analytics(
    word_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение аналитики по конкретному слову"""
    try:
        logger.info(f"Получение аналитики для слова: {word_id}")
        
        # Получаем слово
        word = await db.scalar(select(Word).where(Word.uuid == word_id))
        if not word:
            logger.warning(f"Слово {word_id} не найдено")
            return {"error": "Слово не найдено"}
        
        logger.info(f"Слово найдено: {word.name}")
        
        # Получаем SERP результаты
        serp_results = await db.execute(select(WordSerp).where(WordSerp.word_id == word_id))
        serp_list = list(serp_results.scalars().all())
        
        # Получаем компании
        companies_list = []
        for serp in serp_list:
            companies_result = await db.execute(select(Company).where(Company.serp_id == serp.uuid))
            companies_list.extend(companies_result.scalars().all())
        
        logger.info(f"Найдено SERP: {len(serp_list)}, компаний: {len(companies_list)}")
        
        # Возвращаем простую структуру
        return {
            "word": {
                "uuid": str(word.uuid),
                "name": word.name,
                "group_id": str(word.group_id) if word.group_id else None,
                "status": word.status,
                "create_time": word.create_time.isoformat() if word.create_time else None
            },
            "serp_results": [
                {
                    "uuid": str(serp.uuid),
                    "content": serp.content[:100] + "..." if len(serp.content) > 100 else serp.content,
                    "llm_id": str(serp.llm_id) if serp.llm_id else None,
                    "create_time": serp.create_time.isoformat() if serp.create_time else None
                } for serp in serp_list
            ],
            "companies": [
                {
                    "uuid": str(company.uuid),
                    "name": company.name,
                    "serp_id": str(company.serp_id) if company.serp_id else None
                } for company in companies_list
            ]
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения аналитики по слову {word_id}: {e}")
        import traceback
        traceback.print_exc()
        return {"error": f"Ошибка: {str(e)}"}

@app.post("/api/analytics/start")
async def start_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Запуск общей аналитики"""
    try:
        # Прямое обновление SERP данных без воркера
        await update_serp_data_direct(db)
        return {"message": "Аналитика запущена", "status": "started"}
    except Exception as e:
        logger.error(f"Ошибка запуска аналитики: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка запуска аналитики: {str(e)}")

@app.post("/api/analytics/group/start")
async def start_group_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Запуск аналитики для всех групп"""
    try:
        # Прямое обновление SERP данных без воркера
        await update_serp_data_direct(db)
        return {"message": "Аналитика групп запущена", "status": "started"}
    except Exception as e:
        logger.error(f"Ошибка запуска аналитики групп: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка запуска аналитики групп: {str(e)}")

@app.post("/api/analytics/group/{group_id}/start")
async def start_group_analytics_by_id(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Запуск аналитики для конкретной группы"""
    try:
        # Проверяем существование группы
        group = await db.scalar(select(WordGroup).where(WordGroup.uuid == group_id))
        if not group:
            raise HTTPException(status_code=404, detail="Группа не найдена")
        
        # Прямое обновление SERP данных без воркера
        await update_serp_data_direct(db, group_id=group_id)
        return {"message": f"Аналитика для группы {group.name} запущена", "status": "started"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка запуска аналитики для группы {group_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка запуска аналитики для группы")

@app.get("/api/analytics/group/{group_id}")
async def get_group_analytics(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение аналитики по группе слов"""
    try:
        logger.info(f"Получение аналитики для группы: {group_id}")
        
        # Получаем группу
        group = await db.scalar(select(WordGroup).where(WordGroup.uuid == group_id))
        if not group:
            logger.warning(f"Группа {group_id} не найдена")
            return {"error": "Группа не найдена"}
        
        logger.info(f"Группа найдена: {group.name}")
        
        # Получаем слова в группе
        words_result = await db.execute(select(Word).where(Word.group_id == group_id))
        words_list = list(words_result.scalars().all())
        
        logger.info(f"Найдено слов в группе: {len(words_list)}")
        
        # Формируем аналитику по каждому слову
        words_analytics = []
        for word in words_list:
            # Получаем SERP для каждого слова
            serp_results = await db.execute(select(WordSerp).where(WordSerp.word_id == word.uuid))
            serp_list = list(serp_results.scalars().all())
            
            # Получаем компании
            companies_list = []
            for serp in serp_list:
                companies_result = await db.execute(select(Company).where(Company.serp_id == serp.uuid))
                companies_list.extend(companies_result.scalars().all())
            
            words_analytics.append({
                "word": {
                    "uuid": str(word.uuid),
                    "name": word.name,
                    "status": word.status,
                    "create_time": word.create_time.isoformat() if word.create_time else None
                },
                "serp_count": len(serp_list),
                "companies_count": len(companies_list)
            })
        
        return {
            "group": {
                "uuid": str(group.uuid),
                "name": group.name
            },
            "words": words_analytics,
            "words_count": len(words_list)
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения аналитики по группе {group_id}: {e}")
        import traceback
        traceback.print_exc()
        return {"error": f"Ошибка: {str(e)}"}


@app.post("/api/serp/update")
async def update_serp_data(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Запуск цикла обновления SERP данных"""
    try:
        # Прямое обновление SERP данных без воркера
        await update_serp_data_direct(db)
        return {"message": "Цикл обновления SERP данных запущен"}
    except Exception as e:
        logger.error(f"Ошибка обновления SERP данных: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка обновления SERP данных: {str(e)}")

# === СТАТИСТИКА ===

@app.get("/api/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение общей статистики"""
    # Подсчет различных сущностей
    words_count = await db.scalar(select(func.count(Word.uuid)).where(Word.status == 1))
    groups_count = await db.scalar(select(func.count(WordGroup.uuid)))
    serp_count = await db.scalar(select(func.count(WordSerp.uuid)))
    companies_count = await db.scalar(select(func.count(Company.uuid)))
    
    return {
        "words_count": words_count,
        "groups_count": groups_count,
        "serp_results_count": serp_count,
        "companies_count": companies_count
    }

# === BRAND MONITORING ===

@app.post("/api/brand-projects", response_model=BrandProjectResponse, status_code=201)
async def create_brand_project(
    project_data: BrandProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Логирование для отладки
        logger.info(f"Создание brand проекта с word_group_id: {project_data.word_group_id}")
        
        # Проверяем существование группы слов, если указана
        if project_data.word_group_id:
            group_result = await db.execute(
                select(WordGroup).where(WordGroup.uuid == project_data.word_group_id)
            )
            word_group = group_result.scalar_one_or_none()
            if not word_group:
                logger.warning(f"Группа слов с ID {project_data.word_group_id} не найдена")
                raise HTTPException(status_code=400, detail="Word group not found")
            logger.info(f"Найдена группа слов: {word_group.name}")
        
        # 1. Создаём проект
        brand_project = BrandProject(
            name=project_data.name,
            brand_name=project_data.brand_name,
            brand_description=project_data.brand_description,
            keywords_count=project_data.keywords_count,
            user_id=current_user.uuid,
            word_group_id=project_data.word_group_id  # Привязка к группе слов
        )
        db.add(brand_project)
        await db.flush()
        
        # Логирование после создания
        logger.info(f"Brand проект создан с UUID: {brand_project.uuid}, word_group_id: {brand_project.word_group_id}")

        # 2. Создаём конкурентов (если переданы)
        competitors = []
        for competitor_name in (project_data.competitors or [])[:10]:
            competitor = Competitor(
                name=competitor_name.strip(),
                project_id=brand_project.uuid
            )
            db.add(competitor)
            competitors.append(competitor)

        await db.commit()
        await db.refresh(brand_project)

        # 3. Загружаем конкурентов
        competitors_result = await db.execute(
            select(Competitor).where(Competitor.project_id == brand_project.uuid)
        )
        competitors_db = competitors_result.scalars().all()

        # 4. Формируем dict под BrandProjectResponse (Pydantic v2)
        response = {
            "uuid": brand_project.uuid,
            "name": brand_project.name,
            "brand_name": brand_project.brand_name,
            "brand_description": brand_project.brand_description,
            "keywords_count": brand_project.keywords_count,
            "user_id": brand_project.user_id,
            "word_group_id": brand_project.word_group_id,
            "create_time": brand_project.create_time,
            "status": brand_project.status,
            "competitors": [
                {
                    "uuid": c.uuid,
                    "name": c.name,
                    "create_time": c.create_time
                }
                for c in competitors_db
            ]
        }

        # Логирование ответа
        logger.info(f"Отправляем ответ с word_group_id: {response['word_group_id']}")

        # 5. Возвращаем через модель Pydantic v2 (если не совпадёт — лови ошибку в логе!)
        return BrandProjectResponse.model_validate(response)

    except Exception as e:
        await db.rollback()
        logger.error(f"Ошибка создания brand проекта: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.put("/api/brand-projects/{project_id}", response_model=BrandProjectResponse)
async def update_brand_project(
    project_id: uuid.UUID,
    project_data: BrandProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Логирование для отладки
        logger.info(f"Обновление brand проекта {project_id} с word_group_id: {project_data.word_group_id}")
        
        # 1. Найти проект
        project_result = await db.execute(
            select(BrandProject).where(
                BrandProject.uuid == project_id,
                BrandProject.user_id == current_user.uuid
            )
        )
        brand_project = project_result.scalar_one_or_none()
        
        if not brand_project:
            raise HTTPException(status_code=404, detail="Brand project not found")
        
        logger.info(f"Текущий word_group_id проекта: {brand_project.word_group_id}")
        
        # Проверяем существование группы слов, если указана
        if project_data.word_group_id:
            group_result = await db.execute(
                select(WordGroup).where(WordGroup.uuid == project_data.word_group_id)
            )
            word_group = group_result.scalar_one_or_none()
            if not word_group:
                logger.warning(f"Группа слов с ID {project_data.word_group_id} не найдена")
                raise HTTPException(status_code=400, detail="Word group not found")
            logger.info(f"Найдена группа слов для обновления: {word_group.name}")
        
        # 2. Обновить поля
        if project_data.name is not None:
            brand_project.name = project_data.name
        if project_data.brand_name is not None:
            brand_project.brand_name = project_data.brand_name
        if project_data.brand_description is not None:
            brand_project.brand_description = project_data.brand_description
        if project_data.keywords_count is not None:
            brand_project.keywords_count = project_data.keywords_count
        if project_data.word_group_id is not None:
            brand_project.word_group_id = project_data.word_group_id
        
        # 3. Обновить конкурентов, если переданы
        if project_data.competitors is not None:
            # Удаляем старых конкурентов
            existing_competitors = await db.execute(
                select(Competitor).where(Competitor.project_id == brand_project.uuid)
            )
            for competitor in existing_competitors.scalars().all():
                await db.delete(competitor)
            
            # Добавляем новых конкурентов
            for competitor_name in project_data.competitors[:10]:
                if competitor_name.strip():
                    competitor = Competitor(
                        name=competitor_name.strip(),
                        project_id=brand_project.uuid
                    )
                    db.add(competitor)
            
        await db.commit()
        await db.refresh(brand_project)
        
        # Логирование после обновления
        logger.info(f"Brand проект обновлен, новый word_group_id: {brand_project.word_group_id}")
        
        # 3. Загрузить конкурентов
        competitors_result = await db.execute(
            select(Competitor).where(Competitor.project_id == brand_project.uuid)
        )
        competitors_db = competitors_result.scalars().all()
        
        # 4. Формировать ответ
        response = {
            "uuid": brand_project.uuid,
            "name": brand_project.name,
            "brand_name": brand_project.brand_name,
            "brand_description": brand_project.brand_description,
            "keywords_count": brand_project.keywords_count,
            "user_id": brand_project.user_id,
            "word_group_id": brand_project.word_group_id,
            "create_time": brand_project.create_time,
            "status": brand_project.status,
            "competitors": [
                {
                    "uuid": c.uuid,
                    "name": c.name,
                    "create_time": c.create_time
                }
                for c in competitors_db
            ]
        }
        
        # Логирование ответа для PUT
        logger.info(f"Отправляем ответ PUT с word_group_id: {response['word_group_id']}")
        
        return BrandProjectResponse.model_validate(response)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Ошибка обновления brand проекта: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.get("/api/brand-projects", response_model=List[BrandProjectResponse])
async def get_brand_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    projects_result = await db.execute(
        select(BrandProject).where(
            BrandProject.user_id == current_user.uuid,
            BrandProject.status == 1
        )
    )
    projects = projects_result.scalars().all()
    responses = []
    for project in projects:
        competitors_result = await db.execute(
            select(Competitor).where(Competitor.project_id == project.uuid)
        )
        competitors = competitors_result.scalars().all()
        competitors_resp = [
            CompetitorResponse(
                uuid=c.uuid,
                name=c.name,
                create_time=c.create_time
            ) for c in competitors
        ]
        responses.append(BrandProjectResponse.model_validate({
            "uuid": project.uuid,
            "name": project.name,
            "brand_name": project.brand_name,
            "brand_description": project.brand_description,
            "keywords_count": project.keywords_count,
            "user_id": project.user_id,
            "word_group_id": project.word_group_id,
            "create_time": project.create_time,
            "status": project.status,
            "competitors": competitors_resp,
        }))
    return responses


@app.get("/api/brand-projects/{project_id}", response_model=BrandProjectResponse)
async def get_brand_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = await db.scalar(
        select(BrandProject)
        .where(BrandProject.uuid == project_id)
        .where(BrandProject.user_id == current_user.uuid)
    )
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")

    competitors_result = await db.execute(
        select(Competitor).where(Competitor.project_id == project.uuid)
    )
    competitors = competitors_result.scalars().all()
    competitors_resp = [
        CompetitorResponse(
            uuid=c.uuid,
            name=c.name,
            create_time=c.create_time
        ) for c in competitors
    ]

    return BrandProjectResponse.model_validate({
        "uuid": project.uuid,
        "name": project.name,
        "brand_name": project.brand_name,
        "brand_description": project.brand_description,
        "keywords_count": project.keywords_count,
        "user_id": project.user_id,
        "word_group_id": project.word_group_id,
        "create_time": project.create_time,
        "status": project.status,
        "competitors": competitors_resp,
    })

@app.get("/api/brand-projects/{project_id}/analytics")
async def get_brand_analytics(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Проверяем существование проекта
        project = await db.scalar(
            select(BrandProject)
            .where(BrandProject.uuid == project_id)
            .where(BrandProject.user_id == current_user.uuid)
        )
        if not project:
            raise HTTPException(status_code=404, detail="Проект не найден")

        # Получаем все упоминания для проекта
        mentions_result = await db.execute(
            select(BrandMention).where(BrandMention.project_id == project_id)
        )
        mentions_list = mentions_result.scalars().all()

        total_queries = len(mentions_list)
        brand_mentions = sum(1 for m in mentions_list if m.brand_mentioned == 1)
        competitor_mentions = sum(1 for m in mentions_list if m.competitor_mentioned == 1)

        competitor_stats = {}
        for mention in mentions_list:
            if mention.mentioned_competitor:
                competitor_stats[mention.mentioned_competitor] = competitor_stats.get(mention.mentioned_competitor, 0) + 1
        top_competitors = [
            {"name": name, "mentions": count}
            for name, count in sorted(competitor_stats.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

        # Если тебе нужна схема — BrandAnalytics (как у тебя в schemas.py)
        return {
            "project_name": project.name,
            "brand_name": project.brand_name,
            "total_queries": total_queries,
            "brand_mentions": brand_mentions,
            "competitor_mentions": competitor_mentions,
            "brand_visibility_percentage": (brand_mentions / total_queries * 100) if total_queries > 0 else 0,
            "competitor_visibility_percentage": (competitor_mentions / total_queries * 100) if total_queries > 0 else 0,
            "top_competitors": top_competitors,
            "recent_mentions": [
                {
                    "uuid": str(m.uuid),
                    "serp_id": str(m.serp_id),
                    "brand_mentioned": m.brand_mentioned,
                    "competitor_mentioned": m.competitor_mentioned,
                    "mentioned_competitor": m.mentioned_competitor,
                    "brand_position": m.brand_position,
                    "competitor_position": m.competitor_position,
                    "analysis_confidence": m.analysis_confidence,
                    "create_time": m.create_time.isoformat() if m.create_time else None,
                }
                for m in mentions_list[:10]
            ]
        }
        # Можно завернуть это в BrandAnalytics.model_validate(...), если хочешь строго

    except Exception as e:
        logger.error(f"Ошибка получения brand аналитики: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения аналитики: {str(e)}")


@app.delete("/api/brand-projects/{project_id}")
async def delete_brand_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = await db.scalar(
        select(BrandProject)
        .where(BrandProject.uuid == project_id)
        .where(BrandProject.user_id == current_user.uuid)
    )
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")

    # Мягкое удаление
    project.status = 0
    await db.commit()
    return {"message": "Проект удален"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
