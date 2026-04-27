# AgentWatch API Reference

## Overview

AgentWatch provides a RESTful API for tracking and monitoring AI Agent executions. The API supports both HTTP endpoints and WebSocket for real-time updates.

**Base URL**: `http://localhost:8000` (default)

**Version**: 0.3.0

---

## HTTP API Endpoints

### Health & Stats

#### GET /health

Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "version": "0.3.0",
  "uptime_seconds": 3600,
  "database_connected": true,
  "traces_count": 100
}
```

#### GET /stats

Get overall statistics.

**Response**:
```json
{
  "total_traces": 100,
  "running_traces": 5,
  "completed_traces": 90,
  "failed_traces": 5,
  "total_cost": 0.0123,
  "total_tokens": 50000,
  "avg_latency_ms": 500,
  "by_provider": {
    "openai": { "traces": 50, "cost": 0.01 },
    "deepseek": { "traces": 30, "cost": 0.001 }
  }
}
```

---

### Trace API

#### POST /api/v1/trace

Create a new trace.

**Request Body**:
```json
{
  "agent_id": "agent_001",
  "agent_name": "MyAgent",
  "provider": "openai",
  "model": "gpt-4o",
  "session_id": "session_001",
  "user_id": "user_001",
  "prompt": "Hello, AI!"
}
```

**Response**:
```json
{
  "trace_id": "tr_abc123",
  "agent_id": "agent_001",
  "agent_name": "MyAgent",
  "provider": "openai",
  "model": "gpt-4o",
  "status": "running",
  "created_at": "2026-04-27T12:00:00Z",
  "input_tokens": 0,
  "output_tokens": 0,
  "cost": 0,
  "events": []
}
```

#### GET /api/v1/trace/{trace_id}

Get trace details.

#### PUT /api/v1/trace/{trace_id}

Update a trace.

**Request Body**:
```json
{
  "status": "completed",
  "output": "Response from AI..."
}
```

#### DELETE /api/v1/trace/{trace_id}

Delete a trace.

#### POST /api/v1/trace/{trace_id}/event

Add an event to a trace.

**Request Body**:
```json
{
  "event_id": "ev_001",
  "event_type": "call",
  "model": "gpt-4o",
  "input_tokens": 100,
  "output_tokens": 0,
  "latency_ms": 50,
  "content": "User prompt sent"
}
```

#### GET /api/v1/traces

List all traces with pagination and filtering.

**Query Parameters**:
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)
- `agent_id`: Filter by agent ID
- `provider`: Filter by provider
- `status`: Filter by status
- `start_time`: Filter by start time
- `end_time`: Filter by end time

---

### Cost API

#### GET /api/v1/cost/summary

Get cost summary grouped by provider/model.

**Query Parameters**:
- `provider`: Filter by provider
- `start_time`: Start time filter
- `end_time`: End time filter

**Response**:
```json
[
  {
    "provider": "openai",
    "model": "gpt-4o",
    "total_traces": 50,
    "total_cost": 0.01,
    "total_tokens": 10000,
    "avg_latency_ms": 500
  }
]
```

#### GET /api/v1/cost/models

Get token cost configuration for all models.

**Response**:
```json
{
  "models": [
    {
      "provider": "openai",
      "model": "gpt-4o",
      "input_cost_per_1k": 0.005,
      "output_cost_per_1k": 0.015
    },
    {
      "provider": "deepseek",
      "model": "deepseek-v4",
      "input_cost_per_1k": 0.00014,
      "output_cost_per_1k": 0.00028
    }
  ]
}
```

---

### Dashboard API

#### GET /api/v1/dashboard

Get dashboard overview data.

**Response**:
```json
{
  "total_traces": 100,
  "running_traces": 5,
  "completed_traces": 90,
  "failed_traces": 5,
  "total_cost": 0.0123,
  "avg_latency_ms": 500,
  "provider_distribution": { "openai": 50, "deepseek": 30 },
  "model_distribution": { "gpt-4o": 40, "deepseek-v4": 30 },
  "latency_distribution": {
    "<100ms": 10,
    "100-500ms": 30,
    "500ms-1s": 40,
    "1-2s": 15,
    ">10s": 5
  },
  "recent_traces": [...]
}
```

---

### Analytics API (NEW)

#### GET /api/v1/analytics/timeline

Get timeline data for traces over time.

**Query Parameters**:
- `interval`: Time interval (`minute`, `hour`, `day`)
- `hours`: Time range in hours (default: 24, max: 168)

**Response**:
```json
{
  "interval": "hour",
  "data": [
    {
      "time": "2026-04-27 10:00",
      "traces": 5,
      "cost": 0.001,
      "tokens": 1000
    },
    {
      "time": "2026-04-27 11:00",
      "traces": 8,
      "cost": 0.002,
      "tokens": 2000
    }
  ]
}
```

#### GET /api/v1/analytics/providers

Get detailed provider performance analytics.

**Response**:
```json
[
  {
    "provider": "openai",
    "traces": 50,
    "total_cost": 0.01,
    "total_tokens": 10000,
    "input_tokens": 5000,
    "output_tokens": 5000,
    "avg_latency_ms": 500,
    "success_rate": 95.0,
    "models": ["gpt-4o", "gpt-4o-mini"]
  }
]
```

---

## WebSocket API

### Connection

**Endpoint**: `ws://localhost:8000/ws`

