"""
AgentWatch SDK 装饰器
简化 Agent 追踪的装饰器工具，支持同步/异步函数和流式响应
"""

import functools
import asyncio
import json
from typing import Optional, Callable, Any, AsyncIterator, Iterator, Union
from .client import AgentWatch, TraceContext


def trace_agent(
    agent_name: str,
    model: str,
    provider: str = "openai",
    api_url: Optional[str] = None,
    **trace_kwargs,
):
    """
    装饰器 - 自动追踪 Agent 函数（支持同步和异步）

    使用示例:
        @trace_agent("my_agent", model="gpt-4o")
        def my_llm_function(prompt: str):
            response = openai.chat.completions.create(...)
            return response

        @trace_agent("my_agent", model="gpt-4o")
        async def my_async_llm_function(prompt: str):
            response = await openai.chat.completions.create(...)
            return response

        # 自动追踪每次调用
        result = my_llm_function("Hello")
        result = await my_async_llm_function("Hello")

    Args:
        agent_name: Agent 名称
        model: 使用的模型
        provider: 提供商 (openai/anthropic/deepseek/google)
        api_url: AgentWatch API 地址
        trace_kwargs: 其他 trace 参数
    """

    def decorator(func: Callable) -> Callable:
        # 检测是否是异步函数
        is_async = asyncio.iscoroutinefunction(func)

        if is_async:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                aw = AgentWatch(api_url=api_url)
                trace = None

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
                    result = await func(*args, **kwargs)

                    # 尝试从结果中提取 tokens
                    _extract_tokens(trace, result)

                    trace.complete()
                    return result

                except Exception as e:
                    if trace:
                        trace.log_error(str(e))
                    raise

                finally:
                    aw.close()

            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                aw = AgentWatch(api_url=api_url)
                trace = None

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
                    _extract_tokens(trace, result)

                    trace.complete()
                    return result

                except Exception as e:
                    if trace:
                        trace.log_error(str(e))
                    raise

                finally:
                    aw.close()

            return sync_wrapper

    return decorator


def _extract_tokens(trace: TraceContext, result: Any) -> None:
    """从结果中提取 token 使用量"""
    if hasattr(result, "usage"):
        trace.log_tokens(
            input=getattr(result.usage, "prompt_tokens", 0) or 0,
            output=getattr(result.usage, "completion_tokens", 0) or 0,
        )
    elif isinstance(result, dict) and "usage" in result:
        usage = result["usage"]
        trace.log_tokens(
            input=usage.get("prompt_tokens", 0),
            output=usage.get("completion_tokens", 0),
        )


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


def trace_gemini_call(
    agent_name: str = "gemini_agent",
    model: str = "gemini-1.5-pro",
    **kwargs,
):
    """
    装饰器 - 专门追踪 Google Gemini 调用
    """
    return trace_agent(agent_name, model, provider="google", **kwargs)


# ==================== 流式响应追踪 ====================

class StreamingTraceWrapper:
    """
    流式响应追踪包装器
    
    用于追踪流式 LLM 响应
    """
    
    def __init__(
        self,
        stream: Union[Iterator, AsyncIterator],
        trace: TraceContext,
        client: AgentWatch,
    ):
        self._stream = stream
        self._trace = trace
        self._client = client
        self._input_tokens = 0
        self._output_tokens = 0
        self._chunks = []
        self._is_async = isinstance(stream, AsyncIterator)
    
    def __iter__(self):
        return self
    
    def __next__(self):
        try:
            chunk = next(self._stream)
            self._process_chunk(chunk)
            return chunk
        except StopIteration:
            self._finish()
            raise
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        try:
            chunk = await self._stream.__anext__()
            self._process_chunk(chunk)
            return chunk
        except StopAsyncIteration:
            self._finish()
            raise
    
    def _process_chunk(self, chunk: Any):
        """处理流式响应块"""
        self._chunks.append(chunk)
        
        # 尝试提取 token 信息
        if hasattr(chunk, "usage"):
            if hasattr(chunk.usage, "prompt_tokens"):
                self._input_tokens = chunk.usage.prompt_tokens or 0
            if hasattr(chunk.usage, "completion_tokens"):
                self._output_tokens = chunk.usage.completion_tokens or 0
    
    def _finish(self):
        """完成追踪"""
        self._trace.log_tokens(
            input=self._input_tokens,
            output=self._output_tokens,
        )
        self._trace.complete()
        self._client.close()


