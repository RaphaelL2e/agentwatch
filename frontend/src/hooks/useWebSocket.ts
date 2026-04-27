/**
 * WebSocket Hook for real-time AgentWatch updates
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { AgentWatchWebSocket, WebSocketCallbacks } from '../api';

interface UseWebSocketOptions {
  autoConnect?: boolean;
  onTraceCreated?: (trace: any) => void;
  onTraceUpdated?: (trace: any) => void;
  onTraceDeleted?: (traceId: string) => void;
  onStatsUpdate?: (stats: any) => void;
  onError?: (error: string) => void;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  connect: () => void;
  disconnect: () => void;
  requestStats: () => void;
  subscribe: (channels?: string[]) => void;
}

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const { 
    autoConnect = true,
    onTraceCreated,
    onTraceUpdated,
    onTraceDeleted,
    onStatsUpdate,
    onError,
  } = options;

  const wsRef = useRef<AgentWatchWebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  const callbacks: WebSocketCallbacks = {
    onConnected: () => setIsConnected(true),
    onDisconnected: () => setIsConnected(false),
    onTraceCreated,
    onTraceUpdated,
    onTraceDeleted,
    onStatsUpdate,
    onError,
  };

  const connect = useCallback(() => {
    if (!wsRef.current) {
      wsRef.current = new AgentWatchWebSocket(callbacks);
    }
    wsRef.current.connect();
  }, [callbacks]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.disconnect();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const requestStats = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.requestStats();
    }
  }, []);

  const subscribe = useCallback((channels?: string[]) => {
    if (wsRef.current) {
      wsRef.current.subscribe(channels);
    }
  }, []);

  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    isConnected,
    connect,
    disconnect,
    requestStats,
    subscribe,
  };
}

export default useWebSocket;