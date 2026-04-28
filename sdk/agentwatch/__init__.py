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

__version__ = "0.2.0"

from .client import AgentWatch, TraceContext
from .decorators import trace_agent
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
    "trace_agent",
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
