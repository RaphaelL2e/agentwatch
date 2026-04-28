# AgentWatch Architecture

本文档描述 AgentWatch 的系统架构、技术栈和设计决策。

## 📐 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AgentWatch Platform                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        Frontend (React + Vite)                        │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐│   │
│  │  │Dashboard │  │ Charts   │  │CostAlerts│  │Settings  │  │TraceDetail││   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘│   │
│  │                              │                                        │   │
│  │                              │ WebSocket Hook                         │   │
│  │                              │ (useWebSocket.ts)                      │   │
│  └──────────────────────────────┼────────────────────────────────────────┘   │
│                                 │                                             │
│                                 │ HTTP REST + WebSocket                       │
│                                 ▼                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        Backend (FastAPI)                              │   │
│  │  ┌────────────────────────────────────────────────────────────────┐  │   │
│  │  │                    API Layer (main.py)                          │  │   │
│  │  │  /api/v1/trace  /api/v1/stats  /api/v1/dashboard  /ws           │  │   │
│  │  └────────────────────────────────────────────────────────────────┘  │   │
│  │                              │                                        │   │
│  │  ┌────────────────────────────────────────────────────────────────┐  │   │
│  │  │                 Service Layer (trace_service.py)                │  │   │
│  │  │  Trace CRUD  │  Cost Calculation  │  Stats Aggregation          │  │   │
│  │  └────────────────────────────────────────────────────────────────┘  │   │
│  │                              │                                        │   │
│  │  ┌────────────────────────────────────────────────────────────────┐  │   │
│  │  │               Storage Abstraction (Repository Pattern)          │  │   │
│  │  │  TraceRepository (interface)                                    │  │   │
│  │  │      ├── MemoryRepository (default)                             │  │   │
│  │  │      └── ClickHouseRepository (production)                      │  │   │
│  │  └────────────────────────────────────────────────────────────────┘  │   │
│  │                              │                                        │   │
│  │  ┌────────────────────────────────────────────────────────────────┐  │   │
│  │  │                   WebSocket Manager                             │  │   │
│  │  │  ConnectionManager  │  Broadcast  │  Real-time Events           │  │   │
│  │  └────────────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                 │                                             │
│                                 ▼                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                          Python SDK                                   │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐│   │
│  │  │ client.py    │  │ decorators.py │  │ trace.py     │  │ providers ││   │
│  │  │ AgentWatch   │  │ @trace_agent  │  │ TraceContext │  │ Integration││   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘│   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🛠 技术栈

### Backend
- **Framework**: FastAPI 0.100+ (高性能异步 Python Web 框架)
- **Data Validation**: Pydantic v2 (类型安全的数据模型)
- **Testing**: pytest + pytest-asyncio (异步测试支持)
- **Storage**: Repository Pattern (内存存储 + ClickHouse 可选)

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite (快速开发服务器和构建)
- **State Management**: TanStack Query (React Query)
- **Styling**: Tailwind CSS (原子化 CSS)
- **Real-time**: WebSocket (原生浏览器 WebSocket API)

### SDK
- **Language**: Python 3.11+
- **HTTP Client**: requests (同步) + aiohttp (异步可选)
- **Design Pattern**: Decorators + Context Managers

## 🧩 核心模块

### 1. Backend API Layer (`backend/main.py`)

FastAPI 端点设计遵循 RESTful 规范：

```
/api/v1/trace          POST   创建新 Trace
/api/v1/trace/{id}     GET    获取 Trace 详情
/api/v1/trace/{id}     PUT    更新 Trace
/api/v1/trace/{id}     DELETE 删除 Trace
/api/v1/traces         GET    列出 Traces (支持分页和过滤)
/api/v1/stats          GET    获取统计数据
/api/v1/cost/summary   GET    成本汇总
/api/v1/dashboard      GET    Dashboard 数据
/ws                    WS     WebSocket 实时推送
```

### 2. Storage Abstraction Layer (`backend/storage/`)

采用 Repository Pattern 实现存储抽象：

```python
# 抽象接口
class TraceRepository(ABC):
    @abstractmethod
    def create(self, trace: Trace) -> Trace: ...
    
    @abstractmethod
    def get(self, trace_id: str) -> Optional[Trace]: ...
    
    @abstractmethod
    def list(self, filters: dict) -> List[Trace]: ...

# 内存存储实现 (开发/测试)
class MemoryRepository(TraceRepository):
    def __init__(self):
        self._traces: Dict[str, Trace] = {}

# ClickHouse 存储 (生产环境)
class ClickHouseRepository(TraceRepository):
    def __init__(self, client: ClickHouseClient):
        self._client = client
```

**优势**:
- 存储后端可无缝切换
- 开发时使用内存存储，生产时切换到 ClickHouse
- 易于添加新的存储后端 (PostgreSQL, MongoDB 等)

### 3. WebSocket Real-time (`backend/main.py`)

实时事件推送架构：

