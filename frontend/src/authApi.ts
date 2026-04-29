/**
 * AgentWatch 认证 API
 * 用户注册、登录、API Key 管理
 */

import axios from 'axios'

// API 请求使用相对路径，通过 nginx 代理
// 不设置 baseURL，让 axios 使用相对路径
const API_BASE = ''

const authClient = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Token 存储
const TOKEN_KEY = 'agentwatch_token'
const REFRESH_TOKEN_KEY = 'agentwatch_refresh_token'
const USER_KEY = 'agentwatch_user'

// Token 管理
export const tokenManager = {
  getToken: () => localStorage.getItem(TOKEN_KEY),
  getRefreshToken: () => localStorage.getItem(REFRESH_TOKEN_KEY),
  getUser: () => {
    const userStr = localStorage.getItem(USER_KEY)
    return userStr ? JSON.parse(userStr) : null
  },
  
  setTokens: (accessToken: string, refreshToken?: string, user?: any) => {
    localStorage.setItem(TOKEN_KEY, accessToken)
    if (refreshToken) localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
    if (user) localStorage.setItem(USER_KEY, JSON.stringify(user))
  },
  
  clearTokens: () => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  },
  
  isAuthenticated: () => !!localStorage.getItem(TOKEN_KEY),
}

// 添加认证头
authClient.interceptors.request.use((config) => {
  const token = tokenManager.getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 处理认证错误
authClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      tokenManager.clearTokens()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// 认证 API
export const authApi = {
  // 用户注册
  register: (data: {
    email: string
    password: string
    name?: string
    organization?: string
  }) => authClient.post('/auth/register', data).then(r => r.data),
  
  // 用户登录
  login: (data: {
    email: string
    password: string
  }) => authClient.post('/auth/login', data).then(r => r.data),
  
  // 刷新 Token
  refreshToken: (refreshToken: string) => 
    authClient.post('/auth/refresh', { refresh_token: refreshToken }).then(r => r.data),
  
  // 获取当前用户
  getCurrentUser: () => authClient.get('/auth/me').then(r => r.data),
  
  // 更新用户信息
  updateProfile: (data: { name?: string; organization?: string }) => 
    authClient.patch('/auth/me', data).then(r => r.data),
  
  // 修改密码
  changePassword: (data: { old_password: string; new_password: string }) => 
    authClient.post('/auth/me/password', data).then(r => r.data),
  
  // 用户注销
  logout: () => authClient.post('/auth/logout').then(r => r.data),
  
  // 创建 API Key
  createApiKey: (data: {
    name: string
    scope: string[]
    rate_limit?: number
    description?: string
  }) => authClient.post('/auth/api-keys', data).then(r => r.data),
  
  // 列出 API Keys
  listApiKeys: () => authClient.get('/auth/api-keys').then(r => r.data),
  
  // 获取单个 API Key
  getApiKey: (keyId: string) => authClient.get(`/auth/api-keys/${keyId}`).then(r => r.data),
  
  // 撤销 API Key
  revokeApiKey: (keyId: string) => authClient.delete(`/auth/api-keys/${keyId}`).then(r => r.data),
  
  // 验证 API Key
  validateApiKey: () => authClient.get('/auth/validate').then(r => r.data),
}

export default authApi