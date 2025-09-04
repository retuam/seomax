# 🚀 SEO Analyzer Frontend - Проект для Lovable

## 📋 Описание проекта

**SEO Analyzer Frontend** - современный React приложение для анализа SEO ключевых слов с интеграцией множественных LLM провайдеров и мониторингом брендов. Подключается к готовому FastAPI backend через REST API.

### 🎯 Цель проекта
Создать интуитивный веб-интерфейс для управления SEO анализом, мониторинга брендов и работы с различными LLM провайдерами.

---

## 🛠 Технический стек

### Frontend (React + Vite)
- **React 18** - современная библиотека для UI
- **Vite** - быстрый сборщик и dev-сервер
- **TypeScript** - типизированный JavaScript
- **Tailwind CSS** - utility-first CSS фреймворк
- **React Router** - маршрутизация SPA
- **Axios** - HTTP клиент для API
- **React Hook Form** - управление формами
- **React Query (TanStack Query)** - управление состоянием сервера
- **Zustand** - легковесное управление состоянием
- **React Hot Toast** - уведомления
- **Lucide React** - иконки
- **Recharts** - графики и аналитика
- **Headless UI** - доступные компоненты

### Backend API (уже готов)
- **URL**: `http://165.227.141.253` или `https://api.yourdomain.com`
- **Документация**: `/docs` (Swagger UI)
- **Авторизация**: JWT Bearer токены

---

## 🏗 Структура проекта

```
src/
├── components/           # Переиспользуемые компоненты
│   ├── ui/              # Базовые UI компоненты
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── Modal.tsx
│   │   ├── Table.tsx
│   │   ├── Card.tsx
│   │   └── LoadingSpinner.tsx
│   ├── layout/          # Компоненты макета
│   │   ├── Header.tsx
│   │   ├── Sidebar.tsx
│   │   ├── Layout.tsx
│   │   └── Navigation.tsx
│   ├── forms/           # Формы
│   │   ├── LoginForm.tsx
│   │   ├── RegisterForm.tsx
│   │   ├── WordGroupForm.tsx
│   │   ├── WordForm.tsx
│   │   └── BrandProjectForm.tsx
│   └── charts/          # Компоненты графиков
│       ├── AnalyticsChart.tsx
│       ├── BrandChart.tsx
│       └── ComparisonChart.tsx
├── pages/               # Страницы приложения
│   ├── auth/
│   │   ├── LoginPage.tsx
│   │   └── RegisterPage.tsx
│   ├── dashboard/
│   │   └── DashboardPage.tsx
│   ├── groups/
│   │   ├── GroupsPage.tsx
│   │   ├── GroupDetailPage.tsx
│   │   └── CreateGroupPage.tsx
│   ├── words/
│   │   ├── WordsPage.tsx
│   │   └── WordDetailPage.tsx
│   ├── analytics/
│   │   ├── AnalyticsPage.tsx
│   │   └── ReportsPage.tsx
│   ├── brands/
│   │   ├── BrandsPage.tsx
│   │   ├── BrandDetailPage.tsx
│   │   └── CreateBrandPage.tsx
│   └── settings/
│       ├── SettingsPage.tsx
│       └── LLMSettingsPage.tsx
├── hooks/               # Кастомные хуки
│   ├── useAuth.ts
│   ├── useApi.ts
│   ├── useWordGroups.ts
│   ├── useWords.ts
│   ├── useBrands.ts
│   └── useAnalytics.ts
├── services/            # API сервисы
│   ├── api.ts           # Базовый API клиент
│   ├── auth.service.ts
│   ├── groups.service.ts
│   ├── words.service.ts
│   ├── brands.service.ts
│   └── analytics.service.ts
├── store/               # Управление состоянием
│   ├── authStore.ts
│   ├── appStore.ts
│   └── index.ts
├── types/               # TypeScript типы
│   ├── api.types.ts
│   ├── auth.types.ts
│   ├── groups.types.ts
│   ├── words.types.ts
│   └── brands.types.ts
├── utils/               # Утилиты
│   ├── constants.ts
│   ├── helpers.ts
│   ├── formatters.ts
│   └── validators.ts
├── styles/              # Стили
│   ├── globals.css
│   └── components.css
├── App.tsx              # Главный компонент
├── main.tsx             # Точка входа
└── vite-env.d.ts        # Типы Vite
```

