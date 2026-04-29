"""
AgentWatch JWT Token 处理
JWT 生成、验证、刷新 + Token 黑名单
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Set
from jose import JWTError, jwt
import bcrypt
import secrets
import threading

# JWT 配置
JWT_SECRET_KEY = secrets.token_hex(32)  # 生产环境应从配置读取
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    """密码哈希 - 使用 bcrypt 直接"""
    # bcrypt 密码限制 72 bytes，截断处理
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt(rounds=12)  # work factor 12
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """密码验证 - 使用 bcrypt 直接"""
    try:
        password_bytes = plain_password.encode('utf-8')[:72]
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


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
    
    # 生成唯一 jti (JWT ID) 用于黑名单
    jti = secrets.token_hex(16)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
        "jti": jti
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
        
        # 检查黑名单
        jti = payload.get("jti") or token
        if TokenBlacklist.is_blacklisted(jti):
            return None
        
        return payload
        
    except JWTError:
        return None


def get_token_expiry(token: str, secret_key: Optional[str] = None) -> Optional[datetime]:
    """获取Token过期时间"""
    try:
        key = secret_key or JWT_SECRET_KEY
        payload = jwt.decode(token, key, algorithms=[JWT_ALGORITHM])
        if payload.get("exp"):
            return datetime.fromtimestamp(payload["exp"])
    except JWTError:
        pass
    return None


def create_token_pair(
    user_id: str,
    email: str,
    tenant_id: str,
    role: str = "member",
    secret_key: Optional[str] = None
) -> Dict[str, Any]:
    """创建访问令牌和刷新令牌对
    
    Returns:
        {"access_token": "...", "refresh_token": "...", "expires_in": 86400, "refresh_jti": "..."}
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
    
    # 获取 refresh token 的 jti
    refresh_payload = jwt.decode(refresh_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    refresh_jti = refresh_payload.get("jti")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": ACCESS_TOKEN_EXPIRE_HOURS * 3600,
        "refresh_jti": refresh_jti
    }


class TokenBlacklist:
    """Token 黑名单管理
    
    使用内存存储 + 线程锁确保安全
    自动清理过期 token 以节省内存
    生产环境应使用 Redis 或数据库
    """
    
    _blacklist: Set[str] = set()
    _expiry_map: Dict[str, datetime] = {}  # token_jti -> expiry_time
    _lock = threading.Lock()
    
    @classmethod
    def add(cls, token_or_jti: str, expires_at: Optional[datetime] = None) -> None:
        """添加到黑名单
        
        Args:
            token_or_jti: token 字符串或 jti
            expires_at: token 过期时间（用于自动清理）
        """
        with cls._lock:
            cls._blacklist.add(token_or_jti)
            if expires_at:
                cls._expiry_map[token_or_jti] = expires_at
    
    @classmethod
    def is_blacklisted(cls, token_or_jti: str) -> bool:
        """检查是否在黑名单"""
        with cls._lock:
            return token_or_jti in cls._blacklist
    
    @classmethod
    def remove(cls, token_or_jti: str) -> bool:
        """从黑名单移除"""
        with cls._lock:
            if token_or_jti in cls._blacklist:
                cls._blacklist.remove(token_or_jti)
                cls._expiry_map.pop(token_or_jti, None)
                return True
            return False
    
    @classmethod
    def clear_expired(cls) -> int:
        """清理已过期的黑名单条目
        
        Returns:
            清理的数量
        """
        with cls._lock:
            now = datetime.utcnow()
            expired = [
                jti for jti, exp in cls._expiry_map.items()
                if exp < now
            ]
            for jti in expired:
                cls._blacklist.discard(jti)
                cls._expiry_map.pop(jti, None)
            return len(expired)
    
    @classmethod
    def clear(cls) -> None:
        """清空黑名单"""
        with cls._lock:
            cls._blacklist.clear()
            cls._expiry_map.clear()
    
    @classmethod
    def size(cls) -> int:
        """黑名单大小"""
        with cls._lock:
            return len(cls._blacklist)
    
    @classmethod
    def add_access_token(cls, token: str) -> None:
        """添加访问令牌到黑名单"""
        expiry = get_token_expiry(token)
        cls.add(token, expiry)
    
    @classmethod
    def add_refresh_token(cls, refresh_token: str) -> None:
        """添加刷新令牌到黑名单（使用 jti）"""
        try:
            payload = jwt.decode(refresh_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti and exp:
                cls.add(jti, datetime.fromtimestamp(exp))
        except JWTError:
            pass


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
        return verify_token(token)
    
    @staticmethod
    def verify_refresh_token(refresh_token: str) -> Optional[Dict[str, Any]]:
        """验证刷新令牌"""
        return verify_token(refresh_token, token_type="refresh")
    
    @staticmethod
    def refresh_access_token(refresh_token: str) -> Optional[Dict[str, str]]:
        """使用刷新令牌获取新的访问令牌
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            新的 token pair 或 None
        """
        payload = verify_token(refresh_token, token_type="refresh")
        if not payload:
            return None
        
        user_id = payload.get("sub") or payload.get("user_id")
        tenant_id = payload.get("tenant_id")
        
        if not user_id or not tenant_id:
            return None
        
        # 生成新的 token pair
        return create_token_pair(
            user_id=user_id,
            email="",  # 刷新时不需要 email
            tenant_id=tenant_id,
            role=payload.get("role", "member")
        )