Connect to receive real-time updates.

### Message Types

#### Server → Client Messages

| Type | Description | Data |
|------|-------------|------|
| `connected` | Connection confirmed | `{ message: "Connected..." }` |
| `trace_created` | New trace created | Full trace object |
| `trace_updated` | Trace updated | Full trace object |
| `trace_deleted` | Trace deleted | `{ trace_id: "..." }` |
| `trace_event` | Event added to trace | `{ trace_id, event, trace }` |
| `stats_update` | Stats update | Stats object |
| `test_trace_created` | Test trace created | Full trace object |
| `pong` | Heartbeat response | `{ timestamp: "..." }` |
| `error` | Error message | `{ message: "..." }` |

#### Client → Server Messages

| Type | Description | Data |
|------|-------------|------|
| `ping` | Heartbeat request | `{ type: "ping" }` |
| `subscribe` | Subscribe to channels | `{ type: "subscribe", channels: ["all"] }` |
| `get_stats` | Request current stats | `{ type: "get_stats" }` |

### Example Usage

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  console.log('Connected!');
  ws.send(JSON.stringify({ type: 'ping' }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch (message.type) {
    case 'trace_created':
      console.log('New trace:', message.data);
      break;
    case 'stats_update':
      console.log('Stats:', message.data);
      break;
  }
};
```

---

## SDK Reference

### Python SDK

#### Installation

```bash
pip install agentwatch
```

#### Basic Usage

```python
from agentwatch import AgentWatch

aw = AgentWatch(api_url="http://localhost:8000")

# Create trace
trace = aw.create_trace(
    agent_id="agent_001",
    agent_name="MyAgent",
    provider="openai",
    model="gpt-4o",
    prompt="Hello!"
)

# Log tokens
trace.log_tokens(input=100, output=200)

# Complete trace
trace.complete()
```

#### Decorators

```python
from agentwatch.decorators import trace_agent, trace_openai_call

# Generic decorator
@trace_agent("my_agent", model="gpt-4o")
def my_llm_function(prompt):
    return openai.chat.completions.create(...)

# OpenAI specific
@trace_openai_call(model="gpt-4o-mini")
def call_gpt(prompt):
    return openai.chat.completions.create(...)

# Async support
@trace_agent("async_agent", model="gpt-4o")
async def async_llm_call(prompt):
    return await openai.chat.completions.create(...)
```

#### Streaming Support

```python
from agentwatch.decorators import trace_streaming

@trace_streaming("stream_agent", model="gpt-4o")
def stream_gpt(prompt):
    return openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )

# Use the wrapped stream
for chunk in stream_gpt("Hello"):
    print(chunk.choices[0].delta.content)
```

---

## Token Costs (USD per 1K tokens)

| Provider | Model | Input | Output |
|----------|-------|-------|--------|
| OpenAI | gpt-4o | $0.005 | $0.015 |
| OpenAI | gpt-4o-mini | $0.00015 | $0.0006 |
| Anthropic | claude-3.5-sonnet | $0.003 | $0.015 |
| DeepSeek | deepseek-v4 | $0.00014 | $0.00028 |
| Google | gemini-1.5-pro | $0.00125 | $0.005 |

**Key Insight**: DeepSeek is **89x cheaper** than OpenAI GPT-4o!

---

## Error Handling

All endpoints return standard HTTP status codes:

- `200`: Success
- `400`: Bad Request (invalid input)
- `404`: Not Found (trace not found)
- `500`: Internal Server Error

Error response format:
```json
{
  "detail": "Trace abc123 not found"
}
```

---

## Rate Limits

Currently no rate limits (memory-based storage). Future versions with ClickHouse will implement rate limiting.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.3.0 | 2026-04-27 | WebSocket support, Analytics API, SDK streaming |
| 0.2.0 | 2026-04-26 | Dashboard API, Cost comparison, Provider stats |
| 0.1.0 | 2026-04-25 | Initial release, basic Trace API |