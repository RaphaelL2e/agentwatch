/**
 * AgentWatch 认证上下文
 * 全局认证状态管理
 */

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { authApi, tokenManager } from './authApi'

interface User {
  user_id: string
  email: string
  name?: string
  organization?: string
  role: string
  plan: string
  tenant_id: string
  created_at: string
  is_active: boolean
  api_keys_count: number
}

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (data: {
    email: string
    password: string
    name?: string
    organization?: string
  }) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  // 初始化时检查 Token
  useEffect(() => {
    const storedUser = tokenManager.getUser()
    const token = tokenManager.getToken()
    
    if (storedUser && token) {
      setUser(storedUser)
      
      // 验证 Token 是否有效
      authApi.getCurrentUser()
        .then((userData) => setUser(userData))
        .catch(() => {
          tokenManager.clearTokens()
          setUser(null)
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (email: string, password: string) => {
    const response = await authApi.login({ email, password })
    tokenManager.setTokens(response.access_token, response.refresh_token, response.user)
    setUser(response.user)
  }

  const register = async (data: {
    email: string
    password: string
    name?: string
    organization?: string
  }) => {
    const response = await authApi.register(data)
    tokenManager.setTokens(response.access_token, response.refresh_token, response.user)
    setUser(response.user)
  }

  const logout = () => {
    authApi.logout().catch(() => {})
    tokenManager.clearTokens()
    setUser(null)
  }

  const refreshUser = async () => {
    if (tokenManager.isAuthenticated()) {
      const userData = await authApi.getCurrentUser()
      setUser(userData)
      tokenManager.setTokens(tokenManager.getToken()!, undefined, userData)
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        loading,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
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

export default AuthContext