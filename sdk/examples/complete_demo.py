"""
AgentWatch 完整 Demo

模拟真实 AI Agent 工作流程，展示完整的监控功能：
- 多步骤 Agent 执行
- Token 成本追踪
- 性能分析
- 错误处理
"""

import time
import random
from agentwatch import AgentWatch

# 创建客户端
aw = AgentWatch(api_url="http://localhost:8000")

print("🚀 AgentWatch Complete Demo")
print("=" * 50)

# ==================== 场景1: 代码分析 Agent ====================

print("\n📊 场景1: 代码分析 Agent")
print("-" * 30)

with aw.trace(
    agent_id="code_analyzer_001",
    agent_name="CodeAnalyzer",
    provider="openai",
    model="gpt-4o",
    prompt="分析这段 Python 代码的性能瓶颈",
    metadata={"project": "agentwatch", "file": "main.py"}
) as trace:
    
    # 步骤1: 读取代码
    trace.add_event(
        event_type="tool_use",
        content="读取 main.py 文件",
        metadata={"tool": "read_file", "file": "main.py"}
    )
    time.sleep(0.1)
    
    # 步骤2: 分析代码结构
    trace.log_tokens(input=500, output=200)
    trace.add_event(
        event_type="call",
        content="分析代码结构",
        latency_ms=150,
    )
    time.sleep(0.15)
    
    # 步骤3: 性能建议
    trace.log_tokens(input=200, output=800)
    trace.add_event(
        event_type="response",
        content="生成性能优化建议",
        latency_ms=800,
    )
    
print(f"✅ Trace完成: {trace.trace_id}")

# ==================== 场景2: 多模型对比 Agent ====================

print("\n📈 场景2: 多模型成本对比")
print("-" * 30)

models = [
    ("openai", "gpt-4o-mini", 100, 300),
    ("anthropic", "claude-3.5-sonnet", 150, 400),
    ("deepseek", "deepseek-v4", 200, 500),
]

for provider, model, input_tokens, output_tokens in models:
    with aw.trace(
        agent_id="benchmark_agent",
        agent_name="BenchmarkAgent",
        provider=provider,
        model=model,
        prompt="解决同一个问题的成本对比测试",
    ) as trace:
        trace.log_tokens(input=input_tokens, output=output_tokens)
        trace.add_event(
            event_type="response",
            content=f"{model} 完成任务",
            latency_ms=random.randint(100, 500),
        )
    
    print(f"  {model}: {input_tokens + output_tokens} tokens")

# ==================== 场景3: 错误处理演示 ====================

print("\n⚠️ 场景3: 错误处理演示")
print("-" * 30)

try:
    with aw.trace(
        agent_id="error_demo",
        agent_name="ErrorAgent",
        provider="openai",
        model="gpt-4o",
        prompt="模拟错误场景",
    ) as trace:
        trace.log_tokens(input=50, output=0)
        trace.add_event(
            event_type="call",
            content="开始处理",
        )
        
        # 模拟错误
        raise ValueError("模拟 Agent 执行错误")
        
except ValueError as e:
    # Trace 自动记录错误（上下文管理器会调用 log_error）
    print(f"❌ 错误已捕获: {e}")

# ==================== 获取统计数据 ====================

print("\n📊 统计数据")
print("-" * 30)

stats = aw.get_stats()
print(f"总 Traces: {stats['total_traces']}")
print(f"完成: {stats['completed_traces']}")
print(f"失败: {stats['failed_traces']}")
print(f"总成本: ${stats['total_cost']:.6f}")

traces = aw.list_traces(page=1, page_size=10)
print(f"\n最近 Traces ({traces['total']} 条):")
for t in traces['traces'][:5]:
    print(f"  - {t['trace_id'][:16]}... | {t['agent_name']} | {t['model']} | ${t['total_cost']:.6f}")

cost_summary = aw.get_cost_summary()
print(f"\n成本汇总:")
for cs in cost_summary:
    print(f"  - {cs['provider']}/{cs['model']}: {cs['total_traces']} traces, ${cs['total_cost']:.6f}")

# ==================== Dashboard API 测试 ====================

print("\n🎯 Dashboard 数据")
print("-" * 30)

import requests

# 获取 Dashboard 数据
resp = requests.get("http://localhost:8000/api/v1/dashboard")
dashboard = resp.json()

print(f"总 Traces: {dashboard['total_traces']}")
print(f"运行中: {dashboard['running_traces']}")
print(f"已完成: {dashboard['completed_traces']}")
print(f"失败: {dashboard['failed_traces']}")
print(f"总成本: ${dashboard['total_cost']:.6f}")
print(f"平均延迟: {dashboard['avg_latency_ms']:.1f}ms")

print(f"\nProvider 分布:")
for p, count in dashboard['provider_distribution'].items():
    print(f"  - {p}: {count}")

print(f"\nModel 分布:")
for m, count in dashboard['model_distribution'].items():
    print(f"  - {m}: {count}")

aw.close()
print("\n✅ Demo 完成！")
print("=" * 50)