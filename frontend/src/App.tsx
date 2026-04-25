import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Dashboard from './components/Dashboard'

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
      <div className="min-h-screen bg-slate-900">
        <header className="bg-slate-800 border-b border-slate-700">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <h1 className="text-2xl font-bold text-white">
              🔍 AgentWatch
              <span className="text-sm text-slate-400 ml-2">v0.2.0</span>
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              AI Agent Security Monitoring Platform
            </p>
          </div>
        </header>
        
        <main className="max-w-7xl mx-auto px-4 py-6">
          <Dashboard />
        </main>
        
        <footer className="bg-slate-800 border-t border-slate-700 mt-8">
          <div className="max-w-7xl mx-auto px-4 py-4 text-center text-slate-400 text-sm">
            AgentWatch © 2026 | Track, Debug, and Optimize Your AI Agents
          </div>
        </footer>
      </div>
    </QueryClientProvider>
  )
}

export default App