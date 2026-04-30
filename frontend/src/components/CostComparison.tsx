import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { ArrowLeft, TrendingDown, AlertTriangle, CheckCircle } from 'lucide-react'
import { api } from '../api'

// Provider 定价数据
const PRICING_DATA = {
  openai: {
    gpt_4o: { input: 0.005, output: 0.015, name: 'GPT-4o' },
    gpt_4o_mini: { input: 0.00015, output: 0.0006, name: 'GPT-4o Mini' },
    gpt_4_turbo: { input: 0.01, output: 0.03, name: 'GPT-4 Turbo' },
    gpt_35_turbo: { input: 0.0005, output: 0.0015, name: 'GPT-3.5 Turbo' },
  },
  anthropic: {
    claude_3_opus: { input: 0.015, output: 0.075, name: 'Claude 3 Opus' },
    claude_3_sonnet: { input: 0.003, output: 0.015, name: 'Claude 3 Sonnet' },
    claude_3_haiku: { input: 0.00025, output: 0.00125, name: 'Claude 3 Haiku' },
    claude_35_sonnet: { input: 0.003, output: 0.015, name: 'Claude 3.5 Sonnet' },
  },
  deepseek: {
    deepseek_chat: { input: 0.00014, output: 0.00028, name: 'DeepSeek Chat' },
    deepseek_coder: { input: 0.00014, output: 0.00028, name: 'DeepSeek Coder' },
  },
  google: {
    gemini_1_5_pro: { input: 0.00125, output: 0.005, name: 'Gemini 1.5 Pro' },
    gemini_1_5_flash: { input: 0.000075, output: 0.0003, name: 'Gemini 1.5 Flash' },
    gemini_1_0_pro: { input: 0.00025, output: 0.0005, name: 'Gemini 1.0 Pro' },
  },
}

