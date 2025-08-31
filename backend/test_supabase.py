#!/usr/bin/env python3
"""
Тестовый скрипт для проверки подключения к Supabase
"""
import asyncio
import asyncpg
import psycopg2
from dotenv import load_dotenv
import os
import urllib.parse
import ssl
from typing import Optional

def create_ssl_context(insecure: bool = False) -> ssl.SSLContext:
    """Создает SSL контекст. По умолчанию с проверкой сертификата (использует certifi, если доступен).
    При insecure=True отключает проверку (только для локальных тестов, небезопасно для продакшна).
    """
    cafile: Optional[str] = None
    try:
        import certifi  # type: ignore
        cafile = certifi.where()
    except Exception:
        cafile = None
    ctx = ssl.create_default_context(cafile=cafile) if cafile else ssl.create_default_context()
    if insecure:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return ctx

# Загружаем переменные окружения
load_dotenv()

# Параметры подключения (оба варианта + SSL)
PROJECT_REF = "usshslzenyrubetvwenc"
DB_PASSWORD = "d93b4zd0ivn8a4G8"

SUPABASE_CONFIGS = [
    {
        "name": "Transaction Pooler (working)",
        # ВАЖНО: для pooler имя пользователя должно быть с project ref: postgres.<ref>
        "url": f"postgresql://postgres.{PROJECT_REF}:{DB_PASSWORD}@aws-0-eu-central-1.pooler.supabase.com:5432/postgres?sslmode=require"
    }
]

def test_sync_connection():
    """Тест синхронного подключения с psycopg2"""
    print("\n🔄 Тестируем синхронное подключение (psycopg2)...")
    
    for config in SUPABASE_CONFIGS:
        print(f"\n📡 Тестируем {config['name']}...")
        try:
            conn = psycopg2.connect(config['url'])
            cursor = conn.cursor()
            cursor.execute("SELECT NOW(), version();")
            result = cursor.fetchone()
            print(f"✅ {config['name']} - УСПЕШНО!")
            print(f"   Время: {result[0]}")
            print(f"   Версия: {result[1][:50]}...")
            cursor.close()
            conn.close()
            return config['url']  # Возвращаем рабочий URL
        except Exception as e:
            print(f"❌ {config['name']} - ОШИБКА: {e}")
            if "getaddrinfo failed" in str(e) or "could not translate host name" in str(e):
                print("   ↪️ Проблема DNS. Проверьте доступ к доменам supabase.co/ *.pooler.supabase.com, VPN/Firewall")
    
    return None

async def test_async_connection():
    """Тест асинхронного подключения с asyncpg"""
    print("\n🔄 Тестируем асинхронное подключение (asyncpg)...")
    
    for config in SUPABASE_CONFIGS:
        print(f"\n📡 Тестируем {config['name']}...")
        try:
            # Преобразуем URL для SQLAlchemy (async)
            async_url = config['url'].replace('postgresql://', 'postgresql+asyncpg://')
            
            # Парсим URL для asyncpg.connect
            import urllib.parse
            parsed = urllib.parse.urlparse(config['url'])
            
            try:
                conn = await asyncpg.connect(
                    host=parsed.hostname,
                    port=parsed.port,
                    database=parsed.path[1:],  # убираем '/' в начале
                    user=parsed.username,
                    password=parsed.password,
                    ssl=create_ssl_context(insecure=False)  # Верифицированный TLS
                )
            except Exception as ssl_err:
                if "CERTIFICATE_VERIFY_FAILED" in str(ssl_err):
                    print("   ⚠️ Ошибка проверки сертификата. Пробуем без проверки (локально, небезопасно)...")
                    conn = await asyncpg.connect(
                        host=parsed.hostname,
                        port=parsed.port,
                        database=parsed.path[1:],
                        user=parsed.username,
                        password=parsed.password,
                        ssl=create_ssl_context(insecure=True)  # Фолбэк без проверки
                    )
                else:
                    raise
            
            result = await conn.fetchrow("SELECT NOW(), version();")
            print(f"✅ {config['name']} - УСПЕШНО!")
            print(f"   Время: {result[0]}")
            print(f"   Версия: {result[1][:50]}...")
            await conn.close()
            return async_url  # Возвращаем рабочий URL для SQLAlchemy
        except Exception as e:
            print(f"❌ {config['name']} - ОШИБКА: {e}")
            if "getaddrinfo failed" in str(e) or "could not translate host name" in str(e):
                print("   ↪️ Проблема DNS. Проверьте доступ к доменам supabase.co/ *.pooler.supabase.com, VPN/Firewall")
    
    return None

