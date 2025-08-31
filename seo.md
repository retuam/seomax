Вот готовый SQL для создания всех нужных таблиц в Supabase (PostgreSQL, используется стандартный синтаксис, подходящий для Supabase). Все поля uuid делаем основным ключом с автогенерацией через gen_random_uuid(), где нужно. Индексы добавил по foreign key, где это разумно. Если нужно что-то изменить — пиши.

-- 1. Таблица пользователей
create table public."user" (
    uuid uuid primary key default gen_random_uuid(),
    email text not null unique,
    password text not null,
    create_time timestamp with time zone default now(),
    status smallint default 1
);

-- 2. Группы слов
create table public.words_group (
    uuid uuid primary key default gen_random_uuid(),
    name text not null
);

-- 3. Слова
create table public.words (
    uuid uuid primary key default gen_random_uuid(),
    name text not null,
    group_id uuid references public.words_group(uuid) on delete set null,
    create_time timestamp with time zone default now(),
    update_time timestamp with time zone,
    delete_time timestamp with time zone,
    status smallint default 1
);

create index on public.words(group_id);

-- 4. LLM-модели
create table public.llm (
    uuid uuid primary key default gen_random_uuid(),
    name text not null
);

-- 5. SERP по словам
create table public.words_serp (
    uuid uuid primary key default gen_random_uuid(),
    content text not null,
    llm_id uuid references public.llm(uuid) on delete cascade,
    word_id uuid references public.words(uuid) on delete cascade,
    create_time timestamp with time zone default now()
);

create index on public.words_serp(word_id);
create index on public.words_serp(llm_id);

-- 6. Компании
create table public.companies (
    uuid uuid primary key default gen_random_uuid(),
    name text not null,
    serp_id uuid references public.words_serp(uuid) on delete set null
);

create index on public.companies(serp_id);
Примечания:

В Supabase/Postgres лучше не называть таблицу просто user, потому что это зарезервированное слово. Лучше использовать кавычки "user", как здесь, или переименовать.

Все uuid автогенерируются через gen_random_uuid(). Если функция недоступна, включи расширение:

create extension if not exists "pgcrypto";
Тип status — по умолчанию smallint, меняй если нужен другой тип.

Индексы по foreign key созданы для ускорения запросов.

Если нужен экспорт .sql для импорта — этот текст можно использовать напрямую.
Если нужна миграция через Supabase Studio, просто вставь эти запросы по очереди.

Tú dijiste:
переименуй и убери схему public

ChatGPT Plus
Вот исправленный SQL:

Таблицы переименованы (без public).

user → users

words_group → word_groups

words — оставлено (но можно word_items, если надо).

llm — оставлено.

words_serp → word_serp

companies — оставлено.

Схема убрана, теперь просто create table ....

-- 1. Таблица пользователей
create table users (
    uuid uuid primary key default gen_random_uuid(),
    email text not null unique,
    password text not null,
    create_time timestamp with time zone default now(),
    status smallint default 1
);

-- 2. Группы слов
create table word_groups (
    uuid uuid primary key default gen_random_uuid(),
    name text not null
);

-- 3. Слова
create table words (
    uuid uuid primary key default gen_random_uuid(),
    name text not null,
    group_id uuid references word_groups(uuid) on delete set null,
    create_time timestamp with time zone default now(),
    update_time timestamp with time zone,
    delete_time timestamp with time zone,
    status smallint default 1
);

create index on words(group_id);

-- 4. LLM-модели
create table llm (
    uuid uuid primary key default gen_random_uuid(),
    name text not null
);

-- 5. SERP по словам
create table word_serp (
    uuid uuid primary key default gen_random_uuid(),
    content text not null,
    llm_id uuid references llm(uuid) on delete cascade,
    word_id uuid references words(uuid) on delete cascade,
    create_time timestamp with time zone default now()
);

create index on word_serp(word_id);
create index on word_serp(llm_id);

-- 6. Компании
create table companies (
    uuid uuid primary key default gen_random_uuid(),
    name text not null,
    serp_id uuid references word_serp(uuid) on delete set null
);

create index on companies(serp_id);
Если расширение pgcrypto ещё не включено (для UUID):

create extension if not exists "pgcrypto";
Если нужны ещё правки — скажи!

