"""
AgentWatch SDK 装饰器
简化 Agent 追踪的装饰器工具，支持同步/异步函数和流式响应
"""

import functools
import asyncio
import json
import time
from typing import Optional, Callable, Any, AsyncIterator, Iterator, Union, List, Tuple
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


# ==================== 重试装饰器 ====================


def with_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    retry_on: tuple = (Exception,),
    on_retry: Optional[Callable[[int, Exception], None]] = None,
):
    """
    重试装饰器 - 自动重试失败的 LLM 调用
    
    使用示例:
        @with_retry(max_attempts=3, delay=1.0)
        @trace_agent("my_agent", model="gpt-4o")
        def call_gpt(prompt: str):
            return openai.chat.completions.create(...)
        
        # 失败会自动重试3次，每次延迟增加
        result = call_gpt("Hello")
    
    Args:
        max_attempts: 最大重试次数
        delay: 初始延迟（秒）
        backoff: 延迟增长因子
        retry_on: 需要重试的异常类型
        on_retry: 重试回调函数，接收 (attempt, exception)
    """
    
    def decorator(func: Callable) -> Callable:
        is_async = asyncio.iscoroutinefunction(func)
        
        if is_async:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                current_delay = delay
                for attempt in range(max_attempts):
                    try:
                        return await func(*args, **kwargs)
                    except retry_on as e:
                        if attempt == max_attempts - 1:
                            raise
                        
                        if on_retry:
                            on_retry(attempt + 1, e)
                        
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                        
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                import time
                current_delay = delay
                
                for attempt in range(max_attempts):
                    try:
                        return func(*args, **kwargs)
                    except retry_on as e:
                        if attempt == max_attempts - 1:
                            raise
                        
                        if on_retry:
                            on_retry(attempt + 1, e)
                        
                        time.sleep(current_delay)
                        current_delay *= backoff
                        
            return sync_wrapper
    
    return decorator


# ==================== 速率限制装饰器 ====================


class RateLimiter:
    """
    速率限制器
    
    用于限制 API 调用频率，防止超过 provider 的速率限制
    """
    
    def __init__(
        self,
        calls_per_minute: int = 60,
        calls_per_second: int = 10,
    ):
        self.calls_per_minute = calls_per_minute
        self.calls_per_second = calls_per_second
        self._minute_calls: List[float] = []
        self._second_calls: List[float] = []
        self._lock = asyncio.Lock() if asyncio.get_event_loop().is_running() else None
    
    def _clean_old_calls(self, calls: List[float], window: float) -> List[float]:
        """清理超出时间窗口的调用记录"""
        import time
        now = time.time()
        return [t for t in calls if now - t < window]
    
    async def _wait_async(self) -> None:
        """异步等待直到可以调用"""
        import time
        
        async with self._lock:
            now = time.time()
            
            # 清理旧调用记录
            self._minute_calls = self._clean_old_calls(self._minute_calls, 60)
            self._second_calls = self._clean_old_calls(self._second_calls, 1)
            
            # 检查分钟限制
            if len(self._minute_calls) >= self.calls_per_minute:
                wait_time = 60 - (now - self._minute_calls[0]) + 0.1
                await asyncio.sleep(wait_time)
                self._minute_calls = self._clean_old_calls(self._minute_calls, 60)
            
            # 检查秒限制
            if len(self._second_calls) >= self.calls_per_second:
                wait_time = 1 - (now - self._second_calls[0]) + 0.1
                await asyncio.sleep(wait_time)
                self._second_calls = self._clean_old_calls(self._second_calls, 1)
            
            # 记录本次调用
            self._minute_calls.append(time.time())
            self._second_calls.append(time.time())
    
    def _wait_sync(self) -> None:
        """同步等待直到可以调用"""
        import time
        
        now = time.time()
        
        # 清理旧调用记录
        self._minute_calls = self._clean_old_calls(self._minute_calls, 60)
        self._second_calls = self._clean_old_calls(self._second_calls, 1)
        
        # 检查分钟限制
        if len(self._minute_calls) >= self.calls_per_minute:
            wait_time = 60 - (now - self._minute_calls[0]) + 0.1
            time.sleep(wait_time)
            self._minute_calls = self._clean_old_calls(self._minute_calls, 60)
        
        # 检查秒限制
        if len(self._second_calls) >= self.calls_per_second:
            wait_time = 1 - (now - self._second_calls[0]) + 0.1
            time.sleep(wait_time)
            self._second_calls = self._clean_old_calls(self._second_calls, 1)
        
        # 记录本次调用
        self._minute_calls.append(time.time())
        self._second_calls.append(time.time())


