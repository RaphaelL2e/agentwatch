import { useQuery } from '@tanstack/react-query';
import { api } from '../api';

interface ChartData {
  provider: string;
  cost: number;
  traces: number;
  color: string;
}

export default function Charts() {
  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: () => api.getStats(),
  });

  const { data: modelCosts } = useQuery({
    queryKey: ['modelCosts'],
    queryFn: () => api.getModelCosts(),
  });

  // 准备图表数据
  const chartData: ChartData[] = stats?.by_provider
    ? Object.entries(stats.by_provider).map(([provider, data], index) => ({
        provider,
        cost: data.cost,
        traces: data.traces,
        color: getColor(index),
      }))
    : [];

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">📊 Analytics Charts</h1>

      {/* 成本分布图 */}
      <div className="mb-8 p-6 bg-gray-800 rounded-lg">
        <h2 className="text-lg font-semibold mb-4">Cost Distribution by Provider</h2>
        
        {/* 简单柱状图 */}
        <div className="flex items-end gap-4 h-64">
          {chartData.map((item) => (
            <div key={item.provider} className="flex-1 flex flex-col items-center">
              <div
                className="w-full rounded-t transition-all duration-300"
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