'use client'

import { useState, useEffect } from 'react'
import Layout from '@/components/Layout'
import { llmAPI } from '@/lib/api'
import toast from 'react-hot-toast'
import { 
  Key, 
  Eye, 
  EyeOff, 
  Save, 
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertTriangle
} from 'lucide-react'

interface ApiKeyConfig {
  provider: string
  name: string
  description: string
  apiKey: string
  isConfigured: boolean
  isActive: boolean
  lastTested?: string
  status: 'success' | 'error' | 'warning' | 'unknown'
}

export default function ApiKeysPage() {
  const [apiKeys, setApiKeys] = useState<ApiKeyConfig[]>([
    {
      provider: 'openai',
      name: 'OpenAI GPT',
      description: 'GPT-3.5 и GPT-4 модели от OpenAI',
      apiKey: '',
      isConfigured: false,
      isActive: true,
      status: 'unknown'
    },
    {
      provider: 'gemini',
      name: 'Google Gemini',
      description: 'Gemini Pro модель от Google',
      apiKey: '',
      isConfigured: false,
      isActive: true,
      status: 'unknown'
    },
    {
      provider: 'anthropic',
      name: 'Anthropic Claude',
      description: 'Claude модели от Anthropic',
      apiKey: '',
      isConfigured: false,
      isActive: true,
      status: 'unknown'
    },
    {
      provider: 'grok',
      name: 'Grok',
      description: 'Grok модель от X.AI',
      apiKey: '',
      isConfigured: false,
      isActive: true,
      status: 'unknown'
    },
    {
      provider: 'mistral',
      name: 'Mistral AI',
      description: 'Mistral модели',
      apiKey: '',
      isConfigured: false,
      isActive: true,
      status: 'unknown'
    },
    {
      provider: 'perplexity',
      name: 'Perplexity',
      description: 'Perplexity AI модели',
      apiKey: '',
      isConfigured: false,
      isActive: true,
      status: 'unknown'
    }
  ])
  
  const [visibleKeys, setVisibleKeys] = useState<Set<string>>(new Set())
  const [loading, setLoading] = useState(false)
  const [testingProvider, setTestingProvider] = useState<string | null>(null)

  useEffect(() => {
    loadApiKeysStatus()
  }, [])

  const loadApiKeysStatus = async () => {
    try {
      // Здесь будет запрос к API для получения статуса ключей
      // Пока что используем моковые данные
      setApiKeys(prev => prev.map(key => ({
        ...key,
        isConfigured: Math.random() > 0.5,
        status: Math.random() > 0.3 ? 'success' : 'warning'
      })))
    } catch (error) {
      toast.error('Ошибка загрузки статуса API ключей')
    }
  }

  const toggleKeyVisibility = (provider: string) => {
    const newVisible = new Set(visibleKeys)
    if (newVisible.has(provider)) {
      newVisible.delete(provider)
    } else {
      newVisible.add(provider)
    }
    setVisibleKeys(newVisible)
  }

  const updateApiKey = (provider: string, value: string) => {
    setApiKeys(prev => prev.map(key => 
      key.provider === provider 
        ? { ...key, apiKey: value, isConfigured: value.length > 0 }
        : key
    ))
  }

  const saveApiKey = async (provider: string) => {
    const keyConfig = apiKeys.find(k => k.provider === provider)
    if (!keyConfig) return

    setLoading(true)
    try {
      // Здесь будет запрос к API для сохранения ключа
      await new Promise(resolve => setTimeout(resolve, 1000)) // Мок
      
      toast.success(`API ключ для ${keyConfig.name} сохранен`)
      
      // Обновляем статус
      setApiKeys(prev => prev.map(key => 
        key.provider === provider 
          ? { ...key, status: 'success', lastTested: new Date().toISOString() }
          : key
      ))
    } catch (error) {
      toast.error('Ошибка сохранения API ключа')
    } finally {
      setLoading(false)
    }
  }

  const testApiKey = async (provider: string) => {
    const keyConfig = apiKeys.find(k => k.provider === provider)
    if (!keyConfig || !keyConfig.apiKey) {
      toast.error('Введите API ключ для тестирования')
      return
    }

    setTestingProvider(provider)
    try {
      // Здесь будет запрос к API для тестирования ключа
      await new Promise(resolve => setTimeout(resolve, 2000)) // Мок
      
      const success = Math.random() > 0.3 // Мок результата
      
      if (success) {
        toast.success(`API ключ для ${keyConfig.name} работает`)
        setApiKeys(prev => prev.map(key => 
          key.provider === provider 
            ? { ...key, status: 'success', lastTested: new Date().toISOString() }
            : key
        ))
      } else {
        toast.error(`API ключ для ${keyConfig.name} недействителен`)
        setApiKeys(prev => prev.map(key => 
          key.provider === provider 
            ? { ...key, status: 'error', lastTested: new Date().toISOString() }
            : key
        ))
      }
    } catch (error) {
      toast.error('Ошибка тестирования API ключа')
      setApiKeys(prev => prev.map(key => 
        key.provider === provider 
          ? { ...key, status: 'error', lastTested: new Date().toISOString() }
          : key
      ))
    } finally {
      setTestingProvider(null)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'error':
        return <XCircle className="h-5 w-5 text-red-500" />
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />
      default:
        return <div className="h-5 w-5 bg-gray-300 rounded-full" />
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'success':
        return 'Работает'
      case 'error':
        return 'Ошибка'
      case 'warning':
        return 'Предупреждение'
      default:
        return 'Не проверен'
    }
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">API Ключи</h1>
            <p className="mt-2 text-gray-600">
              Настройка API ключей для интеграции с LLM провайдерами
            </p>
          </div>
          
          <button
            onClick={loadApiKeysStatus}
            className="btn-secondary flex items-center space-x-2"
          >
            <RefreshCw className="h-4 w-4" />
            <span>Обновить статус</span>
          </button>
        </div>

        {/* Warning */}
        <div className="card bg-yellow-50 border-yellow-200">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
            <div>
              <h3 className="font-semibold text-yellow-900 mb-2">
                Безопасность API ключей
              </h3>
              <ul className="text-sm text-yellow-800 space-y-1">
                <li>• API ключи хранятся в зашифрованном виде</li>
                <li>• Рекомендуется использовать переменные окружения в продакшене</li>
                <li>• Регулярно обновляйте ключи для безопасности</li>
                <li>• Не передавайте ключи третьим лицам</li>
              </ul>
            </div>
          </div>
        </div>

        {/* API Keys List */}
        <div className="space-y-4">
          {apiKeys.map((keyConfig) => (
            <div key={keyConfig.provider} className="card">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <Key className="h-5 w-5 text-primary-600" />
                  <div>
                    <h3 className="font-semibold text-gray-900">{keyConfig.name}</h3>
                    <p className="text-sm text-gray-600">{keyConfig.description}</p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  {getStatusIcon(keyConfig.status)}
                  <span className="text-sm text-gray-600">
                    {getStatusText(keyConfig.status)}
                  </span>
                </div>
              </div>

              <div className="space-y-4">
                {/* API Key Input */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    API Ключ
                  </label>
                  <div className="relative">
                    <input
                      type={visibleKeys.has(keyConfig.provider) ? 'text' : 'password'}
                      placeholder={`Введите ${keyConfig.name} API ключ`}
                      value={keyConfig.apiKey}
                      onChange={(e) => updateApiKey(keyConfig.provider, e.target.value)}
                      className="input-field pr-20"
                    />
                    <div className="absolute inset-y-0 right-0 flex items-center space-x-1 pr-3">
                      <button
                        type="button"
                        onClick={() => toggleKeyVisibility(keyConfig.provider)}
                        className="p-1 text-gray-400 hover:text-gray-600"
                      >
                        {visibleKeys.has(keyConfig.provider) ? (
                          <EyeOff className="h-4 w-4" />
                        ) : (
                          <Eye className="h-4 w-4" />
                        )}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center justify-between">
                  <div className="text-sm text-gray-500">
                    {keyConfig.lastTested && (
                      <span>
                        Последняя проверка: {new Date(keyConfig.lastTested).toLocaleString('ru-RU')}
                      </span>
                    )}
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => testApiKey(keyConfig.provider)}
                      disabled={!keyConfig.apiKey || testingProvider === keyConfig.provider}
                      className="btn-secondary text-sm flex items-center space-x-1"
                    >
                      {testingProvider === keyConfig.provider ? (
                        <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-gray-600"></div>
                      ) : (
                        <RefreshCw className="h-3 w-3" />
                      )}
                      <span>Тест</span>
                    </button>
                    
                    <button
                      onClick={() => saveApiKey(keyConfig.provider)}
                      disabled={!keyConfig.apiKey || loading}
                      className="btn-primary text-sm flex items-center space-x-1"
                    >
                      <Save className="h-3 w-3" />
                      <span>Сохранить</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Instructions */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Как получить API ключи
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">OpenAI</h4>
              <p className="text-sm text-gray-600 mb-2">
                1. Зарегистрируйтесь на platform.openai.com
              </p>
              <p className="text-sm text-gray-600 mb-2">
                2. Перейдите в раздел API Keys
              </p>
              <p className="text-sm text-gray-600">
                3. Создайте новый ключ
              </p>
            </div>
            
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Google Gemini</h4>
              <p className="text-sm text-gray-600 mb-2">
                1. Перейдите на ai.google.dev
              </p>
              <p className="text-sm text-gray-600 mb-2">
                2. Получите API ключ
              </p>
              <p className="text-sm text-gray-600">
                3. Включите Gemini API
              </p>
            </div>
            
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Anthropic Claude</h4>
              <p className="text-sm text-gray-600 mb-2">
                1. Зарегистрируйтесь на console.anthropic.com
              </p>
              <p className="text-sm text-gray-600 mb-2">
                2. Создайте API ключ
              </p>
              <p className="text-sm text-gray-600">
                3. Настройте лимиты
              </p>
            </div>
            
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Другие провайдеры</h4>
              <p className="text-sm text-gray-600 mb-2">
                Grok, Mistral, Perplexity - получите ключи
              </p>
              <p className="text-sm text-gray-600">
                на соответствующих платформах
              </p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}
