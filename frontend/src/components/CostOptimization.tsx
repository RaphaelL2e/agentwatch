import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { api } from '../api';
import { TrendingUp, DollarSign, Zap, Calculator, ArrowRight, CheckCircle, AlertCircle } from 'lucide-react';

// Provider cost data (per 1K tokens)
const PROVIDER_COSTS = {
  openai: {
    gpt_4o: { input: 0.005, output: 0.015 },
    gpt_4o_mini: { input: 0.00015, output: 0.0006 },
  },
  anthropic: {
    claude_3_5_sonnet: { input: 0.003, output: 0.015 },
    claude_3_haiku: { input: 0.00025, output: 0.00125 },
  },
  deepseek: {
    deepseek_chat: { input: 0.00014, output: 0.00028 },
    deepseek_reasoner: { input: 0.00014, output: 0.00028 },
  },
  google: {
    gemini_1_5_pro: { input: 0.00125, output: 0.005 },
    gemini_1_5_flash: { input: 0.000075, output: 0.0003 },
  },
};

const PROVIDER_NAMES = {
  openai: 'OpenAI',
  anthropic: 'Anthropic',
  deepseek: 'DeepSeek',
  google: 'Google',
};

const MODEL_NAMES = {
  gpt_4o: 'GPT-4o',
  gpt_4o_mini: 'GPT-4o-mini',
  claude_3_5_sonnet: 'Claude 3.5 Sonnet',
  claude_3_haiku: 'Claude 3 Haiku',
  deepseek_chat: 'DeepSeek Chat',
  deepseek_reasoner: 'DeepSeek Reasoner R1',
  gemini_1_5_pro: 'Gemini 1.5 Pro',
  gemini_1_5_flash: 'Gemini 1.5 Flash',
};

interface SavingsCalculation {
  currentProvider: string;
  currentModel: string;
  targetProvider: string;
  targetModel: string;
  monthlyTokens: number;
  currentCost: number;
  targetCost: number;
  savings: number;
  savingsPercent: number;
}

function calculateSavings(
  currentProvider: string,
  currentModel: string,
  targetProvider: string,
  targetModel: string,
  monthlyTokens: number,
  inputRatio: number = 0.7, // 70% input tokens, 30% output tokens typical
): SavingsCalculation {
  const currentCosts = PROVIDER_COSTS[currentProvider]?.[currentModel];
  const targetCosts = PROVIDER_COSTS[targetProvider]?.[targetModel];

  if (!currentCosts || !targetCosts) {
    return null;
  }

  const inputTokens = monthlyTokens * inputRatio;
  const outputTokens = monthlyTokens * (1 - inputRatio);

  const currentCost = (inputTokens * currentCosts.input) + (outputTokens * currentCosts.output);
  const targetCost = (inputTokens * targetCosts.input) + (outputTokens * targetCosts.output);
  const savings = currentCost - targetCost;
  const savingsPercent = ((currentCost - targetCost) / currentCost) * 100;

  return {
    currentProvider,
    currentModel,
    targetProvider,
    targetModel,
    monthlyTokens,
    currentCost,
    targetCost,
    savings,
    savingsPercent,
  };
}

