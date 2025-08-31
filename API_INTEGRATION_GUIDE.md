# 🚀 API Integration Guide - Подключение React Vite к SEO Analyzer API

## 📋 Обзор

Ваш SEO Analyzer уже имеет **полноценный REST API**, готовый для подключения React Vite frontend. Все эндпоинты работают, документация доступна, нужно только правильно настроить интеграцию.

---

## 🔧 Что у вас уже есть (готово к использованию)

### ✅ Backend API (FastAPI)
- **Базовый URL**: `http://localhost:5000`
- **Документация**: `http://localhost:5000/docs` (Swagger UI)
- **Формат**: JSON REST API
- **Авторизация**: JWT Bearer Token
- **CORS**: Настроен для frontend подключения

### ✅ Готовые эндпоинты (20+ endpoints)

#### 🔐 Авторизация
```http
POST /api/auth/register    # Регистрация
POST /api/auth/login       # Логин  
GET  /api/auth/me          # Информация о пользователе
```

#### 📁 Группы слов
```http
GET    /api/word-groups           # Список групп
POST   /api/word-groups           # Создание группы
PUT    /api/word-groups/{id}      # Обновление группы
DELETE /api/word-groups/{id}      # Удаление группы
```

#### 🔤 Ключевые слова
```http
GET    /api/words                 # Список слов
POST   /api/words                 # Создание слова
PUT    /api/words/{id}            # Обновление слова
DELETE /api/words/{id}            # Удаление слова
```

#### 🤖 LLM провайдеры
```http
GET    /api/llm                   # Список провайдеров
POST   /api/llm                   # Добавление провайдера
PUT    /api/llm/{id}              # Обновление провайдера
DELETE /api/llm/{id}              # Удаление провайдера
```

#### 📊 Аналитика
```http
GET /api/analytics/word/{id}      # Аналитика по слову
GET /api/analytics/group/{id}     # Аналитика по группе
GET /api/stats                    # Общая статистика
```

#### 🏷️ Brand Monitoring
```http
GET    /api/brand-projects        # Список проектов
POST   /api/brand-projects        # Создание проекта
GET    /api/brand-projects/{id}   # Получение проекта
DELETE /api/brand-projects/{id}   # Удаление проекта
GET    /api/brand-projects/{id}/analytics # Аналитика бренда
```

---

## 🛠 Что нужно сделать для React Vite

### 1. 📦 Установка зависимостей

```bash
npm create vite@latest seo-analyzer-frontend -- --template react-ts
cd seo-analyzer-frontend
npm install

# Установка дополнительных пакетов
npm install axios react-router-dom @types/react-router-dom
npm install react-hook-form @hookform/resolvers yup
npm install react-hot-toast lucide-react
npm install @headlessui/react clsx tailwindcss
```

### 2. 🔧 Настройка Axios для API

Создайте `src/lib/api.ts`:

```typescript
import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000';

// Создаем экземпляр axios
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Интерсептор для добавления токена
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Интерсептор для обработки ошибок
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

### 3. 🔐 Сервис авторизации

Создайте `src/services/auth.ts`:

```typescript
import { api } from '../lib/api';

export interface LoginData {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
}

export interface User {
  uuid: string;
  email: string;
  create_time: string;
  status: number;
}

export const authService = {
  async login(data: LoginData) {
    const response = await api.post('/api/auth/login', data);
    const { access_token } = response.data;
    localStorage.setItem('access_token', access_token);
    return response.data;
  },

  async register(data: RegisterData) {
    const response = await api.post('/api/auth/register', data);
    return response.data;
  },

  async getCurrentUser(): Promise<User> {
    const response = await api.get('/api/auth/me');
    return response.data;
  },

  logout() {
    localStorage.removeItem('access_token');
    window.location.href = '/login';
  },

  isAuthenticated() {
    return !!localStorage.getItem('access_token');
  }
};
```

### 4. 📝 Сервис для работы со словами

Создайте `src/services/words.ts`:

```typescript
import { api } from '../lib/api';

export interface WordGroup {
  uuid: string;
  name: string;
}

export interface Word {
  uuid: string;
  name: string;
  group_id?: string;
  create_time: string;
  update_time?: string;
  status: number;
}

export const wordsService = {
  // Группы слов
  async getWordGroups(): Promise<WordGroup[]> {
    const response = await api.get('/api/word-groups');
    return response.data;
  },

  async createWordGroup(name: string): Promise<WordGroup> {
    const response = await api.post('/api/word-groups', { name });
    return response.data;
  },

  async updateWordGroup(id: string, name: string): Promise<WordGroup> {
    const response = await api.put(`/api/word-groups/${id}`, { name });
    return response.data;
  },

  async deleteWordGroup(id: string): Promise<void> {
    await api.delete(`/api/word-groups/${id}`);
  },

  // Ключевые слова
  async getWords(groupId?: string): Promise<Word[]> {
    const params = groupId ? { group_id: groupId } : {};
    const response = await api.get('/api/words', { params });
    return response.data;
  },

  async createWord(name: string, groupId?: string): Promise<Word> {
    const response = await api.post('/api/words', { 
      name, 
      group_id: groupId 
    });
    return response.data;
  },

  async updateWord(id: string, data: Partial<Word>): Promise<Word> {
    const response = await api.put(`/api/words/${id}`, data);
    return response.data;
  },

  async deleteWord(id: string): Promise<void> {
    await api.delete(`/api/words/${id}`);
  }
};
```

### 5. 🏷️ Сервис Brand Monitoring

Создайте `src/services/brandMonitoring.ts`:

```typescript
import { api } from '../lib/api';

