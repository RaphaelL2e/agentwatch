# AgentWatch SDK

**Open-source AI Agent Monitoring Platform**

[![PyPI](https://img.shields.io/badge/PyPI-0.7.1-blue.svg)](https://pypi.org/project/agentwatch/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://python.org)

AgentWatch helps you track, analyze, and optimize AI agent performance and costs.

**🔥 Key Discovery: DeepSeek costs only 1/107 of OpenAI GPT-4o!**

## Features

- **Trace Tracking** - Full execution flow with timestamps, inputs/outputs, events
- **Cost Monitoring** - Real-time cost calculation for OpenAI, Anthropic, DeepSeek, Gemini
- **Performance Analysis** - Latency metrics, success rates, token usage
- **Real-time Updates** - WebSocket for live dashboard updates
- **Multi-provider Support** - Works with any LLM client (OpenAI, Claude, DeepSeek, Gemini)
- **Zero Intrusion** - Context manager + decorator patterns, minimal code changes

## Installation

```bash
pip install agentwatch
```

## Quick Start

### 1. Start the Backend

```bash
# Clone and run backend
git clone https://github.com/RaphaelL2e/agentwatch.git
cd agentwatch/backend
python main.py
```

Backend runs at http://localhost:8000
- API Docs: http://localhost:8000/docs
- Dashboard: http://localhost:8000/api/v1/dashboard

### 2. Use in Your Agent

```python
from agentwatch import AgentWatch

# Create client
aw = AgentWatch(api_url="http://localhost:8000")

# Method 1: Context manager (auto-tracking)
with aw.trace("my_agent", model="gpt-4o") as trace:
    response = openai.chat.completions.create(...)
    trace.log_tokens(
        input=response.usage.prompt_tokens,
        output=response.usage.completion_tokens
    )

# Method 2: Decorator (zero intrusion)
from agentwatch.decorators import trace_agent

@trace_agent("my_agent", model="gpt-4o")
def call_gpt(prompt: str):
    return openai.chat.completions.create(...)

# Get statistics
stats = aw.get_stats()
print(f"Total traces: {stats['total_traces']}")
print(f"Total cost: ${stats['total_cost']}")
```

## Cost Comparison

| Provider | Model | Input Cost | Output Cost | vs GPT-4o |
|----------|-------|------------|-------------|-----------|
| OpenAI | GPT-4o | $5.00/1M | $15.00/1M | baseline |
| OpenAI | GPT-4o-mini | $0.15/1M | $0.60/1M | 16x cheaper |
| Anthropic | Claude 3.5 Sonnet | $3.00/1M | $15.00/1M | 1.7x cheaper |
| **DeepSeek** | **DeepSeek V4** | **$0.14/1M** | **$0.28/1M** | **107x cheaper** |
| Google | Gemini 1.5 Pro | $1.25/1M | $5.00/1M | 4x cheaper |

**AgentWatch automatically calculates costs and suggests optimizations!**

## SDK Features

### Decorators

```python
from agentwatch.decorators import (
    trace_agent,       # Basic tracing
    with_retry,        # Auto retry with backoff
    with_rate_limit,   # Rate limiting
    with_timeout,      # Timeout control
    with_cache,        # Response caching
    with_fallback,     # Provider fallback
)

# Retry on failure
@with_retry(max_attempts=3, backoff=2.0)
def call_with_retry():
    return openai.chat.completions.create(...)

# Rate limiting
@with_rate_limit(requests_per_minute=60)
def call_with_limit():
    return openai.chat.completions.create(...)

# Timeout control
@with_timeout(seconds=30)
def call_with_timeout():
    return openai.chat.completions.create(...)

# Response caching
@with_cache(ttl_seconds=300)
def call_with_cache(prompt):
    return openai.chat.completions.create(...)

# Provider fallback
@with_fallback(
    primary="openai",
    fallbacks=["deepseek", "claude"]
)
def call_with_fallback():
    return openai.chat.completions.create(...)
```

### Circuit Breaker

```python
from agentwatch.decorators import CircuitBreaker

breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60
)

@breaker.protect
def protected_call():
    return openai.chat.completions.create(...)
```

## Dashboard

AgentWatch includes a real-time React Dashboard:

- **Stats Cards** - Total traces, success rate, costs
- **Trace List** - Searchable, filterable trace history
- **Cost Alerts** - Daily/monthly budget thresholds
- **WebSocket Updates** - Live updates without polling
- **Charts** - Token distribution, cost trends, latency histograms

## Integration Examples

### OpenAI

```python
from openai import OpenAI
from agentwatch import AgentWatch

client = OpenAI()
aw = AgentWatch()

with aw.trace("openai_agent", model="gpt-4o") as trace:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    trace.log_tokens(
        input=response.usage.prompt_tokens,
        output=response.usage.completion_tokens
    )
    trace.add_event("response", content=response.choices[0].message.content)
```

### Claude (Anthropic)

```python
from anthropic import Anthropic
from agentwatch import AgentWatch

client = Anthropic()
aw = AgentWatch()

with aw.trace("claude_agent", model="claude-3-5-sonnet") as trace:
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Hello!"}]
    )
    trace.log_tokens(
        input=response.usage.input_tokens,
        output=response.usage.output_tokens
    )
```

### DeepSeek

```python
from openai import OpenAI  # DeepSeek uses OpenAI-compatible API
from agentwatch import AgentWatch

client = OpenAI(
    api_key="your-deepseek-key",
    base_url="https://api.deepseek.com/v1"
)
aw = AgentWatch()

with aw.trace("deepseek_agent", model="deepseek-chat") as trace:
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    trace.log_tokens(
        input=response.usage.prompt_tokens,
        output=response.usage.completion_tokens
    )
    # 107x cheaper than GPT-4o!
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/traces` | POST | Create trace |
| `/api/v1/traces` | GET | List traces |
| `/api/v1/traces/{id}` | GET | Get trace detail |
| `/api/v1/stats` | GET | Get statistics |
| `/api/v1/cost/summary` | GET | Cost summary |
| `/api/v1/budget` | GET/PUT | Budget management |
| `/api/v1/models/pricing` | GET | Model pricing data |
| `/api/v1/models/comparison` | GET | Cost comparison |
| `/ws` | WebSocket | Real-time updates |

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  AI Agent   │────▶│  SDK Client │────▶│  Backend    │
│             │     │             │     │  (FastAPI)  │
│ OpenAI/     │     │ trace()     │     │             │
│ Claude/     │     │ log_tokens()│     │ WebSocket   │
│ DeepSeek    │     │ decorators  │     │ REST API    │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │  Dashboard  │
                                        │  (React)    │
                                        │             │
                                        │ Real-time   │
                                        │ Updates     │
                                        └─────────────┘
```

## Development

### Run Tests

```bash
cd sdk
pytest tests/ -v
```

### Build Package

```bash
cd sdk
python -m build
```

### Upload to PyPI

```bash
cd sdk
twine upload dist/*
```

## Links

- **GitHub**: https://github.com/RaphaelL2e/agentwatch
- **Issues**: https://github.com/RaphaelL2e/agentwatch/issues
- **Documentation**: https://github.com/RaphaelL2e/agentwatch#readme
- **Changelog**: https://github.com/RaphaelL2e/agentwatch/releases

## License

Apache 2.0 - See [LICENSE](LICENSE) for details.

---

**Made with ❤️ by RaphaelL2e**

🚀 **AgentWatch - Make AI Agents Observable, Optimizable, and Trustworthy**