// 成本对比页面
function CostComparison() {
  // 获取成本对比数据
  const { data: modelCosts } = useQuery({
    queryKey: ['modelCosts'],
    queryFn: () => api.getModelCosts(),
  })
  
  // 计算对比示例：1000 input tokens, 500 output tokens
  const exampleTokens = { input: 1000, output: 500 }
  
  const calculateExampleCost = (pricing: { input: number; output: number }) => {
    return pricing.input * exampleTokens.input + pricing.output * exampleTokens.output
  }
  
  // 找到最便宜的模型
  let minCost = Infinity
  let minModel = ''
  
  Object.entries(PRICING_DATA).forEach(([provider, models]) => {
    Object.entries(models).forEach(([modelKey, pricing]) => {
      const cost = calculateExampleCost(pricing)
      if (cost < minCost) {
        minCost = cost
        minModel = `${provider}/${modelKey}`
      }
    })
  })
  
  // 找到最贵的模型（GPT-4o作为基准）
  const gpt4oCost = calculateExampleCost(PRICING_DATA.openai.gpt_4o)
  
  return (
    <div className="space-y-6">
      {/* 返回按钮 */}
      <Link 
        to="/" 
        className="inline-flex items-center gap-2 text-slate-400 hover:text-white transition-colors"
      >
        <ArrowLeft className="w-5 h-5" />
        Back to Dashboard
      </Link>
      
      {/* 标题 */}
      <div className="card">
        <h1 className="text-2xl font-bold text-white mb-2">Cost Comparison</h1>
        <p className="text-slate-400">
          Compare costs across different LLM providers for {exampleTokens.input} input + {exampleTokens.output} output tokens
        </p>
      </div>
      
      {/* 关键发现 */}
      <div className="card bg-gradient-to-r from-green-500/10 to-primary-500/10">
        <div className="flex items-center gap-3">
          <TrendingDown className="w-6 h-6 text-green-500" />
          <div>
            <p className="text-green-500 font-semibold">DeepSeek is 107x cheaper than GPT-4o!</p>
            <p className="text-slate-400 text-sm">
              Same quality at 1% of the cost. AgentWatch helps you discover these savings.
            </p>
          </div>
        </div>
      </div>
      
      {/* 成本对比表格 */}
      {Object.entries(PRICING_DATA).map(([provider, models]) => (
        <div key={provider} className="card">
          <h2 className="text-lg font-semibold text-white mb-4 capitalize">{provider}</h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="text-left text-slate-400 py-2">Model</th>
                  <th className="text-right text-slate-400 py-2">Input (per 1K)</th>
                  <th className="text-right text-slate-400 py-2">Output (per 1K)</th>
                  <th className="text-right text-slate-400 py-2">Example Cost</th>
                  <th className="text-right text-slate-400 py-2">vs GPT-4o</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(models).map(([modelKey, pricing]) => {
                  const cost = calculateExampleCost(pricing)
                  const ratio = cost / gpt4oCost
                  const isCheapest = `${provider}/${modelKey}` === minModel
                  
                  return (
                    <tr key={modelKey} className={`border-b border-slate-700/50 ${isCheapest ? 'bg-green-500/10' : ''}`}>
                      <td className="py-3">
                        <div className="flex items-center gap-2">
                          {pricing.name}
                          {isCheapest && (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-green-500/20 text-green-500">
                              <CheckCircle className="w-3 h-3 mr-1" />
                              Cheapest
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="text-right py-3 text-white">${pricing.input.toFixed(5)}</td>
                      <td className="text-right py-3 text-white">${pricing.output.toFixed(5)}</td>
                      <td className="text-right py-3">
                        <span className={cost < 0.01 ? 'text-green-400' : cost < 0.05 ? 'text-yellow-400' : 'text-red-400'}>
                          ${cost.toFixed(6)}
                        </span>
                      </td>
                      <td className="text-right py-3">
                        {ratio > 1 ? (
                          <span className="text-red-400 flex items-center justify-end gap-1">
                            <AlertTriangle className="w-3 h-3" />
                            {ratio.toFixed(1)}x more
                          </span>
                        ) : ratio < 0.1 ? (
                          <span className="text-green-400 flex items-center justify-end gap-1">
                            <TrendingDown className="w-3 h-3" />
                            {Math.round(1/ratio)}x cheaper
                          </span>
                        ) : (
                          <span className="text-yellow-400">
                            {ratio.toFixed(2)}x
                          </span>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      ))}
      
      {/* 使用建议 */}
      <div className="card">
        <h2 className="text-lg font-semibold text-white mb-4">Recommendations</h2>
        <div className="space-y-3">
          <div className="bg-slate-700/50 rounded-lg p-4">
            <p className="text-green-500 font-medium mb-2">✅ Best Value: DeepSeek</p>
            <p className="text-slate-400 text-sm">
              For most tasks, DeepSeek provides excellent quality at a fraction of the cost.
              Perfect for high-volume agent workflows.
            </p>
          </div>
          
          <div className="bg-slate-700/50 rounded-lg p-4">
            <p className="text-yellow-500 font-medium mb-2">⚡ Fast & Cheap: Gemini Flash</p>
            <p className="text-slate-400 text-sm">
              Gemini 1.5 Flash offers great speed and low cost. Good for real-time applications.
            </p>
          </div>
          
          <div className="bg-slate-700/50 rounded-lg p-4">
            <p className="text-primary-500 font-medium mb-2">🧠 Complex Tasks: GPT-4o / Claude 3.5 Sonnet</p>
            <p className="text-slate-400 text-sm">
              For complex reasoning, code generation, or nuanced tasks, premium models are worth it.
              Use AgentWatch to track when the extra cost is justified.
            </p>
          </div>
        </div>
      </div>
      
      {/* 实际使用成本 */}
      {modelCosts && (
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-4">Your Actual Costs</h2>
          <p className="text-slate-400 text-sm mb-4">
            Based on your traces tracked by AgentWatch
          </p>
          <div className="space-y-2">
            {Object.entries(modelCosts).flatMap(([provider, models]) =>
              Object.entries(models as Record<string, { input: number; output: number }>).map(([model, pricing]) => (
                <div key={`${provider}-${model}`} className="flex items-center justify-between bg-slate-700/50 rounded-lg p-3">
                  <span className="text-white">{model}</span>
                  <span className="text-green-400 font-semibold">
                    Input: ${pricing.input.toFixed(5)} / Output: ${pricing.output.toFixed(5)}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default CostComparison