---

## 🔗 API Интеграция

### Базовая конфигурация API

```typescript
// src/services/api.ts
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://165.227.141.253';

export const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Интерцептор для добавления токена
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Интерцептор для обработки ошибок
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

### Основные API Endpoints

#### Авторизация
```typescript
// POST /api/auth/register
interface RegisterRequest {
  email: string;
  password: string;
}

// POST /api/auth/login
interface LoginRequest {
  email: string;
  password: string;
}

interface LoginResponse {
  access_token: string;
  token_type: string;
}

// GET /api/auth/me
interface UserResponse {
  uuid: string;
  email: string;
  create_time: string;
  status: number;
}
```

#### Группы слов
```typescript
// GET /api/word-groups
// POST /api/word-groups
// PUT /api/word-groups/{id}
// DELETE /api/word-groups/{id}

interface WordGroup {
  uuid: string;
  name: string;
  words?: Word[];
}

interface WordGroupCreate {
  name: string;
}
```

#### Слова
```typescript
// GET /api/words?group_id={id}
// POST /api/words
// PUT /api/words/{id}
// DELETE /api/words/{id}

interface Word {
  uuid: string;
  name: string;
  group_id?: string;
  create_time: string;
  update_time?: string;
  status: number;
  serp_results?: WordSerp[];
}

interface WordCreate {
  name: string;
  group_id?: string;
}
```

#### Brand Monitoring
```typescript
// GET /api/brands
// POST /api/brands
// PUT /api/brands/{id}
// DELETE /api/brands/{id}

interface BrandProject {
  uuid: string;
  name: string;
  description: string;
  user_id: string;
  created_at: string;
  competitors?: Competitor[];
}

// GET /api/brands/{id}/analytics
interface BrandAnalytics {
  total_mentions: number;
  average_position: number;
  visibility_score: number;
  competitor_comparison: CompetitorStats[];
  timeline_data: TimelinePoint[];
}
```

#### Аналитика
```typescript
// GET /api/analytics/word/{id}
interface WordAnalytics {
  word_id: string;
  total_serp_results: number;
  llm_distribution: LLMStats[];
  companies_found: Company[];
  timeline: AnalyticsPoint[];
}

// GET /api/analytics/group/{id}
interface GroupAnalytics {
  group_id: string;
  total_words: number;
  active_words: number;
  total_serp_results: number;
  top_companies: Company[];
}

