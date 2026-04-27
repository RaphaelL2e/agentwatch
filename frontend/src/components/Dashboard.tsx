import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Activity, DollarSign, Clock, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react'
import { api } from '../api'

// 统计卡片组件
function StatCard({ title, value, icon, color }: { 
  title: string; 
  value: string | number; 
  icon: React.ReactNode;
  color: string;
}) {
  return (
    <div className="stat-card">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-slate-400 text-sm">{title}</p>
          <p className={`text-2xl font-bold mt-1 ${color}`}>{value}</p>
        </div>
        <div className={`p-3 rounded-full bg-slate-700 ${color}`}>
          {icon}
        </div>
      </div>
    </div>
  )
}

// Trace 状态徽章
function StatusBadge({ status }: { status: string }) {
  const colors = {
    running: 'bg-yellow-500/20 text-yellow-500',
    completed: 'bg-green-500/20 text-green-500',
    failed: 'bg-red-500/20 text-red-500',
    timeout: 'bg-orange-500/20 text-orange-500',
  }
  
  const icons = {
    running: <Loader2 className="w-4 h-4 animate-spin" />,
    completed: <CheckCircle2 className="w-4 h-4" />,
    failed: <AlertCircle className="w-4 h-4" />,
    timeout: <Clock className="w-4 h-4" />,
  }
  
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${colors[status as keyof typeof colors] || 'bg-slate-500/20 text-slate-500'}`}>
      {icons[status as keyof typeof icons] || null}
      {status}
    </span>
  )
}

// Trace 列表项
function TraceItem({ trace }: { trace: any }) {
  return (
    <Link 
      to={`/trace/${trace.trace_id}`}
      className="trace-item block cursor-pointer hover:border-primary-500 transition-colors"
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-3">
          <StatusBadge status={trace.status} />
          <span className="text-white font-medium">{trace.agent_name}</span>
        </div>
        <span className="text-slate-400 text-xs">
          {new Date(trace.created_at).toLocaleString()}
        </span>
      </div>
      
      <div className="grid grid-cols-4 gap-4 text-sm">
        <div>
          <p className="text-slate-400">Provider</p>
          <p className="text-white">{trace.provider}</p>
        </div>
        <div>
          <p className="text-slate-400">Model</p>
          <p className="text-white">{trace.model}</p>
        </div>
        <div>
          <p className="text-slate-400">Tokens</p>
          <p className="text-white">{trace.total_tokens}</p>
        </div>
        <div>
          <p className="text-slate-400">Cost</p>
          <p className="text-green-400">${trace.total_cost.toFixed(4)}</p>
        </div>
      </div>
      
      <div className="mt-2 text-xs text-slate-500">
        Trace ID: {trace.trace_id} → Click to view details
      </div>
    </Link>
  )
}

// Dashboard 主组件
function Dashboard() {
  // 获取统计信息
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: () => api.getStats(),
  })
  
  // 获取 Trace 列表
  const { data: traces, isLoading: tracesLoading } = useQuery({
    queryKey: ['traces'],
    queryFn: () => api.getTraces(),
  })
  
  // 获取健康状态
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.getHealth(),
  })
  
  return (
    <div className="space-y-6">
      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          title="Total Traces"
          value={stats?.total_traces || 0}
          icon={<Activity className="w-6 h-6" />}
          color="text-primary-500"
        />
        <StatCard
          title="Completed"
          value={stats?.completed_traces || 0}
          icon={<CheckCircle2 className="w-6 h-6" />}
          color="text-green-500"
        />
        <StatCard
          title="Running"
          value={stats?.running_traces || 0}
          icon={<Loader2 className="w-6 h-6 animate-spin" />}
          color="text-yellow-500"
        />
        <StatCard
          title="Total Cost"
          value={`$${(stats?.total_cost || 0).toFixed(4)}`}
          icon={<DollarSign className="w-6 h-6" />}
          color="text-green-500"
        />
      </div>
      
      {/* 系统状态 */}
      <div className="card">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
              health?.status === 'healthy' 
                ? 'bg-green-500/20 text-green-500' 
                : 'bg-red-500/20 text-red-500'
            }`}>
              {health?.status === 'healthy' ? '●' : '○'} {health?.status || 'Unknown'}
            </span>
          </div>
          <div className="text-slate-400 text-sm">
            Version: {health?.version || 'N/A'} | 
            Uptime: {health?.uptime_seconds ? `${Math.floor(health.uptime_seconds / 60)}m` : 'N/A'}
          </div>
        </div>
      </div>
      
      {/* Trace 列表 */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white">Recent Traces</h2>
          <span className="text-slate-400 text-sm">
            {traces?.total || 0} total
          </span>
        </div>
        
        {tracesLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
            <span className="ml-2 text-slate-400">Loading traces...</span>
          </div>
        ) : traces?.traces?.length > 0 ? (
          <div className="space-y-3">
            {traces.traces.map((trace: any) => (
              <TraceItem key={trace.trace_id} trace={trace} />
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-slate-400">
            <Activity className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>No traces yet. Create one using the API!</p>
            <p className="text-xs mt-1">POST /api/v1/test/trace</p>
          </div>
        )}
      </div>
      
      {/* 快速操作 */}
      <div className="card">
        <h2 className="text-lg font-semibold text-white mb-4">Quick Actions</h2>
        <div className="flex gap-3">
          <button 
            onClick={() => api.createTestTrace()}
            className="btn-primary"
          >
            Create Test Trace
          </button>
          <Link 
            to="/costs"
            className="btn-secondary inline-flex items-center gap-2"
          >
            <DollarSign className="w-4 h-4" />
            Cost Comparison
          </Link>
          <button 
            onClick={() => window.location.reload()}
            className="btn-secondary"
          >
            Refresh Dashboard
          </button>
        </div>
      </div>
    </div>
  )
}

export default Dashboard