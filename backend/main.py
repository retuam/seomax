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
from llm_worker import llm_worker
from llm_service_modern import llm_service

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
    """Получение всех групп слов"""
    result = await db.execute(select(WordGroup))
    return result.scalars().all()

@app.post("/api/word-groups", response_model=WordGroupResponse)
async def create_word_group(
    group_data: WordGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Создание новой группы слов"""
    new_group = WordGroup(name=group_data.name)
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
    group = await db.scalar(select(WordGroup).where(WordGroup.uuid == group_id))
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
    group = await db.scalar(select(WordGroup).where(WordGroup.uuid == group_id))
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
        
        # Формируем аналитику по каждому слову с использованием только последнего среза
        words_analytics = []
        for word in words_list:
            # Получаем ТОЛЬКО последний SERP для каждого слова
            latest_serp = await db.scalar(
                select(WordSerp)
                .where(WordSerp.word_id == word.uuid)
                .order_by(WordSerp.create_time.desc())
                .limit(1)
            )
            
            # Получаем предыдущий SERP для сравнения
            previous_serp = await db.scalar(
                select(WordSerp)
                .where(WordSerp.word_id == word.uuid)
                .order_by(WordSerp.create_time.desc())
                .offset(1)
                .limit(1)
            )
            
            # Данные последнего среза
            latest_companies_count = 0
            latest_brand_mentions = 0
            latest_competitor_mentions = 0
            last_analysis_date = None
            
            if latest_serp:
                # Компании из последнего среза
                latest_companies_result = await db.execute(
                    select(Company).where(Company.serp_id == latest_serp.uuid)
                )
                latest_companies_count = len(list(latest_companies_result.scalars().all()))
                
                # Brand mentions из последнего среза
                from models import BrandMention
                latest_brand_result = await db.execute(
                    select(BrandMention).where(BrandMention.serp_id == latest_serp.uuid)
                )
                brand_mentions_list = list(latest_brand_result.scalars().all())
                latest_brand_mentions = sum(1 for bm in brand_mentions_list if bm.brand_mentioned == 1)
                latest_competitor_mentions = sum(1 for bm in brand_mentions_list if bm.competitor_mentioned == 1)
                last_analysis_date = latest_serp.create_time
            
            # Данные предыдущего среза для сравнения
            previous_companies_count = 0
            previous_brand_mentions = 0
            
            if previous_serp:
                previous_companies_result = await db.execute(
                    select(Company).where(Company.serp_id == previous_serp.uuid)
                )
                previous_companies_count = len(list(previous_companies_result.scalars().all()))
                
                previous_brand_result = await db.execute(
                    select(BrandMention).where(BrandMention.serp_id == previous_serp.uuid)
                )
                previous_brand_list = list(previous_brand_result.scalars().all())
                previous_brand_mentions = sum(1 for bm in previous_brand_list if bm.brand_mentioned == 1)
            
            words_analytics.append({
                "word": {
                    "uuid": str(word.uuid),
                    "name": word.name,
                    "status": word.status,
                    "create_time": word.create_time.isoformat() if word.create_time else None
                },
                "latest_companies_count": latest_companies_count,
                "latest_brand_mentions": latest_brand_mentions,
                "latest_competitor_mentions": latest_competitor_mentions,
                "previous_companies_count": previous_companies_count,
                "previous_brand_mentions": previous_brand_mentions,
                "companies_change": latest_companies_count - previous_companies_count,
                "brand_mentions_change": latest_brand_mentions - previous_brand_mentions,
                "last_analysis_date": last_analysis_date.isoformat() if last_analysis_date else None
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

# === ВОРКЕР ===

@app.post("/api/worker/run-cycle")
async def run_worker_cycle(
    current_user: User = Depends(get_current_user)
):
    """Запуск цикла обновления SERP данных"""
    # Запускаем воркер асинхронно
    import asyncio
    asyncio.create_task(llm_worker.run_worker_cycle())
    return {"message": "Цикл обновления SERP данных запущен в фоне"}

@app.post("/api/analytics/group/{group_id}/start")
async def start_group_analysis(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Принудительный запуск анализа для конкретной группы слов"""
    try:
        logger.info(f"Запуск принудительного анализа для группы: {group_id}")
        
        # Проверяем что группа существует
        group = await db.scalar(select(WordGroup).where(WordGroup.uuid == group_id))
        if not group:
            return {"error": "Группа не найдена"}
        
        # Получаем слова в группе
        words_result = await db.execute(select(Word).where(Word.group_id == group_id))
        words_list = list(words_result.scalars().all())
        
        if not words_list:
            return {"error": "В группе нет слов для анализа"}
        
        # Получаем активные LLM провайдеры
        llms_result = await db.execute(select(LLM).where(LLM.is_active == 1))
        llms_list = list(llms_result.scalars().all())
        
        if not llms_list:
            return {"error": "Нет активных LLM провайдеров"}
        
        # Запускаем анализ для каждого слова с каждым LLM
        from llm_worker_sync import sync_llm_worker
        import asyncio
        
        async def run_group_analysis():
            """Асинхронная функция для запуска анализа группы"""
            processed_count = 0
            
            # Используем синхронный воркер в отдельном потоке
            import threading
            
            def sync_analysis():
                nonlocal processed_count
                with sync_llm_worker.SessionLocal() as db_session:
                    for word in words_list:
                        for llm in llms_list:
                            # Принудительно обновляем - удаляем проверку на 2 недели
                            logger.info(f"Принудительный анализ для '{word.name}' с {llm.name}")
                            
                            # Получаем SERP данные
                            if llm.name.lower() == "openai" and hasattr(sync_llm_worker, 'get_serp_from_openai_sync'):
                                serp_content = sync_llm_worker.get_serp_from_openai_sync(word.name)
                            else:
                                serp_content = sync_llm_worker.get_mock_serp(word.name, llm.name)
                            
                            # Сохраняем новый SERP
                            from datetime import datetime, timezone
                            word_serp = WordSerp(
                                content=serp_content,
                                llm_id=llm.uuid,
                                word_id=word.uuid,
                                create_time=datetime.now(timezone.utc)
                            )
                            
                            db_session.add(word_serp)
                            db_session.flush()
                            
                            # Извлекаем компании
                            companies = sync_llm_worker.extract_companies_simple(serp_content)
                            for company_name in companies:
                                company = Company(
                                    name=company_name,
                                    serp_id=word_serp.uuid
                                )
                                db_session.add(company)
                            
                            db_session.commit()
                            processed_count += 1
                            
                            logger.info(f"Создан новый SERP для '{word.name}' с {llm.name}, извлечено {len(companies)} компаний")
            
            # Запускаем в отдельном потоке
            thread = threading.Thread(target=sync_analysis)
            thread.start()
            thread.join()
            
            logger.info(f"✅ Принудительный анализ завершен. Обработано {processed_count} комбинаций")
        
        # Запускаем анализ асинхронно
        asyncio.create_task(run_group_analysis())
        
        return {
            "message": f"Принудительный анализ запущен для группы '{group.name}'",
            "group_id": str(group_id),
            "words_count": len(words_list),
            "llm_count": len(llms_list),
            "total_combinations": len(words_list) * len(llms_list)
        }
        
    except Exception as e:
        logger.error(f"Ошибка запуска принудительного анализа: {e}")
        return {"error": f"Ошибка запуска анализа: {str(e)}"}

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
        # 1. Создаём проект
        brand_project = BrandProject(
            name=project_data.name,
            brand_name=project_data.brand_name,
            brand_description=project_data.brand_description,
            keywords_count=project_data.keywords_count,
            user_id=current_user.uuid
        )
        db.add(brand_project)
        await db.flush()

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

        # 5. Возвращаем через модель Pydantic v2 (если не совпадёт — лови ошибку в логе!)
        return BrandProjectResponse.model_validate(response)

    except Exception as e:
        await db.rollback()
        logger.error(f"Ошибка создания brand проекта: {e}")
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
