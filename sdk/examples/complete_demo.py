"""
AgentWatch SDK 完整示例
演示各种使用场景
"""

import os
from agentwatch import AgentWatch, trace_agent, TracedAgent

# ============================================
# 示例 1: 基础使用 - 上下文管理器
# ============================================


def example_basic():
    """最简单的使用方式"""
    aw = AgentWatch(api_url="http://localhost:8000")

    with aw.trace("chat_agent", model="gpt-4o") as trace:
        # 你的 LLM 调用逻辑
        # 这里模拟 OpenAI API 调用
        print("Calling GPT-4o...")

        # 记录 Token 使用
        trace.log_tokens(input=100, output=200)

        print(f"Trace ID: {trace.trace_id}")
        print(f"Agent: {trace.agent_name}")

    # 获取统计
    stats = aw.get_stats()
    print(f"Total traces: {stats['total_traces']}")
    print(f"Total cost: ${stats['total_cost']}")

    aw.close()


# ============================================
# 示例 2: 装饰器使用
# ============================================


@trace_agent("qa_agent", model="gpt-4o-mini", provider="openai")
def answer_question(question: str):
    """使用装饰器自动追踪"""
    # 模拟 LLM 调用
    print(f"Answering: {question}")

    # 返回模拟的响应对象（包含 usage）
    return {
        "answer": "This is a sample answer",
        "usage": {"prompt_tokens": 50, "completion_tokens": 100},
    }


def example_decorator():
    """装饰器示例"""
    result = answer_question("What is AI?")
    print(f"Answer: {result['answer']}")


# ============================================
# 示例 3: DeepSeek 成本优化
# ============================================


def example_cost_comparison():
    """展示 DeepSeek 成本优势"""
    aw = AgentWatch()

    # 使用 OpenAI
    with aw.trace("openai_agent", model="gpt-4o", provider="openai") as t1:
        t1.log_tokens(input=10000, output=20000)

    # 使用 DeepSeek
    with aw.trace("deepseek_agent", model="deepseek-chat", provider="deepseek") as t2:
        t2.log_tokens(input=10000, output=20000)

    # 获取成本对比
    cost_summary = aw.get_cost_summary()

    print("\n=== Cost Comparison ===")
    print(f"OpenAI cost: ${cost_summary['by_provider']['openai']['total_cost']}")
    print(f"DeepSeek cost: ${cost_summary['by_provider']['deepseek']['total_cost']}")
    print(f"Savings: {cost_summary['cost_savings']['deepseek_vs_openai']}x cheaper!")

    aw.close()


# ============================================
# 示例 4: 多 Provider 监控
# ============================================


def example_multi_provider():
    """同时监控多个 Provider"""
    aw = AgentWatch()

    providers = [
        ("openai", "gpt-4o-mini"),
        ("anthropic", "claude-3-haiku"),
        ("deepseek", "deepseek-chat"),
        ("google", "gemini-1.5-flash"),
    ]

    for provider, model in providers:
        with aw.trace(f"{provider}_agent", model=model, provider=provider) as trace:
            # 模拟不同模型的调用
            trace.log_tokens(input=500, output=1000)
            print(f"Called {provider}/{model}")

    # 获取总体统计
    stats = aw.get_stats()

    print("\n=== Multi-Provider Stats ===")
    print(f"Total traces: {stats['total_traces']}")
    print(f"Total cost: ${stats['total_cost']:.4f}")

    for provider, data in stats["by_provider"].items():
        print(f"{provider}: {data['traces']} traces, ${data['cost']:.4f}")

    aw.close()


# ============================================
# 示例 5: TracedAgent 类使用
# ============================================


class MyChatAgent(TracedAgent):
    """自定义 Agent 类"""

    def __init__(self):
        super().__init__(name="chat_agent", model="gpt-4o", provider="openai")

    def run(self, prompt: str):
        """运行 Agent"""
        self.start_trace(prompt=prompt)

        try:
            # 模拟 LLM 调用
            print(f"Processing: {prompt}")

            # 记录 Token
            self.log_tokens(input=100, output=200)

            result = f"Response to: {prompt}"

            self.end_trace()
            return result

        except Exception as e:
            self.log_error(str(e))
            self.end_trace()
            raise


def example_traced_agent():
    """TracedAgent 类示例"""
    agent = MyChatAgent()

    try:
        result = agent.run("Hello, AI!")
        print(f"Result: {result}")
    finally:
        agent.close()


# ============================================
# 示例 6: 错误追踪
# ============================================


def example_error_tracking():
    """追踪错误"""
    aw = AgentWatch()

    try:
        with aw.trace("error_agent", model="gpt-4o") as trace:
            # 模拟一个失败的调用
            raise Exception("API rate limit exceeded")
    except Exception as e:
        # Trace 会自动记录错误
        print(f"Error tracked: {e}")

    # 检查失败的 traces
    traces = aw.list_traces(status="failed")
    print(f"Failed traces: {len(traces['traces'])}")

    aw.close()


# ============================================
# 示例 7: 批量追踪
# ============================================


def example_batch():
    """批量创建多个 traces"""
    aw = AgentWatch()

    # 创建 10 个 traces
    for i in range(10):
        with aw.trace(
            f"batch_agent_{i}", model="deepseek-chat", provider="deepseek"
        ) as trace:
            trace.log_tokens(input=100, output=200)

    # 获取统计
    stats = aw.get_stats()
    print(f"Created {stats['total_traces']} traces")
    print(f"Total cost: ${stats['total_cost']}")

    aw.close()


# ============================================
# 示例 8: 实时监控
# ============================================


def example_realtime():
    """模拟实时监控场景"""
    aw = AgentWatch()

    # 模拟连续的 Agent 调用
    for i in range(5):
        with aw.trace(f"stream_agent_{i}", model="gpt-4o-mini") as trace:
            # 添加多个事件
            trace.add_event("llm_call", input_tokens=50)
            trace.add_event("tool_use", input_tokens=20, output_tokens=30)
            trace.add_event("llm_response", output_tokens=100)

            print(f"Agent {i}: Added 3 events")

    # 获取 Dashboard 数据
    dashboard = aw._request("GET", "/api/v1/dashboard")

    print("\n=== Dashboard ===")
    print(f"Running: {dashboard['summary']['running']}")
    print(f"Completed: {dashboard['summary']['completed']}")
    print(f"Recent traces: {len(dashboard['recent_traces'])}")

    aw.close()


# ============================================
# 运行所有示例
# ============================================

if __name__ == "__main__":
    print("=" * 50)
    print("AgentWatch SDK Examples")
    print("=" * 50)

    print("\n[Example 1] Basic Usage")
    example_basic()

    print("\n[Example 2] Decorator")
    example_decorator()

    print("\n[Example 3] Cost Comparison")
    example_cost_comparison()

    print("\n[Example 4] Multi-Provider")
    example_multi_provider()

    print("\n[Example 5] TracedAgent Class")
    example_traced_agent()

    print("\n[Example 6] Error Tracking")
    example_error_tracking()

    print("\n[Example 7] Batch Traces")
    example_batch()

    print("\n[Example 8] Realtime Monitoring")
    example_realtime()

    print("\n" + "=" * 50)
    print("All examples completed!")
    print("=" * 50)
