// About.tsx - No React imports needed (no hooks used)

export default function About() {
  return (
    <div className="p-8 max-w-4xl">
      <h1 className="text-3xl font-bold mb-6">About AgentWatch</h1>

      {/* Mission */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">🎯 Our Mission</h2>
        <p className="text-gray-300 leading-relaxed">
          AgentWatch is an open-source AI Agent monitoring platform. We help developers
          track, analyze, and optimize their AI Agents' performance and costs.
        </p>
        <p className="text-gray-300 leading-relaxed mt-4">
          Our goal is to make AI Agents <strong className="text-white">observable, optimizable, and trustworthy</strong>.
        </p>
      </div>

      {/* Key Discovery */}
      <div className="mb-8 p-6 bg-gradient-to-r from-blue-900 to-purple-900 rounded-lg">
        <h2 className="text-xl font-semibold mb-4">💡 Key Discovery</h2>
        <p className="text-white leading-relaxed">
          <strong>DeepSeek costs only 1/107 of OpenAI GPT-4o!</strong>
        </p>
        <div className="mt-4 grid grid-cols-2 gap-4">
          <div className="bg-black/30 p-4 rounded">
            <p className="text-gray-400">GPT-4o</p>
            <p className="text-2xl font-bold text-red-400">$0.18/1M tokens</p>
          </div>
          <div className="bg-black/30 p-4 rounded">
            <p className="text-gray-400">DeepSeek</p>
            <p className="text-2xl font-bold text-green-400">$0.002/1M tokens</p>
          </div>
        </div>
        <p className="text-gray-300 mt-4">
          AgentWatch helps you discover these savings automatically.
        </p>
      </div>

      {/* Features */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">🚀 Features</h2>
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 bg-gray-800 rounded-lg">
            <h3 className="font-semibold mb-2">📊 Real-time Tracing</h3>
            <p className="text-gray-400 text-sm">
              Track every agent execution with full visibility
            </p>
          </div>
          <div className="p-4 bg-gray-800 rounded-lg">
            <h3 className="font-semibold mb-2">💰 Cost Monitoring</h3>
            <p className="text-gray-400 text-sm">
              Calculate costs for OpenAI, Claude, DeepSeek, Gemini
            </p>
          </div>
          <div className="p-4 bg-gray-800 rounded-lg">
            <h3 className="font-semibold mb-2">📈 Performance Analytics</h3>
            <p className="text-gray-400 text-sm">
              Latency stats, success rates, execution times
            </p>
          </div>
          <div className="p-4 bg-gray-800 rounded-lg">
            <h3 className="font-semibold mb-2">🔓 Open Source</h3>
            <p className="text-gray-400 text-sm">
              Apache 2.0 license, self-hosted, no data sharing
            </p>
          </div>
        </div>
      </div>

      {/* Tech Stack */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">🛠️ Tech Stack</h2>
        <div className="flex gap-4">
          <div className="px-4 py-2 bg-blue-900 rounded-lg text-sm">FastAPI</div>
          <div className="px-4 py-2 bg-blue-900 rounded-lg text-sm">React</div>
          <div className="px-4 py-2 bg-blue-900 rounded-lg text-sm">TypeScript</div>
          <div className="px-4 py-2 bg-blue-900 rounded-lg text-sm">Tailwind CSS</div>
          <div className="px-4 py-2 bg-blue-900 rounded-lg text-sm">Python SDK</div>
        </div>
      </div>

      {/* Links */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">🔗 Links</h2>
        <div className="flex gap-4">
          <a
            href="https://github.com/RaphaelL2e/agentwatch"
            target="_blank"
            rel="noopener noreferrer"
            className="px-6 py-3 bg-gray-800 text-white rounded-lg hover:bg-gray-700 flex items-center gap-2"
          >
            <span>📦</span> GitHub Repository
          </a>
          <a
            href="https://pypi.org/project/agentwatch/"
            target="_blank"
            rel="noopener noreferrer"
            className="px-6 py-3 bg-gray-800 text-white rounded-lg hover:bg-gray-700 flex items-center gap-2"
          >
            <span>🐍</span> PyPI Package
          </a>
        </div>
      </div>

      {/* Roadmap */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">📈 Roadmap</h2>
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <span className="text-green-400">✅</span>
            <span className="text-gray-300">Week 1: MVP - Backend, SDK, Basic Dashboard</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-yellow-400">⏳</span>
            <span className="text-gray-300">Week 2: Full Dashboard + WebSocket + ClickHouse</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-gray-400">📋</span>
            <span className="text-gray-300">Week 3: User Auth + Team Management</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-gray-400">📋</span>
            <span className="text-gray-300">Week 4: GitHub Marketplace + npm CLI</span>
          </div>
        </div>
      </div>

      {/* Author */}
      <div className="p-6 bg-gray-800 rounded-lg">
        <h2 className="text-xl font-semibold mb-4">👤 Author</h2>
        <p className="text-gray-300">
          Built with ❤️ by <strong className="text-white">RaphaelL2e</strong>
        </p>
        <p className="text-gray-400 mt-2">
          A developer passionate about AI Agents and open-source software.
        </p>
      </div>
    </div>
  );
}