# AgentWatch - AI Agent Monitoring Platform

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-teal.svg)](https://fastapi.tiangolo.com)

**AgentWatch** 是一个开源的 AI Agent 监控平台，帮助开发者追踪、分析和优化 AI Agent 的运行性能和成本。

## 🎯 核心功能

- **Trace 追踪** - 完整记录 Agent 执行流程，包括输入输出、Token 使用、延迟等
- **成本监控** - 实时计算各模型（OpenAI、Anthropic、DeepSeek、Google）的 API 成本
- **性能分析** - 提供延迟统计、成功率分析、执行时间分布
- **多 Provider 支持** - 统一监控 OpenAI、Claude、DeepSeek、Gemini 等主流模型
- **Dashboard 可视化** - 实时查看 Agent 运行状态和统计数据

## 🚀 快速开始

### 1. 安装 SDK

```bash
pip install agentwatch
```

### 2. 启动后端服务

```bash
# 克隆仓库
git clone https://github.com/RaphaelL2e/agentwatch.git
cd agentwatch

# 启动后端
cd backend && python main.py
```

服务启动后访问:
- API 文档: http://localhost:8000/docs
- Dashboard: http://localhost:8000/api/v1/dashboard

### 3. 在你的 Agent 中使用

```python
from agentwatch import AgentWatch

# 创建客户端
aw = AgentWatch(api_url="http://localhost:8000")

# 方式1: 上下文管理器（自动追踪）
with aw.trace("my_agent", model="gpt-4o") as trace:
    # 你的 Agent 逻辑
    response = openai.chat.completions.create(...)
    
    # 记录 Token 使用
    trace.log_tokens(
        input=response.usage.prompt_tokens,
        output=response.usage.completion_tokens
    )

# 方式2: 手动追踪
trace = aw.create_trace(
    agent_id="agent_001",
    agent_name="MyAgent",
    provider="openai",
    model="gpt-4o-mini",
    prompt="Hello, AI!"
)

trace.add_event(event_type="call", content="开始处理")
trace.log_tokens(input=100, output=200)
trace.complete()

# 获取统计数据
stats = aw.get_stats()
print(f"总 Traces: {stats['total_traces']}")
print(f"总成本: ${stats['total_cost']}")
```

## 📊 API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/api/v1/trace` | POST | 创建 Trace |
| `/api/v1/trace/{id}` | GET | 获取 Trace 详情 |
| `/api/v1/trace/{id}` | PUT | 更新 Trace |
| `/api/v1/traces` | GET | 列出所有 Traces |
| `/api/v1/stats` | GET | 获取统计数据 |
| `/api/v1/cost/summary` | GET | 成本汇总 |
| `/api/v1/cost/models` | GET | 各模型成本配置 |
| `/api/v1/dashboard` | GET | Dashboard 数据 |

## 💰 Token 成本配置

AgentWatch 内置各模型的 Token 成本（USD per 1K tokens）:

| Provider | Model | Input | Output |
|----------|-------|-------|--------|
| OpenAI | gpt-4o | $0.005 | $0.015 |
| OpenAI | gpt-4o-mini | $0.00015 | $0.0006 |
| Anthropic | claude-3.5-sonnet | $0.003 | $0.015 |
| DeepSeek | deepseek-v4 | $0.00014 | $0.00028 |
| Google | gemini-1.5-pro | $0.00125 | $0.005 |

**成本差异**: DeepSeek 成本仅 OpenAI 的 **1/107**！

## 🏗️ 项目架构

```
agentwatch/
├── backend/           # FastAPI 后端
│   ├── main.py        # API 端点
│   ├── models.py      # Pydantic 数据模型
│   └── trace_service.py  # Trace 服务层
│
├── frontend/          # React Dashboard（开发中）
│   └── src/
│       └── components/
│           └── Dashboard.tsx
│
├── sdk/               # Python SDK
│   └── agentwatch/
│       ├── client.py  # AgentWatch 客户端
│       ├── trace.py   # Trace 数据结构
│       └── decorators.py  # 装饰器
│   └── examples/      # 使用示例
│       ├── basic_usage.py
│       └ complete_demo.py
│
└── docs/              # 文档
    └── PROGRESS.md    # 进度追踪
```

## 📈 Roadmap

### Week 1 (当前)
- [x] FastAPI 后端骨架
- [x] Trace API 端点
- [x] Python SDK
- [x] 基础 Demo

### Week 2
- [ ] React Dashboard 完善
- [ ] ClickHouse 数据存储
- [ ] 实时数据推送（WebSocket）

### Week 3
- [ ] 用户认证
- [ ] 团队管理
- [ ] 数据导出

### Week 4
- [ ] npm CLI 发布
- [ ] GitHub Marketplace 上架
- [ ] 首批用户获取

## 🤝 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 📄 License

Apache 2.0 - 查看 [LICENSE](LICENSE) 了解详情。

---

**Made with ❤️ by RaphaelL2e**

🚀 **AgentWatch - 让 AI Agent 可观测、可优化、可信赖**