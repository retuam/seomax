"""
Скрипт для инициализации базы данных и создания тестовых данных
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from database import engine, Base, get_async_session
from models import User, WordGroup, Word, LLM, WordSerp, Company
from auth import hash_password

async def create_tables():
    """Создание всех таблиц"""
    async with engine.begin() as conn:
        # Удаляем все таблицы (осторожно!)
        # await conn.run_sync(Base.metadata.drop_all)
        
        # Создаем все таблицы
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Таблицы созданы успешно")

async def create_initial_data():
    """Создание начальных данных"""
    async with get_async_session() as db:
        try:
            # Создаем тестового пользователя
            test_user = User(
                email="admin@example.com",
                password=hash_password("admin123")
            )
            db.add(test_user)
            
            # Создаем LLM провайдеров
            llm_providers = [
                LLM(name="openai", api_url="https://api.openai.com/v1/chat/completions"),
                LLM(name="grok", api_url="https://api.grok.com/v1/chat/completions"),
                LLM(name="gemini", api_url="https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent")
            ]
            
            for llm in llm_providers:
                db.add(llm)
            
            # Создаем тестовые группы слов
            groups = [
                WordGroup(name="Технологии"),
                WordGroup(name="Маркетинг"),
                WordGroup(name="E-commerce")
            ]
            
            for group in groups:
                db.add(group)
            
            await db.flush()  # Получаем ID для связей
            
            # Создаем тестовые слова
            test_words = [
                Word(name="искусственный интеллект", group_id=groups[0].uuid),
                Word(name="машинное обучение", group_id=groups[0].uuid),
                Word(name="веб разработка", group_id=groups[0].uuid),
                Word(name="SEO оптимизация", group_id=groups[1].uuid),
                Word(name="контент маркетинг", group_id=groups[1].uuid),
                Word(name="интернет магазин", group_id=groups[2].uuid),
                Word(name="онлайн продажи", group_id=groups[2].uuid)
            ]
            
            for word in test_words:
                db.add(word)
            
            await db.commit()
            print("✅ Начальные данные созданы успешно")
            print("📧 Тестовый пользователь: admin@example.com / admin123")
            
        except Exception as e:
            print(f"❌ Ошибка создания данных: {e}")
            await db.rollback()

async def main():
    """Главная функция инициализации"""
    print("🚀 Инициализация базы данных...")
    
    try:
        await create_tables()
        await create_initial_data()
        print("✅ Инициализация завершена успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")

if __name__ == "__main__":
    asyncio.run(main())
