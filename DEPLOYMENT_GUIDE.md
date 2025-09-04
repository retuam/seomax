# 🚀 SEO Analyzer - Deployment Guide для сервера 165.227.141.253

## 📋 Обзор деплоя

Инструкция по развертыванию SEO Analyzer на продакшн сервере с использованием:
- **Сервер**: 165.227.141.253
- **Путь**: /srv/maxseo
- **Git**: git@github.com:retuam/seomax.git
- **База данных**: Supabase PostgreSQL
- **Веб-сервер**: Nginx + Uvicorn

---

## 🔧 Подготовка сервера

### 1. Подключение к серверу
```bash
ssh root@165.227.141.253
```

### 2. Обновление системы
```bash
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv git nginx supervisor curl
```

### 3. Создание пользователя для приложения
```bash
useradd -m -s /bin/bash maxseo
usermod -aG sudo maxseo
```

### 4. Создание директории проекта
```bash
mkdir -p /srv/maxseo
chown maxseo:maxseo /srv/maxseo
```

---

## 📦 Клонирование и настройка проекта

### 1. Переключение на пользователя maxseo
```bash
su - maxseo
cd /srv
```

### 2. Клонирование репозитория
```bash
git clone git@github.com:retuam/seomax.git maxseo
cd maxseo
```

### 3. Создание виртуального окружения
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

### 4. Установка зависимостей
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🔐 Настройка переменных окружения

### 1. Создание .env файла
```bash
cd /srv/maxseo/backend
cp .env.example .env
nano .env
```

### 2. Конфигурация .env для продакшена
```env
# Database Configuration (Supabase)
DATABASE_URL=postgresql+asyncpg://postgres.usshslzenyrubetvwenc:d93b4zd0ivn8a4G8@aws-0-eu-central-1.pooler.supabase.com:5432/postgres

# JWT Configuration
SECRET_KEY=your-super-secret-jwt-key-here-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=20160

# Environment
ENVIRONMENT=production
DEBUG=false
CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com

# LLM API Keys (добавьте ваши ключи)
OPENAI_API_KEY=your-openai-key
GEMINI_API_KEY=your-gemini-key
ANTHROPIC_API_KEY=your-anthropic-key
GROK_API_KEY=your-grok-key
MISTRAL_API_KEY=your-mistral-key
PERPLEXITY_API_KEY=your-perplexity-key

# Server Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=4
```

### 3. Защита .env файла
```bash
chmod 600 .env
chown maxseo:maxseo .env
```

---

## 🗄️ Настройка базы данных

### 1. Тестирование подключения
```bash
cd /srv/maxseo/backend
source venv/bin/activate
python test_supabase.py
```

### 2. Инициализация таблиц (если нужно)
```bash
python -c "
from database import init_database
import asyncio
asyncio.run(init_database())
"
```

---

## 🔄 Настройка Supervisor для автозапуска

### 1. Создание конфигурации Supervisor
```bash
sudo nano /etc/supervisor/conf.d/maxseo.conf
```

### 2. Содержимое конфигурации
```ini
[program:maxseo]
command=/srv/maxseo/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
directory=/srv/maxseo/backend
user=maxseo
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/maxseo.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=5
environment=PATH="/srv/maxseo/backend/venv/bin"
```

