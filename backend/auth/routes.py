"""
AgentWatch 认证 API 路由
用户注册、登录、API Key 管理
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List

from .models import (
    UserCreate,
    UserResponse,
    UserLogin,
    APIKeyCreate,
    APIKeyResponse,
    TokenResponse,
    RefreshTokenRequest,
    PasswordChange,
    UserProfileUpdate,
)
from .service import AuthService
from .middleware import get_current_user, verify_api_key


router = APIRouter(prefix="/auth", tags=["Authentication"])


# ==================== 用户相关 ====================

@router.post("/register", response_model=TokenResponse, summary="用户注册")
async def register(user_data: UserCreate):
    """用户注册
    
    - 创建新用户
    - 自动创建租户
    - 返回 JWT Token
    """
    try:
        user = AuthService.register_user(user_data)
        
        # 注册后自动登录
        login_result = AuthService.login_user(UserLogin(
            email=user_data.email,
            password=user_data.password
        ))
        
        return login_result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse, summary="用户登录")
async def login(login_data: UserLogin):
    """用户登录
    
    - 验证邮箱和密码
    - 返回 JWT Token
    """
    try:
        return AuthService.login_user(login_data)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/refresh", response_model=TokenResponse, summary="刷新Token")
async def refresh_token(refresh_data: RefreshTokenRequest, current_user: UserResponse = Depends(get_current_user)):
    """刷新访问令牌
    
    使用刷新令牌获取新的访问令牌
    """
    # TODO: 实现刷新令牌验证
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return current_user


@router.patch("/me", response_model=UserResponse, summary="更新用户信息")
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """更新用户信息"""
    # TODO: 实现用户信息更新
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/me/password", summary="修改密码")
async def change_password(
    password_data: PasswordChange,
    current_user: UserResponse = Depends(get_current_user)
):
    """修改密码"""
    # TODO: 实现密码修改
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/logout", summary="用户注销")
async def logout(current_user: UserResponse = Depends(get_current_user)):
    """用户注销
    
    将当前Token加入黑名单
    """
    # TODO: 实现Token黑名单
    return {"message": "Logged out successfully"}


# ==================== API Key 管理 ====================

@router.post("/api-keys", response_model=APIKeyResponse, summary="创建 API Key")
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """创建新的 API Key
    
    - 完整 API Key 仅在创建时返回一次
    - 请妥善保存
    """
    return AuthService.create_api_key(
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
        key_data=key_data
    )


@router.get("/api-keys", response_model=List[APIKeyResponse], summary="列出 API Keys")
async def list_api_keys(current_user: UserResponse = Depends(get_current_user)):
    """列出租户的所有 API Key
    
    - 不返回完整的 Key，只返回元信息
    """
    return AuthService.list_api_keys(current_user.tenant_id)


@router.get("/api-keys/{key_id}", response_model=APIKeyResponse, summary="获取 API Key详情")
async def get_api_key(
    key_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """获取单个 API Key 详情"""
    keys = AuthService.list_api_keys(current_user.tenant_id)
    for key in keys:
        if key.key_id == key_id:
            return key
    raise HTTPException(status_code=404, detail="API Key not found")


@router.delete("/api-keys/{key_id}", summary="撤销 API Key")
async def revoke_api_key(
    key_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """撤销（禁用）API Key"""
    success = AuthService.revoke_api_key(current_user.tenant_id, key_id)
    if success:
        return {"message": "API Key revoked", "key_id": key_id}
    raise HTTPException(status_code=404, detail="API Key not found")


# ==================== 认证状态 ====================

@router.get("/stats", summary="获取认证统计")
async def get_auth_stats(current_user: UserResponse = Depends(get_current_user)):
    """获取认证系统统计数据
    
    仅管理员可访问
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    return AuthService.get_stats()


@router.get("/validate", summary="验证 API Key")
async def validate_key(request: Request, auth_info: dict = Depends(verify_api_key)):
    """验证当前请求的 API Key
    
    返回验证结果
    """
    return {
        "valid": True,
        "tenant_id": auth_info["tenant_id"],
        "key_id": auth_info["key_id"],
        "scope": [s.value for s in auth_info["scope"]],
        "rate_limit": auth_info["rate_limit"],
    }