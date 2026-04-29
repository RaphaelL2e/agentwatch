/**
 * AgentWatch 登录页面
 */

import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { authApi, tokenManager } from '../authApi'

export default function Login() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await authApi.login({ email, password })
      
      // 存储 Token
      tokenManager.setTokens(
        response.access_token,
        response.refresh_token,
        response.user
      )
      
      // 跳转到 Dashboard
      navigate('/')
    } catch (err: any) {
      setError(err.response?.data?.detail || '登录失败，请检查邮箱和密码')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white">
            🔍 AgentWatch
          </h1>
          <p className="text-slate-400 mt-2">
            AI Agent Security Monitoring Platform
          </p>
        </div>

        {/* 登录表单 */}
        <div className="bg-slate-800 rounded-lg p-8 border border-slate-700">
          <h2 className="text-xl font-semibold text-white mb-6">
            登录账号
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* 邮箱 */}
            <div>
              <label className="block text-sm text-slate-400 mb-1">
                邮箱
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                placeholder="your@email.com"
                required
              />
            </div>

            {/* 密码 */}
            <div>
              <label className="block text-sm text-slate-400 mb-1">
                密码
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                placeholder="••••••••"
                required
              />
            </div>

            {/* 错误提示 */}
            {error && (
              <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-3 text-red-400 text-sm">
                {error}
              </div>
            )}

            {/* 登录按钮 */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-600/50 text-white rounded-lg font-medium transition-colors"
            >
              {loading ? '登录中...' : '登录'}
            </button>
          </form>

          {/* 注册链接 */}
          <div className="mt-6 text-center text-slate-400">
            还没有账号？
            <Link 
              to="/register" 
              className="text-blue-400 hover:text-blue-300 ml-1"
            >
              注册
            </Link>
          </div>
        </div>

        {/* 功能介绍 */}
        <div className="mt-8 grid grid-cols-3 gap-4 text-center">
          <div className="bg-slate-800/50 rounded-lg p-4">
            <div className="text-2xl mb-2">💰</div>
            <div className="text-sm text-slate-400">107倍成本节省</div>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-4">
            <div className="text-2xl mb-2">📊</div>
            <div className="text-sm text-slate-400">实时监控</div>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-4">
            <div className="text-2xl mb-2">🔐</div>
            <div className="text-sm text-slate-400">安全认证</div>
          </div>
        </div>
      </div>
    </div>
  )
}