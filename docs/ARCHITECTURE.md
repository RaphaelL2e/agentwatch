# AgentWatch 系统架构

## 系统概览

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           AgentWatch Platform                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────┐     ┌────────────────┐     ┌────────────────┐       │
│  │   AI Agents    │────▶│  SDK Client    │────▶│  Backend API   │       │
│  │                │     │                │     │                │       │
│  │ • Claude       │     │ • trace()      │     │ • FastAPI      │       │
│  │ • DeepSeek     │     │ • log_tokens() │     │ • WebSocket    │       │
│  │ • OpenAI       │     │ • decorator    │     │ • REST API     │       │
│  │ • Gemini       │     │                │     │                │       │
│  └────────────────┘     └────────────────┘     └───────┬────────┘       │
│                                                        │                 │
│                                                        ▼                 │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │                      Dashboard (React)                       │       │
│  │                                                              │       │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │       │
│  │  │  Stats   │  │  Alerts  │  │  Traces  │  │  Charts  │     │       │
│  │  │  Cards   │  │  Panel   │  │  List    │  │  View    │     │       │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │       │
│  │                                                              │       │
│  │  • Real-time WebSocket updates                               │       │
│  │  • Cost alerts & threshold monitoring                        │       │
│  │  • Provider cost breakdown                                   │       │
│  │  • Cost-saving suggestions                                   │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## 核心组件

### 1. SDK Client (`sdk/agentwatch/`)

```python
AgentWatch(api_url)
  │
  ├── trace(agent_name, model, provider)  # Context manager
  │     ├── log_tokens(input, output)
  │     ├── add_event(event_type, **kwargs)
  │     ├── calculate_cost()
  │     └── complete() / error()
  │
  ├── create_trace(...)                     # Manual mode
  ├── get_stats()                           # Statistics
  ├── get_cost_summary()                    # Cost breakdown
  ├── list_traces(status, limit)            # Query traces
  │
  └── TracedAgent base class                # Agent wrapper
      ├── start_trace(prompt)
      ├── log_tokens(input, output)
      ├── log_error(error)
      └── end_trace()
```

### 2. Backend API (`backend/`)

```
FastAPI Application
│
├── REST API (/api/v1/)
│   ├── POST /traces               # Create trace
│   ├── GET  /traces               # List traces
│   ├── GET  /traces/{id}          # Get trace detail
│   ├── PUT  /traces/{id}          # Update trace
│   ├── GET  /stats                # Get statistics
│   ├── GET  /cost-summary         # Cost breakdown
│   ├── GET  /health               # Health check
│   └── GET  /dashboard            # Dashboard data
│
├── WebSocket (/ws)
│   ├── Real-time trace updates
│   ├── Stats broadcasting
│   └── Connection management
│
└── TraceService (Business Logic)
    ├── In-memory trace storage (Fast mode)
    ├── ClickHouse persistence (Future)
    ├── Cost calculation
    └── Event aggregation
```

### 3. Dashboard (`frontend/`)

```
React + TypeScript + Vite
│
├── Dashboard Component
│   ├── StatCards (Total, Completed, Running, Cost)
│   ├── WebSocketBadge (Live/Offline status)
│   ├── CostAlerts
│   │   ├── Daily/Monthly threshold alerts
│   │   ├── Token spike detection
│   │   ├── Failure rate monitoring
│   │   └── Configurable thresholds
│   ├── ProviderCostBreakdown
│   │   ├── Cost distribution bars
│   │   ├── Provider comparison
│   │   └── Percentage visualization
│   ├── CostSavingSuggestions
│   │   ├── DeepSeek migration advice
│   │   ├── High-cost provider alerts
│   │   └── Optimization recommendations
│   └── TraceList
│       └── TraceItem (clickable → TraceDetail)
│
├── TraceDetail Component
│   ├── Timeline view
│   ├── Token breakdown
│   ├── Cost analysis
│   └── Event history
│
└── Charts Component
    ├── Cost comparison chart
    ├── Latency distribution
    └── Provider comparison
```

## 数据流