export interface BrandProject {
  uuid: string;
  name: string;
  brand_name: string;
  brand_description: string;
  keywords_count: number;
  user_id: string;
  word_group_id?: string;
  create_time: string;
  status: number;
  competitors: Competitor[];
}

export interface Competitor {
  uuid: string;
  name: string;
  create_time: string;
}

export interface CreateBrandProjectData {
  name: string;
  brand_name: string;
  brand_description: string;
  keywords_count: number;
  competitors: string[];
}

export const brandMonitoringService = {
  async getBrandProjects(): Promise<BrandProject[]> {
    const response = await api.get('/api/brand-projects');
    return response.data;
  },

  async createBrandProject(data: CreateBrandProjectData): Promise<BrandProject> {
    const response = await api.post('/api/brand-projects', data);
    return response.data;
  },

  async getBrandProject(id: string): Promise<BrandProject> {
    const response = await api.get(`/api/brand-projects/${id}`);
    return response.data;
  },

  async deleteBrandProject(id: string): Promise<void> {
    await api.delete(`/api/brand-projects/${id}`);
  },

  async getBrandAnalytics(id: string) {
    const response = await api.get(`/api/brand-projects/${id}/analytics`);
    return response.data;
  }
};
```

### 6. 📊 Сервис аналитики

Создайте `src/services/analytics.ts`:

```typescript
import { api } from '../lib/api';

export const analyticsService = {
  async getWordAnalytics(wordId: string) {
    const response = await api.get(`/api/analytics/word/${wordId}`);
    return response.data;
  },

  async getGroupAnalytics(groupId: string) {
    const response = await api.get(`/api/analytics/group/${groupId}`);
    return response.data;
  },

  async getStats() {
    const response = await api.get('/api/stats');
    return response.data;
  }
};
```

### 7. 🎨 Пример React компонента

Создайте `src/components/WordGroups.tsx`:

```typescript
import React, { useState, useEffect } from 'react';
import { wordsService, WordGroup } from '../services/words';
import toast from 'react-hot-toast';

export const WordGroups: React.FC = () => {
  const [groups, setGroups] = useState<WordGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [newGroupName, setNewGroupName] = useState('');

  useEffect(() => {
    loadGroups();
  }, []);

  const loadGroups = async () => {
    try {
      const data = await wordsService.getWordGroups();
      setGroups(data);
    } catch (error) {
      toast.error('Ошибка загрузки групп');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateGroup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newGroupName.trim()) return;

    try {
      const newGroup = await wordsService.createWordGroup(newGroupName);
      setGroups([...groups, newGroup]);
      setNewGroupName('');
      toast.success('Группа создана');
    } catch (error) {
      toast.error('Ошибка создания группы');
    }
  };

  const handleDeleteGroup = async (id: string) => {
    if (!confirm('Удалить группу?')) return;

    try {
      await wordsService.deleteWordGroup(id);
      setGroups(groups.filter(g => g.uuid !== id));
      toast.success('Группа удалена');
    } catch (error) {
      toast.error('Ошибка удаления группы');
    }
  };

  if (loading) return <div>Загрузка...</div>;

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Группы слов</h1>
      
      <form onSubmit={handleCreateGroup} className="mb-6">
        <div className="flex gap-2">
          <input
            type="text"
            value={newGroupName}
            onChange={(e) => setNewGroupName(e.target.value)}
            placeholder="Название новой группы"
            className="flex-1 px-3 py-2 border rounded"
          />
          <button
            type="submit"
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Создать
          </button>
        </div>
      </form>

      <div className="grid gap-4">
        {groups.map((group) => (
          <div key={group.uuid} className="p-4 border rounded flex justify-between items-center">
            <h3 className="font-medium">{group.name}</h3>
            <button
              onClick={() => handleDeleteGroup(group.uuid)}
              className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600"
            >
              Удалить
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};
```

---

## 🚀 Запуск и тестирование

### 1. Запуск Backend
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 5000
```

### 2. Запуск Frontend
```bash
cd seo-analyzer-frontend
npm run dev
```

### 3. Тестирование API
- Откройте `http://localhost:5000/docs` для Swagger UI
- Протестируйте эндпоинты через интерфейс
- Проверьте CORS настройки

---

## 🔧 Дополнительные настройки

### Environment Variables (.env)
```env
VITE_API_BASE_URL=http://localhost:5000
VITE_APP_NAME=SEO Analyzer
```

### Vite Config (vite.config.ts)
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      }
    }
  }
})
```

---

## 📋 Чек-лист готовности

### ✅ Backend готов:
- [x] FastAPI сервер запущен
- [x] База данных инициализирована  
- [x] API эндпоинты работают
- [x] JWT авторизация настроена
- [x] CORS настроен
- [x] Swagger документация доступна

### 🔧 Frontend нужно создать:
- [ ] React Vite проект
- [ ] Axios настройка
- [ ] Сервисы для API
- [ ] Компоненты UI
- [ ] Роутинг
- [ ] Авторизация

---

## 🎯 Заключение

**Ваш API уже готов к использованию!** Нужно только создать React Vite frontend и подключить его к существующим эндпоинтам. Все необходимые сервисы и примеры кода предоставлены выше.

**Следующие шаги:**
1. Создайте React Vite проект
2. Скопируйте предоставленные сервисы
3. Создайте UI компоненты
4. Протестируйте интеграцию
5. Деплойте на Netlify/Vercel

Ваш SEO Analyzer с Brand Monitoring готов стать полноценным SaaS продуктом! 🚀
