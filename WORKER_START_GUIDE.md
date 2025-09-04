# 🤖 Запуск воркера для сканирования SERP

## 🎯 Проблема
В логах видно, что API работает, но нет SERP данных. Воркер для автоматического сканирования не запущен.

## 📋 Команды для запуска воркера

### 1. Подключиться к серверу
```bash
ssh root@165.227.141.253
cd /srv/maxseo/backend
source venv/bin/activate
```

### 2. Проверить статус воркера
```bash
# Проверить, запущен ли воркер
ps aux | grep llm_worker
ps aux | grep python | grep worker
```

### 3. Запустить воркер вручную (для тестирования)
```bash
# Разовый запуск воркера
python llm_worker.py
```

### 4. Запустить воркер через API endpoint
```bash
# Запустить цикл обновления через API
curl -X POST https://165.227.141.253:5350/api/worker/run-cycle \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 5. Настроить автоматический запуск воркера

#### Вариант A: Через supervisor
```bash
# Создать конфигурацию для воркера
nano /etc/supervisor/conf.d/maxseo-worker.conf
```

Содержимое:
```ini
[program:maxseo-worker]
command=/srv/maxseo/backend/venv/bin/python llm_worker.py
directory=/srv/maxseo/backend
user=maxseo
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/maxseo-worker.log
environment=PATH="/srv/maxseo/backend/venv/bin"
```

```bash
supervisorctl reread
supervisorctl update
supervisorctl start maxseo-worker
```

#### Вариант B: Через cron (каждые 2 недели)
```bash
crontab -e
# Добавить строку (запуск каждые 2 недели в 2:00):
0 2 */14 * * cd /srv/maxseo/backend && source venv/bin/activate && python llm_worker.py
```

### 6. Проверить работу воркера
```bash
# Проверить логи
tail -f /var/log/maxseo-worker.log

# Или логи через supervisor
supervisorctl tail -f maxseo-worker
```

## 🔧 Настройки воркера в .env

Убедитесь, что в .env файле есть:
```env
# LLM API ключи (минимум один)
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AIza...
GROK_API_KEY=...

# Worker настройки
WORKER_INTERVAL_HOURS=336  # 14 дней
WORKER_ENABLED=true
WORKER_MAX_CONCURRENT=5
```

## ✅ Результат

После запуска воркера:
- Система будет автоматически сканировать активные слова (status=1)
- Каждые 2 недели запрашивать SERP от всех LLM провайдеров

## 🚀 Быстрый запуск воркера

### 1. Запуск вручную для теста
```bash
cd /srv/maxseo/backend
source venv/bin/activate

# Остановить текущий воркер если запущен
pkill -f llm_worker.py

# Запустить исправленный воркер
python llm_worker.py
```

После этого в API появятся SERP данные для аналитики.
