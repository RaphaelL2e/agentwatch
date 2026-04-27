# AgentWatch 架构文档

## 系统架构

AgentWatch 采用三层架构：

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend Layer                        │
│  ┌─────────────────────────────────────────────────┐   │
│  │  React + TypeScript + Tailwind CSS Dashboard    │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────┐  │   │
│  │  │Dashboard│ │Traces   │ │Costs    │ │Stats │  │   │
│  │  │  Page   │ │ Detail  │ │Compare  │ │Page  │  │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └──────┘  │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          │
                          │ HTTP/WebSocket
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    Backend Layer                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              FastAPI + Python 3.11              │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐          │   │
│  │  │Trace API│ │Cost API │ │Stats API│          │   │
│  │  │Service  │ │Service  │ │Service  │          │   │
│  │  └─────────┘ └─────────┘ └─────────┘          │   │
│  │  ┌───────────────────────────────────────┐    │   │
│  │  │         TraceService (Core)           │    │   │
│  │  │  - In-memory storage (SQLite later)   │    │   │
│  │  │  - Cost calculation                   │    │   │
│  │  │  - Event management                   │    │   │
│  │  └───────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          │
                          │ HTTP
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    SDK Layer                             │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Python SDK (pip)                   │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐          │   │
│  │  │Client   │ │Trace    │ │Decorator│          │   │
│  │  │API      │ │Context  │ │Utils    │          │   │
│  │  └─────────┘ └─────────┘ └─────────┘          │   │
│  │  ┌───────────────────────────────────────┐    │   │
│  │  │         AgentWatch Client             │    │   │
│  │  │  - create_trace()                     │    │   │
│  │  │  - trace() (context manager)          │    │   │
│  │  │  - get_stats()                        │    │   │
│  │  └───────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 数据流

### 1. Trace 创建流程

```
User Code              SDK              Backend             Frontend
   │                    │                  │                   │
   │ aw.trace()         │                  │                   │
   │──────────────────>│                  │                   │
   │                    │ POST /trace      │                   │
   │                    │─────────────────>│                   │
   │                    │                  │ Create Trace      │
   │                    │                  │ Calculate Cost    │
   │                    │                  │──────────────────>│
   │                    │                  │                   │ Update Dashboard
   │                    │{trace_id}        │                   │
   │                    │<─────────────────│                   │
   │{TraceContext}      │                  │                   │
   │<──────────────────│                  │                   │
   │                    │                  │                   │
   │ trace.log_tokens() │                  │                   │
   │──────────────────>│                  │                   │
   │                    │ POST /event      │                   │
   │                    │─────────────────>│                   │
   │                    │                  │ Update Trace      │
   │                    │                  │ Recalc Cost       │
   │                    │                  │──────────────────>│
   │                    │                  │                   │ Live Update
```

### 2. 成本计算流程

```
Trace Event         TraceService          Cost Calculator
     │                    │                    │
     │{input: 100,        │                    │
     │ output: 200,       │                    │
     │ model: "gpt-4o"}   │                    │
     │──────────────────>│                    │
     │                    │ Get Cost Config    │
     │                    │──────────────────>│
     │                    │                    │ Lookup Model Cost
     │                    │                    │ Input: $0.005/1K
     │                    │                    │ Output: $0.015/1K
     │                    │{input_cost: 0.005, │
     │                    │ output_cost: 0.015}│
     │                    │<──────────────────│
     │                    │                    │
     │                    │ Calculate:         │
     │                    │ 100 * 0.005/1000   │
     │                    │ + 200 * 0.015/1000 │
     │                    │ = $0.0035          │
     │                    │                    │
     │{cost: 0.0035}      │                    │
     │<──────────────────│                    │
```

---

## 模块设计

### Backend (FastAPI)

#### `main.py` - API 端点
```python
@app.post("/api/v1/trace")
async def create_trace(trace: TraceCreate):
    return trace_service.create_trace(trace)

@app.get("/api/v1/trace/{trace_id}")
async def get_trace(trace_id: str):
    return trace_service.get_trace(trace_id)

@app.get("/api/v1/stats")
async def get_stats():
    return trace_service.get_stats()
```

