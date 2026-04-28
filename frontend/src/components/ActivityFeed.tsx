import { useState, useEffect } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { 
  Activity, 
  PlusCircle, 
  RefreshCw, 
  Trash2, 
  AlertTriangle,
  CheckCircle,
  Clock,
  Zap,
  Wifi,
  WifiOff
} from 'lucide-react';

interface ActivityEvent {
  id: string;
  type: 'trace_created' | 'trace_updated' | 'trace_deleted' | 'trace_event' | 'stats_update' | 'error';
  timestamp: string;
  data: any;
}

interface RealTimeActivityFeedProps {
  maxEvents?: number;
  showConnectionStatus?: boolean;
  onEventClick?: (event: ActivityEvent) => void;
}

/**
 * Real-time Activity Feed Component
 * 
 * Displays live WebSocket events as they occur
 */
export function RealTimeActivityFeed({ 
  maxEvents = 50, 
  showConnectionStatus = true,
  onEventClick
}: RealTimeActivityFeedProps) {
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [isPaused, setIsPaused] = useState(false);
  
  const { isConnected, connectionStatus, lastMessage } = useWebSocket({
    autoConnect: true,
    onTraceCreated: (trace) => {
      if (!isPaused) {
        addEvent('trace_created', trace);
      }
    },
    onTraceUpdated: (trace) => {
      if (!isPaused) {
        addEvent('trace_updated', trace);
      }
    },
    onTraceDeleted: (traceId) => {
      if (!isPaused) {
        addEvent('trace_deleted', { trace_id: traceId });
      }
    },
    onStatsUpdate: (stats) => {
      if (!isPaused) {
        addEvent('stats_update', stats);
      }
    },
    onError: (error) => {
      if (!isPaused) {
        addEvent('error', { message: error });
      }
    },
  });
  
  const addEvent = (type: ActivityEvent['type'], data: any) => {
    const newEvent: ActivityEvent = {
      id: `${type}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type,
      timestamp: new Date().toISOString(),
      data,
    };
    
    setEvents(prev => {
      const updated = [newEvent, ...prev];
      // Keep only the last N events
      return updated.slice(0, maxEvents);
    });
  };
  
  const clearEvents = () => {
    setEvents([]);
  };
  
  const getEventIcon = (type: ActivityEvent['type']) => {
    switch (type) {
      case 'trace_created':
        return <PlusCircle className="w-4 h-4 text-green-500" />;
      case 'trace_updated':
        return <RefreshCw className="w-4 h-4 text-blue-500" />;
      case 'trace_deleted':
        return <Trash2 className="w-4 h-4 text-red-500" />;
      case 'trace_event':
        return <Zap className="w-4 h-4 text-yellow-500" />;
      case 'stats_update':
        return <Activity className="w-4 h-4 text-purple-500" />;
      case 'error':
        return <AlertTriangle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };
  
  const getEventColor = (type: ActivityEvent['type']) => {
    switch (type) {
      case 'trace_created':
        return 'border-green-500/30 bg-green-500/10';
      case 'trace_updated':
        return 'border-blue-500/30 bg-blue-500/10';
      case 'trace_deleted':
        return 'border-red-500/30 bg-red-500/10';
      case 'trace_event':
        return 'border-yellow-500/30 bg-yellow-500/10';
      case 'stats_update':
        return 'border-purple-500/30 bg-purple-500/10';
      case 'error':
        return 'border-red-500/50 bg-red-500/20';
      default:
        return 'border-gray-500/30 bg-gray-500/10';
    }
  };
  
  const getEventTitle = (event: ActivityEvent) => {
    switch (event.type) {
      case 'trace_created':
        return `New Trace: ${event.data.agent_name || 'Unknown'}`;
      case 'trace_updated':
        return `Updated: ${event.data.agent_name || event.data.trace_id}`;
      case 'trace_deleted':
        return `Deleted: ${event.data.trace_id}`;
      case 'trace_event':
        return `Event on ${event.data.trace_id}`;
      case 'stats_update':
        return 'Stats Updated';
      case 'error':
        return `Error: ${event.data.message}`;
      default:
        return 'Unknown Event';
    }
  };
  
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };
  
  const formatEventDetails = (event: ActivityEvent) => {
    switch (event.type) {
      case 'trace_created':
        return `${event.data.provider || 'N/A'} | ${event.data.model || 'N/A'}`;
      case 'trace_updated':
        return `Status: ${event.data.status || 'N/A'}`;
      case 'trace_deleted':
        return '';
      case 'trace_event':
        return event.data.event?.event_type || 'N/A';
      case 'stats_update':
        return `Traces: ${event.data.total_traces || 0}`;
      case 'error':
        return event.data.message;
      default:
        return '';
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-semibold text-white">Real-time Activity</h2>
          {showConnectionStatus && (
            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs ${
              isConnected 
                ? 'bg-green-500/20 text-green-500' 
                : connectionStatus === 'connecting'
                ? 'bg-yellow-500/20 text-yellow-500'
                : 'bg-red-500/20 text-red-500'
            }`}>
              {isConnected ? <Wifi className="w-3 h-3 mr-1" /> : <WifiOff className="w-3 h-3 mr-1" />}
              {isConnected ? 'Live' : connectionStatus}
            </span>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsPaused(!isPaused)}
            className={`px-3 py-1 rounded text-sm ${
              isPaused 
                ? 'bg-yellow-500/20 text-yellow-500 hover:bg-yellow-500/30' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            {isPaused ? '▶ Resume' : '⏸ Pause'}
          </button>
          <button
            onClick={clearEvents}
            className="px-3 py-1 rounded text-sm bg-gray-700 text-gray-300 hover:bg-gray-600"
          >
            Clear
          </button>
        </div>
      </div>
      
      {/* Event count */}
      <div className="text-sm text-gray-400 mb-3">
        {events.length} events {isPaused && '(paused)'}
      </div>
      
      {/* Events list */}
      <div className="space-y-2 max-h-400 overflow-y-auto">
        {events.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>No events yet</p>
            <p className="text-xs mt-1">Waiting for WebSocket events...</p>
          </div>
        ) : (
          events.map((event) => (
            <div
              key={event.id}
              onClick={() => onEventClick?.(event)}
              className={`p-3 rounded border ${getEventColor(event.type)} ${
                onEventClick ? 'cursor-pointer hover:opacity-80' : ''
              } transition-opacity`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {getEventIcon(event.type)}
                  <span className="text-white font-medium text-sm">
                    {getEventTitle(event)}
                  </span>
                </div>
                <span className="text-gray-400 text-xs">
                  {formatTime(event.timestamp)}
                </span>
              </div>
              
              {formatEventDetails(event) && (
                <div className="mt-1 text-xs text-gray-400">
                  {formatEventDetails(event)}
                </div>
              )}
            </div>
          ))
        )}
      </div>
      
      {/* Live indicator */}
      {isConnected && !isPaused && (
        <div className="mt-4 flex items-center justify-center">
          <div className="flex items-center gap-1 text-green-500 text-xs">
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span>Listening for events...</span>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Compact Activity Feed for sidebar/embedded use
 */
export function CompactActivityFeed({ maxEvents = 10 }: { maxEvents?: number }) {
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  
  const { isConnected, lastMessage } = useWebSocket({
    autoConnect: true,
    onTraceCreated: (trace) => {
      addEvent('trace_created', trace);
    },
    onTraceUpdated: (trace) => {
      addEvent('trace_updated', trace);
    },
  });
  
  const addEvent = (type: ActivityEvent['type'], data: any) => {
    const newEvent: ActivityEvent = {
      id: `${type}_${Date.now()}`,
      type,
      timestamp: new Date().toISOString(),
      data,
    };
    
    setEvents(prev => [newEvent, ...prev].slice(0, maxEvents));
  };

  return (
    <div className="bg-gray-800 rounded-lg p-3">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-white">Activity</span>
        <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
      </div>
      
      <div className="space-y-1">
        {events.slice(0, 5).map((event) => (
          <div key={event.id} className="flex items-center gap-2 text-xs text-gray-400">
            {event.type === 'trace_created' && <PlusCircle className="w-3 h-3 text-green-500" />}
            {event.type === 'trace_updated' && <RefreshCw className="w-3 h-3 text-blue-500" />}
            <span className="truncate">{event.data.agent_name || event.data.trace_id}</span>
          </div>
        ))}
        
        {events.length === 0 && (
          <div className="text-xs text-gray-500 text-center py-2">
            No activity
          </div>
        )}
      </div>
    </div>
  );
}

export default RealTimeActivityFeed;