function SavingsCard({ calculation }: { calculation: SavingsCalculation }) {
  const isPositive = calculation.savings > 0;

  return (
    <div className={`p-4 rounded-lg ${isPositive ? 'bg-green-900/30 border border-green-700' : 'bg-red-900/30 border border-red-700'}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-300">{MODEL_NAMES[calculation.currentModel]}</span>
          <ArrowRight className="w-4 h-4 text-gray-400" />
          <span className="text-sm font-bold text-white">{MODEL_NAMES[calculation.targetModel]}</span>
        </div>
        {isPositive ? (
          <CheckCircle className="w-5 h-5 text-green-400" />
        ) : (
          <AlertCircle className="w-5 h-5 text-red-400" />
        )}
      </div>

      <div className="grid grid-cols-3 gap-4 text-sm">
        <div>
          <p className="text-gray-400">Current Cost</p>
          <p className="text-lg font-bold">${calculation.currentCost.toFixed(2)}/mo</p>
        </div>
        <div>
          <p className="text-gray-400">New Cost</p>
          <p className={`text-lg font-bold ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
            ${calculation.targetCost.toFixed(2)}/mo
          </p>
        </div>
        <div>
          <p className="text-gray-400">Savings</p>
          <p className={`text-lg font-bold ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
            {isPositive ? '-' : '+'}${Math.abs(calculation.savings).toFixed(2)}/mo
            <span className="text-xs ml-1">({calculation.savingsPercent.toFixed(1)}%)</span>
          </p>
        </div>
      </div>
    </div>
  );
}

function ModelSelector({ 
  provider, 
  model, 
  onProviderChange, 
  onModelChange,
  label 
}: { 
  provider: string; 
  model: string; 
  onProviderChange: (p: string) => void;
  onModelChange: (m: string) => void;
  label: string;
}) {
  const models = PROVIDER_COSTS[provider] ? Object.keys(PROVIDER_COSTS[provider]) : [];

  return (
    <div className="space-y-2">
      <label className="text-sm text-gray-400">{label}</label>
      <select
        value={provider}
        onChange={(e) => {
          onProviderChange(e.target.value);
          // Auto-select first model for new provider
          const newModels = Object.keys(PROVIDER_COSTS[e.target.value] || {});
          if (newModels.length > 0) {
            onModelChange(newModels[0]);
          }
        }}
        className="w-full p-2 bg-gray-700 rounded text-white border border-gray-600"
      >
        {Object.keys(PROVIDER_COSTS).map((p) => (
          <option key={p} value={p}>{PROVIDER_NAMES[p]}</option>
        ))}
      </select>
      <select
        value={model}
        onChange={(e) => onModelChange(e.target.value)}
        className="w-full p-2 bg-gray-700 rounded text-white border border-gray-600"
      >
        {models.map((m) => (
          <option key={m} value={m}>{MODEL_NAMES[m]}</option>
        ))}
      </select>
    </div>
  );
}

export default function CostOptimization() {
  const [currentProvider, setCurrentProvider] = useState('openai');
  const [currentModel, setCurrentModel] = useState('gpt_4o');
  const [targetProvider, setTargetProvider] = useState('deepseek');
  const [targetModel, setTargetModel] = useState('deepseek_chat');
  const [monthlyTokens, setMonthlyTokens] = useState(1000000); // 1M tokens default

  // Calculate all possible savings
  const allSavings: SavingsCalculation[] = [];
  Object.entries(PROVIDER_COSTS).forEach(([p, models]) => {
    Object.keys(models).forEach((m) => {
      if (p !== currentProvider || m !== currentModel) {
        const calc = calculateSavings(currentProvider, currentModel, p, m, monthlyTokens);
        if (calc) {
          allSavings.push(calc);
        }
      }
    });
  });

  // Sort by savings (highest first)
  allSavings.sort((a, b) => b.savings - a.savings);

  // Current calculation
  const currentCalculation = calculateSavings(
    currentProvider, currentModel, targetProvider, targetModel, monthlyTokens
  );

  // Best alternative
  const bestAlternative = allSavings[0];

  // Get actual stats from API
  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: () => api.getStats(),
  });

  // Calculate real monthly tokens from stats if available
  const realMonthlyTokens = stats?.total_input_tokens && stats?.total_output_tokens
    ? (stats.total_input_tokens + stats.total_output_tokens) * 30 // Estimate monthly from daily
    : monthlyTokens;

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
        <Calculator className="w-6 h-6 text-yellow-400" />
        Cost Optimization Calculator
      </h1>

      {/* Key insight banner */}
      <div className="mb-8 p-4 bg-gradient-to-r from-green-900/50 to-blue-900/50 rounded-lg border border-green-700">
        <div className="flex items-center gap-3">
          <TrendingUp className="w-8 h-8 text-green-400" />
          <div>
            <p className="text-lg font-bold text-white">
              DeepSeek costs only 1/107 of GPT-4o!
            </p>
            <p className="text-sm text-gray-300">
              Switching from GPT-4o to DeepSeek can save you up to 99.1% on API costs.
            </p>
          </div>
        </div>
      </div>

      {/* Calculator section */}
      <div className="mb-8 p-6 bg-gray-800 rounded-lg">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <DollarSign className="w-5 h-5 text-blue-400" />
          Compare Providers
        </h2>

        <div className="grid grid-cols-2 gap-6 mb-6">
          <ModelSelector
            provider={currentProvider}
            model={currentModel}
            onProviderChange={setCurrentProvider}
            onModelChange={setCurrentModel}
            label="Current Provider/Model"
          />
          <ModelSelector
            provider={targetProvider}
            model={targetModel}
            onProviderChange={setTargetProvider}
            onModelChange={setTargetModel}
            label="Target Provider/Model"
          />
        </div>

        {/* Monthly tokens slider */}
        <div className="mb-6">
          <label className="text-sm text-gray-400">Monthly Tokens</label>
          <div className="flex items-center gap-4 mt-2">
            <input
              type="range"
              min="10000"
              max="10000000"
              step="10000"
              value={monthlyTokens}
              onChange={(e) => setMonthlyTokens(parseInt(e.target.value))}
              className="w-full h-2 bg-gray-600 rounded-lg appearance-none cursor-pointer"
            />
            <span className="text-lg font-bold text-white">
              {monthlyTokens.toLocaleString()}
            </span>
          </div>
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>10K</span>
            <span>1M</span>
            <span>10M</span>
          </div>
        </div>

        {/* Current comparison result */}
        {currentCalculation && (
          <div className="mb-6">
            <SavingsCard calculation={currentCalculation} />
          </div>
        )}

        {/* Per-token cost breakdown */}
        <div className="p-4 bg-gray-700 rounded-lg">
          <h3 className="text-sm font-semibold mb-3 text-gray-300">Per-Token Cost Breakdown</h3>
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div>
              <p className="text-gray-400">{MODEL_NAMES[currentModel]}</p>
              <p className="text-white">
                Input: ${(PROVIDER_COSTS[currentProvider]?.[currentModel]?.input || 0).toFixed(5)}/1K
              </p>
              <p className="text-white">
                Output: ${(PROVIDER_COSTS[currentProvider]?.[currentModel]?.output || 0).toFixed(5)}/1K
              </p>
            </div>
            <div>
              <p className="text-gray-400">{MODEL_NAMES[targetModel]}</p>
              <p className="text-white">
                Input: ${(PROVIDER_COSTS[targetProvider]?.[targetModel]?.input || 0).toFixed(5)}/1K
              </p>
              <p className="text-white">
                Output: ${(PROVIDER_COSTS[targetProvider]?.[targetModel]?.output || 0).toFixed(5)}/1K
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Best alternatives section */}
      <div className="mb-8 p-6 bg-gray-800 rounded-lg">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Zap className="w-5 h-5 text-yellow-400" />
          Best Alternatives for {MODEL_NAMES[currentModel]}
        </h2>

        <div className="space-y-3">
          {allSavings.slice(0, 5).map((calc, i) => (
            <SavingsCard key={i} calculation={calc} />
          ))}
        </div>
      </div>

      {/* Annual savings projection */}
      {bestAlternative && bestAlternative.savings > 0 && (
        <div className="mb-8 p-6 bg-gradient-to-r from-green-900/30 to-emerald-900/30 rounded-lg border border-green-600">
          <h2 className="text-lg font-semibold mb-4 text-green-400">
            🎯 Annual Savings Projection
          </h2>

          <div className="grid grid-cols-3 gap-4">
            <div className="p-4 bg-gray-800 rounded-lg">
              <p className="text-sm text-gray-400">Current Annual Cost</p>
              <p className="text-2xl font-bold text-white">
                ${(currentCalculation?.currentCost * 12 || 0).toFixed(2)}
              </p>
            </div>
            <div className="p-4 bg-gray-800 rounded-lg">
              <p className="text-sm text-gray-400">New Annual Cost</p>
              <p className="text-2xl font-bold text-green-400">
                ${(currentCalculation?.targetCost * 12 || 0).toFixed(2)}
              </p>
            </div>
            <div className="p-4 bg-gray-800 rounded-lg">
              <p className="text-sm text-gray-400">Annual Savings</p>
              <p className="text-2xl font-bold text-green-400">
                ${(currentCalculation?.savings * 12 || 0).toFixed(2)}
              </p>
            </div>
          </div>

          {currentCalculation && currentCalculation.savings > 100 && (
            <p className="mt-4 text-center text-green-300 font-semibold">
              💰 Switching to {MODEL_NAMES[targetModel]} saves you ${((currentCalculation.savings * 12) / 1000).toFixed(1)}K per year!
            </p>
          )}
        </div>
      )}

      {/* Cost comparison table */}
      <div className="p-6 bg-gray-800 rounded-lg">
        <h2 className="text-lg font-semibold mb-4">📊 Full Provider Cost Comparison</h2>
        
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-400 border-b border-gray-700">
                <th className="p-2">Provider</th>
                <th className="p-2">Model</th>
                <th className="p-2">Input Cost</th>
                <th className="p-2">Output Cost</th>
                <th className="p-2">vs GPT-4o</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(PROVIDER_COSTS).flatMap(([p, models]) =>
                Object.entries(models).map(([m, costs]) => {
                  const avgCost = (costs.input + costs.output) / 2;
                  const gpt4oAvgCost = (PROVIDER_COSTS.openai.gpt_4o.input + PROVIDER_COSTS.openai.gpt_4o.output) / 2;
                  const ratio = avgCost / gpt4oAvgCost;
                  
                  return (
                    <tr key={`${p}-${m}`} className="border-b border-gray-700">
                      <td className="p-2 text-gray-300">{PROVIDER_NAMES[p]}</td>
                      <td className="p-2 text-white font-semibold">{MODEL_NAMES[m]}</td>
                      <td className="p-2 text-gray-300">${costs.input.toFixed(5)}/1K</td>
                      <td className="p-2 text-gray-300">${costs.output.toFixed(5)}/1K</td>
                      <td className={`p-2 font-bold ${ratio < 0.1 ? 'text-green-400' : ratio < 0.5 ? 'text-yellow-400' : 'text-gray-300'}`}>
                        {ratio < 1 ? `${((1 - ratio) * 100).toFixed(1)}% cheaper` : `${((ratio - 1) * 100).toFixed(1)}% more`}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Real data comparison */}
      {stats && (
        <div className="mt-8 p-6 bg-gray-800 rounded-lg">
          <h2 className="text-lg font-semibold mb-4">📈 Your Current Usage Stats</h2>
          <div className="grid grid-cols-4 gap-4">
            <div className="p-3 bg-gray-700 rounded">
              <p className="text-xs text-gray-400">Total Traces</p>
              <p className="text-lg font-bold">{stats.total_traces || 0}</p>
            </div>
            <div className="p-3 bg-gray-700 rounded">
              <p className="text-xs text-gray-400">Input Tokens</p>
              <p className="text-lg font-bold">{(stats.total_input_tokens || 0).toLocaleString()}</p>
            </div>
            <div className="p-3 bg-gray-700 rounded">
              <p className="text-xs text-gray-400">Output Tokens</p>
              <p className="text-lg font-bold">{(stats.total_output_tokens || 0).toLocaleString()}</p>
            </div>
            <div className="p-3 bg-gray-700 rounded">
              <p className="text-xs text-gray-400">Current Cost</p>
              <p className="text-lg font-bold text-green-400">${(stats.total_cost || 0).toFixed(4)}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}