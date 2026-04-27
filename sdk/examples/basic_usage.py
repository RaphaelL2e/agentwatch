"""
AgentWatch SDK 使用示例

演示如何使用 AgentWatch SDK追踪 AI Agent
"""

# ==================== 基础使用 ====================

from agentwatch import AgentWatch

# 创建客户端
aw = AgentWatch(api_url="http://localhost:8000")

# 健康检查
health = aw.health_check()
print(f"Health: {health}")

# 创建 trace
trace = aw.create_trace(
    agent_id="example_agent",
    agent_name="ExampleAgent",
    provider="openai",
    model="gpt-4o-mini",
    prompt="What is AI?",
)

print(f"Trace ID: {trace.trace_id}")

# 添加事件
trace.add_event(
    event_type="call",
    input_tokens=50,
    content="User prompt sent",
)

trace.add_event(
    event_type="response",
    input_tokens=50,
    output_tokens=150,
    latency_ms=800,
    content="AI response received",
)

# 完成 trace
trace.complete()

# 掷取 trace 详情
trace_data = aw.get_trace(trace.trace_id)
print(f"Trace data: {trace_data}")


# ==================== 上下文管理器 ====================

print("\n--- Context Manager Example ---")

with aw.trace("auto_agent", model="gpt-4o") as t:
    # 模拟 LLM 调用
    t.log_tokens(input=100, output=200)
    print(f"Auto trace ID: {t.trace_id}")

# 自动完成


# ==================== 获取统计 ====================

print("\n--- Statistics ---")

stats = aw.get_stats()
print(f"Stats: {stats}")

traces = aw.list_traces(page=1, page_size=10)
print(f"Traces: {traces['total']} total")

cost = aw.get_cost_summary()
print(f"Cost summary: {cost}")


# ==================== 关闭客户端 ====================

aw.close()
print("\nDone!")
