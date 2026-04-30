/**
 * AgentWatch 登录页面
 */

import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import { useLanguage } from '../LanguageContext'

export default function Login() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const { lang, t, toggleLang } = useLanguage()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await login(email, password)
      // 跳转到 Dashboard
      navigate('/')
    } catch (err: any) {
      setError(err.response?.data?.detail || t.login.error)
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
            🔍 {t.brand.name}
          </h1>
          <p className="text-slate-400 mt-2">
            {t.brand.subtitle}
          </p>
        </div>

        {/* 登录表单 */}
        <div className="bg-slate-800 rounded-lg p-8 border border-slate-700">
          <h2 className="text-xl font-semibold text-white mb-6">
            {t.login.title}
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* 邮箱 */}
            <div>
              <label className="block text-sm text-slate-400 mb-1">
                {t.login.email}
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                placeholder={t.login.emailPlaceholder}
                required
              />
            </div>

            {/* 密码 */}
            <div>
              <label className="block text-sm text-slate-400 mb-1">
                {t.login.password}
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                placeholder={t.login.passwordPlaceholder}
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
              {loading ? t.login.submitting : t.login.submit}
            </button>
          </form>

          {/* 注册链接 */}
          <div className="mt-6 text-center text-slate-400">
            {t.login.noAccount}
            <Link 
              to="/register" 
              className="text-blue-400 hover:text-blue-300 ml-1"
            >
              {t.login.registerLink}
            </Link>
          </div>

          {/* 语言切换 */}
          <div className="mt-4 text-center">
            <button
              onClick={toggleLang}
              className="text-slate-400 hover:text-white text-sm"
            >
              {lang === 'en' ? '🇨🇳 切换到中文' : '🇺🇸 Switch to English'}
            </button>
          </div>
        </div>

        {/* 功能介绍 */}
        <div className="mt-8 grid grid-cols-3 gap-4 text-center">
          <div className="bg-slate-800/50 rounded-lg p-4">
            <div className="text-2xl mb-2">💰</div>
            <div className="text-sm text-slate-400">{t.login.features.savings}</div>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-4">
            <div className="text-2xl mb-2">📊</div>
            <div className="text-sm text-slate-400">{t.login.features.realtime}</div>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-4">
            <div className="text-2xl mb-2">🔐</div>
            <div className="text-sm text-slate-400">{t.login.features.security}</div>
          </div>
        </div>
      </div>
    </div>
  )
}