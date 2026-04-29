"""
AgentWatch JWT Token 处理
JWT 生成、验证、刷新
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
import secrets

# JWT 配置
JWT_SECRET_KEY = secrets.token_hex(32)  # 生产环境应从配置读取
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
REFRESH_TOKEN_EXPIRE_DAYS = 7

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """密码哈希"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """密码验证"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
    secret_key: Optional[str] = None
) -> str:
    """生成 JWT 访问令牌
    
    Args:
        data: 要编码的数据 (user_id, email, tenant_id, role等)
        expires_delta: 过期时间增量
        secret_key: 自定义密钥(可选)
    
    Returns:
        JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    key = secret_key or JWT_SECRET_KEY
    encoded_jwt = jwt.encode(to_encode, key, algorithm=JWT_ALGORITHM)
    
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
    secret_key: Optional[str] = None
) -> str:
    """生成刷新令牌
    
    刷新令牌有效期更长，用于获取新的访问令牌
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    key = secret_key or JWT_SECRET_KEY
    encoded_jwt = jwt.encode(to_encode, key, algorithm=JWT_ALGORITHM)
    
    return encoded_jwt


def verify_token(
    token: str,
    secret_key: Optional[str] = None,
    token_type: str = "access"
) -> Optional[Dict[str, Any]]:
    """验证 JWT Token
    
    Args:
        token: JWT token string
        secret_key: 自定义密钥(可选)
        token_type: 期望的token类型 (access/refresh)
    
    Returns:
        解码后的数据字典，验证失败返回 None
    """
    try:
        key = secret_key or JWT_SECRET_KEY
        payload = jwt.decode(token, key, algorithms=[JWT_ALGORITHM])
        
        # 检查token类型
        if payload.get("type") != token_type:
            return None
        
        # 检查过期
        exp = payload.get("exp")
        if exp and datetime.utcnow() > datetime.fromtimestamp(exp):
            return None
        
        return payload
        
    except JWTError:
        return None


def get_token_expiry(token: str, secret_key: Optional[str] = None) -> Optional[datetime]:
    """获取Token过期时间"""
    payload = verify_token(token, secret_key)
    if payload and payload.get("exp"):
        return datetime.fromtimestamp(payload["exp"])
    return None


def create_token_pair(
    user_id: str,
    email: str,
    tenant_id: str,
    role: str = "member",
    secret_key: Optional[str] = None
) -> Dict[str, str]:
    """创建访问令牌和刷新令牌对
    
    Returns:
        {"access_token": "...", "refresh_token": "...", "expires_in": 86400}
    """
    access_data = {
        "sub": user_id,
        "email": email,
        "tenant_id": tenant_id,
        "role": role
    }
    
    refresh_data = {
        "sub": user_id,
        "tenant_id": tenant_id
    }
    
    access_token = create_access_token(access_data, secret_key=secret_key)
    refresh_token = create_refresh_token(refresh_data, secret_key=secret_key)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": ACCESS_TOKEN_EXPIRE_HOURS * 3600
    }


class TokenBlacklist:
    """Token黑名单(用于注销)
    
    生产环境应使用 Redis 或数据库存储
    """
    
    _blacklist: set = set()
    
    @classmethod
    def add(cls, token: str) -> None:
        """添加到黑名单"""
        cls._blacklist.add(token)
    
    @classmethod
    def is_blacklisted(cls, token: str) -> bool:
        """检查是否在黑名单"""
        return token in cls._blacklist
    
    @classmethod
    def clear(cls) -> None:
        """清空黑名单"""
        cls._blacklist.clear()


class JWTHandler:
    """JWT处理类 - 封装JWT操作"""
    
    @staticmethod
    def create_access_token(
        user_id: str,
        tenant_id: str,
        role: str = "member",
        expires_delta: Optional[int] = None
    ) -> str:
        """创建访问令牌"""
        data = {
            "sub": user_id,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "role": role
        }
        if expires_delta:
            return create_access_token(data, timedelta(hours=expires_delta))
        return create_access_token(data)
    
    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """创建刷新令牌"""
        data = {"sub": user_id, "user_id": user_id}
        return create_refresh_token(data)
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """验证令牌"""
        payload = verify_token(token)
        if payload and not TokenBlacklist.is_blacklisted(token):
            return payload
        return None