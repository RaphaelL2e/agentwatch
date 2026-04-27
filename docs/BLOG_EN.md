# AgentWatch: Why I Built an AI Agent Monitoring Platform

## The Problem: A Shocking Discovery

Last week, while working on an AI Agent project, I discovered something shocking:

**DeepSeek costs only 1/107 of OpenAI GPT-4o!**

- GPT-4o: $0.18 per 1M tokens
- DeepSeek: $0.002 per 1M tokens

This means if you consume 100M tokens daily:
- OpenAI: **$18/day = $540/month**
- DeepSeek: **$0.2/day = $6/month**

Over a year, that's **$6,480 vs $72**!

But here's the problem: **Most developers don't know how many tokens their agents actually consume, or the massive cost differences between models.**

That's why I built **AgentWatch**.

---

## What is AgentWatch?

AgentWatch is an open-source AI Agent monitoring platform that helps developers:

1. **Track Agent Execution** - Log every call with input, output, tokens, latency
2. **Calculate Costs** - Real-time cost calculation for OpenAI, Claude, DeepSeek, Gemini
3. **Optimize Choices** - Automatically discover cost-saving opportunities

### Quick Start

```python
from agentwatch import AgentWatch

aw = AgentWatch(api_url="http://localhost:8000")

with aw.trace("my_agent", model="gpt-4o") as trace:
    response = openai.chat.completions.create(...)
    trace.log_tokens(
        input=response.usage.prompt_tokens,
        output=response.usage.completion_tokens
    )

# Check costs
stats = aw.get_stats()
print(f"Total cost: ${stats['total_cost']}")
```

---

## Why Open Source?

Three reasons:

### 1. Data Privacy

AI Agent data may contain sensitive information:
- User conversations
- Business logic
- API key usage patterns

Open source means **self-hosted** - your data stays with you.

### 2. Customization

Every team has different needs:
- Integrate with internal systems?
- Custom Dashboard?
- Specific database?

Open source lets you modify freely.

### 3. Cost Transparency

Commercial monitoring tools are expensive:
- LangSmith: $39/user/month
- Datadog: $15-23/host/month

AgentWatch is completely free - only server costs.

---

## Tech Stack

Simple and practical:

### Backend: FastAPI
```python
@app.post("/api/v1/trace")
async def create_trace(trace: TraceCreate):
    return await trace_service.create_trace(trace)
```

### Frontend: React + TypeScript + Tailwind
```typescript
const { data: stats } = useQuery({
  queryKey: ['stats'],
  queryFn: () => api.getStats(),
});
```

### SDK: Python
```python
class AgentWatch:
    def trace(self, agent_name: str, model: str):
        return TraceContext(self, agent_name, model)
```

---

## Key Features

### 1. Trace Tracking

Every Agent execution generates a Trace with:
- Agent ID and name
- Provider and Model
- Input/Output tokens
- Execution time
- Cost calculation

### 2. Cost Comparison

Built-in Token costs:

| Provider | Model | Input | Output |
|----------|-------|-------|--------|
| OpenAI | gpt-4o | $0.005/1K | $0.015/1K |
| Anthropic | claude-3.5-sonnet | $0.003/1K | $0.015/1K |
| DeepSeek | deepseek-v4 | $0.00014/1K | $0.00028/1K |
| Google | gemini-1.5-pro | $0.00125/1K | $0.005/1K |

**DeepSeek's cost advantage is obvious!**

### 3. Real-time Dashboard

See:
- Total Traces count
- Running/Completed status
- Total Cost accumulated
- Recent Activity

---

## Roadmap

### Week 1 (Complete ✅)
- FastAPI backend
- Trace API endpoints
- Python SDK
- Basic Dashboard

### Week 2
- Full React Dashboard
- ClickHouse storage
- WebSocket real-time updates

### Week 3
- User authentication
- Team management
- Data export

### Week 4
- npm CLI release
- GitHub Marketplace
- First users

---

## Perfect For

1. **AI Engineers** - Building LLM applications
2. **Cost-conscious Teams** - Controlling API spend
3. **Multi-agent Projects** - Managing multiple agents
4. **Open-source Fans** - Prefer self-hosted solutions

---

## Conclusion

AI Agents are changing software development. But without proper monitoring, we can't:
- Know actual resource consumption
- Optimize cost with the right model choice
- Ensure agent reliability

**AgentWatch fills this gap.**

If you're building AI Agents, try AgentWatch:

```bash
pip install agentwatch
```

GitHub: https://github.com/RaphaelL2e/agentwatch

---

**Made with ❤️ by RaphaelL2e**

🚀 **AgentWatch - Make AI Agents Observable, Optimizable, Trustworthy**