// GET /api/stats
interface SystemStats {
  total_users: number;
  total_words: number;
  total_groups: number;
  total_serp_results: number;
  llm_providers: LLMProvider[];
}
```

---

## 📱 Страницы и функционал

### 🔐 Авторизация
- **Страница входа** (`/login`)
  - Форма с email и паролем
  - Валидация полей
  - Обработка ошибок
  - Редирект после входа

- **Страница регистрации** (`/register`)
  - Форма регистрации
  - Подтверждение пароля
  - Валидация email

### 📊 Дашборд (`/dashboard`)
- **Общая статистика**
  - Количество слов, групп, SERP результатов
  - Активность LLM провайдеров
  - Последние обновления

- **Быстрые действия**
  - Создать группу слов
  - Добавить слово
  - Запустить анализ

- **Графики и метрики**
  - Динамика анализа
  - Топ компании
  - Распределение по LLM

### 📝 Управление группами (`/groups`)
- **Список групп**
  - Таблица с группами
  - Поиск и фильтрация
  - Количество слов в группе
  - Действия (редактировать, удалить)

- **Детали группы** (`/groups/{id}`)
  - Информация о группе
  - Список слов в группе
  - Аналитика группы
  - Добавление новых слов

- **Создание группы** (`/groups/create`)
  - Форма создания
  - Валидация названия

### 🔤 Управление словами (`/words`)
- **Список слов**
  - Таблица со всеми словами
  - Фильтрация по группам
  - Статус слов (активные/неактивные)
  - Последнее обновление SERP

- **Детали слова** (`/words/{id}`)
  - История SERP результатов
  - Найденные компании
  - Графики позиций
  - Сравнение по LLM

### 📈 Аналитика (`/analytics`)
- **Общая аналитика**
  - Сводные отчеты
  - Тренды и динамика
  - Экспорт данных

- **Отчеты** (`/analytics/reports`)
  - Детальные отчеты
  - Настраиваемые фильтры
  - Сравнительный анализ

### 🏷️ Brand Monitoring (`/brands`)
- **Список brand проектов**
  - Карточки проектов
  - Статистика по каждому
  - Создание нового проекта

- **Детали brand проекта** (`/brands/{id}`)
  - Информация о бренде
  - Список конкурентов
  - Ключевые слова проекта
  - Аналитика упоминаний
  - Графики позиций

- **Создание brand проекта** (`/brands/create`)
  - Форма с описанием бренда
  - Добавление конкурентов
  - Автогенерация ключевых слов

### ⚙️ Настройки (`/settings`)
- **Общие настройки**
  - Профиль пользователя
  - Уведомления

- **LLM провайдеры** (`/settings/llm`)
  - Список провайдеров
  - Статус активности
  - Настройка API ключей

---

## 🎨 UI/UX Дизайн

### Цветовая схема
```css
:root {
  /* Primary Colors */
  --primary-50: #eff6ff;
  --primary-500: #3b82f6;
  --primary-600: #2563eb;
  --primary-700: #1d4ed8;

  /* Gray Scale */
  --gray-50: #f9fafb;
  --gray-100: #f3f4f6;
  --gray-500: #6b7280;
  --gray-900: #111827;

  /* Success/Error */
  --green-500: #10b981;
  --red-500: #ef4444;
  --yellow-500: #f59e0b;
}
```

### Компоненты дизайна
- **Современный минималистичный дизайн**
- **Адаптивная верстка** для всех устройств
- **Темная/светлая тема** (опционально)
- **Анимации и переходы** для улучшения UX
- **Консистентная типографика**
- **Интуитивная навигация**

### Ключевые UI паттерны
- **Карточки** для отображения данных
- **Таблицы** с сортировкой и фильтрацией
- **Модальные окна** для форм
- **Dropdown меню** для действий
- **Breadcrumbs** для навигации
- **Skeleton loading** для загрузки
- **Toast уведомления** для обратной связи

---

## 🔧 Конфигурация окружения

### Environment Variables
```env
# .env.local
VITE_API_URL=http://165.227.141.253
VITE_APP_NAME=SEO Analyzer
VITE_APP_VERSION=1.0.0

# .env.production
VITE_API_URL=https://api.yourdomain.com
VITE_APP_NAME=SEO Analyzer
VITE_APP_VERSION=1.0.0
```

### Vite конфигурация
```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://165.227.141.253',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})
```

---

## 🚀 Основные функции для реализации

### 1. Система авторизации
- [ ] Компонент LoginForm с валидацией
- [ ] Компонент RegisterForm
- [ ] AuthContext для управления состоянием
- [ ] ProtectedRoute для защищенных страниц
- [ ] Автоматический logout при истечении токена

### 2. Управление группами слов
- [ ] Список групп с поиском и фильтрацией
- [ ] Форма создания/редактирования группы
- [ ] Модальное окно подтверждения удаления
- [ ] Drag & drop для сортировки

### 3. Управление словами
- [ ] Таблица слов с пагинацией
- [ ] Фильтрация по группам и статусу
- [ ] Массовые операции (активация/деактивация)
- [ ] Импорт слов из CSV/Excel

### 4. Аналитика и отчеты
- [ ] Интерактивные графики с Recharts
- [ ] Фильтры по датам и LLM провайдерам
- [ ] Экспорт данных в CSV/PDF
- [ ] Real-time обновления данных

### 5. Brand Monitoring
- [ ] Создание brand проектов с формой
- [ ] Управление конкурентами
- [ ] Автогенерация ключевых слов через API
- [ ] Детальная аналитика упоминаний
- [ ] Сравнительные графики с конкурентами

### 6. Настройки системы
- [ ] Управление LLM провайдерами
- [ ] Настройки уведомлений
- [ ] Профиль пользователя
- [ ] Настройки воркера

---

## 📦 Зависимости проекта

### Основные зависимости
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.8.0",
    "typescript": "^4.9.0",
    "axios": "^1.3.0",
    "react-hook-form": "^7.43.0",
    "@tanstack/react-query": "^4.24.0",
    "zustand": "^4.3.0",
    "react-hot-toast": "^2.4.0",
    "lucide-react": "^0.314.0",
    "recharts": "^2.5.0",
    "@headlessui/react": "^1.7.0",
    "clsx": "^1.2.0",
    "date-fns": "^2.29.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^3.1.0",
    "vite": "^4.1.0",
    "tailwindcss": "^3.2.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "@types/react": "^18.0.0",
    "@types/react-dom": "^18.0.0",
    "eslint": "^8.34.0",
    "prettier": "^2.8.0"
  }
}
```

