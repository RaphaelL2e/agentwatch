# AgentWatch SDK

[![PyPI version](https://badge.fury.io/py/agentwatch.svg)](https://badge.fury.io/py/agentwatch)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

**AgentWatch SDK** 是 [AgentWatch](https://github.com/RaphaelL2e/agentwatch) 的 Python 客户端库，用于追踪和监控 AI Agent 的执行流程、Token 成本和性能指标。

## 安装

```bash
pip install agentwatch
```

## 快速开始

### 1. 基础使用

```python
from agentwatch import AgentWatch

# 创建客户端
aw = AgentWatch(api_url="http://localhost:8000")

# 创建 Trace
trace = aw.create_trace(
    agent_id="my_agent",
    agent_name="MyAgent",
    provider="openai",
    model="gpt-4o-mini",
    prompt="Hello, AI!"
)

# 添加事件
trace.add_event(
    event_type="call",
    input_tokens=100,
    content="开始处理"
)

# 记录 Token
trace.log_tokens(input=100, output=200)

# 完成 Trace
trace.complete()
```

### 2. 上下文管理器（推荐）

```python
from agentwatch import AgentWatch

aw = AgentWatch(api_url="http://localhost:8000")

# 自动追踪
with aw.trace("my_agent", model="gpt-4o") as trace:
    # 你的 Agent 逻辑
    response = openai.chat.completions.create(...)
    
    # 记录 Token 使用
    trace.log_tokens(
        input=response.usage.prompt_tokens,
        output=response.usage.completion_tokens
    )
    
    # Trace 自动完成（包括错误处理）
```

### 3. 获取统计数据

```python
# 获取统计数据
stats = aw.get_stats()
print(f"总 Traces: {stats['total_traces']}")
print(f"总成本: ${stats['total_cost']}")

# 获取 Trace 列表
traces = aw.list_traces(page=1, page_size=10)
for trace in traces['traces']:
    print(f"{trace['agent_name']}: {trace['total_cost']}")

# 获取成本汇总
cost_summary = aw.get_cost_summary()
for cs in cost_summary:
    print(f"{cs['provider']}/{cs['model']}: ${cs['total_cost']}")
```

## API 参考

### AgentWatch 客户端

| 方法 | 说明 |
|------|------|
| `AgentWatch(api_url)` | 创建客户端 |
| `health_check()` | 健康检查 |
| `create_trace(...)` | 创建 Trace |
| `trace(name, model)` | 上下文管理器 |
| `get_trace(trace_id)` | 获取 Trace |
| `list_traces(page, page_size)` | 列出 Traces |
| `get_stats()` | 获取统计 |
| `get_cost_summary()` | 成本汇总 |
| `close()` | 关闭客户端 |

### Trace 方法

| 方法 | 说明 |
|------|------|
| `add_event(event_type, ...)` | 添加事件 |
| `log_tokens(input, output)` | 记录 Token |
| `log_error(message)` | 记录错误 |
| `complete()` | 完成 Trace |

## 支持的 Provider

| Provider | 模型示例 | 成本（USD/1K tokens） |
|----------|----------|-----------------------|
| OpenAI | gpt-4o | $0.005/$0.015 |
| OpenAI | gpt-4o-mini | $0.00015/$0.0006 |
| Anthropic | claude-3.5-sonnet | $0.003/$0.015 |
| DeepSeek | deepseek-v4 | $0.00014/$0.00028 |
| Google | gemini-1.5-pro | $0.00125/$0.005 |

**成本优势**: DeepSeek 成本仅 OpenAI 的 **1/107**！

## 完整示例

查看 `examples/` 目录：

- `basic_usage.py` - 基础使用示例
- `complete_demo.py` - 完整演示（多场景、错误处理、Dashboard）

## 后端服务

SDK 需要 AgentWatch 后端服务运行：

```bash
# 克隆仓库
git clone https://github.com/RaphaelL2e/agentwatch.git

# 启动后端
cd agentwatch/backend
python main.py
```

服务启动后访问:
- API 文档: http://localhost:8000/docs
- Dashboard: http://localhost:3000

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码检查
ruff check .
black .
```

## License

Apache 2.0 - 查看 [LICENSE](https://github.com/RaphaelL2e/agentwatch/blob/main/LICENSE)

## 相关项目

- [AgentWatch](https://github.com/RaphaelL2e/agentwatch) - AI Agent 监控平台
- [AgentWatch Dashboard](https://github.com/RaphaelL2e/agentwatch/tree/main/frontend) - React Dashboard

---

**Made with ❤️ by RaphaelL2e**