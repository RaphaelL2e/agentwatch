/**
 * WebSocket Hook for Real-time Updates
 * 提供 React hook 来使用 WebSocket 实时更新
 */

import { useEffect, useRef, useState, useCallback } from 'react'
import { AgentWatchWebSocket } from '../api'

// WebSocketCallbacks type is exported from api.ts for external use

export interface UseWebSocketOptions {
  autoConnect?: boolean
  onTraceCreated?: (trace: any) => void
  onTraceUpdated?: (trace: any) => void
  onTraceDeleted?: (traceId: string) => void
  onStatsUpdate?: (stats: any) => void
  onError?: (error: string) => void
}

export interface UseWebSocketReturn {
  isConnected: boolean
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error'
  connect: () => void
  disconnect: () => void
  subscribe: (channels?: string[]) => void
  requestStats: () => void
  lastMessage: any
}

/**
 * WebSocket Hook
 * 
 * 使用示例:
 * const { isConnected, lastMessage, onStatsUpdate } = useWebSocket({
 *   autoConnect: true,
 *   onStatsUpdate: (stats) => console.log('Stats:', stats),
 * })
 */
export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const { autoConnect = true, ...callbacks } = options
  
  const [isConnected, setIsConnected] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected')
  const [lastMessage, setLastMessage] = useState<any>(null)
  
  const wsRef = useRef<AgentWatchWebSocket | null>(null)
  
  const handleConnected = useCallback(() => {
    setIsConnected(true)
    setConnectionStatus('connected')
    callbacks.onStatsUpdate?.({ status: 'connected' })
  }, [callbacks])
  
  const handleDisconnected = useCallback(() => {
    setIsConnected(false)
    setConnectionStatus('disconnected')
  }, [])
  
  const handleError = useCallback((error: string) => {
    setConnectionStatus('error')
    callbacks.onError?.(error)
  }, [callbacks])
  
  const handleTraceCreated = useCallback((trace: any) => {
    setLastMessage({ type: 'trace_created', data: trace })
    callbacks.onTraceCreated?.(trace)
  }, [callbacks])
  
  const handleTraceUpdated = useCallback((trace: any) => {
    setLastMessage({ type: 'trace_updated', data: trace })
    callbacks.onTraceUpdated?.(trace)
  }, [callbacks])
  
  const handleTraceDeleted = useCallback((traceId: string) => {
    setLastMessage({ type: 'trace_deleted', data: { traceId } })
    callbacks.onTraceDeleted?.(traceId)
  }, [callbacks])
  
  const handleStatsUpdate = useCallback((stats: any) => {
    setLastMessage({ type: 'stats_update', data: stats })
    callbacks.onStatsUpdate?.(stats)
  }, [callbacks])
  
  const connect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.disconnect()
    }
    
    setConnectionStatus('connecting')
    
    wsRef.current = new AgentWatchWebSocket({
      onConnected: handleConnected,
      onDisconnected: handleDisconnected,
      onError: handleError,
      onTraceCreated: handleTraceCreated,
      onTraceUpdated: handleTraceUpdated,
      onTraceDeleted: handleTraceDeleted,
      onStatsUpdate: handleStatsUpdate,
    })
    
    wsRef.current.connect()
  }, [handleConnected, handleDisconnected, handleError, handleTraceCreated, handleTraceUpdated, handleTraceDeleted, handleStatsUpdate])
  
  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.disconnect()
      wsRef.current = null
    }
    setConnectionStatus('disconnected')
    setIsConnected(false)
  }, [])
  
  const subscribe = useCallback((channels: string[] = ['all']) => {
    if (wsRef.current && wsRef.current.isConnected()) {
      wsRef.current.subscribe(channels)
    }
  }, [])
  
  const requestStats = useCallback(() => {
    if (wsRef.current && wsRef.current.isConnected()) {
      wsRef.current.requestStats()
    }
  }, [])
  
  useEffect(() => {
    if (autoConnect) {
      connect()
    }
    
    return () => {
      disconnect()
    }
  }, [autoConnect]) // 注意: 不添加 connect/disconnect 依赖以避免重复连接
  
  return {
    isConnected,
    connectionStatus,
    connect,
    disconnect,
    subscribe,
    requestStats,
    lastMessage,
  }
}

/**
 * 实时统计数据 Hook
 * 
 * 使用 WebSocket 获取实时统计数据，自动更新 React Query 缓存
 */
export function useRealTimeStats(queryClient: any) {
  return useWebSocket({
    autoConnect: true,
    onStatsUpdate: (stats) => {
      // 更新 React Query 缓存
      queryClient.setQueryData(['stats'], stats)
    },
    onTraceCreated: (trace) => {
      // 更新 traces 缓存
      queryClient.setQueryData(['traces'], (old: any) => {
        if (!old) return { traces: [trace], total: 1 }
        return {
          ...old,
          traces: [trace, ...old.traces],
          total: old.total + 1,
        }
      })
    },
    onTraceUpdated: (trace) => {
      // 更新单个 trace 缓存
      queryClient.setQueryData(['trace', trace.trace_id], trace)
      // 更新 traces 列表缓存
      queryClient.setQueryData(['traces'], (old: any) => {
        if (!old) return old
        return {
          ...old,
          traces: old.traces.map((t: any) => 
            t.trace_id === trace.trace_id ? trace : t
          ),
        }
      })
    },
    onTraceDeleted: (traceId) => {
      // 删除 trace 缓存
      queryClient.removeQueries(['trace', traceId])
      // 更新 traces 列表缓存
      queryClient.setQueryData(['traces'], (old: any) => {
        if (!old) return old
        return {
          ...old,
          traces: old.traces.filter((t: any) => t.trace_id !== traceId),
          total: old.total - 1,
        }
      })
    },
  })
}

export default useWebSocket