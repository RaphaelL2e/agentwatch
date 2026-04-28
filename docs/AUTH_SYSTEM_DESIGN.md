# AgentWatch 用户认证系统设计

## 概述

用户认证系统为 AgentWatch 提供安全的访问控制和多租户支持。

**发布时间**: Month 2 (Week 5-8)
**当前状态**: 无认证（API Key 仅为传递）
**目标**: 完整认证体系 + JWT + OAuth2

---

## 认证架构

### 1. 认证方式

| 认证方式 | 适用场景 | 安全等级 |
|---------|---------|---------|
| API Key | SDK/CLI/自动化脚本 | 中 |
| JWT Token | Dashboard Web 用户 | 高 |
| OAuth2 | 第三方集成 (GitHub/Google) | 高 |
| Session | Dashboard 管理后台 | 高 |

### 2. 多租户架构

```
用户层级:
┌─────────────────────────────────────┐
│ Organization (企业账户)              │
│  - Plan: free/pro/enterprise        │
│  - Billing: 月度订阅                 │
│  - Admin: organization_admin        │
├─────────────────────────────────────┤
│ Tenant (团队/项目)                   │
│  - Isolation: tenant_id             │
│  - Config: 存储配置/告警配置         │
│  - Admin: tenant_admin               │
├─────────────────────────────────────┤
│ API Key (访问凭证)                   │
│  - Scope: read/write/admin          │
│  - Rate Limit: 每分钟请求限制        │
│  - Expiry: 可设置过期时间            │
├─────────────────────────────────────┤
│ Trace (监控数据)                     │
│  - Belongs to: tenant_id            │
│  - Created by: api_key_id           │
└─────────────────────────────────────┘
```

---

## API Key 认证

### API Key 格式

```
格式: aw_<tenant_id>_<key_id>_<secret>

示例: aw_t001_k123_abc123xyz
- tenant_id: t001
- key_id: k123
- secret: abc123xyz (32字符)
```

### API Key 管理

**创建 API Key**:
```
POST /api/v2/api-keys
Authorization: Bearer <JWT>

{
  "name": "Production Key",
  "scope": ["read", "write"],
  "rate_limit": 100,  # 每分钟限制
  "expires_at": "2026-12-31"  # 可选
}

Response:
{
  "api_key": "aw_t001_k124_secret...",
  "key_id": "k124",
  "created_at": "2026-04-29"
}
```

**列出 API Key**:
```
GET /api/v2/api-keys
Authorization: Bearer <JWT>

Response:
{
  "keys": [
    {
      "key_id": "k123",
      "name": "Production Key",
      "scope": ["read", "write"],
      "rate_limit": 100,
      "last_used": "2026-04-28",
      "expires_at": "2026-12-31"
    }
  ]
}
```

**撤销 API Key**:
```
DELETE /api/v2/api-keys/{key_id}
Authorization: Bearer <JWT>
```

### API Key Scope

| Scope | 权限 |
|-------|------|
| `read` | 读取 Trace、统计数据 |
| `write` | 创建、更新 Trace |
| `admin` | 管理 API Key、配置 |
| `billing` | 查看账单、用量 |

---

## JWT Token 认证

### JWT 结构

```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "user_id": "u001",
    "tenant_id": "t001",
    "organization_id": "org001",
    "role": "tenant_admin",
    "scope": ["read", "write", "admin"],
    "iat": 1714560000,
    "exp": 1714563600  # 1小时过期
  },
  "signature": "..."
}
```

### 登录 API

```
POST /api/v2/auth/login
{
  "email": "user@example.com",
  "password": "..."
}

Response:
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "expires_in": 3600,
  "user": {
    "id": "u001",
    "email": "user@example.com",
    "tenant_id": "t001",
    "role": "tenant_admin"
  }
}
```

### Token 刷新

```
POST /api/v2/auth/refresh
{
  "refresh_token": "eyJ..."
}

Response:
{
  "access_token": "eyJ...",
  "expires_in": 3600
}
```

### Token 验证

每个 API 请求携带 JWT:

```
GET /api/v2/traces
Authorization: Bearer eyJ...
```

---

## OAuth2 认证

### 支持的 Provider

| Provider | 适用场景 |
|----------|---------|
| GitHub | 开发者用户 |
| Google | 企业用户 |
| Microsoft | 企业用户 |

### GitHub OAuth2 流程

1. 用户点击 "Login with GitHub"
2. 重定向到 GitHub 授权页面
3. 用户授权后，GitHub 返回 `code`
4. AgentWatch 用 `code` 获取 `access_token`
5. AgentWatch 用 `access_token` 获取用户信息
6. AgentWatch 创建 JWT 并返回

**授权 URL**:
```
GET /api/v2/auth/oauth/github
Redirect: https://github.com/login/oauth/authorize?client_id=...&redirect_uri=...
```

**回调处理**:
```
GET /api/v2/auth/oauth/github/callback?code=...

Response:
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "user": {...}
}
```

---

## 数据模型

### User 表

```python
class User(Base):
    __tablename__ = "users"
    
    user_id: str  # Primary Key
    email: str  # Unique
    password_hash: str  # bcrypt
    tenant_id: str  # FK
    organization_id: str  # FK
    role: str  # user/admin/owner
    created_at: datetime
    last_login: datetime
    is_active: bool
```

### APIKey 表

