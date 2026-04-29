"""
AgentWatch 认证服务
用户注册、登录、API Key 管理
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import uuid
import secrets

from .models import (
    UserCreate,
    UserResponse,
    UserLogin,
    APIKeyCreate,
    APIKeyResponse,
    TokenResponse,
    UserRole,
    APIKeyScope,
    PlanType,
    APIKeyValidation,
    generate_api_key,
    parse_api_key,
)
from .jwt import (
    hash_password,
    verify_password,
    create_token_pair,
    verify_token,
)


@dataclass
class User:
    """内部用户数据结构"""
    user_id: str
    email: str
    password_hash: str
    name: Optional[str] = None
    organization: Optional[str] = None
    role: UserRole = UserRole.MEMBER
    plan: PlanType = PlanType.FREE
    tenant_id: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    is_active: bool = True


@dataclass
class APIKey:
    """内部 API Key 数据结构"""
    key_id: str
    tenant_id: str
    name: str
    secret_hash: str  # 存储secret的hash，不存储完整key
    scope: List[APIKeyScope] = field(default_factory=lambda: [APIKeyScope.READ])
    rate_limit: int = 100
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    usage_count: int = 0
    is_active: bool = True
    description: Optional[str] = None


class AuthService:
    """认证服务类
    
    处理用户和API Key的CRUD操作
    当前使用内存存储，生产环境应替换为数据库
    """
    
    # 内存存储
    _users: Dict[str, User] = {}
    _api_keys: Dict[str, APIKey] = {}
    _email_to_user: Dict[str, str] = {}  # email -> user_id mapping
    _tenant_api_keys: Dict[str, List[str]] = {}  # tenant_id -> key_ids
    
    @classmethod
    def register_user(cls, user_data: UserCreate) -> UserResponse:
        """用户注册
        
        Args:
            user_data: 注册数据
        
        Returns:
            UserResponse
        
        Raises:
            ValueError: 邮箱已存在
        """
        # 检查邮箱是否已注册
        if user_data.email in cls._email_to_user:
            raise ValueError(f"Email {user_data.email} already registered")
        
        # 生成ID
        user_id = f"u_{uuid.uuid4().hex[:12]}"
        tenant_id = f"t_{uuid.uuid4().hex[:8]}"
        
        # 创建用户
        user = User(
            user_id=user_id,
            email=user_data.email,
            password_hash=hash_password(user_data.password),
            name=user_data.name,
            organization=user_data.organization,
            tenant_id=tenant_id,
            role=UserRole.ADMIN,  # 注册用户默认为admin
        )
        
        # 存储
        cls._users[user_id] = user
        cls._email_to_user[user_data.email] = user_id
        
        return UserResponse(
            user_id=user.user_id,
            email=user.email,
            name=user.name,
            organization=user.organization,
            role=user.role,
            plan=user.plan,
            tenant_id=user.tenant_id,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
    
    @classmethod
    def login_user(cls, login_data: UserLogin) -> TokenResponse:
        """用户登录
        
        Args:
            login_data: 登录数据
        
        Returns:
            TokenResponse with JWT
        
        Raises:
            ValueError: 验证失败
        """
        # 查找用户
        user_id = cls._email_to_user.get(login_data.email)
        if not user_id:
            raise ValueError("Invalid email or password")
        
        user = cls._users.get(user_id)
        if not user:
            raise ValueError("Invalid email or password")
        
        # 检查是否活跃
        if not user.is_active:
            raise ValueError("User account is disabled")
        
        # 验证密码
        if not verify_password(login_data.password, user.password_hash):
            raise ValueError("Invalid email or password")
        
        # 更新登录时间
        user.last_login = datetime.utcnow()
        user.updated_at = datetime.utcnow()
        
        # 生成Token
        tokens = create_token_pair(
            user_id=user.user_id,
            email=user.email,
            tenant_id=user.tenant_id,
            role=user.role.value,
        )
        
        # 统计API Key数量
        api_keys_count = len(cls._tenant_api_keys.get(user.tenant_id, []))
        
        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            expires_in=tokens["expires_in"],
            user=UserResponse(
                user_id=user.user_id,
                email=user.email,
                name=user.name,
                organization=user.organization,
                role=user.role,
                plan=user.plan,
                tenant_id=user.tenant_id,
                created_at=user.created_at,
                updated_at=user.updated_at,
                last_login=user.last_login,
                api_keys_count=api_keys_count,
            )
        )
    
    @classmethod
    def create_api_key(cls, tenant_id: str, user_id: str, key_data: APIKeyCreate) -> APIKeyResponse:
        """创建 API Key
        
        Args:
            tenant_id: 租户ID
            user_id: 创建者ID
            key_data: API Key数据
        
        Returns:
            APIKeyResponse (包含完整key，仅此一次)
        """
        # 生成Key ID
        key_id = f"k_{uuid.uuid4().hex[:8]}"
        
        # 生成完整API Key
        full_api_key = generate_api_key(tenant_id, key_id)
        
        # 解析获取secret
        parsed = parse_api_key(full_api_key)
        secret = parsed.get("secret", "")
        
        # 创建API Key记录
        api_key = APIKey(
            key_id=key_id,
            tenant_id=tenant_id,
            name=key_data.name,
            secret_hash=hash_password(secret),  # 存储secret的hash
            scope=key_data.scope,
            rate_limit=key_data.rate_limit,
            created_by=user_id,
            expires_at=key_data.expires_at,
            description=key_data.description,
        )
        
        # 存储
        cls._api_keys[key_id] = api_key
        
        if tenant_id not in cls._tenant_api_keys:
            cls._tenant_api_keys[tenant_id] = []
        cls._tenant_api_keys[tenant_id].append(key_id)
        
        return APIKeyResponse(
            key_id=key_id,
            name=api_key.name,
            api_key=full_api_key,  # 仅创建时返回完整key
            scope=api_key.scope,
            rate_limit=api_key.rate_limit,
            tenant_id=api_key.tenant_id,
            created_by=api_key.created_by,
            created_at=api_key.created_at,
            expires_at=api_key.expires_at,
            description=api_key.description,
        )
    
    @classmethod
    def list_api_keys(cls, tenant_id: str) -> List[APIKeyResponse]:
        """列出租户的所有API Key"""
        key_ids = cls._tenant_api_keys.get(tenant_id, [])
        keys = []
        
        for key_id in key_ids:
            api_key = cls._api_keys.get(key_id)
            if api_key:
                keys.append(APIKeyResponse(
                    key_id=api_key.key_id,
                    name=api_key.name,
                    api_key=None,  # 列表不返回完整key
                    scope=api_key.scope,
                    rate_limit=api_key.rate_limit,
                    tenant_id=api_key.tenant_id,
                    created_by=api_key.created_by,
                    created_at=api_key.created_at,
                    expires_at=api_key.expires_at,
                    last_used=api_key.last_used,
                    usage_count=api_key.usage_count,
                    is_active=api_key.is_active,
                    description=api_key.description,
                ))
        
        return keys
    
    @classmethod
    def validate_api_key(cls, api_key_str: str) -> APIKeyValidation:
        """验证 API Key
        
        Args:
            api_key_str: 完整的API Key字符串
        
        Returns:
            APIKeyValidation
        """
        # 解析格式
        parsed = parse_api_key(api_key_str)
        if not parsed:
            return APIKeyValidation(
                is_valid=False,
                error_message="Invalid API Key format"
            )
        
        tenant_id = parsed["tenant_id"]
        key_id = parsed["key_id"]
        secret = parsed["secret"]
        
        # 查找API Key记录
        api_key = cls._api_keys.get(key_id)
        if not api_key:
            return APIKeyValidation(
                is_valid=False,
                error_message="API Key not found"
            )
        
        # 检查租户ID匹配
        if api_key.tenant_id != tenant_id:
            return APIKeyValidation(
                is_valid=False,
                error_message="Tenant ID mismatch"
            )
        
        # 检查是否活跃
        if not api_key.is_active:
            return APIKeyValidation(
                is_valid=False,
                error_message="API Key is disabled"
            )
        
        # 检查过期
        if api_key.expires_at and datetime.utcnow() > api_key.expires_at:
            return APIKeyValidation(
                is_valid=False,
                error_message="API Key has expired"
            )
        
        # 验证secret
        if not verify_password(secret, api_key.secret_hash):
            return APIKeyValidation(
                is_valid=False,
                error_message="Invalid API Key secret"
            )
        
        # 更新使用记录
        api_key.last_used = datetime.utcnow()
        api_key.usage_count += 1
        
        return APIKeyValidation(
            is_valid=True,
            tenant_id=tenant_id,
            key_id=key_id,
            scope=api_key.scope,
            rate_limit=api_key.rate_limit,
        )
    
    @classmethod
    def revoke_api_key(cls, tenant_id: str, key_id: str) -> bool:
        """撤销 API Key"""
        api_key = cls._api_keys.get(key_id)
        if api_key and api_key.tenant_id == tenant_id:
            api_key.is_active = False
            api_key.updated_at = datetime.utcnow()
            return True
        return False
    
    @classmethod
    def get_user_by_id(cls, user_id: str) -> Optional[UserResponse]:
        """根据ID获取用户"""
        user = cls._users.get(user_id)
        if user:
            api_keys_count = len(cls._tenant_api_keys.get(user.tenant_id, []))
            return UserResponse(
                user_id=user.user_id,
                email=user.email,
                name=user.name,
                organization=user.organization,
                role=user.role,
                plan=user.plan,
                tenant_id=user.tenant_id,
                created_at=user.created_at,
                updated_at=user.updated_at,
                last_login=user.last_login,
                is_active=user.is_active,
                api_keys_count=api_keys_count,
            )
        return None
    
    @classmethod
    def get_user_by_email(cls, email: str) -> Optional[UserResponse]:
        """根据邮箱获取用户"""
        user_id = cls._email_to_user.get(email)
        if user_id:
            return cls.get_user_by_id(user_id)
        return None
    
    @classmethod
    def get_stats(cls) -> Dict[str, int]:
        """获取统计数据"""
        return {
            "total_users": len(cls._users),
            "total_api_keys": len(cls._api_keys),
            "total_tenants": len(cls._tenant_api_keys),
        }