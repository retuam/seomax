'use client'

import { useState, useEffect } from 'react'
import Layout from '@/components/Layout'
import { groupsAPI, analyticsAPI } from '@/lib/api'
import type { WordGroup, WordAnalytics } from '@/lib/api'
import toast from 'react-hot-toast'
import { BarChart3, TrendingUp, Building, Search, Calendar } from 'lucide-react'

export default function AnalyticsPage() {
  const [groups, setGroups] = useState<WordGroup[]>([])
  const [selectedGroup, setSelectedGroup] = useState<string>('')
  const [analytics, setAnalytics] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [analyticsLoading, setAnalyticsLoading] = useState(false)

  useEffect(() => {
    loadGroups()
  }, [])

  useEffect(() => {
    if (selectedGroup) {
      loadAnalytics()
    }
  }, [selectedGroup])

  const loadGroups = async () => {
    try {
      const response = await groupsAPI.getAll()
      setGroups(response.data)
      if (response.data.length > 0) {
        setSelectedGroup(response.data[0].uuid)
      }
    } catch (error) {
      toast.error('Ошибка загрузки групп')
    } finally {
      setLoading(false)
    }
  }

  const loadAnalytics = async () => {
    if (!selectedGroup) return

    setAnalyticsLoading(true)
    try {
      const response = await analyticsAPI.getGroupAnalytics(selectedGroup)
      setAnalytics(response.data)
    } catch (error) {
      toast.error('Ошибка загрузки аналитики')
      setAnalytics(null)
    } finally {
      setAnalyticsLoading(false)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ru-RU', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
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
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Аналитика</h1>
            <p className="mt-2 text-gray-600">
              Анализ SERP результатов и найденных компаний
            </p>
          </div>
          
          {groups.length > 0 && (
            <select
              value={selectedGroup}
              onChange={(e) => setSelectedGroup(e.target.value)}
              className="input-field w-64"
            >
              {groups.map((group) => (
                <option key={group.uuid} value={group.uuid}>
                  {group.name}
                </option>
              ))}
            </select>
          )}
        </div>

        {groups.length === 0 ? (
          <div className="text-center py-12">
            <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500 text-lg">Нет данных для анализа</p>
            <p className="text-gray-400 mt-2">Создайте группы и добавьте ключевые слова</p>
          </div>
        ) : analyticsLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          </div>
        ) : analytics ? (
          <div className="space-y-6">
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="card">
                <div className="flex items-center">
                  <div className="p-3 rounded-lg bg-blue-100">
                    <Search className="h-6 w-6 text-blue-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Слов в группе</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {analytics.words?.length || 0}
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="card">
                <div className="flex items-center">
                  <div className="p-3 rounded-lg bg-green-100">
                    <TrendingUp className="h-6 w-6 text-green-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">SERP результатов</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {analytics.words?.reduce((sum: number, word: WordAnalytics) => 
                        sum + (word.serp_results?.length || 0), 0) || 0}
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="card">
                <div className="flex items-center">
                  <div className="p-3 rounded-lg bg-purple-100">
                    <Building className="h-6 w-6 text-purple-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Найдено компаний</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {analytics.words?.reduce((sum: number, word: WordAnalytics) => 
                        sum + (word.companies?.length || 0), 0) || 0}
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="card">
                <div className="flex items-center">
                  <div className="p-3 rounded-lg bg-orange-100">
                    <Calendar className="h-6 w-6 text-orange-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Последнее обновление</p>
                    <p className="text-sm font-bold text-gray-900">
                      {analytics.words?.length > 0 && analytics.words[0].serp_results?.length > 0
                        ? formatDate(analytics.words[0].serp_results[0].create_time)
                        : 'Нет данных'}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Words Analytics */}
            <div className="space-y-6">
              {analytics.words?.map((wordAnalytics: WordAnalytics) => (
                <div key={wordAnalytics.word.uuid} className="card">
                  <div className="border-b border-gray-200 pb-4 mb-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-xl font-semibold text-gray-900">
                        {wordAnalytics.word.name}
                      </h3>
                      <div className="flex items-center space-x-4 text-sm text-gray-600">
                        <span>{wordAnalytics.serp_results?.length || 0} SERP результатов</span>
                        <span>{wordAnalytics.companies?.length || 0} компаний</span>
                      </div>
                    </div>
                  </div>

                  {/* SERP Results */}
                  {wordAnalytics.serp_results && wordAnalytics.serp_results.length > 0 ? (
                    <div className="space-y-4">
                      <h4 className="font-semibold text-gray-900">SERP Результаты</h4>
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        {wordAnalytics.serp_results.slice(0, 4).map((serp) => (
                          <div key={serp.uuid} className="p-4 bg-gray-50 rounded-lg">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-sm font-medium text-gray-600">
                                LLM: {serp.llm_id}
                              </span>
                              <span className="text-xs text-gray-500">
                                {formatDate(serp.create_time)}
                              </span>
                            </div>
                            <p className="text-sm text-gray-800 line-clamp-3">
                              {serp.content.substring(0, 200)}...
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-8 text-gray-500">
                      <Search className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                      <p>SERP данные еще не собраны</p>
                    </div>
                  )}

                  {/* Companies */}
                  {wordAnalytics.companies && wordAnalytics.companies.length > 0 && (
                    <div className="mt-6 pt-4 border-t border-gray-200">
                      <h4 className="font-semibold text-gray-900 mb-3">
                        Найденные компании ({wordAnalytics.companies.length})
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {wordAnalytics.companies.slice(0, 20).map((company) => (
                          <span
                            key={company.uuid}
                            className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                          >
                            {company.name}
                          </span>
                        ))}
                        {wordAnalytics.companies.length > 20 && (
                          <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-sm">
                            +{wordAnalytics.companies.length - 20} еще
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )) || (
                <div className="text-center py-12">
                  <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">В выбранной группе нет слов</p>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="text-center py-12">
            <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">Выберите группу для просмотра аналитики</p>
          </div>
        )}
      </div>
    </Layout>
  )
}
