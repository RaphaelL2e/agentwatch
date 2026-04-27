"""
AgentWatch SDK + OpenAI 示例

演示如何追踪 OpenAI API 调用
"""

import os
from agentwatch import AgentWatch
from agentwatch.decorators import trace_openai_call

# 设置 API Key（实际使用时需要真实 key）
# os.environ["OPENAI_API_KEY"] = "your-openai-api-key"

aw = AgentWatch(api_url="http://localhost:8000")


# ==================== 方式 1: 手动追踪 ====================


def call_openai_manual(prompt: str):
    """手动追踪 OpenAI 调用"""
    trace = aw.create_trace(
        agent_id="openai_agent",
        agent_name="OpenAIManualAgent",
        provider="openai",
        model="gpt-4o-mini",
        prompt=prompt,
    )

    try:
        # 实际调用（这里用模拟数据）
        # response = openai.chat.completions.create(...)

        # 模拟响应
        mock_response = type(
            "Response",
            (),
            {
                "usage": type(
                    "Usage",
                    (),
                    {
                        "prompt_tokens": 100,
                        "completion_tokens": 200,
                        "total_tokens": 300,
                    },
                ),
                "choices": [{"message": {"content": "AI response"}}],
            },
        )()

        # 记录 tokens
        trace.log_tokens(
            input=mock_response.usage.prompt_tokens,
            output=mock_response.usage.completion_tokens,
        )

        trace.complete()
        return mock_response

    except Exception as e:
        trace.log_error(str(e))
        raise


# ==================== 方式 2: 装饰器 ====================


@trace_openai_call(model="gpt-4o-mini", api_url="http://localhost:8000")
def call_openai_decorated(prompt: str):
    """使用装饰器自动追踪"""
    # 模拟调用
    mock_response = type(
        "Response",
        (),
        {
            "usage": type(
                "Usage",
                (),
                {
                    "prompt_tokens": 150,
                    "completion_tokens": 250,
                    "total_tokens": 400,
                },
            ),
            "choices": [{"message": {"content": "Decorated response"}}],
        },
    )()
    return mock_response


# ==================== 方式 3: 上下文管理器 ====================


def call_openai_context(prompt: str):
    """使用上下文管理器"""
    with aw.trace("openai_ctx_agent", model="gpt-4o-mini") as t:
        # 模拟调用
        mock_response = type(
            "Response",
            (),
            {
                "usage": type(
                    "Usage",
                    (),
                    {
                        "prompt_tokens": 80,
                        "completion_tokens": 120,
                        "total_tokens": 200,
                    },
                ),
            },
        )()

        t.log_tokens(
            input=mock_response.usage.prompt_tokens,
            output=mock_response.usage.completion_tokens,
        )

        return mock_response


# ==================== 运行示例 ====================

if __name__ == "__main__":
    print("=== OpenAI Integration Examples ===\n")

    # 方式 1
    print("1. Manual tracing:")
    result1 = call_openai_manual("What is AI?")
    print(f"   Tokens used: {result1.usage.total_tokens}")

    # 方式 2
    print("\n2. Decorator:")
    result2 = call_openai_decorated("Hello")
    print(f"   Tokens used: {result2.usage.total_tokens}")

    # 方式 3
    print("\n3. Context manager:")
    result3 = call_openai_context("Hi")
    print(f"   Tokens used: {result3.usage.total_tokens}")

    # 查看统计
    print("\n=== Statistics ===")
    stats = aw.get_stats()
    print(f"Total traces: {stats['total_traces']}")
    print(f"Total cost: ${stats['total_cost']:.4f}")

    aw.close()
    print("\nDone!")
