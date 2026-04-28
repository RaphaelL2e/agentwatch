"""
AgentWatch SDK 异常处理模块

异常层次结构:
    AgentWatchError (基类)
    ├── ConnectionError (网络连接问题)
    ├── AuthenticationError (认证失败)
    ├── APIError (API 返回错误)
    │   ├── NotFoundError (404)
    │   ├── ValidationError (400)
    │   ├── RateLimitError (429)
    │   └── ServerError (5xx)
    ├── TimeoutError (超时)
    ├── ConfigurationError (配置问题)
    └── TraceError (Trace 操作问题)
        ├── TraceNotFoundError
        ├── TraceAlreadyExistsError
        ├── TraceValidationError
"""

from typing import Optional, Dict, Any


class AgentWatchError(Exception):
    """
    AgentWatch SDK 基类异常
    
    所有 AgentWatch 异常都继承此类。
    提供统一的错误消息格式和上下文信息。
    """
    
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ):
        self.message = message
        self.code = code or "UNKNOWN"
        self.details = details or {}
        self.request_id = request_id
        
        # 构建完整消息
        full_message = f"[{self.code}] {message}"
        if request_id:
            full_message += f" (request_id: {request_id})"
        if details:
            full_message += f" | Details: {details}"
        
        super().__init__(full_message)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，用于 API 响应或日志"""
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details,
            "request_id": self.request_id,
        }


# ==================== 连接相关异常 ====================

class ConnectionError(AgentWatchError):
    """
    网络连接问题
    
    可能原因：
    - 网络不可达
    - DNS 解析失败
    - 服务器宕机
    - 代理配置错误
    
    建议：检查网络连接、API URL 配置
    """
    
    def __init__(
        self,
        message: str = "Failed to connect to AgentWatch server",
        api_url: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if api_url:
            details["api_url"] = api_url
        
        super().__init__(
            message=message,
            code="CONNECTION_ERROR",
            details=details,
            **kwargs
        )


class AuthenticationError(AgentWatchError):
    """
    认证失败
    
    可能原因：
    - API Key 无效或过期
    - API Key 未配置
    - 权限不足
    
    建议：检查 API Key 配置、确认账户状态
    """
    
    def __init__(
        self,
        message: str = "Authentication failed",
        api_key_hint: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if api_key_hint:
            details["api_key_hint"] = api_key_hint
        
        super().__init__(
            message=message,
            code="AUTH_ERROR",
            details=details,
            **kwargs
        )


# ==================== API 相关异常 ====================

class APIError(AgentWatchError):
    """
    API 返回错误
    
    基类，所有 API 返回的错误都继承此类。
    """
    
    def __init__(
        self,
        message: str,
        status_code: int,
        response_body: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        details["status_code"] = status_code
        if response_body:
            details["response_body"] = response_body[:500]  # 截断
        
        super().__init__(
            message=message,
            code="API_ERROR",
            details=details,
            **kwargs
        )
        self.status_code = status_code


class NotFoundError(APIError):
    """
    404 Not Found
    
    资源不存在：Trace、Agent、Config 等
    """
    
    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        **kwargs
    ):
        message = f"{resource_type} not found: {resource_id}"
        kwargs.setdefault("status_code", 404)
        
        super().__init__(message=message, **kwargs)
        self.code = "NOT_FOUND"
        self.resource_type = resource_type
        self.resource_id = resource_id


class ValidationError(APIError):
    """
    400 Bad Request - 参数验证失败
    
    可能原因：
    - 缺少必填字段
    - 字段类型错误
    - 字段值不合法
    """
    
    def __init__(
        self,
        message: str = "Validation failed",
        field_errors: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        kwargs.setdefault("status_code", 400)
        details = kwargs.pop("details", {})
        if field_errors:
            details["field_errors"] = field_errors
        
        super().__init__(message=message, details=details, **kwargs)
        self.code = "VALIDATION_ERROR"
        self.field_errors = field_errors


class RateLimitError(APIError):
    """
    429 Too Many Requests - 请求频率超限
    
    建议：
    - 减少请求频率
    - 使用批量操作
    - 添加请求间隔
    """
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        **kwargs
    ):
        kwargs.setdefault("status_code", 429)
        details = kwargs.pop("details", {})
        if retry_after:
            details["retry_after_seconds"] = retry_after
        
        super().__init__(message=message, details=details, **kwargs)
        self.code = "RATE_LIMIT"
        self.retry_after = retry_after


class ServerError(APIError):
    """
    5xx Server Error - 服务器内部错误
    
    建议：稍后重试，或联系支持
    """
    
    def __init__(
        self,
        message: str = "Server error",
        **kwargs
    ):
        status_code = kwargs.pop("status_code", 500)
        super().__init__(message=message, status_code=status_code, **kwargs)
        self.code = "SERVER_ERROR"


# ==================== 超时相关异常 ====================

class TimeoutError(AgentWatchError):
    """
    超时错误
    
    可能原因：
    - 网络延迟过高
    - API 响应慢
    - 超时配置过短
    
    建议：增加超时时间、检查网络状况
    """
    
    def __init__(
        self,
        message: str = "Request timeout",
        timeout_seconds: Optional[float] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if timeout_seconds:
            details["timeout_seconds"] = timeout_seconds
        if operation:
            details["operation"] = operation
        
        super().__init__(
            message=message,
            code="TIMEOUT",
            details=details,
            **kwargs
        )
        self.timeout_seconds = timeout_seconds


# ==================== 配置相关异常 ====================

class ConfigurationError(AgentWatchError):
    """
    配置问题
    
    可能原因：
    - 缺少必要配置
    - 配置值不合法
    - 配置文件读取失败
    
    建议：检查配置文件、环境变量
    """
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if config_key:
            details["config_key"] = config_key
        if config_value:
            details["config_value"] = config_value
        
        super().__init__(
            message=message,
            code="CONFIG_ERROR",
            details=details,
            **kwargs
        )


# ==================== Trace 相关异常 ====================

class TraceError(AgentWatchError):
    """
    Trace 操作问题基类
    """
    
    def __init__(
        self,
        message: str,
        trace_id: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if trace_id:
            details["trace_id"] = trace_id
        
        super().__init__(
            message=message,
            code="TRACE_ERROR",
            details=details,
            **kwargs
        )
        self.trace_id = trace_id


class TraceNotFoundError(TraceError):
    """
    Trace 不存在
    """
    
    def __init__(self, trace_id: str, **kwargs):
        message = f"Trace not found: {trace_id}"
        super().__init__(message=message, trace_id=trace_id, **kwargs)
        self.code = "TRACE_NOT_FOUND"


class TraceAlreadyExistsError(TraceError):
    """
    Trace 已存在（创建重复 ID）
    """
    
    def __init__(self, trace_id: str, **kwargs):
        message = f"Trace already exists: {trace_id}"
        super().__init__(message=message, trace_id=trace_id, **kwargs)
        self.code = "TRACE_EXISTS"


class TraceValidationError(TraceError):
    """
    Trace 数据验证失败
    """
    
    def __init__(
        self,
        trace_id: str,
        validation_errors: Dict[str, str],
        **kwargs
    ):
        message = f"Trace validation failed: {trace_id}"
        details = kwargs.pop("details", {})
        details["validation_errors"] = validation_errors
        
        super().__init__(
            message=message,
            trace_id=trace_id,
            details=details,
            **kwargs
        )
        self.code = "TRACE_VALIDATION"
        self.validation_errors = validation_errors


# ==================== 辅助函数 ====================

def is_retryable_error(error: AgentWatchError) -> bool:
    """
    判断错误是否可重试
    
    可重试的错误：
    - ConnectionError
    - TimeoutError  
    - RateLimitError
    - ServerError (5xx)
    
    不可重试的错误：
    - AuthenticationError
    - NotFoundError
    - ValidationError
    - ConfigurationError
    """
    if isinstance(error, (ConnectionError, TimeoutError)):
        return True
    
    if isinstance(error, RateLimitError):
        return True
    
    if isinstance(error, ServerError):
        return True
    
    return False


def get_retry_delay(error: AgentWatchError) -> float:
    """
    获取建议的重试延迟（秒）
    
    - RateLimitError: 使用 retry_after
    - 其他可重试错误: 指数退避建议
    """
    if isinstance(error, RateLimitError) and error.retry_after:
        return error.retry_after
    
    # 默认指数退避建议
    return 1.0


def format_error_for_user(error: AgentWatchError) -> str:
    """
    格式化错误消息给用户
    
    提供友好、可操作的错误提示
    """
    error_type = type(error).__name__
    
    suggestions = {
        "ConnectionError": "检查 API URL 配置和网络连接",
        "AuthenticationError": "检查 API Key 是否正确配置",
        "TimeoutError": "增加超时时间或检查网络状况",
        "RateLimitError": "减少请求频率或等待后重试",
        "NotFoundError": "确认资源 ID 是否正确",
        "ValidationError": "检查请求参数是否符合要求",
        "ServerError": "稍后重试，如持续出现请联系支持",
        "ConfigurationError": "检查配置文件和环境变量",
    }
    
    suggestion = suggestions.get(error_type, "请检查错误详情")
    
    return f"""
❌ AgentWatch Error: {error_type}
{error.message}

💡 建议: {suggestion}

详情: {error.details}
"""


# 导出所有异常
__all__ = [
    # 基类
    "AgentWatchError",
    # 连接相关
    "ConnectionError",
    "AuthenticationError",
    # API 相关
    "APIError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "ServerError",
    # 超时
    "TimeoutError",
    # 配置
    "ConfigurationError",
    # Trace 相关
    "TraceError",
    "TraceNotFoundError",
    "TraceAlreadyExistsError",
    "TraceValidationError",
    # 辅助函数
    "is_retryable_error",
    "get_retry_delay",
    "format_error_for_user",
]