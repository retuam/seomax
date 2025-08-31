# 📋 SEO Analyzer API - Чек-лист проверки

## 🎯 Общая информация
- **Базовый URL**: http://localhost:5000
- **Документация**: http://localhost:5000/docs
- **Формат данных**: JSON
- **Авторизация**: Bearer Token (JWT)

## 🔐 Авторизация

### ✅ Регистрация пользователя
- **Endpoint**: `POST /api/auth/register`
- **Тело запроса**:
```json
{
  "email": "test@example.com",
  "password": "password123"
}
```
- **Ожидаемый ответ**: 201 Created
- **Проверить**: Создание пользователя в БД

### ✅ Авторизация пользователя
- **Endpoint**: `POST /api/auth/login`
- **Тело запроса**:
```json
{
  "email": "test@example.com",
  "password": "password123"
}
```
- **Ожидаемый ответ**: 200 OK с access_token
- **Проверить**: Получение JWT токена

### ✅ Получение информации о пользователе
- **Endpoint**: `GET /api/auth/me`
- **Заголовки**: `Authorization: Bearer {token}`
- **Ожидаемый ответ**: 200 OK с данными пользователя

## 📁 Управление группами слов

### ✅ Создание группы слов
- **Endpoint**: `POST /api/word-groups`
- **Заголовки**: `Authorization: Bearer {token}`
- **Тело запроса**:
```json
{
  "name": "Моя тестовая группа"
}
```
- **Ожидаемый ответ**: 201 Created
- **Проверить**: UUID группы в ответе

### ✅ Получение списка групп
- **Endpoint**: `GET /api/word-groups`
- **Заголовки**: `Authorization: Bearer {token}`
- **Ожидаемый ответ**: 200 OK с массивом групп

### ✅ Обновление группы
- **Endpoint**: `PUT /api/word-groups/{group_id}`
- **Заголовки**: `Authorization: Bearer {token}`
- **Тело запроса**:
```json
{
  "name": "Обновленное название группы"
}
```
- **Ожидаемый ответ**: 200 OK

### ✅ Удаление группы
- **Endpoint**: `DELETE /api/word-groups/{group_id}`
- **Заголовки**: `Authorization: Bearer {token}`
- **Ожидаемый ответ**: 200 OK

## 🔤 Управление словами

### ✅ Создание слова
- **Endpoint**: `POST /api/words`
- **Заголовки**: `Authorization: Bearer {token}`
- **Тело запроса**:
```json
{
  "name": "тестовое ключевое слово",
  "group_id": "uuid-группы"
}
```
- **Ожидаемый ответ**: 201 Created

### ✅ Получение всех слов
- **Endpoint**: `GET /api/words`
- **Заголовки**: `Authorization: Bearer {token}`
- **Ожидаемый ответ**: 200 OK с массивом слов

### ✅ Получение слов по группе
- **Endpoint**: `GET /api/words?group_id={group_id}`
- **Заголовки**: `Authorization: Bearer {token}`
- **Ожидаемый ответ**: 200 OK с отфильтрованными словами

### ✅ Обновление слова
- **Endpoint**: `PUT /api/words/{word_id}`
- **Заголовки**: `Authorization: Bearer {token}`
- **Тело запроса**:
```json
{
  "name": "обновленное слово",
  "group_id": "uuid-группы",
  "status": 1
}
```
- **Ожидаемый ответ**: 200 OK

### ✅ Удаление слова (мягкое)
- **Endpoint**: `DELETE /api/words/{word_id}`
- **Заголовки**: `Authorization: Bearer {token}`
- **Ожидаемый ответ**: 200 OK
- **Проверить**: Статус слова изменился на неактивный

## 🤖 LLM Провайдеры

### ✅ Создание LLM провайдера
- **Endpoint**: `POST /api/llm`
- **Заголовки**: `Authorization: Bearer {token}`
- **Тело запроса**:
```json
{
  "name": "Test LLM",
  "api_url": "https://api.example.com/v1/chat",
  "api_key": "test_key_123"
}
```
- **Ожидаемый ответ**: 201 Created

