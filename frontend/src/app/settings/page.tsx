'use client'

import { useState, useEffect } from 'react'
import Layout from '@/components/Layout'
import { useAuth } from '@/contexts/AuthContext'
import { workerAPI, statsAPI } from '@/lib/api'
import toast from 'react-hot-toast'
import { 
  Settings as SettingsIcon, 
  User, 
  Cpu, 
  Play, 
  RefreshCw,
  Info,
  Shield,
  Database
} from 'lucide-react'

export default function SettingsPage() {
  const { user } = useAuth()
  const [stats, setStats] = useState<any>(null)
  const [runningWorker, setRunningWorker] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      const response = await statsAPI.getStats()
      setStats(response.data)
    } catch (error) {
      toast.error('Ошибка загрузки статистики')
    } finally {
      setLoading(false)
    }
  }

  const runWorkerCycle = async () => {
    setRunningWorker(true)
    try {
      await workerAPI.runCycle()
      toast.success('Цикл обновления SERP данных запущен в фоне')
      // Обновляем статистику через 5 секунд
      setTimeout(loadStats, 5000)
    } catch (error) {
      toast.error('Ошибка запуска воркера')
    } finally {
      setRunningWorker(false)
    }
  }

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Настройки</h1>
          <p className="mt-2 text-gray-600">
            Управление системой и конфигурация SEO анализатора
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* User Info */}
          <div className="card">
            <div className="flex items-center space-x-3 mb-4">
              <User className="h-5 w-5 text-primary-600" />
              <h2 className="text-lg font-semibold text-gray-900">Профиль пользователя</h2>
            </div>
            
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-600">Email</label>
                <p className="text-gray-900">{user?.email}</p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-600">Дата регистрации</label>
                <p className="text-gray-900">
                  {user?.create_time ? new Date(user.create_time).toLocaleDateString('ru-RU') : 'Не указана'}
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-600">Статус</label>
                <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                  user?.status === 1 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {user?.status === 1 ? 'Активен' : 'Неактивен'}
                </span>
              </div>
            </div>
          </div>

          {/* System Stats */}
          <div className="card">
            <div className="flex items-center space-x-3 mb-4">
              <Database className="h-5 w-5 text-primary-600" />
              <h2 className="text-lg font-semibold text-gray-900">Статистика системы</h2>
            </div>
            
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Групп слов:</span>
                <span className="font-medium">{stats?.groups_count || 0}</span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-gray-600">Активных слов:</span>
                <span className="font-medium">{stats?.words_count || 0}</span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-gray-600">SERP результатов:</span>
                <span className="font-medium">{stats?.serp_results_count || 0}</span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-gray-600">Найдено компаний:</span>
                <span className="font-medium">{stats?.companies_count || 0}</span>
              </div>
            </div>
            
            <button
              onClick={loadStats}
              className="mt-4 w-full btn-secondary flex items-center justify-center space-x-2"
            >
              <RefreshCw className="h-4 w-4" />
              <span>Обновить статистику</span>
            </button>
          </div>

          {/* Worker Control */}
          <div className="card">
            <div className="flex items-center space-x-3 mb-4">
              <Cpu className="h-5 w-5 text-primary-600" />
              <h2 className="text-lg font-semibold text-gray-900">Управление воркером</h2>
            </div>
            
            <div className="space-y-4">
              <div className="p-3 bg-blue-50 rounded-lg">
                <div className="flex items-center space-x-2 mb-2">
                  <Info className="h-4 w-4 text-blue-600" />
                  <span className="text-sm font-medium text-blue-900">Информация</span>
                </div>
                <p className="text-sm text-blue-800">
                  Воркер автоматически обновляет SERP данные каждые 2 недели для всех активных слов.
                </p>
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Статус:</span>
                  <span className="text-green-600 font-medium">Активен</span>
                </div>
                
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Интервал:</span>
                  <span className="font-medium">2 недели</span>
                </div>
                
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">LLM провайдеров:</span>
                  <span className="font-medium">3 активных</span>
                </div>
              </div>
              
              <button
                onClick={runWorkerCycle}
                disabled={runningWorker}
                className="w-full btn-primary flex items-center justify-center space-x-2"
              >
                {runningWorker ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                ) : (
                  <Play className="h-4 w-4" />
                )}
                <span>
                  {runningWorker ? 'Запуск...' : 'Запустить цикл обновления'}
                </span>
              </button>
            </div>
          </div>
        </div>

        {/* System Information */}
        <div className="card">
          <div className="flex items-center space-x-3 mb-6">
            <SettingsIcon className="h-5 w-5 text-primary-600" />
            <h2 className="text-xl font-semibold text-gray-900">Информация о системе</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div>
              <h3 className="font-semibold text-gray-900 mb-3">Backend</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• FastAPI</li>
                <li>• PostgreSQL</li>
                <li>• SQLAlchemy (async)</li>
                <li>• JWT авторизация</li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-semibold text-gray-900 mb-3">Frontend</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Next.js 14 (App Router)</li>
                <li>• TypeScript</li>
                <li>• Tailwind CSS</li>
                <li>• React Hook Form</li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-semibold text-gray-900 mb-3">LLM Интеграции</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• OpenAI GPT</li>
                <li>• Google Gemini</li>
                <li>• Anthropic Claude</li>
                <li>• Grok, Mistral, Perplexity</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Security Settings */}
        <div className="card">
          <div className="flex items-center space-x-3 mb-4">
            <Shield className="h-5 w-5 text-primary-600" />
            <h2 className="text-lg font-semibold text-gray-900">Безопасность</h2>
          </div>
          
          <div className="space-y-4">
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <Shield className="h-4 w-4 text-green-600" />
                <span className="text-sm font-medium text-green-900">Система защищена</span>
              </div>
              <ul className="text-sm text-green-800 space-y-1">
                <li>✓ JWT токены для авторизации</li>
                <li>✓ Bcrypt хеширование паролей</li>
                <li>✓ CORS настройки</li>
                <li>✓ Валидация данных</li>
              </ul>
            </div>
            
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <Info className="h-4 w-4 text-yellow-600" />
                <span className="text-sm font-medium text-yellow-900">Рекомендации</span>
              </div>
              <ul className="text-sm text-yellow-800 space-y-1">
                <li>• Регулярно обновляйте API ключи</li>
                <li>• Используйте сложные пароли</li>
                <li>• Мониторьте активность системы</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}
