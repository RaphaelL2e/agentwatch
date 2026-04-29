"""
AgentWatch 认证数据模型
用户、API Key、Token 相关模型
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import re
import secrets


class UserRole(str, Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class APIKeyScope(str, Enum):
    """API Key 权限范围"""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class PlanType(str, Enum):
    """订阅计划类型"""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class UserCreate(BaseModel):
    """用户注册请求"""
    email: str = Field(..., description="用户邮箱")
    password: str = Field(..., min_length=8, max_length=64, description="密码(8-64字符)")
    name: Optional[str] = Field(None, max_length=50, description="用户名称")
    organization: Optional[str] = Field(None, max_length=100, description="组织名称")
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """邮箱格式验证"""
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", v):
            raise ValueError("Invalid email format")
        return v.lower()
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """密码复杂度验证"""
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("密码必须包含字母")
        if not re.search(r"\d", v):
            raise ValueError("密码必须包含数字")
        return v


class UserLogin(BaseModel):
    """用户登录请求"""
    email: str = Field(..., description="用户邮箱")
    password: str = Field(..., description="密码")
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """邮箱格式验证"""
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", v):
            raise ValueError("Invalid email format")
        return v.lower()


class UserResponse(BaseModel):
    """用户信息响应"""
    user_id: str = Field(..., description="用户ID")
    email: str = Field(..., description="用户邮箱")
    name: Optional[str] = None
    organization: Optional[str] = None
    role: UserRole = Field(default=UserRole.MEMBER)
    plan: PlanType = Field(default=PlanType.FREE)
    tenant_id: str = Field(..., description="租户ID")
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = Field(default=True)
    api_keys_count: int = Field(default=0)


class APIKeyCreate(BaseModel):
    """创建 API Key 请求"""
    name: str = Field(..., max_length=50, description="API Key 名称")
    scope: List[APIKeyScope] = Field(default=[APIKeyScope.READ], description="权限范围")
    rate_limit: int = Field(default=100, ge=10, le=1000, description="每分钟请求限制")
    expires_at: Optional[datetime] = Field(None, description="过期时间(可选)")
    description: Optional[str] = Field(None, max_length=200, description="描述")


class APIKeyResponse(BaseModel):
    """API Key 响应"""
    key_id: str = Field(..., description="Key ID")
    name: str = Field(..., description="API Key 名称")
    full_key: Optional[str] = Field(None, description="完整API Key(仅创建时返回)")
    scope: List[APIKeyScope]
    rate_limit: int
    tenant_id: str
    created_by: str = Field(..., description="创建者用户ID")
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    usage_count: int = Field(default=0)
    is_active: bool = Field(default=True)
    description: Optional[str] = None


class TokenResponse(BaseModel):
    """Token 响应"""
    access_token: str = Field(..., description="JWT访问令牌")
    refresh_token: Optional[str] = Field(None, description="刷新令牌")
    token_type: str = Field(default="bearer")
    expires_in: int = Field(default=3600, description="过期时间(秒)")
    user: UserResponse


class APIKeyValidation(BaseModel):
    """API Key 验证结果"""
    is_valid: bool
    tenant_id: Optional[str] = None
    key_id: Optional[str] = None
    scope: Optional[List[APIKeyScope]] = None
    rate_limit: Optional[int] = None
    error_message: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """刷新Token请求"""
    refresh_token: str = Field(..., description="刷新令牌")


class PasswordChange(BaseModel):
    """密码修改请求"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=8, description="新密码")


class UserProfileUpdate(BaseModel):
    """用户信息更新请求"""
    name: Optional[str] = Field(None, max_length=50)
    organization: Optional[str] = Field(None, max_length=100)


class LogoutRequest(BaseModel):
    """注销请求"""
    refresh_token: Optional[str] = Field(None, description="刷新令牌(可选)")


def generate_api_key(tenant_id: str, key_id: str) -> str:
    """生成完整的 API Key"""
    secret = secrets.token_hex(16)
    return f"aw_{tenant_id}_{key_id}_{secret}"


def parse_api_key(api_key: str) -> Dict[str, str]:
    """解析 API Key
    
    格式: aw_t_xxxxxxxx_k_yyyyyyyy_secret
    - aw_ 前缀
    - t_xxxxxxxx = tenant_id (10 chars)
    - _k_ 分隔符
    - yyyyyyyy = key_id 的 hex 部分 (8 chars)
    - _ 分隔符
    - secret = 32 chars
    """
    if not api_key or not api_key.startswith("aw_"):
        return {}
    
    # 格式验证：总长度应为 57 chars (3 + 10 + 3 + 8 + 1 + 32)
    # aw_t_99b20935_k_021af92b_aa1a58fb2db04f8c18575b0d09db52af
    # = 3 + 10 + 3 + 8 + 1 + 32 = 57
    
    if len(api_key) < 50:  # 最短长度
        return {}
    
    # 去掉 aw_ 前缀
    rest = api_key[3:]
    
    # tenant_id: t_ + 8 hex chars
    if not rest.startswith("t_"):
        return {}
    
    tenant_id = rest[:10]  # t_99b20935
    
    # 检查分隔符 _k_
    if rest[10:13] != "_k_":
        return {}
    
    # key_id_hex: 8 chars
    key_id_hex = rest[13:21]  # 021af92b
    key_id = "k_" + key_id_hex  # k_021af92b
    
    # 检查分隔符 _
    if rest[21] != "_":
        return {}
    
    # secret: 剩下的部分
    secret = rest[22:]
    
    if len(secret) < 16:  # secret 应至少 16 字符
        return {}
    
    return {
        "tenant_id": tenant_id,
        "key_id": key_id,
        "secret": secret
    }