def with_rate_limit(
    calls_per_minute: int = 60,
    calls_per_second: int = 10,
):
    """
    速率限制装饰器 - 自动限制 API 调用频率
    
    使用示例:
        @with_rate_limit(calls_per_minute=60, calls_per_second=10)
        @trace_agent("my_agent", model="gpt-4o")
        def call_gpt(prompt: str):
            return openai.chat.completions.create(...)
        
        # 超过速率限制会自动等待
        for i in range(100):
            result = call_gpt(f"Prompt {i}")  # 自动速率控制
    
    Args:
        calls_per_minute: 每分钟最大调用次数
        calls_per_second: 每秒最大调用次数
    """
    
    limiter = RateLimiter(calls_per_minute, calls_per_second)
    
    def decorator(func: Callable) -> Callable:
        is_async = asyncio.iscoroutinefunction(func)
        
        if is_async:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                await limiter._wait_async()
                return await func(*args, **kwargs)
            
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                limiter._wait_sync()
                return func(*args, **kwargs)
            
            return sync_wrapper
    
    return decorator


# ==================== 组合装饰器 ====================


def traced_llm_call(
    agent_name: str,
    model: str,
    provider: str = "openai",
    api_url: Optional[str] = None,
    max_retry: int = 3,
    retry_delay: float = 1.0,
    rate_limit_per_minute: int = 60,
    rate_limit_per_second: int = 10,
    **trace_kwargs,
):
    """
    组合装饰器 - 同时应用追踪、重试和速率限制
    
    使用示例:
        @traced_llm_call(
            "my_agent",
            model="gpt-4o",
            max_retry=3,
            rate_limit_per_minute=60,
        )
        def call_gpt(prompt: str):
            return openai.chat.completions.create(...)
        
        # 自动追踪、重试和速率控制
        result = call_gpt("Hello")
    
    Args:
        agent_name: Agent 名称
        model: 使用的模型
        provider: 提供商
        api_url: AgentWatch API 地址
        max_retry: 最大重试次数
        retry_delay: 重试初始延迟
        rate_limit_per_minute: 每分钟最大调用次数
        rate_limit_per_second: 每秒最大调用次数
        trace_kwargs: 其他 trace 参数
    """
    
    def decorator(func: Callable) -> Callable:
        # 应用装饰器顺序: trace -> rate_limit -> retry
        # 这样 retry 在最外层，失败会重试整个流程
        decorated = trace_agent(
            agent_name, model, provider, api_url, **trace_kwargs
        )(func)
        
        if rate_limit_per_minute or rate_limit_per_second:
            decorated = with_rate_limit(
                calls_per_minute=rate_limit_per_minute,
                calls_per_second=rate_limit_per_second,
            )(decorated)
        
        if max_retry > 1:
            decorated = with_retry(
                max_attempts=max_retry,
                delay=retry_delay,
            )(decorated)
        
        return decorated
    
    return decorator


# ==================== 超时装饰器 ====================


class TimeoutError(Exception):
    """LLM 调用超时异常"""
    pass


def with_timeout(
    seconds: float = 30.0,
    on_timeout: Optional[Callable[[], Any]] = None,
):
    """
    超时装饰器 - 自动限制 LLM 调用的执行时间
    
    使用示例:
        @with_timeout(seconds=10.0)
        @trace_agent("my_agent", model="gpt-4o")
        def call_gpt(prompt: str):
            return openai.chat.completions.create(...)
        
        # 如果超过10秒，会抛出 TimeoutError
        try:
            result = call_gpt("Hello")
        except TimeoutError:
            print("LLM call timed out!")
    
    Args:
        seconds: 超时时间（秒）
        on_timeout: 超时时的回调函数，可以返回默认值
    
    Returns:
        装饰后的函数，超时时抛出 TimeoutError 或调用回调
    """
    
    def decorator(func: Callable) -> Callable:
        is_async = asyncio.iscoroutinefunction(func)
        
        if is_async:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                try:
                    return await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=seconds
                    )
                except asyncio.TimeoutError:
                    if on_timeout:
                        return on_timeout()
                    raise TimeoutError(
                        f"LLM call timed out after {seconds} seconds"
                    )
            
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                import threading
                import queue
                
                result_queue = queue.Queue()
                exception_queue = queue.Queue()
                
                def worker():
                    try:
                        result = func(*args, **kwargs)
                        result_queue.put(result)
                    except Exception as e:
                        exception_queue.put(e)
                
                thread = threading.Thread(target=worker)
                thread.start()
                thread.join(timeout=seconds)
                
                if thread.is_alive():
                    # Thread is still running, it timed out
                    if on_timeout:
                        return on_timeout()
                    raise TimeoutError(
                        f"LLM call timed out after {seconds} seconds"
                    )
                
                # Check for exceptions
                if not exception_queue.empty():
                    raise exception_queue.get()
                
                # Get result
                return result_queue.get()
            
            return sync_wrapper
    
    return decorator


