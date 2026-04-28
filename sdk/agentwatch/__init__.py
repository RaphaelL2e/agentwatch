"""
AgentWatch SDK
AI Agent 监控 Python 客户端库

使用方式:
    from agentwatch import AgentWatch
    
    aw = AgentWatch(api_key="your_key")
    
    # 自动追踪
    with aw.trace("my_agent", model="gpt-4o"):
        response = openai.chat.completions.create(...)
"""

__version__ = "0.6.0"

from .client import AgentWatch, TraceContext
from .decorators import (
    trace_agent,
    trace_openai_call,
    trace_anthropic_call,
    trace_deepseek_call,
    trace_gemini_call,
    trace_streaming,
    StreamingTraceWrapper,
    TracedAgent,
    AsyncTracedAgent,
    quick_trace,
    async_quick_trace,
    with_retry,
    with_rate_limit,
    RateLimiter,
    traced_llm_call,
    with_timeout,
    TimeoutError as DecoratorTimeoutError,
    with_cache,
    ResponseCache,
    with_fallback,
    FallbackError,
    CircuitBreaker,
    CircuitState,
)
from .exceptions import (
    AgentWatchError,
    ConnectionError,
    AuthenticationError,
    APIError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ConfigurationError,
    TraceError,
    TraceNotFoundError,
    TraceAlreadyExistsError,
    TraceValidationError,
    is_retryable_error,
    get_retry_delay,
)

__all__ = [
    "AgentWatch",
    "TraceContext",
    # Core decorators
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
    # Utility decorators
    "with_retry",
    "with_rate_limit",
    "RateLimiter",
    "traced_llm_call",
    "with_timeout",
    "DecoratorTimeoutError",
    "with_cache",
    "ResponseCache",
    "with_fallback",
    "FallbackError",
    "CircuitBreaker",
    "CircuitState",
    # 异常类
    "AgentWatchError",
    "ConnectionError",
    "AuthenticationError",
    "APIError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "ServerError",
    "TimeoutError",
    "ConfigurationError",
    "TraceError",
    "TraceNotFoundError",
    "TraceAlreadyExistsError",
    "TraceValidationError",
    # 辅助函数
    "is_retryable_error",
    "get_retry_delay",
]