### 3. Обновление Supervisor
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start maxseo
```

### 4. Проверка статуса
```bash
sudo supervisorctl status maxseo
```

---

## 🌐 Настройка Nginx

### 1. Создание конфигурации Nginx
```bash
sudo nano /etc/nginx/sites-available/maxseo
```

### 2. Конфигурация Nginx
```nginx
server {
    listen 80;
    server_name 165.227.141.253 yourdomain.com;
    
    # API endpoints
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS headers
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization";
        
        # Handle preflight requests
        if ($request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin *;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
            add_header Access-Control-Allow-Headers "Content-Type, Authorization";
            return 204;
        }
    }
    
    # Swagger documentation
    location /docs {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Static files (если будут)
    location /static/ {
        alias /srv/maxseo/static/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
    
    # Frontend (если будет размещен на том же сервере)
    location / {
        root /srv/maxseo/frontend/dist;
        try_files $uri $uri/ /index.html;
        expires 1d;
        add_header Cache-Control "public, no-transform";
    }
}
```

### 3. Активация конфигурации
```bash
sudo ln -s /etc/nginx/sites-available/maxseo /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🔒 Настройка SSL (Let's Encrypt)

### 1. Установка Certbot
```bash
sudo apt install certbot python3-certbot-nginx
```

### 2. Получение SSL сертификата
```bash
sudo certbot --nginx -d yourdomain.com
```

### 3. Автообновление сертификата
```bash
sudo crontab -e
# Добавить строку:
0 12 * * * /usr/bin/certbot renew --quiet
```

---

## 🔥 Настройка Firewall

### 1. Настройка UFW
```bash
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### 2. Проверка статуса
```bash
sudo ufw status
```

---

## 📊 Мониторинг и логи

### 1. Просмотр логов приложения
```bash
sudo tail -f /var/log/maxseo.log
```

### 2. Просмотр логов Nginx
```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 3. Мониторинг процессов
```bash
sudo supervisorctl status
htop
```

---

## 🚀 Команды для управления

### Перезапуск приложения
```bash
sudo supervisorctl restart maxseo
```

### Обновление кода из Git
```bash
cd /srv/maxseo
git pull origin main
sudo supervisorctl restart maxseo
```

### Обновление зависимостей
```bash
cd /srv/maxseo/backend
source venv/bin/activate
pip install -r requirements.txt
sudo supervisorctl restart maxseo
```

### Запуск тестов
```bash
cd /srv/maxseo/backend
source venv/bin/activate
python test_api.py
python test_brand_monitoring.py
```

---

## 🔍 Проверка работоспособности

### 1. Проверка API
```bash
curl http://165.227.141.253/docs
curl http://165.227.141.253/api/stats
```

### 2. Проверка базы данных
```bash
cd /srv/maxseo/backend
source venv/bin/activate
python test_supabase.py
```

### 3. Проверка LLM сервисов
```bash
curl -X POST http://165.227.141.253/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}'
```

---

## 📋 Чек-лист деплоя

### ✅ Подготовка сервера
- [ ] Подключение по SSH
- [ ] Обновление системы
- [ ] Установка зависимостей
- [ ] Создание пользователя maxseo

### ✅ Настройка приложения
- [ ] Клонирование репозитория в /srv/maxseo
- [ ] Создание виртуального окружения
- [ ] Установка Python зависимостей
- [ ] Настройка .env файла

### ✅ Настройка сервисов
- [ ] Конфигурация Supervisor
- [ ] Настройка Nginx
- [ ] Настройка Firewall
- [ ] SSL сертификат (опционально)

### ✅ Тестирование
- [ ] Проверка подключения к БД
- [ ] Запуск тестов API
- [ ] Проверка доступности через браузер
- [ ] Тестирование всех эндпоинтов

---

## 🆘 Troubleshooting

### Проблема: Приложение не запускается
```bash
# Проверить логи
sudo tail -f /var/log/maxseo.log

# Проверить статус
sudo supervisorctl status maxseo

# Перезапустить
sudo supervisorctl restart maxseo
```

### Проблема: База данных недоступна
```bash
# Проверить подключение
cd /srv/maxseo/backend
source venv/bin/activate
python test_supabase.py
```

### Проблема: Nginx не работает
```bash
# Проверить конфигурацию
sudo nginx -t

# Перезапустить Nginx
sudo systemctl restart nginx
```

---

## 🎯 Результат

После выполнения всех шагов у вас будет:

- ✅ **SEO Analyzer API** доступен по адресу http://165.227.141.253
- ✅ **Swagger документация** по адресу http://165.227.141.253/docs
- ✅ **Автозапуск** приложения через Supervisor
- ✅ **Nginx** как reverse proxy
- ✅ **SSL сертификат** (если настроен)
- ✅ **Мониторинг** и логирование
- ✅ **Firewall** защита

**API будет доступен для подключения React frontend!** 🚀
