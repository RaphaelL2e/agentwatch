import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useState, useEffect, useMemo } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { api } from '../api';
import { 
  TrendingUp, Activity, Zap, AlertTriangle, Clock, DollarSign,
  ArrowUpRight, ArrowDownRight, Minus
} from 'lucide-react';

// ==================== 高级图表组件 ====================

// 实时连接状态指示器
function ConnectionStatus({ isConnected }: { isConnected: boolean }) {
  return (
    <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm ${
      isConnected 
        ? 'bg-green-900/50 text-green-400' 
        : 'bg-red-900/50 text-red-400'
    }`}>
      <div className={`w-2 h-2 rounded-full ${
        isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'
      }`} />
      {isConnected ? 'Live' : 'Offline'}
    </div>
  );
}

// 实时统计卡片（带趋势指示）
function StatCard({ 
  title, 
  value, 
  unit, 
  trend, 
  icon,
  color = 'blue'
}: {
  title: string;
  value: number;
  unit?: string;
  trend?: 'up' | 'down' | 'stable';
  icon: React.ReactNode;
  color?: 'blue' | 'green' | 'red' | 'yellow' | 'purple' | 'cyan';
}) {
  const colorClasses = {
    blue: 'bg-blue-900/30 text-blue-400',
    green: 'bg-green-900/30 text-green-400',
    red: 'bg-red-900/30 text-red-400',
    yellow: 'bg-yellow-900/30 text-yellow-400',
    purple: 'bg-purple-900/30 text-purple-400',
    cyan: 'bg-cyan-900/30 text-cyan-400',
  };
  
  const trendIcon = trend === 'up' ? <ArrowUpRight className="w-4 h-4 text-green-400" /> :
                    trend === 'down' ? <ArrowDownRight className="w-4 h-4 text-red-400" /> :
                    <Minus className="w-4 h-4 text-gray-400" />;
  
  const formatValue = (v: number, u?: string) => {
    if (u === '$') return `$${v.toFixed(4)}`;
    if (u === 'ms') return `${v.toFixed(0)}ms`;
    if (u === 'tokens') return v.toLocaleString();
    if (u === '%') return `${v.toFixed(1)}%`;
    return v.toString();
  };
  
  return (
    <div className={`${colorClasses[color]} rounded-lg p-4`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-400">{title}</span>
        <div className="flex items-center gap-1">
          {icon}
          {trendIcon}
        </div>
      </div>
      <div className="text-2xl font-bold">
        {formatValue(value, unit)}
      </div>
    </div>
  );
}

// 增强的柱状图（带动画和交互）
function AnimatedBarChart({ 
  data, 
  metric, 
  title,
  showComparison = false
}: {
  data: ChartData[];
  metric: 'traces' | 'cost' | 'tokens' | 'latency';
  title: string;
  showComparison?: boolean;
}) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  
  if (data.length === 0) return null;
  
  const maxValue = Math.max(...data.map(d => d[metric] as number), 1);
  
  const formatValue = (value: number, m: string) => {
    if (m === 'cost') return `$${value.toFixed(4)}`;
    if (m === 'tokens') return value.toLocaleString();
    if (m === 'latency') return `${value.toFixed(0)}ms`;
    return value.toString();
  };
  
  // 计算对比比例（DeepSeek vs OpenAI）
  const getComparisonRatio = (provider: string) => {
    if (!showComparison) return null;
    const openaiData = data.find(d => d.provider === 'openai');
    const currentData = data.find(d => d.provider === provider);
    if (!openaiData || !currentData || provider === 'openai') return null;
    const openaiValue = openaiData[metric] as number;
    const currentValue = currentData[metric] as number;
    if (!openaiValue || !currentValue) return null;
    const ratio = openaiValue / currentValue;
    return ratio > 1 ? `${ratio.toFixed(1)}x cheaper` : ratio < 1 ? `${(1/ratio).toFixed(1)}x expensive` : 'same';
  };
  
  return (
    <div className="mb-8 p-6 bg-gray-800 rounded-lg">
      <h2 className="text-lg font-semibold mb-4">{title}</h2>
      <div className="flex items-end gap-4 h-64">
        {data.map((item, index) => {
          const value = item[metric] as number;
          const height = (value / maxValue) * 200;
          const ratio = getComparisonRatio(item.provider);
          
          return (
            <div 
              key={item.provider} 
              className="flex-1 flex flex-col items-center group"
              onMouseEnter={() => setHoveredIndex(index)}
              onMouseLeave={() => setHoveredIndex(null)}
            >
              <div
                className={`w-full rounded-t transition-all duration-500 cursor-pointer ${
                  hoveredIndex === index ? 'opacity-100 scale-105' : 'opacity-80'
                }`}
                style={{
                  height: `${Math.max(height, 4)}px`,
                  backgroundColor: item.color,
                  minHeight: '20px',
                  boxShadow: hoveredIndex === index ? `0 0 20px ${item.color}` : 'none',
                }}
              >
                <div className={`text-center pt-2 text-xs font-bold ${
                  hoveredIndex === index ? 'block' : 'hidden group-hover:block'
                }`}>
                  {formatValue(value, metric)}
                </div>
              </div>
              <p className="mt-2 text-sm text-gray-400">{item.provider}</p>
              <p className="text-lg font-bold">{formatValue(value, metric)}</p>
              <p className="text-xs text-gray-500">{item.traces} traces</p>
              {ratio && (
                <p className="text-xs text-green-400 mt-1">{ratio}</p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// 增强的折线图（实时数据平滑过渡）
function SmoothLineChart({ 
  data, 
  metric,
  showPoints = true
}: {
  data: TimelinePoint[];
  metric: 'cost' | 'traces' | 'tokens';
  showPoints?: boolean;
}) {
  if (data.length === 0) return null;
  
  const maxValue = Math.max(...data.map(d => d[metric]), 0.01);
  const width = 100;
  const height = 50;
  
  // 使用贝塞尔曲线平滑
  const points = data.map((d, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - (d[metric] / maxValue) * (height - 10);
    return { x, y, value: d[metric] };
  });
  
  // 生成平滑路径
  const pathD = points.reduce((acc, p, i) => {
    if (i === 0) return `M ${p.x} ${p.y}`;
    const prev = points[i - 1];
    const cpx1 = prev.x + (p.x - prev.x) / 2;
    const cpy1 = prev.y;
    const cpx2 = prev.x + (p.x - prev.x) / 2;
    const cpy2 = p.y;
    return `${acc} C ${cpx1} ${cpy1}, ${cpx2} ${cpy2}, ${p.x} ${p.y}`;
  }, '');
  
  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-32">
      {/* 网格 */}
      <defs>
        <pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
          <path d="M 10 0 L 0 0 0 10" fill="none" stroke="#374151" strokeWidth="0.3" />
        </pattern>
      </defs>
      <rect width={width} height={height} fill="url(#grid)" />
      
      {/* 折线 */}
      <path
        d={pathD}
        fill="none"
        stroke="#3b82f6"
        strokeWidth="2"
        className="transition-all duration-500"
      />
      
      {/* 渐变填充 */}
      <defs>
        <linearGradient id="areaGradient" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path
        d={`${pathD} L ${width} ${height} L 0 ${height} Z`}
        fill="url(#areaGradient)"
      />
      
      {/* 数据点 */}
      {showPoints && points.map((p, i) => (
        <circle
          key={i}
          cx={p.x}
          cy={p.y}
          r={i === points.length - 1 ? 3 : 1.5}
          fill={i === points.length - 1 ? '#3b82f6' : '#6b7280'}
          className={i === points.length - 1 ? 'animate-pulse' : ''}
        />
      ))}
    </svg>
  );
}

// 延迟分布直方图
function LatencyHistogram({ data }: { data: LatencyBucket[] }) {
  if (data.length === 0) return null;
  
  const maxCount = Math.max(...data.map(d => d.count), 1);
  
  return (
    <div className="space-y-2">
      {data.map((bucket, index) => (
        <div key={index} className="flex items-center gap-4">
          <span className="text-xs text-gray-400 w-16">{bucket.label}</span>
          <div 
            className="flex-1 h-6 bg-gray-700 rounded overflow-hidden"
            title={`${bucket.count} traces (${bucket.percentage.toFixed(1)}%)`}
          >
            <div 
              className="h-full bg-gradient-to-r from-blue-600 to-blue-400 transition-all duration-500"
              style={{ width: `${(bucket.count / maxCount) * 100}%` }}
            />
          </div>
          <span className="text-xs font-bold text-gray-300 w-12">
            {bucket.count}
          </span>
          <span className="text-xs text-gray-500 w-10">
            {bucket.percentage.toFixed(1)}%
          </span>
        </div>
      ))}
    </div>
  );
}

// 实时预警面板
function AlertsPanel({ alerts }: { alerts: Alert[] }) {
  if (alerts.length === 0) {
    return (
      <div className="p-4 bg-gray-800 rounded-lg text-center text-gray-400">
        No alerts
      </div>
    );
  }
  
  const alertColors = {
    cost_spike: 'bg-red-900/50 text-red-400 border-red-500',
    high_latency: 'bg-yellow-900/50 text-yellow-400 border-yellow-500',
    agent_failure: 'bg-orange-900/50 text-orange-400 border-orange-500',
    token_overflow: 'bg-purple-900/50 text-purple-400 border-purple-500',
  };
  
  return (
    <div className="space-y-2 max-h-64 overflow-y-auto">
      {alerts.map((alert, index) => (
        <div 
          key={index}
          className={`p-3 rounded-lg border ${alertColors[alert.type]} flex items-center gap-3`}
        >
          <AlertTriangle className="w-5 h-5" />
          <div className="flex-1">
            <p className="font-semibold">{alert.message}</p>
            <p className="text-xs opacity-70">
              {new Date(alert.timestamp).toLocaleTimeString()}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}

// 实时活动流（增强版）
function RealtimeActivityFeed({ 
  traces, 
  newTrace 
}: { 
  traces: any[];
  newTrace?: any;
}) {
  const [highlightedId, setHighlightedId] = useState<string | null>(null);
  
  useEffect(() => {
    if (newTrace) {
      setHighlightedId(newTrace.trace_id);
      setTimeout(() => setHighlightedId(null), 2000);
    }
  }, [newTrace]);
  
  return (
    <div className="space-y-2 max-h-64 overflow-y-auto">
      {[...(newTrace ? [newTrace] : []), ...traces.slice(0, 10)].map((trace: any) => (
        <div 
          key={trace.trace_id} 
          className={`flex items-center gap-3 p-2 rounded text-sm transition-all duration-500 ${
            highlightedId === trace.trace_id 
              ? 'bg-blue-900/50 scale-105 border border-blue-500' 
              : 'bg-gray-700/50'
          }`}
        >
          <div className={`w-2 h-2 rounded-full ${
            trace.status === 'completed' ? 'bg-green-500' :
            trace.status === 'running' ? 'bg-yellow-500 animate-pulse' :
            trace.status === 'failed' ? 'bg-red-500' :
            'bg-gray-500'
          }`} />
          <span className="text-gray-300 flex-1 truncate">{trace.agent_name}</span>
          <span className="text-gray-400">{trace.provider}</span>
          <span className="text-green-400">${trace.total_cost.toFixed(4)}</span>
          <span className="text-gray-500 text-xs">
            {new Date(trace.created_at).toLocaleTimeString()}
          </span>
        </div>
      ))}
    </div>
  );
}

// ==================== 类型定义 ====================

interface ChartData {
  provider: string;
  cost: number;
  traces: number;
  tokens: number;
  latency?: number;
  color: string;
}

interface TimelinePoint {
  time: string;
  traces: number;
  cost: number;
  tokens: number;
}

interface LatencyBucket {
  label: string;
  count: number;
  percentage: number;
}

interface Alert {
  type: 'cost_spike' | 'high_latency' | 'agent_failure' | 'token_overflow';
  message: string;
  timestamp: string;
  data?: any;
}

// ==================== 辅助函数 ====================

function getColor(index: number): string {
  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4', '#ef4444'];
  return colors[index % colors.length];
}

// ==================== 主组件 ====================

export default function Charts() {
  const queryClient = useQueryClient();
  const [timeRange, setTimeRange] = useState(24);
  const [selectedMetric, _setSelectedMetric] = useState<'traces' | 'cost' | 'tokens' | 'latency'>('cost');
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [newTrace, setNewTrace] = useState<any>(null);
  
  // WebSocket 实时连接
  const { isConnected, lastMessage } = useWebSocket({
    autoConnect: true,
    onTraceCreated: (trace) => {
      setNewTrace(trace);
      queryClient.setQueryData(['traces'], (old: any) => {
        if (!old) return { traces: [trace], total: 1 };
        return { ...old, traces: [trace, ...old.traces], total: old.total + 1 };
      });
    },
    onStatsUpdate: (stats) => {
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
        ...prev.slice(0, 9), // 保留最近10条
      ]);
    }
  }, [lastMessage]);
  
  // 数据查询
  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: () => api.getStats(),
  });
  
  const { data: traces } = useQuery({
    queryKey: ['traces'],
    queryFn: () => api.getTraces({ page_size: 50 }),
  });
  
  const { data: timeline } = useQuery<{ interval: string; data: TimelinePoint[] }>({
    queryKey: ['timeline', timeRange],
    queryFn: () => api.getTimeline({ hours: timeRange }),
  });
  
  // 准备图表数据
  const chartData: ChartData[] = useMemo(() => {
    if (!stats?.by_provider) return [];
    return Object.entries(stats.by_provider).map(([provider, providerData], index) => {
      const data = providerData as { 
        cost: number; 
        traces: number;
        total_input_tokens?: number;
        total_output_tokens?: number;
        avg_latency_ms?: number;
      };
      const tokens = (data.total_input_tokens || 0) + (data.total_output_tokens || 0);
      return {
        provider,
        cost: data.cost,
        traces: data.traces,
        tokens,
        latency: data.avg_latency_ms || 0,
        color: getColor(index),
      };
    });
  }, [stats]);
  
  // 计算趋势
  const getTrend = (current: number, previous?: number): 'up' | 'down' | 'stable' => {
    if (!previous) return 'stable';
    const change = (current - previous) / previous;
    if (change > 0.05) return 'up';
    if (change < -0.05) return 'down';
    return 'stable';
  };
  
  return (
    <div className="p-8">
      {/* 标题栏 */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">📊 Real-time Analytics</h1>
        <ConnectionStatus isConnected={isConnected} />
      </div>
      
      {/* 实时统计卡片 */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <StatCard
          title="Total Cost"
          value={stats?.total_cost || 0}
          unit="$"
          trend={getTrend(stats?.total_cost || 0, stats?.previous_cost)}
          icon={<DollarSign className="w-4 h-4" />}
          color="green"
        />
        <StatCard
          title="Total Traces"
          value={stats?.total_traces || 0}
          trend={getTrend(stats?.total_traces || 0, stats?.previous_traces)}
          icon={<Activity className="w-4 h-4" />}
          color="blue"
        />
        <StatCard
          title="Total Tokens"
          value={stats?.total_tokens || 0}
          unit="tokens"
          trend={getTrend(stats?.total_tokens || 0, stats?.previous_tokens)}
          icon={<Zap className="w-4 h-4" />}
          color="yellow"
        />
        <StatCard
          title="Avg Latency"
          value={stats?.avg_latency_ms || 0}
          unit="ms"
          trend={getTrend(stats?.avg_latency_ms || 0, stats?.previous_latency)}
          icon={<Clock className="w-4 h-4" />}
          color="purple"
        />
      </div>
      
      {/* 时间范围选择 */}
      <div className="mb-6 flex gap-2">
        {[1, 6, 24, 72, 168].map((hours) => (
          <button
            key={hours}
            onClick={() => setTimeRange(hours)}
            className={`px-4 py-2 rounded ${
              timeRange === hours 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            {hours < 24 ? `${hours}h` : `${hours / 24}d`}
          </button>
        ))}
      </div>
      
      {/* 预警面板 */}
      {alerts.length > 0 && (
        <div className="mb-8 p-4 bg-gray-800 rounded-lg">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            <h2 className="text-lg font-semibold">Active Alerts</h2>
          </div>
          <AlertsPanel alerts={alerts} />
        </div>
      )}
      
      {/* Provider 柱状图 */}
      <AnimatedBarChart 
        data={chartData} 
        metric={selectedMetric === 'latency' ? 'cost' : selectedMetric}
        title="Provider Distribution"
        showComparison={selectedMetric === 'cost'}
      />
      
      {/* 成本趋势图 */}
      <div className="mb-8 p-6 bg-gray-800 rounded-lg">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="w-5 h-5 text-green-400" />
          <h2 className="text-lg font-semibold">Cost Trend (Real-time)</h2>
        </div>
        {timeline && timeline.data && timeline.data.length > 0 ? (
          <>
            <SmoothLineChart data={timeline.data} metric="cost" />
            <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-gray-400">Total:</span>
                <span className="ml-2 font-bold text-green-400">
                  ${timeline.data.reduce((sum, p) => sum + p.cost, 0).toFixed(4)}
                </span>
              </div>
              <div>
                <span className="text-gray-400">Avg/h:</span>
                <span className="ml-2 font-bold">
                  ${(timeline.data.reduce((sum, p) => sum + p.cost, 0) / timeline.data.length).toFixed(4)}
                </span>
              </div>
              <div>
                <span className="text-gray-400">Peak:</span>
                <span className="ml-2 font-bold text-yellow-400">
                  ${Math.max(...timeline.data.map(p => p.cost)).toFixed(4)}
                </span>
              </div>
            </div>
          </>
        ) : (
          <p className="text-gray-400 text-center py-8">No trend data</p>
        )}
      </div>
      
      {/* 实时活动流 */}
      <div className="mb-8 p-6 bg-gray-800 rounded-lg">
        <div className="flex items-center gap-2 mb-4">
          <Activity className="w-5 h-5 text-purple-400" />
          <h2 className="text-lg font-semibold">Live Activity</h2>
        </div>
        <RealtimeActivityFeed 
          traces={traces?.traces || []} 
          newTrace={newTrace}
        />
      </div>
      
      {/* 延迟分布 */}
      {stats?.latency_distribution && (
        <div className="mb-8 p-6 bg-gray-800 rounded-lg">
          <div className="flex items-center gap-2 mb-4">
            <Clock className="w-5 h-5 text-cyan-400" />
            <h2 className="text-lg font-semibold">Latency Distribution</h2>
          </div>
          <LatencyHistogram 
            data={Object.entries(stats.latency_distribution).map(([label, count]) => ({
              label,
              count: count as number,
              percentage: stats.total_traces > 0 
                ? ((count as number) / stats.total_traces) * 100 
                : 0,
            }))} 
          />
        </div>
      )}
    </div>
  );
}