def trace_streaming(
    agent_name: str,
    model: str,
    provider: str = "openai",
    api_url: Optional[str] = None,
    **trace_kwargs,
):
    """
    装饰器 - 追踪流式 LLM 响应
    
    使用示例:
        @trace_streaming("streaming_agent", model="gpt-4o")
        def stream_gpt(prompt: str):
            return openai.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )
        
        # 返回的是包装后的流
        for chunk in stream_gpt("Hello"):
            print(chunk.choices[0].delta.content, end="")
    
    注意: 流式追踪会在流结束时自动完成
    """
    
    def decorator(func: Callable) -> Callable:
        is_async = asyncio.iscoroutinefunction(func)
        
        if is_async:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> StreamingTraceWrapper:
                aw = AgentWatch(api_url=api_url)
                trace = aw.create_trace(
                    agent_id=f"stream_{func.__name__}",
                    agent_name=agent_name,
                    provider=provider,
                    model=model,
                    **trace_kwargs,
                )
                
                stream = await func(*args, **kwargs)
                return StreamingTraceWrapper(stream, trace, aw)
            
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> StreamingTraceWrapper:
                aw = AgentWatch(api_url=api_url)
                trace = aw.create_trace(
                    agent_id=f"stream_{func.__name__}",
                    agent_name=agent_name,
                    provider=provider,
                    model=model,
                    **trace_kwargs,
                )
                
                stream = func(*args, **kwargs)
                return StreamingTraceWrapper(stream, trace, aw)
            
            return sync_wrapper
    
    return decorator


# ==================== Agent 类 ====================

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
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start_trace()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        if exc_type:
            self.log_error(str(exc_val))
        self.end_trace()
        self.close()
        return False


class AsyncTracedAgent:
    """
    异步追踪的 Agent 类
    
    使用示例:
        class MyAsyncAgent(AsyncTracedAgent):
            async def run(self, prompt: str):
                return await self.llm_call(prompt)
        
        agent = MyAsyncAgent(name="my_agent", model="gpt-4o")
        result = await agent.run("Hello")
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

    async def start_trace(self, prompt: Optional[str] = None):
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
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start_trace()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if exc_type:
            self.log_error(str(exc_val))
        self.end_trace()
        self.close()
        return False


# ==================== 便捷函数 ====================

def quick_trace(
    func: Callable,
    *args,
    agent_name: str = "quick_agent",
    model: str = "gpt-4o",
    provider: str = "openai",
    api_url: Optional[str] = None,
    **kwargs,
) -> Any:
    """
    快速追踪函数调用（一次性使用）
    
    使用示例:
        result = quick_trace(
            my_llm_function,
            "prompt",
            agent_name="quick",
            model="gpt-4o",
        )
    """
    decorated = trace_agent(agent_name, model, provider, api_url)(func)
    return decorated(*args, **kwargs)


async def async_quick_trace(
    func: Callable,
    *args,
    agent_name: str = "quick_agent",
    model: str = "gpt-4o",
    provider: str = "openai",
    api_url: Optional[str] = None,
    **kwargs,
) -> Any:
    """
    快速追踪异步函数调用
    
    使用示例:
        result = await async_quick_trace(
            my_async_llm_function,
            "prompt",
            agent_name="quick",
            model="gpt-4o",
        )
    """
    decorated = trace_agent(agent_name, model, provider, api_url)(func)
    return await decorated(*args, **kwargs)