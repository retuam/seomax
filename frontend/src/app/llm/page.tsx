'use client'

import { useState, useEffect } from 'react'
import Layout from '@/components/Layout'
import { llmAPI } from '@/lib/api'
import type { LLMProvider } from '@/lib/api'
import toast from 'react-hot-toast'
import { Plus, Cpu, CheckCircle, XCircle } from 'lucide-react'

export default function LLMPage() {
  const [providers, setProviders] = useState<LLMProvider[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newProvider, setNewProvider] = useState({
    name: '',
    api_url: '',
    api_key: ''
  })

  useEffect(() => {
    loadProviders()
  }, [])

  const loadProviders = async () => {
    try {
      const response = await llmAPI.getAll()
      setProviders(response.data)
    } catch (error) {
      toast.error('Ошибка загрузки LLM провайдеров')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateProvider = async () => {
    if (!newProvider.name.trim()) {
      toast.error('Введите название провайдера')
      return
    }

    try {
      await llmAPI.create(newProvider)
      toast.success('LLM провайдер создан')
      setNewProvider({ name: '', api_url: '', api_key: '' })
      setShowCreateModal(false)
      loadProviders()
    } catch (error) {
      toast.error('Ошибка создания провайдера')
    }
  }

  const predefinedProviders = [
    {
      name: 'OpenAI GPT',
      api_url: 'https://api.openai.com/v1/chat/completions',
      description: 'GPT-3.5 и GPT-4 модели от OpenAI'
    },
    {
      name: 'Google Gemini',
      api_url: 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent',
      description: 'Gemini Pro модель от Google'
    },
    {
      name: 'Anthropic Claude',
      api_url: 'https://api.anthropic.com/v1/messages',
      description: 'Claude модели от Anthropic'
    },
    {
      name: 'Grok',
      api_url: 'https://api.grok.com/v1/chat/completions',
      description: 'Grok модель от X.AI'
    },
    {
      name: 'Mistral AI',
      api_url: 'https://api.mistral.ai/v1/chat/completions',
      description: 'Mistral модели'
    },
    {
      name: 'Perplexity',
      api_url: 'https://api.perplexity.ai/chat/completions',
      description: 'Perplexity AI модели'
    }
  ]

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
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">LLM Провайдеры</h1>
            <p className="mt-2 text-gray-600">
              Управление интеграциями с различными LLM сервисами
            </p>
          </div>
          
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-primary flex items-center space-x-2"
          >
            <Plus className="h-4 w-4" />
            <span>Добавить провайдера</span>
          </button>
        </div>

        {/* Current Providers */}
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Активные провайдеры
          </h2>
          
          {providers.length > 0 ? (
            <div className="space-y-4">
              {providers.map((provider) => (
                <div key={provider.uuid} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-4">
                    <div className="p-2 bg-primary-100 rounded-lg">
                      <Cpu className="h-6 w-6 text-primary-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{provider.name}</h3>
                      <p className="text-sm text-gray-600">{provider.api_url}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    {provider.is_active === 1 ? (
                      <div className="flex items-center space-x-1 text-green-600">
                        <CheckCircle className="h-4 w-4" />
                        <span className="text-sm">Активен</span>
                      </div>
                    ) : (
                      <div className="flex items-center space-x-1 text-red-600">
                        <XCircle className="h-4 w-4" />
                        <span className="text-sm">Неактивен</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <Cpu className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">LLM провайдеры не настроены</p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="mt-4 btn-primary"
              >
                Добавить первого провайдера
              </button>
            </div>
          )}
        </div>

        {/* Predefined Providers */}
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Рекомендуемые провайдеры
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {predefinedProviders.map((provider) => (
              <div key={provider.name} className="p-4 border border-gray-200 rounded-lg hover:border-primary-300 transition-colors">
                <div className="flex items-center space-x-3 mb-2">
                  <Cpu className="h-5 w-5 text-primary-600" />
                  <h3 className="font-semibold text-gray-900">{provider.name}</h3>
                </div>
                <p className="text-sm text-gray-600 mb-3">{provider.description}</p>
                <button
                  onClick={() => {
                    setNewProvider({
                      name: provider.name,
                      api_url: provider.api_url,
                      api_key: ''
                    })
                    setShowCreateModal(true)
                  }}
                  className="text-primary-600 hover:text-primary-700 text-sm font-medium"
                >
                  Добавить →
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Integration Info */}
        <div className="card bg-blue-50 border-blue-200">
          <div className="flex items-start space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Cpu className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <h3 className="font-semibold text-blue-900 mb-2">
                Как работает интеграция
              </h3>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• Система автоматически запрашивает SERP данные каждые 2 недели</li>
                <li>• Каждое активное слово обрабатывается всеми настроенными LLM</li>
                <li>• Из результатов извлекаются компании и бренды</li>
                <li>• Все данные сохраняются для аналитики</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Create Provider Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-96 max-w-full mx-4">
              <h3 className="text-lg font-semibold mb-4">Добавить LLM провайдера</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Название
                  </label>
                  <input
                    type="text"
                    placeholder="Например: OpenAI GPT"
                    value={newProvider.name}
                    onChange={(e) => setNewProvider({ ...newProvider, name: e.target.value })}
                    className="input-field"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    API URL
                  </label>
                  <input
                    type="url"
                    placeholder="https://api.example.com/v1/chat/completions"
                    value={newProvider.api_url}
                    onChange={(e) => setNewProvider({ ...newProvider, api_url: e.target.value })}
                    className="input-field"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    API Key (опционально)
                  </label>
                  <input
                    type="password"
                    placeholder="Будет использоваться из переменных окружения"
                    value={newProvider.api_key}
                    onChange={(e) => setNewProvider({ ...newProvider, api_key: e.target.value })}
                    className="input-field"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Рекомендуется настраивать API ключи через переменные окружения
                  </p>
                </div>
              </div>
              
              <div className="flex space-x-3 mt-6">
                <button onClick={handleCreateProvider} className="btn-primary">
                  Добавить
                </button>
                <button 
                  onClick={() => {
                    setShowCreateModal(false)
                    setNewProvider({ name: '', api_url: '', api_key: '' })
                  }}
                  className="btn-secondary"
                >
                  Отмена
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  )
}
