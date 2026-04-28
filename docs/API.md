# AgentWatch API 文档

## 基础信息

- **Base URL**: `http://localhost:8000`
- **版本**: v0.4.0
- **协议**: HTTP/REST + WebSocket (实时推送)

---

## 健康检查

### GET /health

检查服务健康状态。

**Response:**
```json
{
  "status": "healthy",
  "version": "0.2.0",
  "uptime_seconds": 12345
}
```

---

## Trace API

### POST /api/v1/trace

创建一个新的 Trace。

**Request Body:**
```json
{
  "agent_id": "agent_001",
  "agent_name": "MyAgent",
  "provider": "openai",
  "model": "gpt-4o",
  "session_id": "session_123",
  "user_id": "user_456",
  "prompt": "Hello, AI!",
  "metadata": {
    "environment": "production",
    "version": "1.0.0"
  }
}
```

**Response:**
```json
{
  "trace_id": "trace_abc123",
  "agent_id": "agent_001",
  "agent_name": "MyAgent",
  "provider": "openai",
  "model": "gpt-4o",
  "status": "running",
  "created_at": "2026-04-27T04:00:00Z",
  "cost": 0.0
}
```

---

### GET /api/v1/trace/{trace_id}

获取 Trace 详情。

**Response:**
```json
{
  "trace_id": "trace_abc123",
  "agent_id": "agent_001",
  "agent_name": "MyAgent",
  "provider": "openai",
  "model": "gpt-4o",
  "status": "completed",
  "input_tokens": 100,
  "output_tokens": 200,
  "total_tokens": 300,
  "cost": 0.0035,
  "duration_ms": 1500,
  "created_at": "2026-04-27T04:00:00Z",
  "completed_at": "2026-04-27T04:00:01.5Z",
  "events": [
    {
      "event_id": "ev_001",
      "event_type": "llm_call",
      "input_tokens": 100,
      "output_tokens": 200,
      "latency_ms": 1500,
      "timestamp": "2026-04-27T04:00:01Z"
    }
  ]
}
```

---

### PUT /api/v1/trace/{trace_id}

更新 Trace 状态。

**Request Body:**
```json
{
  "status": "completed",
  "duration_ms": 1500
}
```

**Response:**
```json
{
  "trace_id": "trace_abc123",
  "status": "updated"
}
```

---

### POST /api/v1/trace/{trace_id}/event

添加事件到 Trace。

**Request Body:**
```json
{
  "event_id": "ev_002",
  "event_type": "tool_use",
  "model": "gpt-4o",
  "input_tokens": 50,
  "output_tokens": 100,
  "latency_ms": 200,
  "message": "Called search API",
  "timestamp": "2026-04-27T04:00:00Z"
}
```

**Response:**
```json
{
  "event_id": "ev_002",
  "trace_id": "trace_abc123",
  "status": "added"
}
```

---

### GET /api/v1/traces

列出所有 Traces。

**Query Parameters:**
- `page` (int): 页码，默认 1
- `page_size` (int): 每页数量，默认 20
- `agent_id` (str): 按 Agent ID 过滤
- `provider` (str): 按 Provider 过滤
- `status` (str): 按状态过滤