async def test_tables(working_url: str):
    """Тест создания и проверки таблиц"""
    print("\n🔄 Тестируем создание таблиц...")
    
    try:
        # Используем проверенный рабочий URL (включая pooler)
        parsed = urllib.parse.urlparse(working_url)
        
        try:
            conn = await asyncpg.connect(
                host=parsed.hostname,
                port=parsed.port,
                database=parsed.path[1:],
                user=parsed.username,
                password=parsed.password,
                ssl=create_ssl_context(insecure=False)
            )
        except Exception as ssl_err:
            if "CERTIFICATE_VERIFY_FAILED" in str(ssl_err):
                print("   ⚠️ Ошибка проверки сертификата. Пробуем без проверки (локально, небезопасно)...")
                conn = await asyncpg.connect(
                    host=parsed.hostname,
                    port=parsed.port,
                    database=parsed.path[1:],
                    user=parsed.username,
                    password=parsed.password,
                    ssl=create_ssl_context(insecure=True)
                )
            else:
                raise
        
        # Проверяем существующие таблицы
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        print(f"📊 Найдено таблиц: {len(tables)}")
        for table in tables:
            print(f"   - {table['table_name']}")
        
        # Создаем тестовую таблицу
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_connection (
                id SERIAL PRIMARY KEY,
                message TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        
        # Вставляем тестовые данные
        await conn.execute("""
            INSERT INTO test_connection (message) 
            VALUES ('SEO Analyzer test connection successful!');
        """)
        
        # Читаем данные
        result = await conn.fetchrow("SELECT * FROM test_connection ORDER BY id DESC LIMIT 1;")
        print(f"✅ Тестовая запись: {result['message']} в {result['created_at']}")
        
        # Удаляем тестовую таблицу
        await conn.execute("DROP TABLE IF EXISTS test_connection;")
        print("🧹 Тестовая таблица удалена")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при работе с таблицами: {e}")
        return False

def update_env_file(working_url):
    """Обновляем .env файл с рабочим URL"""
    if not working_url:
        return
        
    print(f"\n📝 Обновляем .env файл с рабочим подключением...")
    
    # Читаем текущий .env
    with open('.env', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Обновляем DATABASE_URL
    async_url = working_url.replace('postgresql://', 'postgresql+asyncpg://')
    
    with open('.env', 'w', encoding='utf-8') as f:
        for line in lines:
            if line.startswith('DATABASE_URL='):
                f.write(f'DATABASE_URL={async_url}\n')
                print(f"✅ Обновлен DATABASE_URL: {async_url}")
            else:
                f.write(line)

async def main():
    """Главная функция тестирования"""
    print("🚀 ТЕСТИРОВАНИЕ ПОДКЛЮЧЕНИЯ К SUPABASE")
    print("=" * 50)
    
    # Тест 1: Синхронное подключение
    working_url = test_sync_connection()
    
    if working_url:
        # Тест 2: Асинхронное подключение
        async_url = await test_async_connection()
        
        if async_url:
            # Тест 3: Работа с таблицами
            tables_ok = await test_tables(working_url)
            
            if tables_ok:
                # Обновляем .env файл
                update_env_file(working_url)
                
                print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
                print("✅ Supabase подключение работает")
                print("✅ Можно запускать сервер")
                return True
    
    print("\n💥 ТЕСТЫ НЕ ПРОЙДЕНЫ!")
    print("❌ Проблемы с подключением к Supabase")
    print("🔧 Проверьте:")
    print("   1. Интернет соединение")
    print("   2. Правильность пароля базы данных")
    print("   3. Статус Supabase проекта")
    return False

if __name__ == "__main__":
    import urllib.parse
    
    print("🔍 Проверяем зависимости...")
    try:
        import psycopg2
        print("✅ psycopg2 установлен")
    except ImportError:
        print("❌ psycopg2 не установлен: pip install psycopg2-binary")
        exit(1)
    
    try:
        import asyncpg
        print("✅ asyncpg установлен")
    except ImportError:
        print("❌ asyncpg не установлен: pip install asyncpg")
        exit(1)
    
    # Запускаем тесты
    success = asyncio.run(main())
    
    if success:
        print("\n🚀 Теперь можно запускать сервер:")
        print("   python main.py")
    else:
        print("\n🔧 Исправьте проблемы и запустите тест снова:")
        print("   python test_supabase.py")
