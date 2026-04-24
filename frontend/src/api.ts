import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1';

export interface Trace {
  trace_id: string;
  agent_id: string;
  timestamp: string;
  status: string;
}

export interface AgentMetrics {
  agent_id: string;
  executions: number;
  success_rate: number;
  avg_latency: number;
}

export const api = {
  // Trace API
  getTraces: async (limit = 100): Promise<{ traces: Trace[] }> => 
    axios.get(`${API_BASE}/traces?limit=${limit}`).then(r => r.data),
  
  getTrace: async (traceId: string): Promise<Trace> =>
    axios.get(`${API_BASE}/trace/${traceId}`).then(r => r.data),

  // Agent API
  getAgents: async (): Promise<{ agents: string[] }> =>
    axios.get(`${API_BASE}/agents`).then(r => r.data),

  getAgentMetrics: async (agentId: string): Promise<AgentMetrics> =>
    axios.get(`${API_BASE}/agent/${agentId}/metrics`).then(r => r.data),

  // Security API
  getSecurityAlerts: async (): Promise<{ alerts: any[] }> =>
    axios.get(`${API_BASE}/security/alerts`).then(r => r.data),

  scanDependencies: async (data: any): Promise<{ scan_id: string }> =>
    axios.post(`${API_BASE}/security/scan`, data).then(r => r.data),
};