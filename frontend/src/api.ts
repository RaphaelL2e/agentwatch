/**
 * AgentWatch API Client
 * 与后端 FastAPI 通信，支持 WebSocket 实时更新
 */

import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const client = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ==================== HTTP API ====================

export const api = {
  // 基础端点
  getHealth: () => client.get('/health').then(r => r.data),
  getStats: () => client.get('/stats').then(r => r.data),
  getRoot: () => client.get('/').then(r => r.data),
  
  // Trace API
  getTraces: (params?: { page?: number; page_size?: number; agent_id?: string; provider?: string; status?: string }) => 
    client.get('/api/v1/traces', { params }).then(r => r.data),
  
  getTrace: (traceId: string) => 
    client.get(`/api/v1/trace/${traceId}`).then(r => r.data),
  
  createTrace: (data: {
    agent_id: string;
    agent_name: string;
    provider: string;
    model: string;
    session_id?: string;
    user_id?: string;
    prompt?: string;
  }) => client.post('/api/v1/trace', data).then(r => r.data),
  
  createTestTrace: () => 
    client.post('/api/v1/test/trace').then(r => r.data),
  
  updateTrace: (traceId: string, data: any) => 
    client.put(`/api/v1/trace/${traceId}`, data).then(r => r.data),
  
  addEvent: (traceId: string, event: any) => 
    client.post(`/api/v1/trace/${traceId}/event`, event).then(r => r.data),
  
  deleteTrace: (traceId: string) => 
    client.delete(`/api/v1/trace/${traceId}`).then(r => r.data),
  
  // Cost API
  getCostSummary: (params?: { provider?: string }) => 
    client.get('/api/v1/cost/summary', { params }).then(r => r.data),
  
  getModelCosts: () => 
    client.get('/api/v1/cost/models').then(r => r.data),
  
  // Dashboard API
  getDashboard: () => 
    client.get('/api/v1/dashboard').then(r => r.data),
  
  // Analytics API
  getTimeline: (params?: { interval?: string; hours?: number }) => 
    client.get('/api/v1/analytics/timeline', { params }).then(r => r.data),
  
  getProviderAnalytics: () => 
    client.get('/api/v1/analytics/providers').then(r => r.data),
  
  // Model Cost Comparison API
  getModelPricing: () => 
    client.get('/api/v1/models/pricing').then(r => r.data),
  
  getModelComparison: (params?: { input_tokens?: number; output_tokens?: number; compare_to?: string }) => 
    client.get('/api/v1/models/comparison', { params }).then(r => r.data),
  
  getModelRecommendation: (params?: { monthly_budget?: number; expected_tokens?: number }) => 
    client.get('/api/v1/models/recommendation', { params }).then(r => r.data),
  
  getModelPerformance: () => 
    client.get('/api/v1/models/performance').then(r => r.data),
}

// ==================== WebSocket 连接 ====================

export type WebSocketMessageType = 
  | 'connected'
  | 'trace_created'
  | 'trace_updated'
  | 'trace_deleted'
  | 'trace_event'
  | 'test_trace_created'
  | 'stats_update'
  | 'ping'
  | 'pong'
  | 'error'
  | 'subscribed'

export interface WebSocketMessage {
  type: WebSocketMessageType
  data?: any
  message?: string
  timestamp: string
}

export interface WebSocketCallbacks {
  onConnected?: () => void
  onTraceCreated?: (trace: any) => void
  onTraceUpdated?: (trace: any) => void
  onTraceDeleted?: (traceId: string) => void
  onTraceEvent?: (data: { trace_id: string; event: any; trace: any }) => void
  onStatsUpdate?: (stats: any) => void
  onError?: (error: string) => void
  onDisconnected?: () => void
}

export class AgentWatchWebSocket {
  private ws: WebSocket | null = null
  private callbacks: WebSocketCallbacks
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private pingInterval: number | null = null
  
  constructor(callbacks: WebSocketCallbacks = {}) {
    this.callbacks = callbacks
  }
  
  connect() {
    const wsUrl = API_BASE.replace('http://', 'ws://').replace('https://', 'wss://')
    this.ws = new WebSocket(`${wsUrl}/ws`)
    
    this.ws.onopen = () => {
      console.log('WebSocket connected')
      this.reconnectAttempts = 0
      this.startPingInterval()
      this.callbacks.onConnected?.()
    }
    
    this.ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data)
        this.handleMessage(message)
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e)
      }
    }
    
    this.ws.onclose = () => {
      console.log('WebSocket disconnected')
      this.stopPingInterval()
      this.callbacks.onDisconnected?.()
      this.tryReconnect()
    }
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      this.callbacks.onError?.('WebSocket connection error')
    }
  }
  
  private handleMessage(message: WebSocketMessage) {
    switch (message.type) {
      case 'connected':
        console.log('Server confirmed connection')
        break
      
      case 'trace_created':
        this.callbacks.onTraceCreated?.(message.data)
        break
      
      case 'trace_updated':
        this.callbacks.onTraceUpdated?.(message.data)
        break
      
      case 'trace_deleted':
        this.callbacks.onTraceDeleted?.(message.data.trace_id)
        break
      
      case 'trace_event':
        this.callbacks.onTraceEvent?.(message.data)
        break
      
      case 'stats_update':
        this.callbacks.onStatsUpdate?.(message.data)
        break
      
      case 'pong':
        // Heartbeat response
        break
      
      case 'error':
        this.callbacks.onError?.(message.message || 'Unknown error')
        break
      
      default:
        console.log('Unknown message type:', message.type)
    }
  }
  
  private startPingInterval() {
    this.pingInterval = window.setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }))
      }
    }, 30000) // 每30秒发送一次心跳
  }
  
  private stopPingInterval() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval)
      this.pingInterval = null
    }
  }
  
  private tryReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      const delay = this.reconnectDelay * this.reconnectAttempts
      console.log(`Attempting reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`)
      setTimeout(() => this.connect(), delay)
    }
  }
  
  subscribe(channels: string[] = ['all']) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'subscribe', channels }))
    }
  }
  
  requestStats() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'get_stats' }))
    }
  }
  
  disconnect() {
    this.stopPingInterval()
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }
  
  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN
  }
}

export default api