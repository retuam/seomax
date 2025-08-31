'use client'

import { useState, useEffect } from 'react'
import Layout from '@/components/Layout'
import { statsAPI, workerAPI } from '@/lib/api'
import type { Stats } from '@/lib/api'
import toast from 'react-hot-toast'
import { 
  Tag as TagIcon, 
  FileText as DocumentTextIcon, 
  Cpu as CpuChipIcon, 
  Building as BuildingOfficeIcon,
  Play as PlayIcon
} from 'lucide-react'

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [runningWorker, setRunningWorker] = useState(false)

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

  const statCards = [
    {
      title: 'Группы слов',
      value: stats?.groups_count || 0,
      icon: TagIcon,
      color: 'bg-blue-500',
    },
    {
      title: 'Активные слова',
      value: stats?.words_count || 0,
      icon: DocumentTextIcon,
      color: 'bg-green-500',
    },
    {
      title: 'SERP результаты',
      value: stats?.serp_results_count || 0,
      icon: CpuChipIcon,
      color: 'bg-purple-500',
    },
    {
      title: 'Найденные компании',
      value: stats?.companies_count || 0,
      icon: BuildingOfficeIcon,
      color: 'bg-orange-500',
    },
  ]

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Панель управления</h1>
            <p className="mt-2 text-gray-600">
              Обзор вашего SEO анализа и управление системой
            </p>
          </div>
          
          <button
            onClick={runWorkerCycle}
            disabled={runningWorker}
            className="btn-primary flex items-center space-x-2"
          >
            {runningWorker ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            ) : (
              <PlayIcon className="h-4 w-4" />
            )}
            <span>Запустить обновление SERP</span>
          </button>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {statCards.map((stat) => (
            <div key={stat.title} className="card">
              <div className="flex items-center">
                <div className={`p-3 rounded-lg ${stat.color}`}>
                  <stat.icon className="h-6 w-6 text-white" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                  <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Быстрые действия
            </h3>
            <div className="space-y-3">
              <a
                href="/groups"
                className="block p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-center">
                  <TagIcon className="h-5 w-5 text-gray-500 mr-3" />
                  <div>
                    <p className="font-medium text-gray-900">Управление группами</p>
                    <p className="text-sm text-gray-600">Создание и редактирование групп слов</p>
                  </div>
                </div>
              </a>
              
              <a
                href="/llm"
                className="block p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-center">
                  <CpuChipIcon className="h-5 w-5 text-gray-500 mr-3" />
                  <div>
                    <p className="font-medium text-gray-900">LLM провайдеры</p>
                    <p className="text-sm text-gray-600">Настройка интеграций с LLM</p>
                  </div>
                </div>
              </a>
              
              <a
                href="/analytics"
                className="block p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-center">
                  <DocumentTextIcon className="h-5 w-5 text-gray-500 mr-3" />
                  <div>
                    <p className="font-medium text-gray-900">Аналитика</p>
                    <p className="text-sm text-gray-600">Просмотр результатов анализа</p>
                  </div>
                </div>
              </a>
            </div>
          </div>

          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Информация о системе
            </h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Статус воркера:</span>
                <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-sm">
                  Активен
                </span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Интервал обновления:</span>
                <span className="text-gray-900">2 недели</span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Активные LLM:</span>
                <span className="text-gray-900">3 из 6</span>
              </div>
              
              <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-800">
                  💡 Система автоматически обновляет SERP данные каждые 2 недели для всех активных слов
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}
