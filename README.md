# 🔍 SEO Analyzer - Современная система анализа ключевых слов

Полнофункциональная система для анализа SEO ключевых слов с интеграцией множественных LLM провайдеров, автоматическим сбором SERP данных, извлечением компаний и **мониторингом брендов**.

## ✨ Основные возможности

### 🚀 Backend (FastAPI)
- **Авторизация JWT** с регистрацией и логином
- **CRUD операции** для групп слов и ключевых слов
- **🏷️ Brand Monitoring** - мониторинг упоминаний бренда и конкурентов в LLM ответах
- **Интеграция с 6 LLM провайдерами**: OpenAI GPT, Google Gemini, Anthropic Claude, Grok, Mistral, Perplexity
- **Автоматический воркер** для обновления SERP данных каждые 2 недели
- **Извлечение компаний** из SERP результатов с помощью AI
- **PostgreSQL база данных** с полной схемой
- **API документация** Swagger/OpenAPI
- **Логирование и мониторинг** с Loguru и Sentry
- **Кеширование** запросов к LLM
- **Retry логика** с экспоненциальной задержкой

### 🎨 Frontend (Next.js 14)
- **Современный UI** с Tailwind CSS
- **Авторизация** с JWT токенами в cookies
- **Управление группами и словами** с CRUD операциями
- **Настройка LLM провайдеров** через веб-интерфейс
- **Аналитика и статистика** с графиками
- **Адаптивный дизайн** для всех устройств
- **Уведомления** с react-hot-toast
- **Защищенные маршруты** с автоматическим редиректом

### 🤖 LLM Интеграция
- **OpenAI GPT-4o-mini** - основной провайдер для анализа
- **Google Gemini Pro** - альтернативный анализ
- **Anthropic Claude 3** - качественная обработка текста
- **Grok** - инновационный подход к анализу
- **Mistral Large** - европейская альтернатива
- **Perplexity** - поиск в реальном времени

## 🛠 Технический стек

### Backend
- **FastAPI** 0.104+ - современный веб-фреймворк
- **SQLAlchemy 2.0** - асинхронная ORM
- **PostgreSQL** - надежная база данных
- **Pydantic** - валидация данных
- **aiohttp** - асинхронные HTTP запросы
- **Loguru** - продвинутое логирование
- **APScheduler** - планировщик задач

### Frontend
- **Next.js 14** - React фреймворк с App Router
- **TypeScript** - типизированный JavaScript
- **Tailwind CSS** - utility-first CSS
- **Axios** - HTTP клиент
- **React Hook Form** - управление формами
- **Lucide React** - иконки

## 🚀 Быстрый старт

### 1. Клонирование репозитория
```bash
git clone <your-repo-url>
cd maxseo
```

### 2. Настройка Backend

#### Установка зависимостей
```bash
cd backend
pip install -r requirements.txt
```

#### Настройка переменных окружения
```bash
# Скопируйте и отредактируйте .env файл
cp .env.example .env
```

**Обязательные настройки в .env:**
```env
# База данных (Supabase рекомендуется)
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db

# JWT секрет (минимум 32 символа)
SECRET_KEY=your-super-secret-key-change-this-in-production

# LLM API ключи (минимум один)
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AIza...
ANTHROPIC_API_KEY=sk-ant-...
MISTRAL_API_KEY=...
PERPLEXITY_API_KEY=pplx-...
```

#### Инициализация базы данных
```bash
python init_db.py
```

#### Тестирование LLM сервиса
```bash
python test_llm.py
```

#### Запуск сервера
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 5000
```

### 3. Настройка Frontend

#### Установка зависимостей
```bash
cd frontend
npm install
```

#### Запуск в режиме разработки
```bash
npm run dev
```

### 4. Автоматический запуск

#### Windows
```bash
# Запуск всех сервисов одновременно
start.bat
```

#### Linux/Mac
```bash
# Запуск всех сервисов одновременно
./start.sh
```

## 📋 API Документация

После запуска backend сервера документация доступна по адресам:
- **Swagger UI**: http://localhost:5000/docs
- **ReDoc**: http://localhost:5000/redoc

## 🗄 Структура базы данных

```sql
-- Пользователи
users (uuid, email, password_hash, created_at)

