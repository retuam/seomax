"""
Конфигурация логирования с использованием Loguru
"""
import sys
from pathlib import Path
from loguru import logger
from config import settings

def setup_logging():
    """Настройка системы логирования"""
    
    # Удаляем стандартный обработчик
    logger.remove()
    
    # Отключаем логи SQLAlchemy
    import logging
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.dialects').setLevel(logging.WARNING)
    
    # Формат логов
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # Консольный вывод
    logger.add(
        sys.stdout,
        format=log_format,
        level=settings.log_level,
        colorize=True,
        backtrace=True,
        diagnose=True,
        filter=lambda record: not record["name"].startswith("sqlalchemy")
    )
    
    # Файловый вывод
    log_file = Path(settings.log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.add(
        log_file,
        format=log_format,
        level=settings.log_level,
        rotation="10 MB",  # Ротация при достижении 10MB
        retention="30 days",  # Хранить логи 30 дней
        compression="zip",  # Сжимать старые логи
        backtrace=True,
        diagnose=True,
        enqueue=True,  # Асинхронная запись
        filter=lambda record: not record["name"].startswith("sqlalchemy")
    )
    
    # Отдельный файл для ошибок
    error_log_file = log_file.parent / "errors.log"
    logger.add(
        error_log_file,
        format=log_format,
        level="ERROR",
        rotation="5 MB",
        retention="60 days",
        compression="zip",
        backtrace=True,
        diagnose=True,
        enqueue=True
    )
    
    # Логирование для воркера
    worker_log_file = log_file.parent / "worker.log"
    logger.add(
        worker_log_file,
        format=log_format,
        level="INFO",
        rotation="5 MB",
        retention="14 days",
        compression="zip",
        filter=lambda record: "worker" in record["name"].lower(),
        enqueue=True
    )
    
    logger.info("🚀 Logging system initialized")
    logger.info(f"📁 Log files: {log_file.parent}")
    logger.info(f"📊 Log level: {settings.log_level}")

# Настройка Sentry для мониторинга в продакшене
def setup_sentry():
    """Настройка Sentry для мониторинга ошибок"""
    if settings.sentry_dsn and settings.is_production:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.loguru import LoguruIntegration
        
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            integrations=[
                FastApiIntegration(auto_enabling_integrations=False),
                SqlalchemyIntegration(),
                LoguruIntegration(),
            ],
            traces_sample_rate=0.1,  # 10% трейсов для производительности
            environment=settings.environment,
            release="seo-analyzer@1.0.0",
        )
        
        logger.info("📊 Sentry monitoring initialized")

# Декоратор для логирования выполнения функций
def log_execution(func_name: str = None):
    """Декоратор для логирования времени выполнения функций"""
    def decorator(func):
        import functools
        import time
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            name = func_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            
            try:
                logger.debug(f"⏳ Starting {name}")
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.debug(f"✅ Completed {name} in {execution_time:.2f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"❌ Failed {name} after {execution_time:.2f}s: {e}")
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            name = func_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            
            try:
                logger.debug(f"⏳ Starting {name}")
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.debug(f"✅ Completed {name} in {execution_time:.2f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"❌ Failed {name} after {execution_time:.2f}s: {e}")
                raise
        
        # Возвращаем соответствующий wrapper в зависимости от типа функции
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

# Инициализация при импорте модуля
setup_logging()
setup_sentry()