**Response:**
```json
{
  "traces": [
    {
      "trace_id": "trace_abc123",
      "agent_name": "MyAgent",
      "provider": "openai",
      "model": "gpt-4o",
      "status": "completed",
      "cost": 0.0035,
      "created_at": "2026-04-27T04:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

## Cost API

### GET /api/v1/cost/summary

获取成本汇总。

**Query Parameters:**
- `provider` (str): 按 Provider 过滤

**Response:**
```json
{
  "total_cost": 1.25,
  "by_provider": {
    "openai": {
      "total_cost": 0.75,
      "total_tokens": 15000,
      "traces": 5
    },
    "deepseek": {
      "total_cost": 0.002,
      "total_tokens": 10000,
      "traces": 3
    }
  },
  "cost_savings": {
    "deepseek_vs_openai": 89.0,
    "message": "DeepSeek costs 89x less than OpenAI!"
  }
}
```

---

### GET /api/v1/cost/models

获取各模型成本配置。

**Response:**
```json
{
  "models": [
    {
      "provider": "openai",
      "model": "gpt-4o",
      "input_cost_per_1k": 0.005,
      "output_cost_per_1k": 0.015,
      "description": "OpenAI flagship model"
    },
    {
      "provider": "deepseek",
      "model": "deepseek-chat",
      "input_cost_per_1k": 0.00014,
      "output_cost_per_1k": 0.00028,
      "description": "DeepSeek cost-effective model"
    }
  ],
  "recommendations": [
    {
      "scenario": "high_volume",
      "recommended": "deepseek",
      "savings": "89x cheaper than OpenAI"
    }
  ]
}
```

---

## Statistics API

### GET /api/v1/stats

获取统计数据。

**Response:**
```json
{
  "total_traces": 100,
  "running_traces": 5,
  "completed_traces": 90,
  "failed_traces": 5,
  "total_cost": 12.5,
  "total_tokens": 250000,
  "avg_latency_ms": 1500,
  "success_rate": 0.95,
  "by_provider": {
    "openai": {
      "traces": 50,
      "cost": 10.0,
      "avg_latency_ms": 2000
    },
    "deepseek": {
      "traces": 50,
      "cost": 2.5,
      "avg_latency_ms": 1000
    }
  }
}
```

---

## Dashboard API

### GET /api/v1/dashboard

获取 Dashboard 数据。

**Response:**
```json
{
  "summary": {
    "total_traces": 100,
    "running": 5,
    "completed": 90,
    "failed": 5,
    "total_cost": 12.5
  },
  "recent_traces": [
    {
      "trace_id": "trace_xyz",
      "agent_name": "ChatAgent",
      "status": "running",
      "cost": 0.01,
      "created_at": "2026-04-27T04:00:00Z"
    }
  ],
  "hourly_stats": [
    {
      "hour": "2026-04-27T03:00:00Z",
      "traces": 10,
      "cost": 0.5
    }
  ]
}
```

---

## Budget API

### GET /api/v1/budget

获取预算配置和当前状态。

**Response:**
```json
{
  "config": {
    "daily_limit": 10.0,
    "monthly_limit": 100.0,
    "alert_threshold": 0.8,
    "providers_limits": {}
  },
  "status": {
    "today_cost": 2.5,
    "month_cost": 25.0,
    "daily_usage_percent": 25.0,
    "monthly_usage_percent": 25.0,
    "daily_remaining": 7.5,
    "monthly_remaining": 75.0,
    "daily_over_budget": false,
    "monthly_over_budget": false
  },
  "alerts": [
    {
      "type": "daily_budget",
      "severity": "warning",
      "message": "Daily budget 80% used",
      "current": 8.0,
      "limit": 10.0
    }
  ]
}
```

---

### PUT /api/v1/budget

更新预算配置。

**Query Parameters:**
- `daily_limit` (float): 每日预算限制 ($)
- `monthly_limit` (float): 每月预算限制 ($)
- `alert_threshold` (float): 告警阈值 (0-1)

**Request Example:**
```
PUT /api/v1/budget?daily_limit=20.0&monthly_limit=200.0&alert_threshold=0.9
```

**Response:**
```json
{
  "message": "Budget config updated",
  "config": {
    "daily_limit": 20.0,
    "monthly_limit": 200.0,
    "alert_threshold": 0.9
  }
}
```

---

### GET /api/v1/budget/history

获取预算历史（过去 N 天的每日成本）。

**Query Parameters:**
- `days` (int): 分析天数，范围 1-30，默认 7

**Response:**
```json
{
  "days": 7,
  "daily_limit": 10.0,
  "history": [
    {
      "date": "2026-04-28",
      "cost": 5.25,
      "traces": 120,
      "over_budget": false
    },
    {
      "date": "2026-04-27",
      "cost": 12.50,
      "traces": 300,
      "over_budget": true
    }
  ],
  "total_cost": 45.75,
  "avg_daily_cost": 6.54
}
```

---

### GET /api/v1/budget/providers

获取各 Provider 的预算状态和成本优化建议。

**Response:**
```json
{
  "providers": [
    {
      "provider": "openai",
      "cost": 10.50,
      "traces": 50,
      "limit": 100.0,
      "usage_percent": 10.5
    },
    {
      "provider": "deepseek",
      "cost": 0.10,
      "traces": 30,
      "limit": 100.0,
      "usage_percent": 0.1
    }
  ],
  "suggestions": [
    {
      "type": "switch_provider",
      "from": "openai",
      "to": "deepseek",
      "current_cost": 10.50,
      "potential_cost": 0.10,
      "savings": 10.40,
      "savings_percent": 99.1
    }
  ]
}
```

---

## WebSocket 实时推送 API

### WebSocket 连接

**Endpoint**: `ws://localhost:8000/ws`

WebSocket 连接用于实时接收 Trace 创建、更新、删除等事件推送。