Tú dijiste:
тайм зона не нужна


ChatGPT Plus
Вот чистый SQL без тайм-зоны (timestamp без time zone):

sql
Copiar
Editar
-- 1. Таблица пользователей
create table users (
    uuid uuid primary key default gen_random_uuid(),
    email text not null unique,
    password text not null,
    create_time timestamp default now(),
    status smallint default 1
);

-- 2. Группы слов
create table word_groups (
    uuid uuid primary key default gen_random_uuid(),
    name text not null
);

-- 3. Слова
create table words (
    uuid uuid primary key default gen_random_uuid(),
    name text not null,
    group_id uuid references word_groups(uuid) on delete set null,
    create_time timestamp default now(),
    update_time timestamp,
    delete_time timestamp,
    status smallint default 1
);

create index on words(group_id);

-- 4. LLM-модели
create table llm (
    uuid uuid primary key default gen_random_uuid(),
    name text not null
);

-- 5. SERP по словам
create table word_serp (
    uuid uuid primary key default gen_random_uuid(),
    content text not null,
    llm_id uuid references llm(uuid) on delete cascade,
    word_id uuid references words(uuid) on delete cascade,
    create_time timestamp default now()
);

create index on word_serp(word_id);
create index on word_serp(llm_id);

-- 6. Компании
create table companies (
    uuid uuid primary key default gen_random_uuid(),
    name text not null,
    serp_id uuid references word_serp(uuid) on delete set null
);

create index on companies(serp_id);
Готово. Если ещё что-то упростить/добавить — пиши!

Tú dijiste:
Под эту структуру надо написать fastapi бекенд
Авторизация, регистрация юзера, токен выписывается с которым будем ходить к другим эндпоинтам
CRUD групп, слов
Список груп, слов, ллм, серп, Компании

демон процесс для регулярной проверки списка слов для среза позиций. Если слово имеет статус 1, то раз в две недели для него запускает срез по этому слову в ЛЛМ, что ЛЛМ выдаст, всего используется 6 ллм * грок, гемини, гпт, мистраль, клод, перплексити, и результат выдачи запоминается в таблице серп поле контент, и из текста извлекаются компании, которые там упоминаются или товары, вообщем коммерческие слова, бренды, товары, компании и сохраняются в компаниях. Слова извлекаются с помощью гпт ллм через промпт, который ты напишешь

ChatGPT Plus
Вот подробная структура FastAPI-бэкенда под твою задачу:

1. Основные зависимости
FastAPI

SQLAlchemy (async)

asyncpg

passlib (bcrypt)

python-jose (jwt)

pydantic

httpx (для LLM)

apscheduler (демон-процесс, периодика)

2. Структура проекта
pgsql
Copiar
Editar
project/
├── main.py
├── database.py
├── models.py
├── schemas.py
├── crud.py
├── auth.py
├── llm_worker.py
└── utils.py
3. Схемы и Модели
models.py (пример)

python
Copiar
Editar
from sqlalchemy import Column, String, Integer, TIMESTAMP, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    create_time = Column(TIMESTAMP, nullable=False)
    status = Column(Integer, default=1)

class WordGroup(Base):
    __tablename__ = "word_groups"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)

class Word(Base):
    __tablename__ = "words"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    group_id = Column(UUID(as_uuid=True), ForeignKey("word_groups.uuid"))
    create_time = Column(TIMESTAMP)
    update_time = Column(TIMESTAMP)
    delete_time = Column(TIMESTAMP)
    status = Column(Integer, default=1)

class LLM(Base):
    __tablename__ = "llm"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)

class WordSerp(Base):
    __tablename__ = "word_serp"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(String, nullable=False)
    llm_id = Column(UUID(as_uuid=True), ForeignKey("llm.uuid"))
    word_id = Column(UUID(as_uuid=True), ForeignKey("words.uuid"))
    create_time = Column(TIMESTAMP)

class Company(Base):
    __tablename__ = "companies"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    serp_id = Column(UUID(as_uuid=True), ForeignKey("word_serp.uuid"))
4. Авторизация и регистрация
JWT токены, храним только uuid/email

Пример функции регистрации:

auth.py

python
Copiar
Editar
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta

SECRET_KEY = "your-secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60*24*14

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
main.py (регистрация и логин):

python
Copiar
Editar
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import User
from auth import hash_password, verify_password, create_access_token

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

app = FastAPI()

@app.post("/register")
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    exists = await db.scalar(select(User).where(User.email == user.email))
    if exists:
        raise HTTPException(400, detail="User exists")
    db_user = User(email=user.email, password=hash_password(user.password))
    db.add(db_user)
    await db.commit()
    return {"msg": "ok"}

@app.post("/login")
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    db_user = await db.scalar(select(User).where(User.email == user.email))
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(401, detail="Invalid credentials")
    token = create_access_token({"sub": str(db_user.uuid), "email": db_user.email})
    return {"access_token": token, "token_type": "bearer"}
5. CRUD для групп, слов и списки
Все CRUD-эндпоинты делаются через стандартные методы FastAPI (GET, POST, PUT, DELETE).

Примеры для word_groups, words.

python
Copiar
Editar
@app.get("/word-groups")
async def list_word_groups(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WordGroup))
    return result.scalars().all()

@app.post("/word-groups")
async def create_word_group(group: WordGroupSchema, db: AsyncSession = Depends(get_db)):
    obj = WordGroup(name=group.name)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj

@app.get("/words")
async def list_words(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Word))
    return result.scalars().all()

# Аналогично — CRUD для words, llm, word_serp, companies
6. Демон-процесс (llm_worker.py)
Используется APScheduler или отдельный async-скрипт.

Каждые 2 недели для каждого слова со status=1 запрашиваем выдачу у всех LLM, записываем результат в word_serp, извлекаем компании.

llm_worker.py (псевдокод):

python
Copiar
Editar
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from models import Word, LLM, WordSerp, Company
from database import get_async_session
import httpx

LLMS = [
    {"name": "grok", "url": "..."},
    {"name": "gemini", "url": "..."},
    # ... остальные
]

async def fetch_llm_result(llm_url, word):
    # Например, POST запрос к API LLM
    async with httpx.AsyncClient() as client:
        resp = await client.post(llm_url, json={"prompt": word})
        return resp.json()["result"]

async def extract_companies_from_text(text):
    # Используем GPT-llm для извлечения компаний через промпт
    prompt = f"""В этом тексте найди все упоминания компаний, товаров, брендов и коммерческих слов. Дай список через запятую:"""
    async with httpx.AsyncClient() as client:
        resp = await client.post("GPT_LLM_ENDPOINT", json={"prompt": prompt + text})
        return [item.strip() for item in resp.json()["result"].split(",")]

async def llm_worker():
    async with get_async_session() as db:
        now = datetime.utcnow()
        two_weeks_ago = now - timedelta(days=14)
        words = (await db.execute(select(Word).where(Word.status==1))).scalars().all()
        for word in words:
            for llm in LLMS:
                # Проверяем — был ли уже срез за последние 2 недели
                existing = await db.scalar(
                    select(WordSerp).where(
                        WordSerp.word_id==word.uuid,
                        WordSerp.llm_id==llm['uuid'],
                        WordSerp.create_time > two_weeks_ago
                    )
                )
                if existing: continue
                result = await fetch_llm_result(llm["url"], word.name)
                ws = WordSerp(content=result, llm_id=llm["uuid"], word_id=word.uuid, create_time=now)
                db.add(ws)
                await db.commit()
                companies = await extract_companies_from_text(result)
                for company in companies:
                    c = Company(name=company, serp_id=ws.uuid)
                    db.add(c)
                await db.commit()

# Для запуска как background job: APScheduler/uvicorn/свой цикл
7. Пример промпта для GPT LLM
text
Copiar
Editar
В этом тексте найди все упоминания компаний, товаров, брендов и коммерческих слов.
Дай только список, через запятую, без лишнего текста и объяснений.
8. Финал
Регистрация, авторизация через JWT.

CRUD для групп, слов.

Списки групп, слов, llm, serp, companies.

Демон-воркер раз в 2 недели запрашивает выдачу LLM по активным словам, сохраняет результаты, парсит компании.

Могу написать любой конкретный кусок — например, весь main.py или отдельный воркер. Скажи, что развёрнуто расписать или дай детали по API для LLM.