import { useState } from 'react';
import { api } from '../api';
import { Download, FileJson, FileSpreadsheet, BarChart2, Filter, Calendar } from 'lucide-react';

export default function Export() {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [_format, _setFormat] = useState<'json' | 'csv'>('json');
  const [provider, setProvider] = useState<string>('');
  const [status, setStatus] = useState<string>('');
  const [days, setDays] = useState<number>(7);
  const [exporting, setExporting] = useState<string>('');

  const handleExportTraces = async (type: 'json' | 'csv') => {
    setExporting('traces');
    try {
      const params = {
        provider: provider || undefined,
        status: status || undefined,
      };
      
      if (type === 'json') {
        await api.exportTracesJson(params);
      } else {
        await api.exportTracesCsv(params);
      }
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setExporting('');
    }
  };

  const handleExportCostSummary = async (type: 'json' | 'csv') => {
    setExporting('cost');
    try {
      const params = {
        provider: provider || undefined,
      };
      await api.exportCostSummary(type, params);
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setExporting('');
    }
  };

  const handleExportAnalyticsReport = async (type: 'json' | 'csv') => {
    setExporting('analytics');
    try {
      await api.exportAnalyticsReport(type, days);
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setExporting('');
    }
  };

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">📥 Data Export</h1>
      
      {/* Export Filters */}
      <div className="mb-8 p-6 bg-gray-800 rounded-lg">
        <div className="flex items-center gap-2 mb-4">
          <Filter className="w-5 h-5 text-blue-400" />
          <h2 className="text-lg font-semibold">Export Filters</h2>
        </div>
        
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="text-sm text-gray-400 block mb-2">Provider</label>
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="w-full bg-gray-700 text-white rounded px-3 py-2"
            >
              <option value="">All Providers</option>
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="deepseek">DeepSeek</option>
              <option value="google">Google</option>
            </select>
          </div>
          
          <div>
            <label className="text-sm text-gray-400 block mb-2">Status</label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="w-full bg-gray-700 text-white rounded px-3 py-2"
            >
              <option value="">All Statuses</option>
              <option value="running">Running</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
            </select>
          </div>
          
          <div>
            <label className="text-sm text-gray-400 block mb-2">Days for Analytics</label>
            <select
              value={days}
              onChange={(e) => setDays(parseInt(e.target.value))}
              className="w-full bg-gray-700 text-white rounded px-3 py-2"
            >
              <option value="1">1 day</option>
              <option value="7">7 days</option>
              <option value="14">14 days</option>
              <option value="30">30 days</option>
            </select>
          </div>
        </div>
      </div>

      {/* Export Options */}
      <div className="grid grid-cols-3 gap-6">
        {/* Traces Export */}
        <div className="p-6 bg-gray-800 rounded-lg">
          <div className="flex items-center gap-2 mb-4">
            <Download className="w-5 h-5 text-green-400" />
            <h2 className="text-lg font-semibold">Export Traces</h2>
          </div>
          <p className="text-gray-400 text-sm mb-4">
            Export all trace data including agent info, costs, and tokens.
          </p>
          
          <div className="flex gap-2">
            <button
              onClick={() => handleExportTraces('json')}
              disabled={exporting === 'traces'}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded disabled:opacity-50"
            >
              <FileJson className="w-4 h-4" />
              {exporting === 'traces' ? 'Exporting...' : 'JSON'}
            </button>
            <button
              onClick={() => handleExportTraces('csv')}
              disabled={exporting === 'traces'}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 rounded disabled:opacity-50"
            >
              <FileSpreadsheet className="w-4 h-4" />
              {exporting === 'traces' ? 'Exporting...' : 'CSV'}
            </button>
          </div>
        </div>

        {/* Cost Summary Export */}
        <div className="p-6 bg-gray-800 rounded-lg">
          <div className="flex items-center gap-2 mb-4">
            <BarChart2 className="w-5 h-5 text-yellow-400" />
            <h2 className="text-lg font-semibold">Cost Summary</h2>
          </div>
          <p className="text-gray-400 text-sm mb-4">
            Export cost breakdown by provider and model.
          </p>
          
          <div className="flex gap-2">
            <button
              onClick={() => handleExportCostSummary('json')}
              disabled={exporting === 'cost'}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded disabled:opacity-50"
            >
              <FileJson className="w-4 h-4" />
              {exporting === 'cost' ? 'Exporting...' : 'JSON'}
            </button>
            <button
              onClick={() => handleExportCostSummary('csv')}
              disabled={exporting === 'cost'}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 rounded disabled:opacity-50"
            >
              <FileSpreadsheet className="w-4 h-4" />
              {exporting === 'cost' ? 'Exporting...' : 'CSV'}
            </button>
          </div>
        </div>

        {/* Analytics Report Export */}
        <div className="p-6 bg-gray-800 rounded-lg">
          <div className="flex items-center gap-2 mb-4">
            <Calendar className="w-5 h-5 text-purple-400" />
            <h2 className="text-lg font-semibold">Analytics Report</h2>
          </div>
          <p className="text-gray-400 text-sm mb-4">
            Comprehensive report with daily trends and provider stats.
          </p>
          
          <div className="flex gap-2">
            <button
              onClick={() => handleExportAnalyticsReport('json')}
              disabled={exporting === 'analytics'}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded disabled:opacity-50"
            >
              <FileJson className="w-4 h-4" />
              {exporting === 'analytics' ? 'Exporting...' : 'JSON'}
            </button>
            <button
              onClick={() => handleExportAnalyticsReport('csv')}
              disabled={exporting === 'analytics'}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 rounded disabled:opacity-50"
            >
              <FileSpreadsheet className="w-4 h-4" />
              {exporting === 'analytics' ? 'Exporting...' : 'CSV'}
            </button>
          </div>
        </div>
      </div>

      {/* Usage Tips */}
      <div className="mt-8 p-6 bg-gray-800/50 rounded-lg border border-gray-700">
        <h3 className="text-lg font-semibold mb-3">💡 Export Tips</h3>
        <ul className="text-gray-400 text-sm space-y-2">
          <li>• <strong>JSON</strong> format preserves full data structure, ideal for API integration or backup</li>
          <li>• <strong>CSV</strong> format is spreadsheet-friendly, perfect for analysis in Excel or Google Sheets</li>
          <li>• Use filters to export only the data you need for focused analysis</li>
          <li>• Analytics report includes daily trends and provider breakdown for cost optimization insights</li>
        </ul>
      </div>
    </div>
  );
}