# ==================== 缓存装饰器 ====================


class ResponseCache:
    """
    LLM 响应缓存
    
    用于缓存重复的 LLM 调用，节省成本和时间
    """
    
    def __init__(self, max_size: int = 1000, ttl_seconds: float = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: dict = {}
        self._timestamps: dict = {}
    
    def _hash_key(self, args: tuple, kwargs: dict) -> str:
        """生成缓存键"""
        import hashlib
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, args: tuple, kwargs: dict) -> Optional[Any]:
        """获取缓存"""
        import time
        key = self._hash_key(args, kwargs)
        
        if key in self._cache:
            # Check TTL
            if time.time() - self._timestamps[key] < self.ttl_seconds:
                return self._cache[key]
            else:
                # Expired, remove
                del self._cache[key]
                del self._timestamps[key]
        
        return None
    
    def set(self, args: tuple, kwargs: dict, result: Any) -> None:
        """设置缓存"""
        import time
        key = self._hash_key(args, kwargs)
        
        # Evict old entries if at max size
        if len(self._cache) >= self.max_size:
            oldest_key = min(self._timestamps.keys(), key=self._timestamps.get)
            del self._cache[oldest_key]
            del self._timestamps[oldest_key]
        
        self._cache[key] = result
        self._timestamps[key] = time.time()
    
    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
        self._timestamps.clear()
    
    def stats(self) -> dict:
        """获取缓存统计"""
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
        }


def with_cache(
    max_size: int = 1000,
    ttl_seconds: float = 3600,
    cache_key_func: Optional[Callable] = None,
):
    """
    缓存装饰器 - 缓存 LLM 响应，避免重复调用
    
    使用示例:
        @with_cache(max_size=100, ttl_seconds=300)
        @trace_agent("my_agent", model="gpt-4o")
        def call_gpt(prompt: str):
            return openai.chat.completions.create(...)
        
        # 第一次调用会执行
        result1 = call_gpt("What is AI?")
        
        # 5分钟内第二次相同调用会返回缓存
        result2 = call_gpt("What is AI?")  # 立即返回，不消耗 tokens
    
    Args:
        max_size: 最大缓存数量
        ttl_seconds: 缓存过期时间（秒）
        cache_key_func: 自定义缓存键生成函数
    
    Returns:
        装饰后的函数，支持缓存
    """
    
    cache = ResponseCache(max_size, ttl_seconds)
    
    def decorator(func: Callable) -> Callable:
        is_async = asyncio.iscoroutinefunction(func)
        
        if is_async:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                # Check cache
                cached = cache.get(args, kwargs)
                if cached is not None:
                    return cached
                
                # Execute and cache
                result = await func(*args, **kwargs)
                cache.set(args, kwargs, result)
                return result
            
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                # Check cache
                cached = cache.get(args, kwargs)
                if cached is not None:
                    return cached
                
                # Execute and cache
                result = func(*args, **kwargs)
                cache.set(args, kwargs, result)
                return result
            
            return sync_wrapper
    
    return decorator


# ==================== Fallback 装饰器 ====================


class FallbackError(Exception):
    """所有 fallback 尝试都失败时的异常"""
    pass


def with_fallback(
    fallbacks: List[Tuple[str, str, Callable]] = None,
    on_all_fail: Optional[Callable[[List[Exception]], Any]] = None,
):
    """
    Fallback 装饰器 - 自动切换到备用 provider/model 当主调用失败
    
    使用示例:
        # 定义 fallback 链
        @with_fallback([
            ("deepseek", "deepseek-chat", deepseek_call),
            ("anthropic", "claude-3-haiku", claude_call),
        ])
        def call_gpt(prompt: str):
            return openai.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            )
        
        # 如果 OpenAI 失败，自动尝试 DeepSeek，然后 Claude
        result = call_gpt("Hello")
        
        # 设置 fallback 处理函数
        def handle_all_fail(errors):
            return {"error": "All providers failed", "details": [str(e) for e in errors]}
        
        @with_fallback(
            fallbacks=[("deepseek", "deepseek-chat", deepseek_call)],
            on_all_fail=handle_all_fail
        )
        def call_gpt(prompt):
            return openai.chat.completions.create(...)
    
    Args:
        fallbacks: Fallback 链列表，每项为 (provider, model, call_function)
        on_all_fail: 所有 fallback 都失败时的回调函数，接收异常列表
    
    Returns:
        装饰后的函数，失败时自动 fallback
    """
    
    def decorator(func: Callable) -> Callable:
        is_async = asyncio.iscoroutinefunction(func)
        
        if is_async:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                errors: List[Exception] = []
                
                # 尝试主函数
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    errors.append(e)
                
                # 尝试 fallbacks
                for provider, model, fallback_func in (fallbacks or []):
                    try:
                        if asyncio.iscoroutinefunction(fallback_func):
                            return await fallback_func(*args, **kwargs)
                        else:
                            return fallback_func(*args, **kwargs)
                    except Exception as e:
                        errors.append(e)
                
                # 所有都失败
                if on_all_fail:
                    return on_all_fail(errors)
                raise FallbackError(
                    f"All providers failed: {[str(e) for e in errors]}"
                )
            
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                errors: List[Exception] = []
                
                # 尝试主函数
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    errors.append(e)
                
                # 尝试 fallbacks
                for provider, model, fallback_func in (fallbacks or []):
                    try:
                        return fallback_func(*args, **kwargs)
                    except Exception as e:
                        errors.append(e)
                
                # 所有都失败
                if on_all_fail:
                    return on_all_fail(errors)
                raise FallbackError(
                    f"All providers failed: {[str(e) for e in errors]}"
                )
            
            return sync_wrapper
    
    return decorator