#### `trace_service.py` - 业务逻辑
```python
class TraceService:
    def __init__(self):
        self.traces: Dict[str, Trace] = {}
        self.cost_config = CostConfig()

    def create_trace(self, trace_data: TraceCreate) -> Trace:
        trace_id = generate_id()
        trace = Trace(
            trace_id=trace_id,
            **trace_data.dict(),
            status="running"
        )
        self.traces[trace_id] = trace
        return trace

    def calculate_cost(self, provider: str, model: str,
                       input_tokens: int, output_tokens: int) -> float:
        config = self.cost_config.get(provider, model)
        cost = (input_tokens * config.input_cost_per_1k / 1000 +
                output_tokens * config.output_cost_per_1k / 1000)
        return cost
```

#### `models.py` - 数据模型
```python
class Trace(BaseModel):
    trace_id: str
    agent_id: str
    agent_name: str
    provider: str
    model: str
    status: str = "running"
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0
    events: List[TraceEvent] = []
```

### Frontend (React)

#### `Dashboard.tsx` - 主仪表盘
```typescript
export default function Dashboard() {
  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: () => api.getStats(),
  });

  return (
    <div>
      <StatsCards stats={stats} />
      <RecentTraces traces={stats?.recent_traces} />
      <CostChart data={stats?.by_provider} />
    </div>
  );
}
```

#### `api.ts` - API 客户端
```typescript
const API_BASE = 'http://localhost:8000';

export const api = {
  getStats: () => fetch(`${API_BASE}/api/v1/stats`).then(r => r.json()),
  getTraces: () => fetch(`${API_BASE}/api/v1/traces`).then(r => r.json()),
  getTrace: (id) => fetch(`${API_BASE}/api/v1/trace/${id}`).then(r => r.json()),
};
```

### SDK (Python)

#### `client.py` - 主客户端
```python
class AgentWatch:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self._client = httpx.Client()

    def create_trace(self, agent_id, agent_name, provider, model) -> TraceContext:
        data = {
            "agent_id": agent_id,
            "agent_name": agent_name,
            "provider": provider,
            "model": model
        }
        resp = self._client.post(f"{self.api_url}/api/v1/trace", json=data)
        result = resp.json()
        return TraceContext(result["trace_id"], self)

    def trace(self, agent_name, model, provider="openai") -> TraceContext:
        return self.create_trace(...)
```

---

## 成本配置

### 当前配置 (v0.2.0)

```python
COST_CONFIG = {
    "openai": {
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    },
    "anthropic": {
        "claude-3.5-sonnet": {"input": 0.003, "output": 0.015},
        "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
    },
    "deepseek": {
        "deepseek-chat": {"input": 0.00014, "output": 0.00028},
        "deepseek-coder": {"input": 0.00014, "output": 0.00028},
    },
    "google": {
        "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
        "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
    }
}
```

### 成本差异分析

```
Cost per 1M tokens (Input + Output average):

OpenAI GPT-4o:       $10.00
Anthropic Claude:    $9.00
Google Gemini Pro:   $3.125
DeepSeek:            $0.21

DeepSeek vs OpenAI:  47x cheaper
DeepSeek vs Claude:  43x cheaper
DeepSeek vs Gemini:  15x cheaper
```

---

## 扩展计划

### Phase 1 (Week 2)
- ClickHouse 数据存储
- WebSocket 实时推送
- 用户认证

### Phase 2 (Week 3)
- 团队管理
- 数据导出
- Alert 系统

### Phase 3 (Week 4)
- GitHub Marketplace
- npm CLI
- Docker 部署

---

## 技术选型理由

| 技术 | 原因 |
|------|------|
| FastAPI | 高性能异步、自动 API 文档、Pydantic 数据验证 |
| React + TypeScript | 类型安全、组件化、生态成熟 |
| Tailwind CSS | 快速开发、响应式设计、暗色主题 |
| Python SDK | LLM 生态主流语言、易于集成 |
| SQLite → ClickHouse | 开发简单 → 生产高性能 |
| httpx | 异步支持、现代 HTTP 客户端 |

---

**Made with ❤️ by AgentWatch Team**