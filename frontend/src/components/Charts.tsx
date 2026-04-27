import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { api } from '../api';

interface ChartData {
  provider: string;
  cost: number;
  traces: number;
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

export default function Charts() {
  const [timeRange, setTimeRange] = useState(24);
  
  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: () => api.getStats(),
  });

  const { data: modelCosts } = useQuery({
    queryKey: ['modelCosts'],
    queryFn: () => api.getModelCosts(),
  });

  const { data: dashboard } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => api.getDashboard(),
  });

  const { data: timeline } = useQuery<{ interval: string; data: TimelinePoint[] }>({
    queryKey: ['timeline', timeRange],
    queryFn: () => api.getTimeline({ hours: timeRange }),
  });

  const { data: providerAnalytics } = useQuery({
    queryKey: ['providerAnalytics'],
    queryFn: () => api.getProviderAnalytics(),
  });

  // 准备图表数据
  const chartData: ChartData[] = stats?.by_provider
    ? Object.entries(stats.by_provider).map(([provider, providerData], index) => ({
        provider,
        cost: (providerData as { cost: number }).cost,
        traces: (providerData as { traces: number }).traces,
        color: getColor(index),
      }))
    : [];

  // 准备延迟分布数据
  const latencyDistribution: LatencyBucket[] = dashboard?.latency_distribution
    ? Object.entries(dashboard.latency_distribution).map(([label, count]) => ({
        label,
        count: count as number,
        percentage: dashboard.total_traces > 0 
          ? ((count as number) / dashboard.total_traces) * 100 
          : 0,
      }))
    : [];

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">📊 Analytics Charts</h1>

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

      {/* 时间线图表 */}
      <div className="mb-8 p-6 bg-gray-800 rounded-lg">
        <h2 className="text-lg font-semibold mb-4">📈 Trace Timeline</h2>
        
        {timeline && timeline.data && timeline.data.length > 0 ? (
          <div className="h-64 flex items-end gap-1 overflow-x-auto">
            {(() => {
              const timelineData = timeline.data;
              const maxTraces = Math.max(...timelineData.map(p => p.traces), 1);
              return timelineData.map((point, index) => {
                const height = (point.traces / maxTraces) * 200;
                return (
                  <div 
                    key={index}
                    className="flex flex-col items-center min-w-[40px]"
                    title={`${point.time}: ${point.traces} traces, $${point.cost.toFixed(4)}`}
                  >
                    <div
                      className="w-8 rounded-t transition-all duration-300 hover:opacity-80"
                      style={{
                        height: `${Math.max(height, 4)}px`,
                        backgroundColor: point.traces > 0 ? '#3b82f6' : '#374151',
                      }}
                    />
                    <p className="mt-1 text-xs text-gray-500 truncate max-w-[40px]">
                      {point.time.split(' ')[1] || point.time}
                    </p>
                  </div>
                );
              });
            })()}
          </div>
        ) : (
          <p className="text-gray-400 text-center py-8">No timeline data available</p>
        )}
        
        {timeline && timeline.data && timeline.data.length > 0 && (
          <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
            <div>
              <span className="text-gray-400">Total traces:</span>
              <span className="ml-2 font-bold">
                {timeline.data.reduce((sum, p) => sum + p.traces, 0)}
              </span>
            </div>
            <div>
              <span className="text-gray-400">Total cost:</span>
              <span className="ml-2 font-bold text-green-400">
                ${timeline.data.reduce((sum, p) => sum + p.cost, 0).toFixed(4)}
              </span>
            </div>
            <div>
              <span className="text-gray-400">Total tokens:</span>
              <span className="ml-2 font-bold">
                {timeline.data.reduce((sum, p) => sum + p.tokens, 0).toLocaleString()}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* 延迟分布图 */}
      {latencyDistribution.length > 0 && (
        <div className="mb-8 p-6 bg-gray-800 rounded-lg">
          <h2 className="text-lg font-semibold mb-4">⚡ Latency Distribution</h2>
          
          <div className="space-y-2">
            {latencyDistribution.map((bucket, index) => (
              <div key={bucket.label} className="flex items-center gap-4">
                <span className="text-sm text-gray-400 w-20">{bucket.label}</span>
                <div className="flex-1 h-8 bg-gray-700 rounded overflow-hidden">
                  <div
                    className="h-full transition-all duration-300"
                    style={{
                      width: `${bucket.percentage}%`,
                      backgroundColor: getLatencyColor(index),
                    }}
                  />
                </div>
                <span className="text-sm font-bold w-20 text-right">
                  {bucket.count} ({bucket.percentage.toFixed(1)}%)
                </span>
              </div>
            ))}
          </div>
          
          <div className="mt-4 pt-4 border-t border-gray-700">
            <p className="text-gray-400">
              Average latency: <span className="font-bold text-blue-400">{dashboard?.avg_latency_ms || 0}ms</span>
            </p>
          </div>
        </div>
      )}

      {/* Provider 分析 */}
      {providerAnalytics && providerAnalytics.length > 0 && (
        <div className="mb-8 p-6 bg-gray-800 rounded-lg">
          <h2 className="text-lg font-semibold mb-4">🏢 Provider Performance</h2>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left text-gray-400">
                  <th className="pb-3">Provider</th>
                  <th className="pb-3">Traces</th>
                  <th className="pb-3">Avg Latency</th>
                  <th className="pb-3">Success Rate</th>
                  <th className="pb-3">Total Cost</th>
                  <th className="pb-3">Tokens</th>
                </tr>
              </thead>
              <tbody>
                {providerAnalytics.map((provider: any) => (
                  <tr key={provider.provider} className="border-t border-gray-700">
                    <td className="py-3">
                      <span className="inline-block px-2 py-1 rounded text-xs" 
                        style={{ backgroundColor: getProviderColor(provider.provider) }}>
                        {provider.provider}
                      </span>
                    </td>
                    <td className="py-3">{provider.traces}</td>
                    <td className="py-3">
                      <span className={provider.avg_latency_ms < 1000 ? 'text-green-400' : 'text-yellow-400'}>
                        {provider.avg_latency_ms}ms
                      </span>
                    </td>
                    <td className="py-3">
                      <span className={provider.success_rate > 95 ? 'text-green-400' : 
                        provider.success_rate > 80 ? 'text-yellow-400' : 'text-red-400'}>
                        {provider.success_rate}%
                      </span>
                    </td>
                    <td className="py-3 text-green-400">${provider.total_cost.toFixed(4)}</td>
                    <td className="py-3">{provider.total_tokens.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 成本分布图 */}
      <div className="mb-8 p-6 bg-gray-800 rounded-lg">
        <h2 className="text-lg font-semibold mb-4">Cost Distribution by Provider</h2>
        
        {chartData.length > 0 ? (
          <div className="flex items-end gap-4 h-64">
            {chartData.map((item) => (
              <div key={item.provider} className="flex-1 flex flex-col items-center">
                <div
                  className="w-full rounded-t transition-all duration-300 hover:opacity-80"
                  style={{
                    height: `${(item.cost / Math.max(...chartData.map(d => d.cost))) * 200}px`,
                    backgroundColor: item.color,
                    minHeight: '20px',
                  }}
                />
                <p className="mt-2 text-sm text-gray-400">{item.provider}</p>
                <p className="text-lg font-bold">${item.cost.toFixed(4)}</p>
                <p className="text-xs text-gray-500">{item.traces} traces</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-400 text-center py-8">No cost data available</p>
        )}
      </div>

      {/* 成本对比表格 */}
      <div className="mb-8 p-6 bg-gray-800 rounded-lg">
        <h2 className="text-lg font-semibold mb-4">Model Cost Comparison</h2>
        
        <table className="w-full">
          <thead>
            <tr className="text-left text-gray-400">
              <th className="pb-3">Provider</th>
              <th className="pb-3">Model</th>
              <th className="pb-3">Input/1K</th>
              <th className="pb-3">Output/1K</th>
              <th className="pb-3">vs OpenAI</th>
            </tr>
          </thead>
          <tbody>
            {modelCosts?.models?.map((model: any) => (
              <tr key={`${model.provider}-${model.model}`} className="border-t border-gray-700">
                <td className="py-3">{model.provider}</td>
                <td className="py-3">{model.model}</td>
                <td className="py-3">${model.input_cost_per_1k.toFixed(5)}</td>
                <td className="py-3">${model.output_cost_per_1k.toFixed(5)}</td>
                <td className="py-3">
                  {model.provider === 'deepseek' && (
                    <span className="text-green-400 font-bold">
                      89x cheaper!
                    </span>
                  )}
                  {model.provider === 'anthropic' && (
                    <span className="text-yellow-400">
                      ~1.5x
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 成本节省计算 */}
      <div className="mb-8 p-6 bg-gradient-to-r from-blue-900 to-purple-900 rounded-lg">
        <h2 className="text-lg font-semibold mb-4">💡 Cost Savings Calculator</h2>
        
        <div className="grid grid-cols-2 gap-6">
          <div>
            <h3 className="text-gray-300 mb-2">If you use OpenAI GPT-4o:</h3>
            <p className="text-3xl font-bold text-red-400">
              ${((stats?.total_tokens || 0) * 0.01 / 1000).toFixed(2)}
            </p>
            <p className="text-sm text-gray-400 mt-1">
              Based on {stats?.total_tokens || 0} tokens
            </p>
          </div>
          <div>
            <h3 className="text-gray-300 mb-2">If you switch to DeepSeek:</h3>
            <p className="text-3xl font-bold text-green-400">
              ${((stats?.total_tokens || 0) * 0.00021 / 1000).toFixed(2)}
            </p>
            <p className="text-sm text-gray-400 mt-1">
              Save ${((stats?.total_tokens || 0) * 0.00979 / 1000).toFixed(2)} (89x savings!)
            </p>
          </div>
        </div>
      </div>

      {/* 统计摘要 */}
      <div className="grid grid-cols-4 gap-4">
        <div className="p-4 bg-gray-800 rounded-lg text-center">
          <p className="text-gray-400 text-sm">Total Traces</p>
          <p className="text-2xl font-bold mt-1">{stats?.total_traces || 0}</p>
        </div>
        <div className="p-4 bg-gray-800 rounded-lg text-center">
          <p className="text-gray-400 text-sm">Total Tokens</p>
          <p className="text-2xl font-bold mt-1">{stats?.total_tokens || 0}</p>
        </div>
        <div className="p-4 bg-gray-800 rounded-lg text-center">
          <p className="text-gray-400 text-sm">Total Cost</p>
          <p className="text-2xl font-bold mt-1">${(stats?.total_cost || 0).toFixed(2)}</p>
        </div>
        <div className="p-4 bg-gray-800 rounded-lg text-center">
          <p className="text-gray-400 text-sm">Avg Latency</p>
          <p className="text-2xl font-bold mt-1">{stats?.avg_latency_ms || 0}ms</p>
        </div>
      </div>
    </div>
  );
}

function getColor(index: number): string {
  const colors = [
    '#3b82f6', // blue
    '#10b981', // green
    '#f59e0b', // yellow
    '#ef4444', // red
    '#8b5cf6', // purple
  ];
  return colors[index % colors.length];
}

function getLatencyColor(index: number): string {
  const colors = [
    '#10b981', // green (<100ms)
    '#22c55e', // green-light (100-500ms)
    '#f59e0b', // yellow (500ms-1s)
    '#f97316', // orange (1-2s)
    '#ef4444', // red (2-5s)
    '#dc2626', // red-dark (5-10s)
    '#991b1b', // red-darker (>10s)
  ];
  return colors[index % colors.length];
}

function getProviderColor(provider: string): string {
  const colors: Record<string, string> = {
    'openai': '#10b981',
    'anthropic': '#f59e0b',
    'deepseek': '#3b82f6',
    'google': '#ef4444',
  };
  return colors[provider] || '#8b5cf6';
}