import { useState, useEffect } from 'react';

export default function Settings() {
  const [settings, setSettings] = useState({
    apiUrl: 'http://localhost:8000',
    refreshInterval: 5000,
    theme: 'dark',
    currency: 'USD',
  });

  const handleSave = () => {
    localStorage.setItem('agentwatch_settings', JSON.stringify(settings));
    alert('Settings saved!');
  };

  useEffect(() => {
    const saved = localStorage.getItem('agentwatch_settings');
    if (saved) {
      setSettings(JSON.parse(saved));
    }
  }, []);

  return (
    <div className="p-8 max-w-2xl">
      <h1 className="text-2xl font-bold mb-6">Settings</h1>

      {/* API URL */}
      <div className="mb-4">
        <label className="block text-sm font-medium mb-2">
          API URL
        </label>
        <input
          type="text"
          value={settings.apiUrl}
          onChange={(e) => setSettings({ ...settings, apiUrl: e.target.value })}
          className="w-full px-3 py-2 border rounded-lg bg-gray-800 text-white"
        />
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
          className="w-full px-3 py-2 border rounded-lg bg-gray-800 text-white"
        />
      </div>

      {/* Theme */}
      <div className="mb-4">
        <label className="block text-sm font-medium mb-2">
          Theme
        </label>
        <select
          value={settings.theme}
          onChange={(e) => setSettings({ ...settings, theme: e.target.value })}
          className="w-full px-3 py-2 border rounded-lg bg-gray-800 text-white"
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
          className="w-full px-3 py-2 border rounded-lg bg-gray-800 text-white"
        >
          <option value="USD">USD ($)</option>
          <option value="CNY">CNY (¥)</option>
        </select>
      </div>

      {/* Save Button */}
      <button
        onClick={handleSave}
        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
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
        className="ml-4 px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
      >
        Reset to Default
      </button>

      {/* Help */}
      <div className="mt-8 p-4 bg-gray-800 rounded-lg">
        <h2 className="text-lg font-semibold mb-2">Help</h2>
        <p className="text-gray-400">
          AgentWatch monitors your AI Agents in real-time. Configure the API URL
          to connect to your backend server. The refresh interval controls how
          often the dashboard updates.
        </p>
      </div>
    </div>
  );
}