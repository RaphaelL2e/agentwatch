"""
AgentWatch 认证模块
JWT + API Key 双认证模式
"""

from .models import (
    UserCreate,
    UserResponse,
    UserLogin,
    APIKeyCreate,
    APIKeyResponse,
    TokenResponse,
    UserRole,
    APIKeyScope,
)
from .jwt import create_access_token, verify_token, create_refresh_token
from .service import AuthService
from .middleware import verify_api_key, get_current_user

__all__ = [
    "UserCreate",
    "UserResponse",
    "UserLogin",
    "APIKeyCreate",
    "APIKeyResponse",
    "TokenResponse",
    "UserRole",
    "APIKeyScope",
    "create_access_token",
    "verify_token",
    "create_refresh_token",
    "AuthService",
    "verify_api_key",
    "get_current_user",
]