```
┌──────────┐                                              ┌──────────┐
│ AI Agent │                                              │ Dashboard│
└────┬─────┘                                              └────┬─────┘
     │                                                         │
     │ 1. Start trace                                          │
     ▼                                                         │
┌──────────┐                                                   │
│   SDK    │                                                   │
└────┬─────┘                                                   │
     │                                                         │
     │ 2. POST /traces                                         │
     ▼                                                         │
┌──────────┐                                                   │
│ Backend  │                                                   │
└────┬─────┘                                                   │
     │                                                         │
     │ 3. Log tokens, events                                   │ WebSocket broadcast
     │ 4. Calculate cost                                       │────────────────────▶
     │                                                         │
     │ 5. Complete trace                                       │
     ▼                                                         ▼
┌──────────┐                                             ┌──────────┐
│ Storage  │                                             │  Update  │
│(Memory)  │                                             │  UI      │
└──────────┘                                             └──────────┘
```

## 成本计算

```
Provider Pricing (per 1M tokens)
─────────────────────────────────
OpenAI GPT-4o:        $2.50 / $10.00
OpenAI GPT-4o-mini:   $0.15 / $0.60
Anthropic Claude Haiku: $0.25 / $1.25
DeepSeek V3:         $0.27 / $1.10 (cached: $0.07)
Google Gemini Flash: $0.075 / $0.30

Cost Formula
─────────────
cost = (input_tokens * input_price + output_tokens * output_price) / 1_000_000

Key Discovery
─────────────
DeepSeek vs GPT-4o: 107x cheaper for same task!
```

## 技术栈

| Layer      | Technology                    |
|------------|-------------------------------|
| SDK        | Python 3.11+, requests        |
| Backend    | FastAPI, Pydantic, WebSocket  |
| Frontend   | React 18, TypeScript, Tailwind|
| State      | TanStack Query (React Query)  |
| Build      | Vite, tsc                     |
| Test       | pytest, vitest                |
| CI/CD      | GitHub Actions                |

## 目录结构

```
agentwatch/
├── sdk/                    # Python SDK
│   ├── agentwatch/
│   │   ├── __init__.py     # Main exports
│   │   ├── client.py       # AgentWatch client
│   │   ├── trace.py        # Trace object
│   │   ├── decorators.py   # @trace_agent
│   │   └── models.py       # Data models
│   ├── examples/
│   │   ├── complete_demo.py
│   │   ├── claude_integration.py  # NEW
│   │   └── deepseek_integration.py # NEW
│   └── tests/
│
├── backend/                # FastAPI Backend
│   ├── main.py             # App entry + WebSocket
│   ├── trace_service.py    # Business logic
│   ├── models.py           # Pydantic models
│   └── tests/
│
├── frontend/               # React Dashboard
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── CostAlerts.tsx     # NEW
│   │   │   ├── TraceDetail.tsx
│   │   │   ├── Charts.tsx
│   │   │   └── Settings.tsx
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts
│   │   ├── api.ts
│   │   └── App.tsx
│   └── dist/
│
├── docs/                   # Documentation
│   ├── API.md              # API reference
│   ├── ARCHITECTURE.md     # This file
│   └── PROGRESS.md         # Development log
│
├── .github/workflows/      # CI/CD
│   └── test.yml
│
└── README.md               # Quick start
```

## 扩展计划

### Phase 1 (Current)
- ✅ SDK with trace, cost calculation
- ✅ FastAPI backend with WebSocket
- ✅ React Dashboard with real-time updates
- ✅ Cost alerts and analytics
- ✅ Claude/DeepSeek integration examples

### Phase 2 (Next)
- ⏳ ClickHouse persistence (real data storage)
- ⏳ PyPI package publish
- ⏳ Advanced analytics (histograms, trends)
- ⏳ Agent comparison charts
- ⏳ Export to CSV/JSON

### Phase 3 (Future)
- 📋 Multi-tenant support
- 📋 Team collaboration
- 📋 RBAC permissions
- 📋 SLA monitoring
- 📋 Enterprise pricing