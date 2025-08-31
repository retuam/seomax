#!/usr/bin/env python3
"""
Отладочный запуск сервера
"""

import os
import sys

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🔍 Отладочный запуск сервера...")
print(f"📁 Рабочая директория: {os.getcwd()}")
print(f"🐍 Python путь: {sys.path[:3]}")

try:
    print("\n1️⃣ Импорт базовых модулей...")
    import asyncio
    from contextlib import asynccontextmanager
    print("✅ Базовые модули OK")
    
    print("\n2️⃣ Импорт FastAPI...")
    from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    print("✅ FastAPI OK")
    
    print("\n3️⃣ Импорт SQLAlchemy...")
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select, and_, func
    print("✅ SQLAlchemy OK")
    
    print("\n4️⃣ Импорт конфигурации...")
    from config import settings
    print("✅ Config OK")
    
    print("\n5️⃣ Импорт логирования...")
    from logging_config import setup_logging, setup_sentry
    print("✅ Logging OK")
    
    print("\n6️⃣ Импорт database...")
    from database import get_db, AsyncSessionLocal
    print("✅ Database OK")
    
    print("\n7️⃣ Импорт моделей...")
    from models import User, WordGroup, Word, LLM, WordSerp, Company
    print("✅ Основные модели OK")
    
    print("\n8️⃣ Импорт Brand моделей...")
    from models import BrandProject, Competitor, BrandMention
    print("✅ Brand модели OK")
    
    print("\n9️⃣ Импорт схем...")
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
    print("✅ Схемы OK")
    
    print("\n🔟 Импорт сервисов...")
    from auth import hash_password, verify_password, create_access_token, get_current_user
    from llm_worker import llm_worker
    from llm_service import llm_service
    print("✅ Сервисы OK")
    
    print("\n🚀 Все импорты успешны! Теперь попробуем запустить main.py...")
    
except Exception as e:
    print(f"\n❌ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
