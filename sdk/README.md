# AgentWatch SDK

AI Agent Monitoring Python Client - Track, Debug, and Optimize Your AI Agents.

## Installation

```bash
pip install agentwatch
```

## Quick Start

### Basic Usage

```python
from agentwatch import AgentWatch

# Create client
aw = AgentWatch(api_url="http://localhost:8000")

# Manual tracing
trace = aw.create_trace(
    agent_id="my_agent",
    agent_name="MyAgent",
    provider="openai",
    model="gpt-4o"
)

# Add events
trace.add_event("call", input_tokens=100)
trace.add_event("response", output_tokens=200)
trace.complete()
```

### Context Manager

```python
from agentwatch import AgentWatch

aw = AgentWatch()

# Auto tracing with context manager
with aw.trace("my_agent", model="gpt-4o") as t:
    response = openai.chat.completions.create(...)
    t.log_tokens(
        input=response.usage.prompt_tokens,
        output=response.usage.completion_tokens
    )
```

### Decorator

```python
from agentwatch.decorators import trace_agent, trace_openai_call

@trace_openai_call(model="gpt-4o-mini")
def call_gpt(prompt: str):
    return openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

# Auto traced!
result = call_gpt("Hello")
```

### Traced Agent Class

```python
from agentwatch.decorators import TracedAgent

class MyAgent(TracedAgent):
    def run(self, prompt: str):
        self.start_trace(prompt)
        response = self.llm_call(prompt)
        self.log_tokens(input=100, output=200)
        self.end_trace()
        return response

agent = MyAgent(name="my_agent", model="gpt-4o")
result = agent.run("Hello")
```

## Supported Providers

| Provider | Models | Cost (per 1K tokens) |
|----------|--------|---------------------|
| OpenAI | gpt-4o, gpt-4o-mini, gpt-3.5-turbo | $0.00015 - $0.015 |
| Anthropic | claude-3-opus, sonnet, haiku | $0.00025 - $0.075 |
| DeepSeek | deepseek-chat, deepseek-v4 | $0.00007 - $0.00028 |
| Google | gemini-pro, gemini-1.5 | $0.000075 - $0.005 |

## Cost Calculation

```python
from agentwatch.providers import calculate_cost

cost = calculate_cost(
    provider="openai",
    model="gpt-4o",
    input_tokens=1000,
    output_tokens=500
)
print(f"Cost: ${cost:.4f}")  # Cost: $0.0085
```

## API Reference

### AgentWatch Client

- `create_trace()` - Create a new trace
- `get_trace(trace_id)` - Get trace details
- `list_traces()` - List traces with filters
- `get_stats()` - Get statistics
- `get_cost_summary()` - Get cost summary
- `trace()` - Context manager for auto tracing

### TraceContext

- `add_event()` - Add an event
- `log_tokens()` - Log token usage
- `log_error()` - Log an error
- `complete()` - Complete the trace

## Configuration

```python
import os

# Environment variables
os.environ["AGENTWATCH_API_URL"] = "http://your-server:8000"
os.environ["AGENTWATCH_API_KEY"] = "your_api_key"

# Or pass directly
aw = AgentWatch(
    api_url="http://your-server:8000",
    api_key="your_api_key"
)
```

## License

MIT License - see [LICENSE](LICENSE) for details.