**连接示例（JavaScript）:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  console.log('Connected to AgentWatch WebSocket');
  // 订阅特定频道
  ws.send(JSON.stringify({ type: 'subscribe', channels: ['all'] }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
  
  switch (data.type) {
    case 'trace_created':
      // 新 Trace 创建
      console.log('New trace:', data.data);
      break;
    case 'trace_updated':
      // Trace 更新
      console.log('Trace updated:', data.data);
      break;
    case 'trace_deleted':
      // Trace 删除
      console.log('Trace deleted:', data.data.trace_id);
      break;
    case 'stats_update':
      // 统计数据更新
      console.log('Stats:', data.data);
      break;
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('WebSocket disconnected');
};
```

---

### WebSocket 消息类型

#### 服务器推送消息

| 类型 | 说明 | 数据结构 |
|------|------|----------|
| `connected` | 连接成功 | `{ type: "connected", message: string, timestamp: string }` |
| `stats_update` | 统计更新 | `{ type: "stats_update", data: StatsObject, timestamp: string }` |
| `trace_created` | Trace 创建 | `{ type: "trace_created", data: TraceObject, timestamp: string }` |
| `trace_updated` | Trace 更新 | `{ type: "trace_updated", data: TraceObject, timestamp: string }` |
| `trace_deleted` | Trace 删除 | `{ type: "trace_deleted", data: { trace_id: string }, timestamp: string }` |
| `trace_event` | Trace 事件添加 | `{ type: "trace_event", data: { trace_id, event, trace }, timestamp }` |
| `pong` | 心跳响应 | `{ type: "pong", timestamp: string }` |
| `subscribed` | 订阅确认 | `{ type: "subscribed", channels: string[], timestamp: string }` |

---

#### 客户端发送消息

| 类型 | 说明 | 数据结构 |
|------|------|----------|
| `ping` | 心跳请求 | `{ type: "ping" }` |
| `get_stats` | 请求统计数据 | `{ type: "get_stats" }` |
| `subscribe` | 订阅频道 | `{ type: "subscribe", channels: ["all"] }` |

---

### React Hook 使用示例

```typescript
import { useWebSocket } from './hooks/useWebSocket';

function Dashboard() {
  const { isConnected, lastMessage, requestStats } = useWebSocket({
    autoConnect: true,
    onTraceCreated: (trace) => {
      console.log('New trace created:', trace);
      // 更新 UI
    },
    onStatsUpdate: (stats) => {
      console.log('Stats updated:', stats);
      // 更新统计显示
    },
    onError: (error) => {
      console.error('WebSocket error:', error);
    },
  });

  return (
    <div>
      <span className={isConnected ? 'text-green' : 'text-red'}>
        {isConnected ? 'Live' : 'Offline'}
      </span>
      <button onClick={requestStats}>Refresh Stats</button>
    </div>
  );
}
```

---

### Python SDK WebSocket 支持

```python
from agentwatch import AgentWatch, WebSocketClient

# WebSocket 客户端
ws_client = WebSocketClient('ws://localhost:8000/ws')

# 连接并订阅
ws_client.connect()

# 接收实时消息
for message in ws_client.listen():
    if message['type'] == 'trace_created':
        print(f"New trace: {message['data']['trace_id']}")
    elif message['type'] == 'stats_update':
        print(f"Stats: {message['data']}")

# 发送消息
ws_client.send({'type': 'ping'})
ws_client.close()
```

---

## 测试 API

### POST /api/v1/test/trace

创建测试 Trace（用于 Demo）。

**Response:**
```json
{
  "trace_id": "test_trace_abc",
  "agent_name": "TestAgent",
  "status": "completed",
  "cost": 0.001,
  "message": "Test trace created successfully"
}
```

---

## Provider 成本配置

| Provider | Model | Input (per 1K) | Output (per 1K) |
|----------|-------|----------------|-----------------|
| OpenAI | gpt-4o | $0.005 | $0.015 |
| OpenAI | gpt-4o-mini | $0.00015 | $0.0006 |
| Anthropic | claude-3.5-sonnet | $0.003 | $0.015 |
| Anthropic | claude-3-haiku | $0.00025 | $0.00125 |
| DeepSeek | deepseek-chat | $0.00014 | $0.00028 |
| DeepSeek | deepseek-coder | $0.00014 | $0.00028 |
| Google | gemini-1.5-pro | $0.00125 | $0.005 |
| Google | gemini-1.5-flash | $0.000075 | $0.0003 |

**成本差异:**
- DeepSeek 比 OpenAI GPT-4o 便宜 **89x**
- Gemini-1.5-flash 比 GPT-4o-mini 便宜 **2x**

---

## 错误码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 404 | Trace 不存在 |
| 500 | 服务器内部错误 |

---

## SDK 使用示例

```python
from agentwatch import AgentWatch

# 初始化
aw = AgentWatch(api_url="http://localhost:8000")

# 方式1: 上下文管理器
with aw.trace("my_agent", model="gpt-4o") as trace:
    response = openai.chat.completions.create(...)
    trace.log_tokens(
        input=response.usage.prompt_tokens,
        output=response.usage.completion_tokens
    )

# 方式2: 装饰器
@aw.trace_agent("my_agent", model="deepseek-chat")
def my_function(prompt):
    return llm_call(prompt)

# 方式3: 手动追踪
trace = aw.create_trace(
    agent_id="agent_001",
    agent_name="MyAgent",
    provider="openai",
    model="gpt-4o"
)
trace.log_tokens(input=100, output=200)
trace.complete()

# 获取统计
stats = aw.get_stats()
print(f"Total cost: ${stats['total_cost']}")
```

---

**Made with ❤️ by AgentWatch Team**