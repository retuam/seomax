import asyncio
import asyncpg
from config_simple import settings

async def init_database():
    """Простая инициализация базы данных без SQLAlchemy"""
    print("🚀 Инициализация базы данных...")
    
    # Подключаемся к базе данных
    conn = await asyncpg.connect(
        settings.database_url.replace("postgresql+asyncpg://", "postgresql://"),
        statement_cache_size=0  # Отключаем prepared statements
    )
    
    try:
        # Создаем таблицы если их нет
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR UNIQUE NOT NULL,
                password VARCHAR NOT NULL,
                create_time TIMESTAMP DEFAULT NOW(),
                status SMALLINT DEFAULT 1
            );
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS word_groups (
                uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR NOT NULL
            );
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS words (
                uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR NOT NULL,
                group_id UUID REFERENCES word_groups(uuid) ON DELETE CASCADE,
                create_time TIMESTAMP DEFAULT NOW(),
                update_time TIMESTAMP,
                delete_time TIMESTAMP,
                status SMALLINT DEFAULT 1
            );
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS llm (
                uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR UNIQUE NOT NULL,
                api_url VARCHAR,
                api_key VARCHAR,
                is_active SMALLINT DEFAULT 1
            );
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS word_serp (
                uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                content TEXT NOT NULL,
                llm_id UUID REFERENCES llm(uuid) ON DELETE CASCADE,
                word_id UUID REFERENCES words(uuid) ON DELETE CASCADE,
                create_time TIMESTAMP DEFAULT NOW()
            );
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR NOT NULL,
                serp_id UUID REFERENCES word_serp(uuid) ON DELETE SET NULL,
                create_time TIMESTAMP DEFAULT NOW()
            );
        """)
        
        print("✅ Таблицы созданы успешно")
        
        # Добавляем базовые LLM провайдеры
        # Сначала проверяем, есть ли уже записи
        existing = await conn.fetchval("SELECT COUNT(*) FROM llm")
        if existing == 0:
            await conn.execute("""
                INSERT INTO llm (name, api_url, api_key, is_active) 
                VALUES 
                    ('openai', 'https://api.openai.com/v1/chat/completions', NULL, 1),
                    ('grok', 'https://api.grok.com/v1/chat/completions', NULL, 1),
                    ('gemini', 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent', NULL, 1);
            """)
        
        print("✅ LLM провайдеры добавлены")
        print("✅ Инициализация завершена успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(init_database())
