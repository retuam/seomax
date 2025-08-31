#!/usr/bin/env python3
"""
Скрипт для применения миграции Brand Monitoring
"""

import asyncio
import asyncpg
from config import settings
from loguru import logger

async def apply_migration():
    """Применение миграции Brand Monitoring"""
    try:
        # Подключаемся к базе данных
        conn = await asyncpg.connect(settings.database_url.replace("postgresql+asyncpg://", "postgresql://"))
        
        # Читаем SQL миграцию
        with open("brand_monitoring_migration.sql", "r", encoding="utf-8") as f:
            migration_sql = f.read()
        
        # Выполняем миграцию
        await conn.execute(migration_sql)
        
        logger.info("✅ Миграция Brand Monitoring успешно применена")
        
        # Проверяем, что таблицы созданы
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('brand_projects', 'competitors', 'brand_mentions')
        """)
        
        logger.info(f"📋 Созданные таблицы: {[t['table_name'] for t in tables]}")
        
        await conn.close()
        
    except Exception as e:
        logger.error(f"❌ Ошибка применения миграции: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(apply_migration())
