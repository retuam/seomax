from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import asyncio
from loguru import logger
from config_simple import settings
import ssl

def _build_ssl_context() -> ssl.SSLContext:
    """Create SSL context for Supabase. For local dev, disable cert verification.
    Supabase (PostgreSQL) requires TLS. We pass the context via connect_args.
    """
    try:
        import certifi  # type: ignore
        ctx = ssl.create_default_context(cafile=certifi.where())
        # For local development, disable certificate verification
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    except Exception:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

# Создаем асинхронный движок базы данных
if settings.database_url.startswith("sqlite"):
    # Настройки для SQLite
    engine = create_async_engine(
        settings.database_url,
        echo=False,  # Отключаем логи SQL запросов
        connect_args={"check_same_thread": False}
    )
else:
    # Настройки для PostgreSQL (Supabase)
    ssl_ctx = _build_ssl_context()
    engine = create_async_engine(
        settings.database_url,
        poolclass=NullPool,
        echo=False,  # Отключаем логи SQL запросов
        connect_args={
            # SSL context is mandatory for Supabase Pooler
            "ssl": ssl_ctx,
            # Optional server settings and asyncpg tuning
            "server_settings": {
                "application_name": "seo_analyzer",
                "jit": "off",
            },
            "command_timeout": 60,
            "statement_cache_size": 0,
        }
    )

# Создаем фабрику сессий
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,  # Отключаем автофлуш для лучшей производительности
)

Base = declarative_base()

# Dependency для получения сессии базы данных
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency для получения сессии базы данных"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

# Контекстный менеджер для background задач
@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Контекстный менеджер для получения сессии в background задачах"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Background task database error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

# Функция для проверки подключения к базе данных
async def check_database_connection() -> bool:
    """Проверка подключения к базе данных"""
    try:
        from sqlalchemy import text
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

# Функция для инициализации базы данных
async def init_database():
    """Инициализация базы данных"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

# Функция для закрытия соединений
async def close_database():
    """Закрытие соединений с базой данных"""
    await engine.dispose()
    logger.info("✅ Database connections closed")