```python
class APIKey(Base):
    __tablename__ = "api_keys"
    
    key_id: str  # Primary Key
    tenant_id: str  # FK
    user_id: str  # FK (创建者)
    name: str
    secret_hash: str  # bcrypt (secret部分)
    scope: List[str]
    rate_limit: int
    last_used: datetime
    expires_at: datetime
    is_active: bool
    created_at: datetime
```

### Tenant 表

```python
class Tenant(Base):
    __tablename__ = "tenants"
    
    tenant_id: str  # Primary Key
    organization_id: str  # FK
    name: str
    plan: str  # free/pro/enterprise
    limits: Dict  # {max_traces: 100000, max_keys: 10}
    config: Dict  # {storage: "clickhouse", alerts: {...}}
    created_at: datetime
    is_active: bool
```

### Organization 表

```python
class Organization(Base):
    __tablename__ = "organizations"
    
    org_id: str  # Primary Key
    name: str
    billing_email: str
    plan: str  # free/pro/enterprise
    billing_cycle: str  # monthly/yearly
    stripe_customer_id: str
    created_at: datetime
    is_active: bool
```

---

## 认证中间件

### FastAPI 中间件实现

```python
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def auth_middleware(request: Request):
    """
    认证中间件
    
    优先级:
    1. Authorization: Bearer <JWT> (Web Dashboard)
    2. X-API-Key: <API Key> (SDK/CLI)
    """
    
    # JWT 认证
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
        user = verify_jwt(token)
        request.state.user = user
        request.state.tenant_id = user["tenant_id"]
        return
    
    # API Key 认证
    api_key = request.headers.get("X-API-Key")
    if api_key:
        key_info = verify_api_key(api_key)
        request.state.api_key = key_info
        request.state.tenant_id = key_info["tenant_id"]
        return
    
    raise HTTPException(401, "Missing authentication")
```

### 权限检查装饰器

```python
def require_scope(scope: str):
    """检查用户是否有指定权限"""
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            user = request.state.user
            api_key = request.state.api_key
            
            scopes = user.get("scope") if user else api_key.get("scope")
            
            if scope not in scopes:
                raise HTTPException(403, f"Missing scope: {scope}")
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

# 使用示例
@router.post("/api-keys")
@require_scope("admin")
async def create_api_key(request: Request):
    ...
```

---

## Rate Limiting

### 实现方案

使用 Redis 滑动窗口限流：

```python
import redis

r = redis.Redis()

def check_rate_limit(api_key_id: str, limit: int) -> bool:
    """
    检查 API Key 是否超限
    
    Args:
        api_key_id: API Key ID
        limit: 每分钟限制数
    
    Returns:
        True if allowed, False if exceeded
    """
    key = f"rate_limit:{api_key_id}"
    current = r.get(key)
    
    if current and int(current) >= limit:
        return False
    
    r.incr(key)
    r.expire(key, 60)  # 60秒窗口
    
    return True
```

### Rate Limit 响应

```
HTTP 429 Too Many Requests
{
  "error": "RATE_LIMIT",
  "message": "Rate limit exceeded",
  "retry_after": 30
}
```

---

## 安全措施

### 1. 密码安全

- bcrypt 加盐哈希 (cost=12)
- 最小长度 12 字符
- 强制包含大小写+数字+符号
- 密码重试限制 (5次锁定)

### 2. API Key 安全

- Secret 部分只显示一次
- 永不存储明文 secret
- 支持即时撤销
- 可设置过期时间

### 3. JWT 安全

- RS256 签名 (非对称)
- 1小时过期
- Refresh Token 7天过期
- 支持 Token 黑名单

### 4. 传输安全

- 强制 HTTPS
- CORS 白名单
- CSRF Token (Web Dashboard)

### 5. 日志审计

- 记录所有认证事件
- 记录 API Key 使用
- 异常登录告警

---

## 实施计划

### Phase 1: API Key 系统 (Week 5-6)

**任务**:
1. 设计 API Key 数据模型
2. 实现 API Key 创建/验证/撤销 API
3. 实现 Rate Limiting
4. 添加认证中间件
5. 测试覆盖

**工作量**: 4-5 天

### Phase 2: JWT 系统 (Week 7)

**任务**:
1. 实现 JWT 生成/验证
2. 实现登录/刷新/注销 API
3. 实现 Token 黑名单
4. 添加 Dashboard 登录页面
5. 测试覆盖

**工作量**: 3-4 天

### Phase 3: OAuth2 (Week 8)

**任务**:
1. 实现 GitHub OAuth2
2. 实现 Google OAuth2
3. 实现 Microsoft OAuth2
4. 添加 OAuth 登录按钮
5. 测试覆盖

**工作量**: 3-4 天

---

## 预算与定价

### 计划定价

| Plan | 月费 | API Keys | Traces/month | 存储 |
|------|------|----------|--------------|------|
| Free | $0 | 1 | 1,000 | 内存 |
| Pro | $49 | 5 | 100,000 | ClickHouse |
| Enterprise | $299 | 20 | 无限 | 自定义 |

### 超量计费

- Pro: 超出部分 $0.01/1K traces
- Enterprise: 按合同约定

---

## 下一步

1. ✅ 确认认证系统设计文档
2. 开始 Phase 1: API Key 系统实现
3. 选择存储方案 (Redis for Rate Limiting)
4. 设计 Dashboard 登录 UI

---

*Created: 2026-04-29*
*Author: AgentWatch Team*