### ✅ Получение списка LLM провайдеров
- **Endpoint**: `GET /api/llm`
- **Заголовки**: `Authorization: Bearer {token}`
- **Ожидаемый ответ**: 200 OK с массивом провайдеров

## 📊 Аналитика

### ✅ Аналитика по слову
- **Endpoint**: `GET /api/analytics/word/{word_id}`
- **Заголовки**: `Authorization: Bearer {token}`
- **Ожидаемый ответ**: 200 OK
- **Структура ответа**:
```json
{
  "word": {...},
  "serp_results": [...],
  "companies": [...]
}
```

### ✅ Аналитика по группе
- **Endpoint**: `GET /api/analytics/group/{group_id}`
- **Заголовки**: `Authorization: Bearer {token}`
- **Ожидаемый ответ**: 200 OK
- **Структура ответа**:
```json
{
  "group": {...},
  "words": [...]
}
```

### ✅ Общая статистика
- **Endpoint**: `GET /api/stats`
- **Заголовки**: `Authorization: Bearer {token}`
- **Ожидаемый ответ**: 200 OK
- **Проверить**: Счетчики пользователей, групп, слов

## ⚙️ Воркер

### ✅ Запуск цикла воркера
- **Endpoint**: `POST /api/worker/run-cycle`
- **Заголовки**: `Authorization: Bearer {token}`
- **Ожидаемый ответ**: 200 OK
- **Проверить**: Фоновая задача запущена

## 🔒 Проверки безопасности

### ✅ Доступ без токена
- **Тест**: Запросы к защищенным эндпоинтам без Authorization
- **Ожидаемый ответ**: 401 Unauthorized

### ✅ Доступ с неверным токеном
- **Тест**: Запросы с недействительным токеном
- **Ожидаемый ответ**: 401 Unauthorized

### ✅ Доступ к чужим данным
- **Тест**: Попытка доступа к данным другого пользователя
- **Ожидаемый ответ**: 403 Forbidden или 404 Not Found

## 🧪 Тестирование ошибок

### ✅ Валидация данных
- **Тест**: Отправка некорректных данных
- **Ожидаемый ответ**: 422 Unprocessable Entity

### ✅ Несуществующие ресурсы
- **Тест**: Запросы к несуществующим ID
- **Ожидаемый ответ**: 404 Not Found

### ✅ Дублирование данных
- **Тест**: Создание пользователя с существующим email
- **Ожидаемый ответ**: 400 Bad Request

## 📈 Производительность

### ✅ Время ответа
- **Проверить**: Все запросы выполняются < 2 секунд
- **Исключение**: Воркер может работать дольше

### ✅ Пагинация
- **Проверить**: Большие списки корректно обрабатываются

## 🔧 Curl команды для тестирования

### Регистрация
```bash
curl -X POST "http://localhost:5000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

### Авторизация
```bash
curl -X POST "http://localhost:5000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

### Создание группы (с токеном)
```bash
curl -X POST "http://localhost:5000/api/word-groups" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"name":"Тестовая группа"}'
```

### Получение групп
```bash
curl -X GET "http://localhost:5000/api/word-groups" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## ✅ Результаты проверки

- [ ] Все эндпоинты авторизации работают
- [ ] CRUD операции с группами работают
- [ ] CRUD операции со словами работают
- [ ] LLM провайдеры управляются корректно
- [ ] Аналитика возвращает данные
- [ ] Воркер запускается
- [ ] Безопасность соблюдается
- [ ] Ошибки обрабатываются корректно
- [ ] Производительность приемлемая

## 📝 Примечания

- Все UUID должны быть валидными
- Даты должны быть в ISO формате
- Пароли должны быть захешированы
- API ключи не должны возвращаться в ответах
- Логи должны записываться корректно

---
**Дата проверки**: ___________  
**Проверил**: ___________  
**Статус**: ___________
