import { useQuery } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Clock, DollarSign, Activity, CheckCircle2, AlertCircle, Loader2, Zap } from 'lucide-react'
import { api } from '../api'

// Trace 详情页面
function TraceDetail() {
  const { traceId } = useParams<{ traceId: string }>()
  
  const { data: trace, isLoading, error } = useQuery({
    queryKey: ['trace', traceId],
    queryFn: () => api.getTrace(traceId!),
    enabled: !!traceId,
  })
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
        <span className="ml-2 text-slate-400">Loading trace details...</span>
      </div>
    )
  }
  
  if (error || !trace) {
    return (
      <div className="card text-center py-12">
        <AlertCircle className="w-12 h-12 mx-auto mb-4 text-red-500" />
        <p className="text-slate-400">Trace not found or error loading trace</p>
        <Link to="/" className="btn-primary mt-4 inline-block">
          Back to Dashboard
        </Link>
      </div>
    )
  }
  
  const duration = trace.end_time 
    ? Math.round((new Date(trace.end_time).getTime() - new Date(trace.created_at).getTime()) / 1000)
    : null
  
  return (
    <div className="space-y-6">
      {/* 返回按钮 */}
      <Link 
        to="/" 
        className="inline-flex items-center gap-2 text-slate-400 hover:text-white transition-colors"
      >
        <ArrowLeft className="w-5 h-5" />
        Back to Dashboard
      </Link>
      
      {/* Trace 基本信息 */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white">{trace.agent_name}</h1>
            <p className="text-slate-400 text-sm mt-1">
              Trace ID: {trace.trace_id}
            </p>
          </div>
          <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium ${
            trace.status === 'completed' ? 'bg-green-500/20 text-green-500' :
            trace.status === 'running' ? 'bg-yellow-500/20 text-yellow-500' :
            trace.status === 'failed' ? 'bg-red-500/20 text-red-500' :
            'bg-slate-500/20 text-slate-500'
          }`}>
            {trace.status === 'completed' && <CheckCircle2 className="w-4 h-4" />}
            {trace.status === 'running' && <Loader2 className="w-4 h-4 animate-spin" />}
            {trace.status === 'failed' && <AlertCircle className="w-4 h-4" />}
            {trace.status}
          </div>
        </div>
        
        {/* 统计信息 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-slate-700/50 rounded-lg p-4">
            <div className="flex items-center gap-2 text-slate-400 mb-2">
              <Activity className="w-4 h-4" />
              Provider
            </div>
            <p className="text-xl font-semibold text-white">{trace.provider}</p>
          </div>
          
          <div className="bg-slate-700/50 rounded-lg p-4">
            <div className="flex items-center gap-2 text-slate-400 mb-2">
              <Zap className="w-4 h-4" />
              Model
            </div>
            <p className="text-xl font-semibold text-white">{trace.model}</p>
          </div>
          
          <div className="bg-slate-700/50 rounded-lg p-4">
            <div className="flex items-center gap-2 text-slate-400 mb-2">
              <Clock className="w-4 h-4" />
              Duration
            </div>
            <p className="text-xl font-semibold text-white">
              {duration ? `${duration}s` : 'Running...'}
            </p>
          </div>
          
          <div className="bg-slate-700/50 rounded-lg p-4">
            <div className="flex items-center gap-2 text-slate-400 mb-2">
              <DollarSign className="w-4 h-4" />
              Cost
            </div>
            <p className="text-xl font-semibold text-green-400">
              ${trace.total_cost?.toFixed(6) || '0.00'}
            </p>
          </div>
        </div>
      </div>
      
      {/* Token 使用 */}
      <div className="card">
        <h2 className="text-lg font-semibold text-white mb-4">Token Usage</h2>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <p className="text-slate-400 text-sm">Input Tokens</p>
            <p className="text-2xl font-bold text-white">{trace.input_tokens || 0}</p>
          </div>
          <div>
            <p className="text-slate-400 text-sm">Output Tokens</p>
            <p className="text-2xl font-bold text-white">{trace.output_tokens || 0}</p>
          </div>
          <div>
            <p className="text-slate-400 text-sm">Total Tokens</p>
            <p className="text-2xl font-bold text-primary-500">{trace.total_tokens || 0}</p>
          </div>
        </div>
      </div>
      
      {/* Prompt 和 Output */}
      {trace.prompt && (
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-4">Prompt</h2>
          <pre className="bg-slate-800 rounded-lg p-4 text-sm text-slate-300 overflow-auto max-h-[200px]">
            {trace.prompt}
          </pre>
        </div>
      )}
      
      {/* Events */}
      {trace.events && trace.events.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-4">
            Events ({trace.events.length})
          </h2>
          <div className="space-y-3">
            {trace.events.map((event: any, index: number) => (
              <div 
                key={index}
                className="bg-slate-700/50 rounded-lg p-4 border border-slate-600"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-primary-500 font-medium">{event.event_type}</span>
                  <span className="text-slate-400 text-xs">
                    {new Date(event.timestamp).toLocaleString()}
                  </span>
                </div>
                {event.message && (
                  <p className="text-slate-300 text-sm">{event.message}</p>
                )}
                {event.data && (
                  <pre className="bg-slate-800 rounded p-2 mt-2 text-xs text-slate-400 overflow-auto">
                    {JSON.stringify(event.data, null, 2)}
                  </pre>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Session Info */}
      {(trace.session_id || trace.user_id) && (
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-4">Session Info</h2>
          <div className="grid grid-cols-2 gap-4 text-sm">
            {trace.session_id && (
              <div>
                <p className="text-slate-400">Session ID</p>
                <p className="text-white">{trace.session_id}</p>
              </div>
            )}
            {trace.user_id && (
              <div>
                <p className="text-slate-400">User ID</p>
                <p className="text-white">{trace.user_id}</p>
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* 时间信息 */}
      <div className="card">
        <h2 className="text-lg font-semibold text-white mb-4">Timeline</h2>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-slate-400">Created At</p>
            <p className="text-white">{new Date(trace.created_at).toLocaleString()}</p>
          </div>
          {trace.end_time && (
            <div>
              <p className="text-slate-400">End Time</p>
              <p className="text-white">{new Date(trace.end_time).toLocaleString()}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default TraceDetail