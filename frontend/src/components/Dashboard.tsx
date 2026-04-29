import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { Activity, DollarSign, Clock, AlertCircle, CheckCircle2, Loader2, Wifi, WifiOff, AlertTriangle, ArrowUpRight, ArrowDownRight } from 'lucide-react'
import { api } from '../api'
import { useWebSocket } from '../hooks/useWebSocket'
import { CostAlerts, ProviderCostBreakdown, CostSavingSuggestions } from './CostAlerts'

// 实时预警类型
interface RealtimeAlert {
  type: 'cost_spike' | 'high_latency' | 'agent_failure' | 'token_overflow'
  message: string
  timestamp: string
  data?: any
}

// 统计卡片组件（增强版）
function StatCard({ title, value, icon, color, trend, previousValue }: { 
  title: string; 
  value: string | number;
  previousValue?: number;
  icon: React.ReactNode;
  color: string;
  trend?: 'up' | 'down' | 'stable';
}) {
  const formatValue = (v: number) => {
    if (title.includes('Cost')) return `$${v.toFixed(4)}`;
    return v.toLocaleString();
  };
  
  const getTrendIcon = () => {
    if (!trend) return null;
    if (trend === 'up') return <ArrowUpRight className="w-4 h-4 text-green-400" />;
    if (trend === 'down') return <ArrowDownRight className="w-4 h-4 text-red-400" />;
    return null;
  };
  
  const getTrendColor = () => {
    if (!trend) return '';
    if (title.includes('Cost')) {
      // 成本增加是坏的
      return trend === 'up' ? 'text-red-400' : trend === 'down' ? 'text-green-400' : '';
    }
    // 其他增加是好的
    return trend === 'up' ? 'text-green-400' : trend === 'down' ? 'text-red-400' : '';
  };
  
  return (
    <div className="stat-card relative overflow-hidden">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-slate-400 text-sm">{title}</p>
          <div className="flex items-center gap-2 mt-1">
            <p className={`text-2xl font-bold ${color}`}>{value}</p>
            {getTrendIcon()}
          </div>
          {previousValue !== undefined && (
            <p className={`text-xs mt-1 ${getTrendColor()}`}>
              {trend === 'up' ? '+' : trend === 'down' ? '-' : ''}{formatValue(previousValue)} prev
            </p>
          )}
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

// Trace 列表项（增强版，支持高亮动画）
function TraceItem({ trace, isNew }: { trace: any; isNew?: boolean }) {
  return (
    <Link 
      to={`/trace/${trace.trace_id}`}
      className={`trace-item block cursor-pointer transition-all duration-500 ${
        isNew 
          ? 'border-primary-500 bg-primary-500/10 scale-[1.02]' 
          : 'hover:border-primary-500'
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-3">
          <StatusBadge status={trace.status} />
          <span className="text-white font-medium">{trace.agent_name}</span>
          {isNew && (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-green-500/20 text-green-400 animate-pulse">
              NEW
            </span>
          )}
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

// 实时预警面板
function RealtimeAlertsPanel({ alerts }: { alerts: RealtimeAlert[] }) {
  if (alerts.length === 0) return null;
  
  const alertStyles = {
    cost_spike: 'bg-red-500/20 border-red-500 text-red-400',
    high_latency: 'bg-yellow-500/20 border-yellow-500 text-yellow-400',
    agent_failure: 'bg-orange-500/20 border-orange-500 text-orange-400',
    token_overflow: 'bg-purple-500/20 border-purple-500 text-purple-400',
  };
  
  return (
    <div className="card border border-red-500/30">
      <div className="flex items-center gap-2 mb-4">
        <AlertTriangle className="w-5 h-5 text-red-400" />
        <h2 className="text-lg font-semibold text-white">Real-time Alerts</h2>
        <span className="text-xs bg-red-500/20 px-2 py-0.5 rounded text-red-400">
          {alerts.length} active
        </span>
      </div>
      <div className="space-y-2 max-h-48 overflow-y-auto">
        {alerts.slice(0, 5).map((alert, index) => (
          <div 
            key={index}
            className={`p-3 rounded-lg border ${alertStyles[alert.type]} flex items-center gap-3`}
          >
            <AlertTriangle className="w-4 h-4" />
            <div className="flex-1">
              <p className="font-medium text-sm">{alert.message}</p>
              <p className="text-xs opacity-70">
                {new Date(alert.timestamp).toLocaleTimeString()}
              </p>
            </div>
            {alert.data?.trace_id && (
              <Link 
                to={`/trace/${alert.data.trace_id}`}
                className="text-xs hover:underline"
              >
                View →
              </Link>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// Dashboard 主组件（增强版）
function Dashboard() {
  const queryClient = useQueryClient()
  const [alerts, setAlerts] = useState<RealtimeAlert[]>([])
  const [newTraceIds, setNewTraceIds] = useState<Set<string>>(new Set())
  const [previousStats, setPreviousStats] = useState<any>(null)
  
  // WebSocket 实时更新（增强版）
  const { isConnected, connectionStatus, lastMessage } = useWebSocket({
    autoConnect: true,
    onTraceCreated: (trace) => {
      // 标记新 Trace
      setNewTraceIds(prev => new Set([...prev, trace.trace_id]))
      // 2秒后移除高亮
      setTimeout(() => {
        setNewTraceIds(prev => {
          const next = new Set(prev);
          next.delete(trace.trace_id);
          return next;
        });
      }, 2000);
      // 更新缓存
      queryClient.setQueryData(['traces'], (old: any) => {
        if (!old) return { traces: [trace], total: 1 };
        return { ...old, traces: [trace, ...old.traces], total: old.total + 1 };
      });
    },
    onStatsUpdate: (stats) => {
      // 记录之前的统计用于计算趋势
      const current = queryClient.getQueryData(['stats']);
      if (current) setPreviousStats(current);
      // 更新缓存
      queryClient.setQueryData(['stats'], stats);
    },
  });
  
  // 处理预警消息
  useEffect(() => {
    if (lastMessage?.type === 'alert') {
      setAlerts(prev => [
        {
          type: lastMessage.alert_type,
          message: lastMessage.data.message,
          timestamp: lastMessage.timestamp,
          data: lastMessage.data,
        },
        ...prev.slice(0, 9),
      ]);
    }
  }, [lastMessage]);
  
  // 获取统计信息
  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: () => api.getStats(),
  });
  
  // 获取 Trace 列表
  const { data: traces, isLoading: tracesLoading } = useQuery({
    queryKey: ['traces'],
    queryFn: () => api.getTraces(),
  });
  
  // 获取健康状态
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.getHealth(),
  });
  
  // 计算趋势
  const getTrend = (current: number, previous?: number): 'up' | 'down' | 'stable' => {
    if (!previous) return 'stable';
    const change = current - previous;
    if (Math.abs(change) < 1) return 'stable';
    return change > 0 ? 'up' : 'down';
  };
  
  // WebSocket 状态徽章
  const WebSocketBadge = () => (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
      isConnected
        ? 'bg-green-500/20 text-green-500'
        : connectionStatus === 'connecting'
        ? 'bg-yellow-500/20 text-yellow-500'
        : 'bg-red-500/20 text-red-500'
    }`}>
      {isConnected ? <Wifi className="w-3 h-3 mr-1 animate-pulse" /> : <WifiOff className="w-3 h-3 mr-1" />}
      {isConnected ? 'Live' : connectionStatus === 'connecting' ? 'Connecting...' : 'Offline'}
    </span>
  )
  
  return (
    <div className="space-y-6">
      {/* 统计卡片（增强版，带趋势） */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          title="Total Traces"
          value={stats?.total_traces || 0}
          previousValue={previousStats?.total_traces}
          trend={getTrend(stats?.total_traces || 0, previousStats?.total_traces)}
          icon={<Activity className="w-6 h-6" />}
          color="text-primary-500"
        />
        <StatCard
          title="Completed"
          value={stats?.completed_traces || 0}
          previousValue={previousStats?.completed_traces}
          trend={getTrend(stats?.completed_traces || 0, previousStats?.completed_traces)}
          icon={<CheckCircle2 className="w-6 h-6" />}
          color="text-green-500"
        />
        <StatCard
          title="Running"
          value={stats?.running_traces || 0}
          previousValue={previousStats?.running_traces}
          trend={getTrend(stats?.running_traces || 0, previousStats?.running_traces)}
          icon={<Loader2 className="w-6 h-6 animate-spin" />}
          color="text-yellow-500"
        />
        <StatCard
          title="Total Cost"
          value={`$${(stats?.total_cost || 0).toFixed(4)}`}
          previousValue={previousStats?.total_cost}
          trend={getTrend(stats?.total_cost || 0, previousStats?.total_cost)}
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
            <WebSocketBadge />
          </div>
          <div className="text-slate-400 text-sm">
            Version: {health?.version || 'N/A'} | 
            Uptime: {health?.uptime_seconds ? `${Math.floor(health.uptime_seconds / 60)}m` : 'N/A'}
          </div>
        </div>
      </div>
      
      {/* 实时预警面板 */}
      <RealtimeAlertsPanel alerts={alerts} />
      
      {/* 成本告警 */}
      <CostAlerts stats={stats} traces={traces?.traces} />
      
      {/* 成本分析 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <ProviderCostBreakdown stats={stats} />
        <CostSavingSuggestions stats={stats} />
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
              <TraceItem 
                key={trace.trace_id} 
                trace={trace} 
                isNew={newTraceIds.has(trace.trace_id)}
              />
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