-- Группы ключевых слов
word_groups (uuid, name, user_id, created_at)

-- Ключевые слова
words (uuid, name, group_id, status, created_at)

-- LLM провайдеры
llm (uuid, name, api_url, api_key, is_active)

-- SERP результаты
word_serp (uuid, word_id, llm_id, content, created_at)

-- Извлеченные компании
companies (uuid, name, serp_id, created_at)

-- Бренды
brands (uuid, name, user_id, created_at)

-- Бренд упоминания
brand_mentions (uuid, brand_id, serp_id, created_at)
```

## 🔧 Конфигурация

### LLM Провайдеры
Все провайдеры настраиваются через переменные окружения:

```env
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# Google Gemini
GEMINI_API_KEY=AIza...
GEMINI_MODEL=gemini-pro

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# И так далее...
```

### Воркер настройки
```env
WORKER_INTERVAL_HOURS=336  # 14 дней
WORKER_ENABLED=true
WORKER_MAX_CONCURRENT=5
```

## 📊 Мониторинг и логирование

### Loguru
Все логи сохраняются в `logs/` директории с ротацией:
- `app.log` - основные логи приложения
- `worker.log` - логи фонового воркера
- `error.log` - только ошибки

### Sentry (опционально)
```env
SENTRY_DSN=https://your-sentry-dsn
SENTRY_ENVIRONMENT=production
```

## 🧪 Тестирование

### Backend тесты
```bash
cd backend
python test_llm.py  # Тест LLM сервиса
pytest  # Запуск всех тестов (если настроены)
```

### Frontend тесты
```bash
cd frontend
npm test  # Jest тесты (если настроены)
npm run lint  # Линтинг кода
```

## 🚀 Деплой

### Backend (Render.com/DigitalOcean)
1. Создайте PostgreSQL базу данных
2. Настройте переменные окружения
3. Деплойте с помощью Docker или прямо из Git

### Frontend (Netlify)
1. Подключите GitHub репозиторий
2. Настройте build команды:
   ```
   Build command: npm run build
   Publish directory: .next
   ```
3. Добавьте переменные окружения для API URL

### All-in-one (DigitalOcean App Platform)
1. Создайте новое приложение
2. Добавьте backend и frontend сервисы
3. Настройте базу данных
4. Деплойте

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📄 Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

## 🆘 Поддержка

Если у вас есть вопросы или проблемы:
1. Проверьте [Issues](../../issues) на GitHub
2. Создайте новый Issue с подробным описанием
3. Проверьте логи в `backend/logs/` для диагностики

## 🎯 Roadmap

- [ ] Добавление новых LLM провайдеров
- [ ] Расширенная аналитика с графиками
- [ ] Экспорт данных в Excel/CSV
- [ ] API для интеграции с внешними системами
- [ ] Мобильное приложение
- [ ] Многопользовательские команды
- [ ] Интеграция с Google Search Console

---

**Создано с ❤️ для современного SEO анализа**

## Архитектура

- **Backend**: FastAPI + PostgreSQL + Qdrant (для семантического поиска)
- **Frontend**: Next.js 14 с App Router + TypeScript + Tailwind CSS
- **AI Integration**: OpenAI API, Grok, Gemini и другие LLM
- **Автоматизация**: Воркер для обновления SERP данных каждые 2 недели

## Функционал

### Основные возможности
- 🔐 Авторизация и регистрация пользователей (JWT)
- 📝 Управление группами слов и ключевыми словами
- 🤖 Интеграция с 6 LLM провайдерами (OpenAI, Grok, Gemini, Mistral, Claude, Perplexity)
- 📊 Автоматический анализ SERP результатов
- 🏢 Извлечение компаний и брендов из результатов поиска
- 📈 Аналитика и отчеты
- ⚙️ Автоматическое обновление данных каждые 2 недели
- 🏷️ **Brand Monitoring** - мониторинг упоминаний бренда и конкурентов в LLM ответах

### Структура данных
- **Пользователи**: Регистрация и авторизация
- **Группы слов**: Организация ключевых слов по категориям
- **Слова**: Ключевые слова для анализа
- **LLM провайдеры**: Настройка интеграций с различными AI сервисами
- **SERP результаты**: Результаты поиска от LLM
- **Компании**: Извлеченные из SERP результатов компании и бренды
- **Бренды**: Мониторинг упоминаний бренда и конкурентов

## Быстрый запуск

### Автоматический запуск (рекомендуется)

**Windows:**
```bash
# Запустите start.bat для автоматического запуска всех сервисов
start.bat
```

**Linux/Mac:**
```bash
# Сделайте файл исполняемым и запустите
chmod +x start.sh
./start.sh
```

### Ручная установка

#### 1. Настройка базы данных

1. Установите PostgreSQL
2. Создайте базу данных:
```sql
CREATE DATABASE seo_analyzer;
```
3. Выполните SQL скрипт:
```bash
psql -d seo_analyzer -f database_init.sql
```

#### 2. Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Отредактируйте .env файл

python main.py
```

#### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

#### 4. Worker (опционально)

```bash
cd backend
source venv/bin/activate  # или venv\Scripts\activate на Windows
python llm_worker.py
```

### Доступ к приложению

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **API Documentation**: http://localhost:5000/docs

## Настройка

### Переменные окружения (.env)

```env
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/seo_analyzer
SECRET_KEY=your-super-secret-key
OPENAI_API_KEY=your-openai-api-key
GEMINI_API_KEY=your-gemini-api-key
```

### Тестовый пользователь

После инициализации базы данных будет создан тестовый пользователь:
- Email: admin@example.com
- Пароль: admin123

## API Документация

После запуска backend, API документация доступна по адресу:
- Swagger UI: http://localhost:5000/docs
- ReDoc: http://localhost:5000/redoc

## Воркер для автоматического обновления

Система включает воркер, который автоматически:
1. Проверяет активные слова (status = 1)
2. Каждые 2 недели запрашивает SERP данные от всех LLM провайдеров
3. Сохраняет результаты в базу данных
4. Извлекает компании и бренды из текста с помощью GPT

Запуск воркера:
```bash
python llm_worker.py
```

## Деплой

### Frontend (Netlify)
1. Подключите репозиторий к Netlify
2. Настройте build команды:
   - Build command: `npm run build`
   - Publish directory: `.next`

### Backend (Render.com или DigitalOcean)
1. Создайте PostgreSQL базу данных
2. Настройте переменные окружения
3. Деплойте FastAPI приложение

## Технологии

### Backend
- FastAPI - современный веб-фреймворк для Python
- SQLAlchemy - ORM для работы с базой данных
- PostgreSQL - реляционная база данных
- Pydantic - валидация данных
- JWT - авторизация
- HTTPx - HTTP клиент для запросов к LLM
- APScheduler - планировщик задач

### Frontend
- Next.js 14 - React фреймворк с App Router
- TypeScript - типизированный JavaScript
- Tailwind CSS - utility-first CSS фреймворк
- Axios - HTTP клиент
- React Hook Form - управление формами
- React Hot Toast - уведомления

## Лицензия

MIT License

## 🏷️ Brand Monitoring & Competitive Analysis
- **Мониторинг бренда** - отслеживание упоминаний вашей компании в LLM ответах
- **Конкурентный анализ** - мониторинг до 10 конкурентов по проекту
- **Автогенерация ключевых слов** - LLM создает релевантные запросы на основе описания бренда
- **Аналитика видимости** - детальная статистика позиций и упоминаний
- **Интеграция с воркером** - автоматический анализ при обновлении SERP
- **До 50 ключевых слов** на brand проект
- **Позиционный анализ** - определение места упоминания в результатах (1-10)
- **Уверенность анализа** - LLM оценивает точность своего анализа (0-100%)
# seomax
