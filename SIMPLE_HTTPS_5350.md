# 🔒 Простой HTTPS на порту 5350

## 🎯 Цель
Настроить SSL прямо в FastAPI на порту 5350, без лишних proxy.

## 📋 Команды для сервера

### 1. Подключиться к серверу
```bash
ssh root@165.227.141.253
```

### 2. Создать SSL сертификат
```bash
# Создать директорию
mkdir -p /etc/ssl/seoapi

# Создать сертификат
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/seoapi/key.pem \
    -out /etc/ssl/seoapi/cert.pem \
    -subj "/C=US/ST=State/L=City/O=SEO/CN=165.227.141.253"
```

### 3. Остановить текущий FastAPI
```bash
# Найти процесс
ps aux | grep uvicorn
# Убить процесс (замените PID на реальный)
kill -9 PID

# Или если через supervisor
supervisorctl stop maxseo
```

### 4. Запустить FastAPI с SSL на порту 5350
```bash
cd /srv/maxseo/backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 5350 \
    --ssl-keyfile /etc/ssl/seoapi/key.pem \
    --ssl-certfile /etc/ssl/seoapi/cert.pem
```

### 5. Для автозапуска обновить supervisor (если используется)
```bash
nano /etc/supervisor/conf.d/maxseo.conf
```

Изменить команду:
```ini
[program:maxseo]
command=/srv/maxseo/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 5350 --ssl-keyfile /etc/ssl/seoapi/key.pem --ssl-certfile /etc/ssl/seoapi/cert.pem
directory=/srv/maxseo/backend
user=maxseo
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/maxseo.log
environment=PATH="/srv/maxseo/backend/venv/bin"
```

```bash
supervisorctl reread
supervisorctl update
supervisorctl start maxseo
```

## ✅ Результат

- **HTTPS API**: `https://165.227.141.253:5350/api`
- **HTTPS Docs**: `https://165.227.141.253:5350/docs`
- Никаких лишних proxy
- Тот же порт 5350, только с SSL

## 📝 Для Lovable

```javascript
const API_BASE_URL = 'https://165.227.141.253:5350/api';
```

**Время настройки: 2 минуты**
