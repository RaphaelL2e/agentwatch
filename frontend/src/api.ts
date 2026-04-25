/**
 * AgentWatch API Client
 * 与后端 FastAPI 通信
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

export const api = {
  // 基础端点
  getHealth: () => client.get('/health').then(r => r.data),
  getStats: () => client.get('/stats').then(r => r.data),
  
  // Trace API
  getTraces: (params?: { page?: number; page_size?: number }) => 
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
}

export default api