import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Dashboard from './components/Dashboard'
import TraceDetail from './components/TraceDetail'
import CostComparison from './components/CostComparison'
import Settings from './components/Settings'
import About from './components/About'
import Charts from './components/Charts'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchInterval: 5000, // 5秒自动刷新
      staleTime: 30000,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-slate-900">
          <header className="bg-slate-800 border-b border-slate-700">
            <div className="max-w-7xl mx-auto px-4 py-4">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-2xl font-bold text-white">
                    🔍 AgentWatch
                    <span className="text-sm text-slate-400 ml-2">v0.2.0</span>
                  </h1>
                  <p className="text-slate-400 text-sm mt-1">
                    AI Agent Security Monitoring Platform
                  </p>
                </div>
                <nav className="flex gap-4">
                  <a 
                    href="/" 
                    className="text-slate-400 hover:text-white transition-colors text-sm"
                  >
                    Dashboard
                  </a>
                  <a 
                    href="/costs" 
                    className="text-slate-400 hover:text-white transition-colors text-sm"
                  >
                    Cost Comparison
                  </a>
                  <a 
                    href="/settings" 
                    className="text-slate-400 hover:text-white transition-colors text-sm"
                  >
                    Settings
                  </a>
                  <a 
                    href="/about" 
                    className="text-slate-400 hover:text-white transition-colors text-sm"
                  >
                    About
                  </a>
                  <a 
                    href="/charts" 
                    className="text-slate-400 hover:text-white transition-colors text-sm"
                  >
                    Charts
                  </a>
                </nav>
              </div>
            </div>
          </header>
          
          <main className="max-w-7xl mx-auto px-4 py-6">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/trace/:traceId" element={<TraceDetail />} />
              <Route path="/costs" element={<CostComparison />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/about" element={<About />} />
              <Route path="/charts" element={<Charts />} />
            </Routes>
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
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App