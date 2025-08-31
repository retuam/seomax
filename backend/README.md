# SEO Analyzer Backend

FastAPI backend для системы анализа SEO с интеграцией различных LLM провайдеров.

## Структура проекта

```
backend/
├── main.py              # Главный файл приложения FastAPI
├── database.py          # Настройка подключения к базе данных
├── models.py            # SQLAlchemy модели
├── schemas.py           # Pydantic схемы для валидации
├── auth.py              # Система авторизации и JWT
├── llm_service.py       # Сервис для работы с LLM провайдерами
├── llm_worker.py        # Воркер для автоматического обновления SERP
├── init_db.py           # Скрипт инициализации базы данных
├── requirements.txt     # Python зависимости
└── .env.example         # Пример переменных окружения
```

## API Endpoints

### Авторизация
- `POST /api/auth/register` - Регистрация пользователя
- `POST /api/auth/login` - Вход в систему
- `GET /api/auth/me` - Информация о текущем пользователе

### Группы слов
- `GET /api/word-groups` - Получить все группы
- `POST /api/word-groups` - Создать группу
- `PUT /api/word-groups/{id}` - Обновить группу
- `DELETE /api/word-groups/{id}` - Удалить группу

### Слова
- `GET /api/words` - Получить все слова
- `POST /api/words` - Создать слово
- `PUT /api/words/{id}` - Обновить слово
- `DELETE /api/words/{id}` - Удалить слово (мягкое удаление)

### LLM провайдеры
- `GET /api/llm` - Получить всех провайдеров
- `POST /api/llm` - Создать провайдера

### Аналитика
- `GET /api/analytics/word/{id}` - Аналитика по слову
- `GET /api/analytics/group/{id}` - Аналитика по группе

### Воркер
- `POST /api/worker/run-cycle` - Запустить цикл обновления SERP

### Статистика
- `GET /api/stats` - Общая статистика системы

## Установка

1. Создайте виртуальное окружение:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Настройте переменные окружения:
```bash
cp .env.example .env
```

4. Инициализируйте базу данных:
```bash
python init_db.py
```

5. Запустите сервер:
```bash
python main.py
```

## Переменные окружения

```env
# База данных
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/seo_analyzer

# JWT
SECRET_KEY=your-super-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=20160

# LLM API ключи
OPENAI_API_KEY=your-openai-api-key
GEMINI_API_KEY=your-gemini-api-key
GROK_API_URL=https://api.grok.com/v1/chat/completions
GEMINI_API_URL=https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent
```

## Воркер для автоматического обновления

Воркер (`llm_worker.py`) автоматически:
1. Проверяет активные слова каждые 2 недели
2. Запрашивает SERP данные от всех LLM провайдеров
3. Извлекает компании из результатов с помощью GPT
4. Сохраняет все данные в базу

Запуск воркера:
```bash
python llm_worker.py
```

## LLM Интеграции

Поддерживаемые провайдеры:
- OpenAI GPT
- Grok (X.AI)
- Google Gemini
- Mistral AI
- Anthropic Claude
- Perplexity AI

## База данных

Структура таблиц:
- `users` - Пользователи системы
- `word_groups` - Группы ключевых слов
- `words` - Ключевые слова для анализа
- `llm` - LLM провайдеры
- `word_serp` - SERP результаты от LLM
- `companies` - Извлеченные компании и бренды

## Безопасность

- JWT токены для авторизации
- Bcrypt для хеширования паролей
- CORS настройки для фронтенда
- Валидация данных через Pydantic

## Мониторинг

- Логирование всех операций воркера
- Обработка ошибок API запросов
- Статистика использования системы