---

## 🎯 Приоритеты разработки

### Фаза 1: Основа (MVP)
1. **Настройка проекта** - Vite + React + TypeScript + Tailwind
2. **Система авторизации** - Login/Register + JWT
3. **Базовая навигация** - Layout + Sidebar + Header
4. **API интеграция** - Axios + базовые сервисы

### Фаза 2: Основной функционал
1. **Управление группами** - CRUD операции
2. **Управление словами** - CRUD + фильтрация
3. **Базовая аналитика** - Простые графики
4. **Настройки** - Профиль + LLM провайдеры

### Фаза 3: Продвинутые функции
1. **Brand Monitoring** - Полный функционал
2. **Расширенная аналитика** - Детальные отчеты
3. **Экспорт данных** - CSV/PDF
4. **Real-time обновления** - WebSocket или polling

### Фаза 4: Улучшения UX
1. **Оптимизация производительности**
2. **Улучшенная анимация**
3. **Темная тема**
4. **Мобильная оптимизация**

---

## 🔍 Особенности интеграции с API

### Обработка ошибок
```typescript
// Централизованная обработка ошибок API
export const handleApiError = (error: any) => {
  if (error.response?.status === 401) {
    // Redirect to login
    window.location.href = '/login';
  } else if (error.response?.status === 403) {
    toast.error('Недостаточно прав доступа');
  } else if (error.response?.status >= 500) {
    toast.error('Ошибка сервера. Попробуйте позже.');
  } else {
    toast.error(error.response?.data?.detail || 'Произошла ошибка');
  }
};
```

### Кеширование данных
```typescript
// React Query для кеширования
export const useWordGroups = () => {
  return useQuery({
    queryKey: ['word-groups'],
    queryFn: () => groupsService.getAll(),
    staleTime: 5 * 60 * 1000, // 5 минут
  });
};
```

### Оптимистичные обновления
```typescript
// Оптимистичные обновления для лучшего UX
export const useCreateWordGroup = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: groupsService.create,
    onMutate: async (newGroup) => {
      // Отменяем исходящие запросы
      await queryClient.cancelQueries(['word-groups']);
      
      // Сохраняем предыдущее состояние
      const previousGroups = queryClient.getQueryData(['word-groups']);
      
      // Оптимистично обновляем
      queryClient.setQueryData(['word-groups'], (old: any) => [
        ...old,
        { ...newGroup, uuid: 'temp-id' }
      ]);
      
      return { previousGroups };
    },
    onError: (err, newGroup, context) => {
      // Откатываем при ошибке
      queryClient.setQueryData(['word-groups'], context?.previousGroups);
    },
    onSettled: () => {
      // Обновляем данные в любом случае
      queryClient.invalidateQueries(['word-groups']);
    },
  });
};
```

---

**Готово к разработке в Lovable! 🚀**

Этот проект создаст современный, функциональный frontend для вашего SEO Analyzer API с использованием React + Vite и всех необходимых инструментов для продуктивной разработки.