```python
class ConnectionManager:
    async def connect(websocket: WebSocket)
    async def disconnect(websocket: WebSocket)
    async def broadcast(message: dict)  # 广播给所有连接
    async def send_to(websocket, message)  # 发送给特定连接

# 事件类型
Events:
  - trace_created  # 新 Trace 创建
  - trace_updated  # Trace 更新
  - trace_deleted  # Trace 删除
  - trace_event    # Trace 事件添加
  - stats_update   # 统计数据更新
```

### 4. SDK Decorators (`sdk/agentwatch/decorators.py`)

装饰器设计支持多种使用场景：

```python
# 基础装饰器 - 同步/异步自动检测
@trace_agent("my_agent", model="gpt-4o")
def my_function(prompt: str):
    ...

# Provider 专用装饰器
@trace_openai_call(model="gpt-4o-mini")
@trace_anthropic_call(model="claude-3-sonnet")
@trace_deepseek_call(model="deepseek-chat")
@trace_gemini_call(model="gemini-1.5-pro")

# 流式响应追踪
@trace_streaming("stream_agent", model="gpt-4o")
def stream_function(prompt):
    return openai.chat.completions.create(stream=True, ...)

# Agent 基类
class MyAgent(TracedAgent):
    def run(self, prompt):
        ...
```

## 💰 Token 成本计算

成本计算在 `trace_service.py` 中实现：

```python
TOKEN_COSTS = {
    "openai": {
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    },
    "anthropic": {
        "claude-3.5-sonnet": {"input": 0.003, "output": 0.015},
    },
    "deepseek": {
        "deepseek-v4": {"input": 0.00014, "output": 0.00028},
    },
    "google": {
        "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
    },
}

def calculate_cost(provider, model, input_tokens, output_tokens):
    cost_per_1k = TOKEN_COSTS[provider][model]
    input_cost = (input_tokens / 1000) * cost_per_1k["input"]
    output_cost = (output_tokens / 1000) * cost_per_1k["output"]
    return input_cost + output_cost
```

**成本对比**: DeepSeek 成本仅 OpenAI 的 1/107！

## 📊 数据模型

### Trace (`backend/models.py`)

```python
class Trace(BaseModel):
    trace_id: str          # UUID 唯一标识
    agent_id: str          # Agent ID
    agent_name: str        # Agent 名称
    provider: AgentProvider  # openai/anthropic/deepseek/google
    model: str             # 模型名称
    status: TraceStatus    # running/completed/failed
    prompt: Optional[str]  # 输入提示词
    output: Optional[str]  # 输出结果
    
    # Token 使用量
    total_input_tokens: int
    total_output_tokens: int
    
    # 成本
    total_cost: float
    
    # 性能指标
    duration_ms: Optional[int]
    
    # 事件列表
    events: List[TraceEvent]
    
    # 时间戳
    created_at: datetime
    updated_at: datetime
```

### TraceEvent

```python
class TraceEvent(BaseModel):
    event_type: str        # call/response/error/tool_use
    content: Optional[str] # 事件内容
    timestamp: datetime    # 时间戳
```

## 🔒 安全考虑

### 当前状态 (Week 1 MVP)
- CORS 配置允许所有来源 (开发便利)
- 无用户认证 (后续添加)
- 内存存储无持久化

### 后续计划 (Week 3)
- JWT 用户认证
- 团队权限管理
- API Key 限流
- 数据加密存储

## 📈 性能优化

### Backend
- 异步 API 端点 (FastAPI async)
- WebSocket 连接池管理
- 存储 Repository Pattern 支持批量操作

### Frontend
- React Query 缓存
- WebSocket 实时更新避免轮询
- Tailwind CSS 按需构建

## 🚀 部署架构

### 开发环境
```
Frontend (Vite Dev Server)  →  Backend (FastAPI)  →  Memory Storage
     localhost:5173               localhost:8000
```

### 生产环境
```
Frontend (Static Files)  →  Backend (FastAPI + Uvicorn)  →  ClickHouse
   CDN/Nginx                   Kubernetes/VPS               Cluster
```

## 🔄 CI/CD Pipeline

GitHub Actions 配置 (`github/workflows/ci.yml`):

```yaml
jobs:
  backend-tests:
    - pytest backend/tests/ -v
    - Coverage: 42+ tests
    
  frontend-tests:
    - npm run lint
    - npm run test
    
  sdk-tests:
    - pytest sdk/tests/ -v
```

## 📝 扩展点

### 1. 新增 Provider
```python
# 在 models.py 添加
class AgentProvider(str, Enum):
    ...
    mistral = "mistral"  # 新增

# 在 trace_service.py 添加成本配置
TOKEN_COSTS["mistral"] = {
    "mistral-large": {"input": ..., "output": ...},
}
```

### 2. 新增 Storage Backend
```python
# 在 storage/ 创建新实现
class PostgreSQLRepository(TraceRepository):
    ...
```

### 3. 新增 SDK Decorator
```python
# 在 decorators.py 添加
def trace_mistral_call(agent_name="mistral_agent", model="mistral-large"):
    return trace_agent(agent_name, model, provider="mistral")
```

---

**AgentWatch Architecture v0.3.0** | Made with ❤️ by RaphaelL2e