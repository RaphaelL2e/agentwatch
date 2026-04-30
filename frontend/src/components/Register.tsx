/**
 * AgentWatch 注册页面
 */

import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import { useLanguage } from '../LanguageContext'

export default function Register() {
  const navigate = useNavigate()
  const { register } = useAuth()
  const { lang, t, toggleLang } = useLanguage()
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
      setError(t.register.passwordMismatch)
      return
    }

    if (formData.password.length < 8) {
      setError(t.register.passwordTooShort)
      return
    }

    setLoading(true)

    try {
      await register({
        email: formData.email,
        password: formData.password,
        name: formData.name,
        organization: formData.organization,
      })
      
      // 跳转到 Dashboard
      navigate('/')
    } catch (err: any) {
      setError(err.response?.data?.detail || t.register.error)
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
            🔍 {t.brand.name}
          </h1>
          <p className="text-slate-400 mt-2">
            {t.brand.subtitle}
          </p>
        </div>

        {/* 注册表单 */}
        <div className="bg-slate-800 rounded-lg p-8 border border-slate-700">
          <h2 className="text-xl font-semibold text-white mb-6">
            {t.register.title}
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* 邮箱 */}
            <div>
              <label className="block text-sm text-slate-400 mb-1">
                {t.register.email} *
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className="w-full px-4 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                placeholder={t.register.emailPlaceholder}
                required
              />
            </div>

            {/* 用户名 */}
            <div>
              <label className="block text-sm text-slate-400 mb-1">
                {t.register.name}
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                className="w-full px-4 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                placeholder={t.register.namePlaceholder}
              />
            </div>

            {/* 组织 */}
            <div>
              <label className="block text-sm text-slate-400 mb-1">
                {t.register.organization}
              </label>
              <input
                type="text"
                name="organization"
                value={formData.organization}
                onChange={handleChange}
                className="w-full px-4 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                placeholder={t.register.orgPlaceholder}
              />
            </div>

            {/* 密码 */}
            <div>
              <label className="block text-sm text-slate-400 mb-1">
                {t.register.password} *
              </label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                className="w-full px-4 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                placeholder={t.register.passwordPlaceholder}
                required
              />
              <p className="text-xs text-slate-500 mt-1">
                {t.register.passwordHint}
              </p>
            </div>

            {/* 确认密码 */}
            <div>
              <label className="block text-sm text-slate-400 mb-1">
                {t.register.confirmPassword} *
              </label>
              <input
                type="password"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                className="w-full px-4 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                placeholder={t.register.confirmPasswordPlaceholder}
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
              {loading ? t.register.submitting : t.register.submit}
            </button>
          </form>

          {/* 登录链接 */}
          <div className="mt-6 text-center text-slate-400">
            {t.register.hasAccount}
            <Link 
              to="/login" 
              className="text-blue-400 hover:text-blue-300 ml-1"
            >
              {t.register.loginLink}
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
        <div className="mt-8 bg-slate-800/50 rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">
            🎯 {t.register.benefits.title}
          </h3>
          <ul className="space-y-3 text-slate-400">
            <li className="flex items-start gap-2">
              <span className="text-green-400">✓</span>
              <span>{t.register.benefits.realtimeDashboard}</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-400">✓</span>
              <span>{t.register.benefits.costComparison}</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-400">✓</span>
              <span>{t.register.benefits.apiKey}</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-400">✓</span>
              <span>{t.register.benefits.alerts}</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  )
}