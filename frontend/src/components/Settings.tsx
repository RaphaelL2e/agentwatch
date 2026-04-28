import { useState, useEffect } from 'react';

interface BackendStatus {
  connected: boolean;
  version?: string;
  uptime?: number;
  traces_count?: number;
  storage_type?: string;
}

export default function Settings() {
  const [settings, setSettings] = useState({
    apiUrl: 'http://localhost:8000',
    refreshInterval: 5000,
    theme: 'dark',
    currency: 'USD',
  });
  
  const [backendStatus, setBackendStatus] = useState<BackendStatus>({
    connected: false,
  });
  
  const [loading, setLoading] = useState(false);

  // Fetch backend health status
  const checkBackendStatus = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${settings.apiUrl}/health`);
      if (response.ok) {
        const data = await response.json();
        setBackendStatus({
          connected: true,
          version: data.version,
          uptime: data.uptime_seconds,
          traces_count: data.traces_count,
          storage_type: data.database_connected ? 'connected' : 'memory',
        });
      } else {
        setBackendStatus({ connected: false });
      }
    } catch (error) {
      setBackendStatus({ connected: false });
    }
    setLoading(false);
  };

  useEffect(() => {
    const saved = localStorage.getItem('agentwatch_settings');
    if (saved) {
      setSettings(JSON.parse(saved));
    }
    // Check backend status on load
    checkBackendStatus();
  }, []);

  // Periodic backend status check
  useEffect(() => {
    const interval = setInterval(checkBackendStatus, 30000); // Check every 30s
    return () => clearInterval(interval);
  }, [settings.apiUrl]);

  const handleSave = () => {
    localStorage.setItem('agentwatch_settings', JSON.stringify(settings));
    checkBackendStatus(); // Re-check backend after saving
    alert('Settings saved!');
  };

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  return (
    <div className="p-8 max-w-2xl">
      <h1 className="text-2xl font-bold mb-6">Settings</h1>

      {/* Backend Status Card */}
      <div className="mb-6 p-4 bg-slate-800 rounded-lg border border-slate-700">
        <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
          Backend Status
          {loading && (
            <span className="text-sm text-slate-400 animate-pulse">checking...</span>
          )}
        </h2>
        
        <div className="flex items-center gap-4 mb-3">
          <div className={`flex items-center gap-2 ${
            backendStatus.connected 
              ? 'text-green-400' 
              : 'text-red-400'
          }`}>
            <span className={`w-3 h-3 rounded-full ${
              backendStatus.connected 
                ? 'bg-green-500 animate-pulse' 
                : 'bg-red-500'
            }`} />
            <span className="text-sm font-medium">
              {backendStatus.connected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          
          {backendStatus.connected && (
            <span className="text-sm text-slate-400">
              v{backendStatus.version}
            </span>
          )}
        </div>
        
        {backendStatus.connected && (
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <span className="text-slate-400">Uptime:</span>
              <span className="ml-2 text-white">
                {formatUptime(backendStatus.uptime || 0)}
              </span>
            </div>
            <div>
              <span className="text-slate-400">Traces:</span>
              <span className="ml-2 text-white">
                {backendStatus.traces_count || 0}
              </span>
            </div>
            <div>
              <span className="text-slate-400">Storage:</span>
              <span className="ml-2 text-white">
                {backendStatus.storage_type === 'connected' 
                  ? 'Database' 
                  : 'Memory'}
              </span>
            </div>
          </div>
        )}
        
        <button
          onClick={checkBackendStatus}
          className="mt-3 px-4 py-1.5 text-sm bg-slate-700 text-slate-300 rounded hover:bg-slate-600 transition-colors"
        >
          Refresh Status
        </button>
      </div>

      {/* API URL */}
      <div className="mb-4">
        <label className="block text-sm font-medium mb-2">
          API URL
        </label>
        <input
          type="text"
          value={settings.apiUrl}
          onChange={(e) => setSettings({ ...settings, apiUrl: e.target.value })}
          className="w-full px-3 py-2 border rounded-lg bg-gray-800 text-white border-slate-600 focus:border-blue-500 focus:outline-none"
        />
        <p className="text-sm text-slate-400 mt-1">
          Backend server URL (e.g., http://localhost:8000)
        </p>
      </div>

      {/* Refresh Interval */}
      <div className="mb-4">
        <label className="block text-sm font-medium mb-2">
          Dashboard Refresh Interval (ms)
        </label>
        <input
          type="number"
          value={settings.refreshInterval}
          onChange={(e) => setSettings({ ...settings, refreshInterval: Number(e.target.value) })}
          className="w-full px-3 py-2 border rounded-lg bg-gray-800 text-white border-slate-600 focus:border-blue-500 focus:outline-none"
        />
        <p className="text-sm text-slate-400 mt-1">
          How often the dashboard data refreshes (5000 = 5 seconds)
        </p>
      </div>

      {/* Theme */}
      <div className="mb-4">
        <label className="block text-sm font-medium mb-2">
          Theme
        </label>
        <select
          value={settings.theme}
          onChange={(e) => setSettings({ ...settings, theme: e.target.value })}
          className="w-full px-3 py-2 border rounded-lg bg-gray-800 text-white border-slate-600 focus:border-blue-500 focus:outline-none"
        >
          <option value="dark">Dark</option>
          <option value="light">Light</option>
        </select>
      </div>

      {/* Currency */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2">
          Currency Display
        </label>
        <select
          value={settings.currency}
          onChange={(e) => setSettings({ ...settings, currency: e.target.value })}
          className="w-full px-3 py-2 border rounded-lg bg-gray-800 text-white border-slate-600 focus:border-blue-500 focus:outline-none"
        >
          <option value="USD">USD ($)</option>
          <option value="CNY">CNY (¥)</option>
        </select>
      </div>

      {/* Save Button */}
      <button
        onClick={handleSave}
        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
      >
        Save Settings
      </button>

      {/* Reset Button */}
      <button
        onClick={() => setSettings({
          apiUrl: 'http://localhost:8000',
          refreshInterval: 5000,
          theme: 'dark',
          currency: 'USD',
        })}
        className="ml-4 px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
      >
        Reset to Default
      </button>

      {/* Help */}
      <div className="mt-8 p-4 bg-slate-800 rounded-lg border border-slate-700">
        <h2 className="text-lg font-semibold mb-2">Help</h2>
        <p className="text-slate-400 text-sm mb-3">
          AgentWatch monitors your AI Agents in real-time. Configure the API URL
          to connect to your backend server. The refresh interval controls how
          often the dashboard updates.
        </p>
        
        <h3 className="text-sm font-semibold mb-2 text-white">Storage Types</h3>
        <ul className="text-slate-400 text-sm space-y-1">
          <li><span className="text-white">Memory</span> - Fast, in-memory storage (restarts clear data)</li>
          <li><span className="text-white">SQLite</span> - Local file database (persistent)</li>
          <li><span className="text-white">ClickHouse</span> - Production-scale analytics database</li>
        </ul>
        
        <h3 className="text-sm font-semibold mb-2 mt-4 text-white">Quick Start</h3>
        <div className="bg-slate-900 rounded p-3 text-sm font-mono text-slate-300">
          <code>cd backend && python main.py</code>
        </div>
      </div>
      
      {/* Version Info */}
      <div className="mt-4 text-center text-slate-400 text-sm">
        AgentWatch v0.6.0 | Open-source AI Agent Monitoring
      </div>
    </div>
  );
}