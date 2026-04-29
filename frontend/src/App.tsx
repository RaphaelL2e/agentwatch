import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './AuthContext'
import Login from './components/Login'
import Register from './components/Register'
import Dashboard from './components/Dashboard'
import TraceDetail from './components/TraceDetail'
import CostComparison from './components/CostComparison'
import CostOptimization from './components/CostOptimization'
import Settings from './components/Settings'
import About from './components/About'
import Charts from './components/Charts'

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
  
  return (
    <div className="min-h-screen bg-slate-900">
      <header className="bg-slate-800 border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">
                🔍 AgentWatch
                <span className="text-sm text-slate-400 ml-2">v0.6.0</span>
              </h1>
              <p className="text-slate-400 text-sm mt-1">
                AI Agent Security Monitoring Platform
              </p>
            </div>
            <div className="flex items-center gap-4">
              <nav className="flex gap-3">
                <a href="/" className="text-slate-400 hover:text-white transition-colors text-sm">
                  Dashboard
                </a>
                <a href="/costs" className="text-slate-400 hover:text-white transition-colors text-sm">
                  Costs
                </a>
                <a href="/optimize" className="text-slate-400 hover:text-white transition-colors text-sm">
                  Optimize
                </a>
                <a href="/charts" className="text-slate-400 hover:text-white transition-colors text-sm">
                  Charts
                </a>
                <a href="/settings" className="text-slate-400 hover:text-white transition-colors text-sm">
                  Settings
                </a>
              </nav>
              {user && (
                <div className="flex items-center gap-3 border-l border-slate-600 pl-3">
                  <div className="text-sm">
                    <span className="text-slate-400">{user.email}</span>
                  </div>
                  <button
                    onClick={logout}
                    className="text-slate-400 hover:text-red-400 text-sm"
                  >
                    Logout
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
          AgentWatch © 2026 | 
          <a 
            href="https://github.com/RaphaelL2e/agentwatch" 
            className="hover:text-primary-500 transition-colors ml-2"
            target="_blank"
            rel="noopener noreferrer"
          >
            GitHub
          </a>
          | Track, Debug, and Optimize Your AI Agents
        </div>
      </footer>
    </div>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
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
                  <Charts />
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
    </QueryClientProvider>
  )
}

export default App