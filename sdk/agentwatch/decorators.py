"""
AgentWatch SDK 装饰器
简化 Agent 追踪的装饰器工具
"""

import functools
from typing import Optional, Callable, Any
from .client import AgentWatch, TraceContext


def trace_agent(
    agent_name: str,
    model: str,
    provider: str = "openai",
    api_url: Optional[str] = None,
    **trace_kwargs,
):
    """
    装饰器 - 自动追踪 Agent 函数

    使用示例:
        @trace_agent("my_agent", model="gpt-4o")
        def my_llm_function(prompt: str):
            response = openai.chat.completions.create(...)
            return response

        # 自动追踪每次调用
        result = my_llm_function("Hello")

    Args:
        agent_name: Agent 名称
        model: 使用的模型
        provider: 提供商 (openai/anthropic/deepseek/google)
        api_url: AgentWatch API 地址
        trace_kwargs: 其他 trace 参数
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 创建 AgentWatch 客户端
            aw = AgentWatch(api_url=api_url)

            try:
                # 创建 trace
                trace = aw.create_trace(
                    agent_id=f"agent_{func.__name__}",
                    agent_name=agent_name,
                    provider=provider,
                    model=model,
                    **trace_kwargs,
                )

                # 执行函数
                result = func(*args, **kwargs)

                # 尝试从结果中提取 tokens
                if hasattr(result, "usage"):
                    trace.log_tokens(
                        input=result.usage.prompt_tokens or 0,
                        output=result.usage.completion_tokens or 0,
                    )
                elif isinstance(result, dict) and "usage" in result:
                    usage = result["usage"]
                    trace.log_tokens(
                        input=usage.get("prompt_tokens", 0),
                        output=usage.get("completion_tokens", 0),
                    )

                trace.complete()
                return result

            except Exception as e:
                if "trace" in locals():
                    trace.log_error(str(e))
                raise

            finally:
                aw.close()

        return wrapper

    return decorator


def trace_openai_call(
    agent_name: str = "openai_agent",
    model: str = "gpt-4o",
    **kwargs,
):
    """
    装饰器 - 专门追踪 OpenAI 调用

    使用示例:
        @trace_openai_call(model="gpt-4o-mini")
        def call_gpt(prompt: str):
            return openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
    """
    return trace_agent(agent_name, model, provider="openai", **kwargs)


def trace_anthropic_call(
    agent_name: str = "anthropic_agent",
    model: str = "claude-3-sonnet",
    **kwargs,
):
    """
    装饰器 - 专门追踪 Anthropic 调用

    使用示例:
        @trace_anthropic_call(model="claude-3-haiku")
        def call_claude(prompt: str):
            return anthropic.messages.create(
                model="claude-3-haiku",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
    """
    return trace_agent(agent_name, model, provider="anthropic", **kwargs)


def trace_deepseek_call(
    agent_name: str = "deepseek_agent",
    model: str = "deepseek-chat",
    **kwargs,
):
    """
    装饰器 - 专门追踪 DeepSeek 调用
    """
    return trace_agent(agent_name, model, provider="deepseek", **kwargs)


class TracedAgent:
    """
    追踪的 Agent 类

    使用示例:
        class MyAgent(TracedAgent):
            def run(self, prompt: str):
                return self.llm_call(prompt)

        agent = MyAgent(name="my_agent", model="gpt-4o")
        result = agent.run("Hello")  # 自动追踪
    """

    def __init__(
        self,
        name: str,
        model: str,
        provider: str = "openai",
        api_url: Optional[str] = None,
    ):
        self.name = name
        self.model = model
        self.provider = provider
        self._aw = AgentWatch(api_url=api_url)
        self._trace: Optional[TraceContext] = None

    def start_trace(self, prompt: Optional[str] = None):
        """开始追踪"""
        self._trace = self._aw.create_trace(
            agent_id=f"agent_{self.name}",
            agent_name=self.name,
            provider=self.provider,
            model=self.model,
            prompt=prompt,
        )

    def log_tokens(self, input: int, output: int):
        """记录 tokens"""
        if self._trace:
            self._trace.log_tokens(input=input, output=output)

    def log_error(self, error: str):
        """记录错误"""
        if self._trace:
            self._trace.log_error(error)

    def end_trace(self):
        """结束追踪"""
        if self._trace:
            self._trace.complete()
            self._trace = None

    def close(self):
        """关闭"""
        self._aw.close()
