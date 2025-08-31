'use client'

import { useState, useEffect } from 'react'
import Layout from '@/components/Layout'
import { groupsAPI, wordsAPI } from '@/lib/api'
import type { WordGroup, Word } from '@/lib/api'
import toast from 'react-hot-toast'
import { Plus, Edit2, Trash2, ChevronDown, ChevronRight } from 'lucide-react'

export default function GroupsPage() {
  const [groups, setGroups] = useState<WordGroup[]>([])
  const [words, setWords] = useState<Record<string, Word[]>>({})
  const [loading, setLoading] = useState(true)
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set())
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showWordModal, setShowWordModal] = useState(false)
  const [selectedGroup, setSelectedGroup] = useState<WordGroup | null>(null)
  const [newGroupName, setNewGroupName] = useState('')
  const [newWordName, setNewWordName] = useState('')

  useEffect(() => {
    loadGroups()
  }, [])

  const loadGroups = async () => {
    try {
      const response = await groupsAPI.getAll()
      setGroups(response.data)
      
      // Загружаем слова для каждой группы
      const wordsData: Record<string, Word[]> = {}
      for (const group of response.data) {
        const wordsResponse = await wordsAPI.getAll(group.uuid)
        wordsData[group.uuid] = wordsResponse.data
      }
      setWords(wordsData)
    } catch (error) {
      toast.error('Ошибка загрузки групп')
    } finally {
      setLoading(false)
    }
  }

  const toggleGroup = (groupId: string) => {
    const newExpanded = new Set(expandedGroups)
    if (newExpanded.has(groupId)) {
      newExpanded.delete(groupId)
    } else {
      newExpanded.add(groupId)
    }
    setExpandedGroups(newExpanded)
  }

  const handleCreateGroup = async () => {
    if (!newGroupName.trim()) return

    try {
      await groupsAPI.create(newGroupName.trim())
      toast.success('Группа создана')
      setNewGroupName('')
      setShowCreateModal(false)
      loadGroups()
    } catch (error) {
      toast.error('Ошибка создания группы')
    }
  }

  const handleEditGroup = async () => {
    if (!selectedGroup || !newGroupName.trim()) return

    try {
      await groupsAPI.update(selectedGroup.uuid, newGroupName.trim())
      toast.success('Группа обновлена')
      setNewGroupName('')
      setShowEditModal(false)
      setSelectedGroup(null)
      loadGroups()
    } catch (error) {
      toast.error('Ошибка обновления группы')
    }
  }

  const handleDeleteGroup = async (group: WordGroup) => {
    if (!confirm(`Удалить группу "${group.name}"?`)) return

    try {
      await groupsAPI.delete(group.uuid)
      toast.success('Группа удалена')
      loadGroups()
    } catch (error) {
      toast.error('Ошибка удаления группы')
    }
  }

  const handleCreateWord = async () => {
    if (!selectedGroup || !newWordName.trim()) return

    try {
      await wordsAPI.create(newWordName.trim(), selectedGroup.uuid)
      toast.success('Слово добавлено')
      setNewWordName('')
      setShowWordModal(false)
      setSelectedGroup(null)
      loadGroups()
    } catch (error) {
      toast.error('Ошибка добавления слова')
    }
  }

  const handleDeleteWord = async (word: Word) => {
    if (!confirm(`Удалить слово "${word.name}"?`)) return

    try {
      await wordsAPI.delete(word.uuid)
      toast.success('Слово удалено')
      loadGroups()
    } catch (error) {
      toast.error('Ошибка удаления слова')
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
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Группы слов</h1>
            <p className="mt-2 text-gray-600">
              Управление группами ключевых слов для SEO анализа
            </p>
          </div>
          
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-primary flex items-center space-x-2"
          >
            <Plus className="h-4 w-4" />
            <span>Создать группу</span>
          </button>
        </div>

        {/* Groups List */}
        <div className="space-y-4">
          {groups.map((group) => (
            <div key={group.uuid} className="card">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <button
                    onClick={() => toggleGroup(group.uuid)}
                    className="p-1 hover:bg-gray-100 rounded"
                  >
                    {expandedGroups.has(group.uuid) ? (
                      <ChevronDown className="h-4 w-4" />
                    ) : (
                      <ChevronRight className="h-4 w-4" />
                    )}
                  </button>
                  <h3 className="text-lg font-semibold text-gray-900">
                    {group.name}
                  </h3>
                  <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded-full text-sm">
                    {words[group.uuid]?.length || 0} слов
                  </span>
                </div>
                
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => {
                      setSelectedGroup(group)
                      setShowWordModal(true)
                    }}
                    className="p-2 text-green-600 hover:bg-green-50 rounded"
                    title="Добавить слово"
                  >
                    <Plus className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => {
                      setSelectedGroup(group)
                      setNewGroupName(group.name)
                      setShowEditModal(true)
                    }}
                    className="p-2 text-blue-600 hover:bg-blue-50 rounded"
                    title="Редактировать"
                  >
                    <Edit2 className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => handleDeleteGroup(group)}
                    className="p-2 text-red-600 hover:bg-red-50 rounded"
                    title="Удалить"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>

              {/* Words List */}
              {expandedGroups.has(group.uuid) && (
                <div className="mt-4 pl-8 space-y-2">
                  {words[group.uuid]?.map((word) => (
                    <div key={word.uuid} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <span className="text-gray-900">{word.name}</span>
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          word.status === 1 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-gray-100 text-gray-600'
                        }`}>
                          {word.status === 1 ? 'Активно' : 'Неактивно'}
                        </span>
                      </div>
                      <button
                        onClick={() => handleDeleteWord(word)}
                        className="p-1 text-red-600 hover:bg-red-50 rounded"
                        title="Удалить слово"
                      >
                        <Trash2 className="h-3 w-3" />
                      </button>
                    </div>
                  )) || (
                    <p className="text-gray-500 italic">Слова не добавлены</p>
                  )}
                </div>
              )}
            </div>
          ))}

          {groups.length === 0 && (
            <div className="text-center py-12">
              <p className="text-gray-500 text-lg">Группы не созданы</p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="mt-4 btn-primary"
              >
                Создать первую группу
              </button>
            </div>
          )}
        </div>

        {/* Create Group Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-96">
              <h3 className="text-lg font-semibold mb-4">Создать группу</h3>
              <input
                type="text"
                placeholder="Название группы"
                value={newGroupName}
                onChange={(e) => setNewGroupName(e.target.value)}
                className="input-field mb-4"
                onKeyPress={(e) => e.key === 'Enter' && handleCreateGroup()}
              />
              <div className="flex space-x-3">
                <button onClick={handleCreateGroup} className="btn-primary">
                  Создать
                </button>
                <button 
                  onClick={() => {
                    setShowCreateModal(false)
                    setNewGroupName('')
                  }}
                  className="btn-secondary"
                >
                  Отмена
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Edit Group Modal */}
        {showEditModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-96">
              <h3 className="text-lg font-semibold mb-4">Редактировать группу</h3>
              <input
                type="text"
                placeholder="Название группы"
                value={newGroupName}
                onChange={(e) => setNewGroupName(e.target.value)}
                className="input-field mb-4"
                onKeyPress={(e) => e.key === 'Enter' && handleEditGroup()}
              />
              <div className="flex space-x-3">
                <button onClick={handleEditGroup} className="btn-primary">
                  Сохранить
                </button>
                <button 
                  onClick={() => {
                    setShowEditModal(false)
                    setNewGroupName('')
                    setSelectedGroup(null)
                  }}
                  className="btn-secondary"
                >
                  Отмена
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Add Word Modal */}
        {showWordModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-96">
              <h3 className="text-lg font-semibold mb-4">
                Добавить слово в "{selectedGroup?.name}"
              </h3>
              <input
                type="text"
                placeholder="Ключевое слово"
                value={newWordName}
                onChange={(e) => setNewWordName(e.target.value)}
                className="input-field mb-4"
                onKeyPress={(e) => e.key === 'Enter' && handleCreateWord()}
              />
              <div className="flex space-x-3">
                <button onClick={handleCreateWord} className="btn-primary">
                  Добавить
                </button>
                <button 
                  onClick={() => {
                    setShowWordModal(false)
                    setNewWordName('')
                    setSelectedGroup(null)
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