# ==================== Circuit Breaker 装饰器 ====================


class CircuitState:
    """Circuit Breaker 状态"""
    CLOSED = "closed"  # 正常状态，允许调用
    OPEN = "open"      # 禁止状态，拒绝调用
    HALF_OPEN = "half_open"  # 半开状态，允许少量调用探测


class CircuitBreaker:
    """
    Circuit Breaker - 防止对失败的 provider 进行持续调用
    
    当 provider 连续失败达到阈值时，自动"断开"，一段时间后尝试恢复。
    
    使用示例:
        breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
        )
        
        @breaker.decorate
        def call_gpt(prompt: str):
            return openai.chat.completions.create(...)
        
        # 如果连续失败5次，breaker 进入 OPEN 状态
        # 60秒后进入 HALF_OPEN，允许一次探测调用
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 1,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
        self._lock = None
    
    def _get_lock(self):
        """获取或创建锁（延迟初始化）"""
        if self._lock is None:
            try:
                if asyncio.get_event_loop().is_running():
                    self._lock = asyncio.Lock()
            except RuntimeError:
                pass
        return self._lock
    
    @property
    def state(self) -> str:
        """当前状态"""
        import time
        if self._state == CircuitState.OPEN:
            # 检查是否应该进入 HALF_OPEN
            if self._last_failure_time and \
               time.time() - self._last_failure_time >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
        return self._state
    
    def _record_success(self):
        """记录成功调用"""
        self._failure_count = 0
        self._state = CircuitState.CLOSED
        self._half_open_calls = 0
    
    def _record_failure(self):
        """记录失败调用"""
        import time
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        if self._state == CircuitState.HALF_OPEN:
            # HALF_OPEN 状态失败，回到 OPEN
            self._state = CircuitState.OPEN
        elif self._failure_count >= self.failure_threshold:
            # 达到阈值，进入 OPEN
            self._state = CircuitState.OPEN
    
    def _can_execute(self) -> bool:
        """检查是否允许执行"""
        state = self.state
        
        if state == CircuitState.CLOSED:
            return True
        
        if state == CircuitState.HALF_OPEN:
            if self._half_open_calls < self.half_open_max_calls:
                self._half_open_calls += 1
                return True
            return False
        
        # OPEN 状态不允许
        return False
    
    def decorate(self, func: Callable) -> Callable:
        """装饰函数"""
        is_async = asyncio.iscoroutinefunction(func)
        
        if is_async:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                if not self._can_execute():
                    raise FallbackError(
                        f"Circuit breaker is {self.state}, refusing call"
                    )
                
                try:
                    result = await func(*args, **kwargs)
                    self._record_success()
                    return result
                except Exception as e:
                    self._record_failure()
                    raise
            
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                if not self._can_execute():
                    raise FallbackError(
                        f"Circuit breaker is {self.state}, refusing call"
                    )
                
                try:
                    result = func(*args, **kwargs)
                    self._record_success()
                    return result
                except Exception as e:
                    self._record_failure()
                    raise
            
            return sync_wrapper


# ==================== 导出所有装饰器 ====================

__all__ = [
    "trace_agent",
    "trace_openai_call",
    "trace_anthropic_call",
    "trace_deepseek_call",
    "trace_gemini_call",
    "trace_streaming",
    "StreamingTraceWrapper",
    "TracedAgent",
    "AsyncTracedAgent",
    "quick_trace",
    "async_quick_trace",
    "with_retry",
    "with_rate_limit",
    "RateLimiter",
    "traced_llm_call",
    "with_timeout",
    "TimeoutError",
    "with_cache",
    "ResponseCache",
    "with_fallback",
    "FallbackError",
    "CircuitBreaker",
    "CircuitState",
]