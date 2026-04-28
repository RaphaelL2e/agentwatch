import { useState, useEffect } from 'react'
import { AlertTriangle, TrendingUp, DollarSign, Bell, X } from 'lucide-react'

interface AlertConfig {
  dailyCostThreshold: number  // 日成本阈值 ($)
  monthlyCostThreshold: number // 月成本阈值 ($)
  tokenSpikeThreshold: number  // Token突增阈值 (倍数)
  failureRateThreshold: number // 失败率阈值 (%)
}

interface CostAlert {
  id: string
  type: 'cost' | 'token_spike' | 'failure_rate' | 'budget'
  severity: 'warning' | 'critical'
  message: string
  details: string
  timestamp: Date
  dismissed?: boolean
}

const DEFAULT_CONFIG: AlertConfig = {
  dailyCostThreshold: 10,      // 日成本超过 $10 告警
  monthlyCostThreshold: 100,   // 月成本超过 $100 告警
  tokenSpikeThreshold: 2,      // Token 使用突增 2x 告警
  failureRateThreshold: 10,    // 失败率超过 10% 告警
}

export function CostAlerts({ stats, traces }: { stats?: any; traces?: any }) {
  const [alerts, setAlerts] = useState<CostAlert[]>([])
  const [config, setConfig] = useState<AlertConfig>(DEFAULT_CONFIG)
  const [showConfig, setShowConfig] = useState(false)

  // 检查告警条件
  useEffect(() => {
    if (!stats) return

    const newAlerts: CostAlert[] = []
    const now = new Date()

    // 日成本告警
    if (stats.today_cost > config.dailyCostThreshold) {
      newAlerts.push({
        id: `daily-cost-${now.getTime()}`,
        type: 'cost',
        severity: stats.today_cost > config.dailyCostThreshold * 2 ? 'critical' : 'warning',
        message: `日成本超阈值: $${stats.today_cost.toFixed(2)}`,
        details: `阈值: $${config.dailyCostThreshold}，超出 ${(stats.today_cost / config.dailyCostThreshold * 100 - 100).toFixed(0)}%`,
        timestamp: now,
      })
    }

    // 月成本告警
    if (stats.month_cost > config.monthlyCostThreshold) {
      newAlerts.push({
        id: `monthly-cost-${now.getTime()}`,
        type: 'budget',
        severity: stats.month_cost > config.monthlyCostThreshold * 1.5 ? 'critical' : 'warning',
        message: `月成本超预算: $${stats.month_cost.toFixed(2)}`,
        details: `预算: $${config.monthlyCostThreshold}，已使用 ${(stats.month_cost / config.monthlyCostThreshold * 100).toFixed(0)}%`,
        timestamp: now,
      })
    }

    // 失败率告警
    if (stats.total_traces > 10) {
      const failureRate = (stats.failed_traces / stats.total_traces) * 100
      if (failureRate > config.failureRateThreshold) {
        newAlerts.push({
          id: `failure-rate-${now.getTime()}`,
          type: 'failure_rate',
          severity: failureRate > 20 ? 'critical' : 'warning',
          message: `失败率过高: ${failureRate.toFixed(1)}%`,
          details: `阈值: ${config.failureRateThreshold}%，${stats.failed_traces} 个失败`,
          timestamp: now,
        })
      }
    }

    // Token 突增告警（需要历史数据）
    if (traces && traces.length > 10) {
      const recentTraces = traces.slice(0, 5)
      const olderTraces = traces.slice(5, 10)
      
      const recentTokens = recentTraces.reduce((sum: number, t: any) => sum + (t.total_tokens || 0), 0)
      const olderTokens = olderTraces.reduce((sum: number, t: any) => sum + (t.total_tokens || 0), 0)
      
      if (olderTokens > 0 && recentTokens / olderTokens > config.tokenSpikeThreshold) {
        newAlerts.push({
          id: `token-spike-${now.getTime()}`,
          type: 'token_spike',
          severity: 'warning',
          message: `Token 使用突增`,
          details: `近期 ${recentTokens} vs 历史 ${olderTokens}，突增 ${(recentTokens / olderTokens).toFixed(1)}x`,
          timestamp: now,
        })
      }
    }

    setAlerts(newAlerts.filter(a => !alerts.find(existing => existing.id === a.id && !existing.dismissed)))
  }, [stats, traces, config])

  // 清除告警
  const dismissAlert = (id: string) => {
    setAlerts(alerts.map(a => a.id === id ? { ...a, dismissed: true } : a))
  }

  // 清除所有告警
  const clearAllAlerts = () => {
    setAlerts([])
  }

  const activeAlerts = alerts.filter(a => !a.dismissed)

  if (activeAlerts.length === 0 && !showConfig) {
    return null
  }

  return (
    <div className="space-y-4">
      {/* 告警列表 */}
      {activeAlerts.length > 0 && (
        <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Bell className="w-5 h-5 text-orange-500" />
              <h3 className="text-white font-semibold">成本告警 ({activeAlerts.length})</h3>
            </div>
            <button
              onClick={clearAllAlerts}
              className="text-slate-400 hover:text-white text-sm"
            >
              清除全部
            </button>
          </div>

          <div className="space-y-3">
            {activeAlerts.map(alert => (
              <div
                key={alert.id}
                className={`p-3 rounded-lg ${
                  alert.severity === 'critical'
                    ? 'bg-red-500/20 border border-red-500/30'
                    : 'bg-orange-500/20 border border-orange-500/30'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    {alert.severity === 'critical' 
                      ? <AlertTriangle className="w-5 h-5 text-red-500 mt-0.5" />
                      : <TrendingUp className="w-5 h-5 text-orange-500 mt-0.5" />
                    }
                    <div>
                      <p className={`font-medium ${
                        alert.severity === 'critical' ? 'text-red-500' : 'text-orange-500'
                      }`}>
                        {alert.message}
                      </p>
                      <p className="text-slate-400 text-sm mt-1">{alert.details}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => dismissAlert(alert.id)}
                    className="text-slate-400 hover:text-white"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 告警配置 */}
      {showConfig && (
        <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <DollarSign className="w-5 h-5 text-green-500" />
              <h3 className="text-white font-semibold">告警阈值配置</h3>
            </div>
            <button
              onClick={() => setShowConfig(false)}
              className="text-slate-400 hover:text-white text-sm"
            >
              关闭
            </button>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-400 text-sm mb-2">日成本阈值 ($)</label>
              <input
                type="number"
                value={config.dailyCostThreshold}
                onChange={(e) => setConfig({ ...config, dailyCostThreshold: Number(e.target.value) })}
                className="w-full px-3 py-2 bg-slate-700 rounded-lg text-white border border-slate-600 focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-slate-400 text-sm mb-2">月成本预算 ($)</label>
              <input
                type="number"
                value={config.monthlyCostThreshold}
                onChange={(e) => setConfig({ ...config, monthlyCostThreshold: Number(e.target.value) })}
                className="w-full px-3 py-2 bg-slate-700 rounded-lg text-white border border-slate-600 focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-slate-400 text-sm mb-2">Token突增阈值 (x倍)</label>
              <input
                type="number"
                value={config.tokenSpikeThreshold}
                onChange={(e) => setConfig({ ...config, tokenSpikeThreshold: Number(e.target.value) })}
                className="w-full px-3 py-2 bg-slate-700 rounded-lg text-white border border-slate-600 focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-slate-400 text-sm mb-2">失败率阈值 (%)</label>
              <input
                type="number"
                value={config.failureRateThreshold}
                onChange={(e) => setConfig({ ...config, failureRateThreshold: Number(e.target.value) })}
                className="w-full px-3 py-2 bg-slate-700 rounded-lg text-white border border-slate-600 focus:border-primary-500"
              />
            </div>
          </div>

          <div className="mt-4 text-xs text-slate-500">
            配置仅保存在本地，刷新页面后重置
          </div>
        </div>
      )}

      {/* 配置按钮 */}
      {!showConfig && (
        <button
          onClick={() => setShowConfig(true)}
          className="text-slate-400 hover:text-white text-sm flex items-center gap-1"
        >
          <DollarSign className="w-4 h-4" />
          配置告警阈值
        </button>
      )}
    </div>
  )
}

// Provider 成本分布组件
export function ProviderCostBreakdown({ stats }: { stats?: any }) {
  if (!stats?.by_provider) return null

  const providers = Object.entries(stats.by_provider)
    .sort(([, a], [, b]) => (b as any).cost - (a as any).cost)

  const totalCost = providers.reduce((sum, [, data]) => sum + (data as any).cost, 0)

  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
        <DollarSign className="w-5 h-5 text-green-500" />
        Provider 成本分布
      </h3>

      <div className="space-y-3">
        {providers.map(([provider, data]) => {
          const cost = (data as any).cost
          const traces = (data as any).traces
          const percentage = (cost / totalCost * 100)

          return (
            <div key={provider} className="flex items-center gap-4">
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-white">{provider}</span>
                  <span className="text-green-400">${cost.toFixed(4)}</span>
                </div>
                <div className="relative h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className="absolute h-full bg-gradient-to-r from-primary-500 to-primary-600 rounded-full"
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>
              <div className="text-right">
                <p className="text-slate-400 text-xs">{percentage.toFixed(1)}%</p>
                <p className="text-slate-500 text-xs">{traces} traces</p>
              </div>
            </div>
          )
        })}
      </div>

      <div className="mt-4 pt-4 border-t border-slate-700">
        <div className="flex items-center justify-between">
          <span className="text-slate-400">总成本</span>
          <span className="text-white font-semibold">${totalCost.toFixed(4)}</span>
        </div>
      </div>
    </div>
  )
}

// 成本节省建议组件
export function CostSavingSuggestions({ stats }: { stats?: any }) {
  if (!stats?.by_provider) return null

  // 假设 DeepSeek 成本是 OpenAI 的 1/107
  const DEEPSEEK_SAVINGS_RATIO = 107

  const suggestions = []
  
  // 检查是否使用 OpenAI 但没用 DeepSeek
  if (stats.by_provider.openai && !stats.by_provider.deepseek) {
    const openaiCost = stats.by_provider.openai.cost
    const potentialSavings = openaiCost - openaiCost / DEEPSEEK_SAVINGS_RATIO
    
    suggestions.push({
      title: '切换到 DeepSeek',
      savings: potentialSavings,
      description: `OpenAI 成本 $${openaiCost.toFixed(4)}，DeepSeek 可节省 $${potentialSavings.toFixed(4)}`,
      action: '考虑迁移到 DeepSeek V3',
    })
  }

  // 检查高成本 Provider
  const highCostProviders = Object.entries(stats.by_provider)
    .filter(([, data]) => (data as any).cost > 0.01)
    .sort(([, a], [, b]) => (b as any).cost - (a as any).cost)

  if (highCostProviders.length > 0) {
    const [provider] = highCostProviders[0]
    suggestions.push({
      title: `监控 ${provider} 使用`,
      savings: 0,
      description: `${provider} 是当前最高成本 Provider，建议审查使用频率`,
      action: '查看详细 Trace 分析',
    })
  }

  if (suggestions.length === 0) return null

  return (
    <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
      <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
        <TrendingUp className="w-5 h-5 text-blue-500" />
        成本优化建议
      </h3>

      <div className="space-y-3">
        {suggestions.map((s, i) => (
          <div key={i} className="p-3 bg-slate-700 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-white font-medium">{s.title}</span>
              {s.savings > 0 && (
                <span className="text-green-400 text-sm">节省 ${s.savings.toFixed(4)}</span>
              )}
            </div>
            <p className="text-slate-400 text-sm">{s.description}</p>
            <p className="text-primary-500 text-sm mt-2">{s.action}</p>
          </div>
        ))}
      </div>
    </div>
  )
}