import { describe, it, expect, vi, beforeEach } from 'vitest';
import { api, AgentWatchWebSocket } from './api';

// Mock axios
vi.mock('axios', () => ({
  default: {
    create: () => ({
      get: vi.fn().mockResolvedValue({ data: {} }),
      post: vi.fn().mockResolvedValue({ data: {} }),
      put: vi.fn().mockResolvedValue({ data: {} }),
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() },
      },
    }),
  },
}));

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should have required API methods', () => {
    expect(api.getStats).toBeDefined();
    expect(api.getTraces).toBeDefined();
    expect(api.getTrace).toBeDefined();
    expect(api.createTrace).toBeDefined();
    expect(api.getDashboard).toBeDefined();
    expect(api.getModelCosts).toBeDefined();
    expect(api.getTimeline).toBeDefined();
    expect(api.getProviderAnalytics).toBeDefined();
  });

  it('should have WebSocket class available', () => {
    expect(AgentWatchWebSocket).toBeDefined();
  });

  it('WebSocket class should have required methods', () => {
    const wsCallbacks = {
      onConnected: vi.fn(),
      onTraceCreated: vi.fn(),
      onTraceUpdated: vi.fn(),
      onTraceDeleted: vi.fn(),
      onTraceEvent: vi.fn(),
      onStatsUpdate: vi.fn(),
      onError: vi.fn(),
      onDisconnected: vi.fn(),
    };
    
    const ws = new AgentWatchWebSocket(wsCallbacks);
    expect(ws.connect).toBeDefined();
    expect(ws.disconnect).toBeDefined();
    expect(ws.subscribe).toBeDefined();
    expect(ws.requestStats).toBeDefined();
    expect(ws.isConnected).toBeDefined();
  });
});