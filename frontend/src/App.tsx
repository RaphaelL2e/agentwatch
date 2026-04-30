import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './AuthContext'
import { LanguageProvider, useLanguage } from './LanguageContext'
import Login from './components/Login'
import Register from './components/Register'
import Dashboard from './components/Dashboard'
import TraceDetail from './components/TraceDetail'
import CostComparison from './components/CostComparison'
import CostOptimization from './components/CostOptimization'
import Settings from './components/Settings'
import About from './components/About'
import ChartsEnhanced from './components/ChartsEnhanced'
import Export from './components/Export'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchInterval: 5000,
      staleTime: 30000,
    },
  },
})

// 认证保护路由
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth()
  
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-white">Loading...</div>
      </div>
    )
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  return <>{children}</>
}

// 主布局
function MainLayout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth()
  const { lang, t, toggleLang } = useLanguage()
  
  return (
    <div className="min-h-screen bg-slate-900">
      <header className="bg-slate-800 border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">
                🔍 {t.brand.name}
                <span className="text-sm text-slate-400 ml-2">{t.brand.version}</span>
              </h1>
              <p className="text-slate-400 text-sm mt-1">
                {t.brand.subtitle}
              </p>
            </div>
            <div className="flex items-center gap-4">
              <nav className="flex gap-3">
                <a href="/" className="text-slate-400 hover:text-white transition-colors text-sm">
                  {t.common.dashboard}
                </a>
                <a href="/costs" className="text-slate-400 hover:text-white transition-colors text-sm">
                  {t.common.costs}
                </a>
                <a href="/optimize" className="text-slate-400 hover:text-white transition-colors text-sm">
                  {t.common.optimize}
                </a>
                <a href="/charts" className="text-slate-400 hover:text-white transition-colors text-sm">
                  {t.common.charts}
                </a>
                <a href="/export" className="text-slate-400 hover:text-white transition-colors text-sm">
                  {t.common.export}
                </a>
                <a href="/settings" className="text-slate-400 hover:text-white transition-colors text-sm">
                  {t.common.settings}
                </a>
              </nav>
              {/* 语言切换按钮 */}
              <button
                onClick={toggleLang}
                className="flex items-center gap-1 px-2 py-1 rounded text-sm bg-slate-700 hover:bg-slate-600 text-slate-300 transition-colors"
              >
                {lang === 'en' ? '🇺🇸 EN' : '🇨🇳 中文'}
              </button>
              {user && (
                <div className="flex items-center gap-3 border-l border-slate-600 pl-3">
                  <div className="text-sm">
                    <span className="text-slate-400">{user.email}</span>
                  </div>
                  <button
                    onClick={logout}
                    className="text-slate-400 hover:text-red-400 text-sm"
                  >
                    {t.common.logout}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>
      
      <main className="max-w-7xl mx-auto px-4 py-6">
        {children}
      </main>
      
      <footer className="bg-slate-800 border-t border-slate-700 mt-8">
        <div className="max-w-7xl mx-auto px-4 py-4 text-center text-slate-400 text-sm">
          {t.footer.copyright} | 
          <a 
            href="https://github.com/RaphaelL2e/agentwatch" 
            className="hover:text-primary-500 transition-colors ml-2"
            target="_blank"
            rel="noopener noreferrer"
          >
            {t.common.github}
          </a>
          | {t.footer.slogan}
        </div>
      </footer>
    </div>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <LanguageProvider>
        <AuthProvider>
          <BrowserRouter>
          <Routes>
            {/* 公开路由 */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            
            {/* 受保护路由 */}
            <Route path="/" element={
              <ProtectedRoute>
                <MainLayout>
                  <Dashboard />
                </MainLayout>
              </ProtectedRoute>
            } />
            <Route path="/trace/:traceId" element={
              <ProtectedRoute>
                <MainLayout>
                  <TraceDetail />
                </MainLayout>
              </ProtectedRoute>
            } />
            <Route path="/costs" element={
              <ProtectedRoute>
                <MainLayout>
                  <CostComparison />
                </MainLayout>
              </ProtectedRoute>
            } />
            <Route path="/optimize" element={
              <ProtectedRoute>
                <MainLayout>
                  <CostOptimization />
                </MainLayout>
              </ProtectedRoute>
            } />
            <Route path="/charts" element={
              <ProtectedRoute>
                <MainLayout>
                  <ChartsEnhanced />
                </MainLayout>
              </ProtectedRoute>
            } />
            <Route path="/export" element={
              <ProtectedRoute>
                <MainLayout>
                  <Export />
                </MainLayout>
              </ProtectedRoute>
            } />
            <Route path="/settings" element={
              <ProtectedRoute>
                <MainLayout>
                  <Settings />
                </MainLayout>
              </ProtectedRoute>
            } />
            <Route path="/about" element={
              <ProtectedRoute>
                <MainLayout>
                  <About />
                </MainLayout>
              </ProtectedRoute>
            } />
            
            {/* 默认重定向 */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </LanguageProvider>
  </QueryClientProvider>
  )
}

export default App