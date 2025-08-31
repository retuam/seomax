'use client'

import React, { createContext, useContext, useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Cookies from 'js-cookie'
import { api } from '@/lib/api'
import toast from 'react-hot-toast'

interface User {
  uuid: string
  email: string
  create_time: string
  status: number
}

interface AuthContextType {
  user: User | null
  login: (email: string, password: string) => Promise<boolean>
  register: (email: string, password: string) => Promise<boolean>
  logout: () => void
  loading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  // Проверка токена при загрузке приложения
  useEffect(() => {
    const token = Cookies.get('token')
    if (token) {
      checkAuth()
    } else {
      setLoading(false)
    }
  }, [])

  const checkAuth = async () => {
    try {
      const response = await api.get('/auth/me')
      setUser(response.data)
    } catch (error) {
      // Токен недействителен, удаляем его
      Cookies.remove('token')
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      const response = await api.post('/auth/login', { email, password })
      const { access_token } = response.data
      
      // Сохраняем токен в cookies
      Cookies.set('token', access_token, { expires: 14 }) // 14 дней
      
      // Получаем информацию о пользователе
      await checkAuth()
      
      toast.success('Успешный вход в систему!')
      return true
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Ошибка входа'
      toast.error(message)
      return false
    }
  }

  const register = async (email: string, password: string): Promise<boolean> => {
    try {
      await api.post('/auth/register', { email, password })
      toast.success('Регистрация успешна! Теперь войдите в систему.')
      return true
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Ошибка регистрации'
      toast.error(message)
      return false
    }
  }

  const logout = () => {
    Cookies.remove('token')
    setUser(null)
    router.push('/auth/login')
    toast.success('Вы вышли из системы')
  }

  const value = {
    user,
    login,
    register,
    logout,
    loading
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
