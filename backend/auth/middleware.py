"""
AgentWatch 认证中间件
API Key 验证 + JWT Token 验证
"""

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
from functools import wraps

from .service import AuthService
from .models import APIKeyValidation, APIKeyScope, UserResponse
from .jwt import verify_token


# HTTP Bearer 认证方案
security = HTTPBearer(auto_error=False)


async def verify_api_key(request: Request) -> Dict[str, Any]:
    """验证 API Key 中间件
    
    从请求头 X-API-Key 或 Authorization Bearer 中获取 API Key
    
    Args:
        request: FastAPI Request
    
    Returns:
        验证结果 {"tenant_id": "...", "key_id": "...", "scope": [...]}
    
    Raises:
        HTTPException: 401 Unauthorized
    """
    # 尝试从 X-API-Key 头获取
    api_key = request.headers.get("X-API-Key")
    
    # 尝试从 Authorization Bearer 获取
    if not api_key:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer aw_"):
            api_key = auth_header[7:]  # 去掉 "Bearer "
    
    # 尝试从查询参数获取
    if not api_key:
        api_key = request.query_params.get("api_key")
    
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API Key required. Provide via X-API-Key header or Authorization Bearer"
        )
    
    # 验证
    validation = AuthService.validate_api_key(api_key)
    
    if not validation.is_valid:
        raise HTTPException(
            status_code=401,
            detail=validation.error_message or "Invalid API Key"
        )
    
    # 存储验证结果到请求状态
    request.state.api_key_validation = validation
    
    return {
        "tenant_id": validation.tenant_id,
        "key_id": validation.key_id,
        "scope": validation.scope,
        "rate_limit": validation.rate_limit,
    }


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> UserResponse:
    """获取当前用户（JWT Token验证）
    
    用于 Dashboard 等 Web 界面的认证
    
    Args:
        credentials: HTTP Bearer credentials
    
    Returns:
        UserResponse
    
    Raises:
        HTTPException: 401 Unauthorized
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authorization token required"
        )
    
    token = credentials.credentials
    
    # 验证JWT
    payload = verify_token(token, token_type="access")
    
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload"
        )
    
    # 获取用户
    user = AuthService.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="User account is disabled"
        )
    
    return user


def require_scope(required_scope: APIKeyScope):
    """权限范围检查装饰器
    
    Args:
        required_scope: 需要的权限范围
    
    Usage:
        @require_scope(APIKeyScope.WRITE)
        async def create_trace(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从kwargs或request获取验证结果
            request = kwargs.get("request")
            if request and hasattr(request.state, "api_key_validation"):
                validation = request.state.api_key_validation
                if validation.scope and required_scope in validation.scope:
                    return await func(*args, **kwargs)
            
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied. Required scope: {required_scope}"
            )
        
        return wrapper
    
    return decorator


async def optional_auth(request: Request) -> Optional[Dict[str, Any]]:
    """可选认证（不强制要求）
    
    如果提供了API Key则验证，否则返回None
    """
    api_key = request.headers.get("X-API-Key")
    
    if not api_key:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer aw_"):
            api_key = auth_header[7:]
    
    if not api_key:
        return None
    
    validation = AuthService.validate_api_key(api_key)
    
    if validation.is_valid:
        return {
            "tenant_id": validation.tenant_id,
            "key_id": validation.key_id,
            "scope": validation.scope,
        }
    
    return None


class RateLimiter:
    """API Key 速率限制器
    
    生产环境应使用 Redis 实现
    """
    
    _usage: Dict[str, Dict[str, int]] = {}  # {key_id: {minute: count}}
    
    @classmethod
    def check_rate_limit(cls, key_id: str, rate_limit: int) -> bool:
        """检查速率限制
        
        Args:
            key_id: API Key ID
            rate_limit: 每分钟限制
        
        Returns:
            True: 允许请求
            False: 超过限制
        """
        current_minute = datetime.utcnow().strftime("%Y%m%d%H%M")
        
        if key_id not in cls._usage:
            cls._usage[key_id] = {}
        
        usage = cls._usage[key_id].get(current_minute, 0)
        
        if usage >= rate_limit:
            return False
        
        cls._usage[key_id][current_minute] = usage + 1
        return True
    
    @classmethod
    def get_remaining(cls, key_id: str, rate_limit: int) -> int:
        """获取剩余请求次数"""
        current_minute = datetime.utcnow().strftime("%Y%m%d%H%M")
        usage = cls._usage.get(key_id, {}).get(current_minute, 0)
        return max(0, rate_limit - usage)


async def rate_limit_check(request: Request) -> None:
    """速率限制检查中间件"""
    validation = getattr(request.state, "api_key_validation", None)
    
    if validation and validation.key_id and validation.rate_limit:
        if not RateLimiter.check_rate_limit(validation.key_id, validation.rate_limit):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Try again later."
            )


from datetime import datetime  # 添加缺失的导入