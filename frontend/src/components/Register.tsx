/**
 * AgentWatch 注册页面
 */

import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { authApi, tokenManager } from '../authApi'

export default function Register() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    name: '',
    organization: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    // 验证密码
    if (formData.password !== formData.confirmPassword) {
      setError('两次输入的密码不一致')
      return
    }

    if (formData.password.length < 8) {
      setError('密码长度至少8位')
      return
    }

    setLoading(true)

    try {
      const response = await authApi.register({
        email: formData.email,
        password: formData.password,
        name: formData.name,
        organization: formData.organization,
      })
      
      // 存储 Token
      tokenManager.setTokens(
        response.access_token,
        response.refresh_token,
        response.user
      )
      
      // 跳转到 Dashboard
      navigate('/')
    } catch (err: any) {
      setError(err.response?.data?.detail || '注册失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center px-4 py-8">
      <div className="max-w-md w-full">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white">
            🔍 AgentWatch
          </h1>
          <p className="text-slate-400 mt-2">
            创建账号，开始监控你的 AI Agent
          </p>
        </div>

        {/* 注册表单 */}
        <div className="bg-slate-800 rounded-lg p-8 border border-slate-700">
          <h2 className="text-xl font-semibold text-white mb-6">
            注册新账号
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* 邮箱 */}
            <div>
              <label className="block text-sm text-slate-400 mb-1">
                邮箱 *
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className="w-full px-4 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                placeholder="your@email.com"
                required
              />
            </div>

            {/* 用户名 */}
            <div>
              <label className="block text-sm text-slate-400 mb-1">
                用户名
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                className="w-full px-4 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                placeholder="你的名字"
              />
            </div>

            {/* 组织 */}
            <div>
              <label className="block text-sm text-slate-400 mb-1">
                组织/公司
              </label>
              <input
                type="text"
                name="organization"
                value={formData.organization}
                onChange={handleChange}
                className="w-full px-4 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                placeholder="公司名称"
              />
            </div>

            {/* 密码 */}
            <div>
              <label className="block text-sm text-slate-400 mb-1">
                密码 *
              </label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                className="w-full px-4 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                placeholder="至少8位，包含字母和数字"
                required
              />
              <p className="text-xs text-slate-500 mt-1">
                密码需包含字母和数字，至少8位
              </p>
            </div>

            {/* 确认密码 */}
            <div>
              <label className="block text-sm text-slate-400 mb-1">
                确认密码 *
              </label>
              <input
                type="password"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                className="w-full px-4 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                placeholder="再次输入密码"
                required
              />
            </div>

            {/* 错误提示 */}
            {error && (
              <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-3 text-red-400 text-sm">
                {error}
              </div>
            )}

            {/* 注册按钮 */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-600/50 text-white rounded-lg font-medium transition-colors"
            >
              {loading ? '注册中...' : '注册'}
            </button>
          </form>

          {/* 登录链接 */}
          <div className="mt-6 text-center text-slate-400">
            已有账号？
            <Link 
              to="/login" 
              className="text-blue-400 hover:text-blue-300 ml-1"
            >
              登录
            </Link>
          </div>
        </div>

        {/* 功能介绍 */}
        <div className="mt-8 bg-slate-800/50 rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">
            🎯 注册后你将获得
          </h3>
          <ul className="space-y-3 text-slate-400">
            <li className="flex items-start gap-2">
              <span className="text-green-400">✓</span>
              <span>实时 AI Agent 监控 Dashboard</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-400">✓</span>
              <span>DeepSeek 107倍成本对比分析</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-400">✓</span>
              <span>自动创建 API Key，集成到你的项目</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-400">✓</span>
              <span>预算监控和告警通知</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  )
}