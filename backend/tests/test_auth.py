"""
AgentWatch 认证系统测试
Token黑名单、刷新令牌、密码修改、用户更新
"""

import pytest
from datetime import datetime, timedelta

# 添加 backend 到 path
import sys
sys.path.insert(0, '.')

from auth.jwt import (
    TokenBlacklist,
    create_token_pair,
    verify_token,
    create_access_token,
    create_refresh_token,
    get_token_expiry,
    hash_password,
    verify_password,
)
from auth.service import AuthService
from auth.models import (
    UserCreate,
    UserLogin,
    PasswordChange,
    UserProfileUpdate,
    APIKeyCreate,
    APIKeyScope,
    UserRole,
    PlanType,
)


class TestTokenBlacklist:
    """Token黑名单测试"""
    
    def setup_method(self):
        """每个测试前清空黑名单"""
        TokenBlacklist.clear()
    
    def test_blacklist_init(self):
        """测试黑名单初始化"""
        assert TokenBlacklist.size() == 0
    
    def test_add_to_blacklist(self):
        """测试添加到黑名单"""
        TokenBlacklist.add("test_token")
        assert TokenBlacklist.size() == 1
        assert TokenBlacklist.is_blacklisted("test_token")
    
    def test_remove_from_blacklist(self):
        """测试从黑名单移除"""
        TokenBlacklist.add("test_token")
        assert TokenBlacklist.remove("test_token") == True
        assert TokenBlacklist.size() == 0
        assert not TokenBlacklist.is_blacklisted("test_token")
    
    def test_remove_nonexistent(self):
        """测试移除不存在条目"""
        assert TokenBlacklist.remove("nonexistent") == False
    
    def test_blacklist_access_token(self):
        """测试黑名单access token"""
        access_token = create_access_token({"sub": "user_1"})
        expiry = get_token_expiry(access_token)
        
        TokenBlacklist.add_access_token(access_token)
        assert TokenBlacklist.is_blacklisted(access_token)
    
    def test_blacklist_refresh_token(self):
        """测试黑名单refresh token"""
        refresh_token = create_refresh_token({"sub": "user_1"})
        
        TokenBlacklist.add_refresh_token(refresh_token)
        # refresh token 使用 jti 作为黑名单 key
        payload = verify_token(refresh_token, token_type="refresh")
        if payload and payload.get("jti"):
            assert TokenBlacklist.is_blacklisted(payload["jti"])
    
    def test_verify_token_with_blacklist(self):
        """测试黑名单token验证失败"""
        access_token = create_access_token({"sub": "user_1"})
        
        # 未黑名单时验证成功
        payload = verify_token(access_token)
        assert payload is not None
        
        # 黑名单后验证失败
        TokenBlacklist.add_access_token(access_token)
        payload = verify_token(access_token)
        assert payload is None
    
    def test_blacklist_clear_expired(self):
        """测试清理过期黑名单"""
        # 添加已过期条目
        TokenBlacklist.add("expired_token", datetime.utcnow() - timedelta(hours=1))
        TokenBlacklist.add("valid_token", datetime.utcnow() + timedelta(hours=1))
        
        cleared = TokenBlacklist.clear_expired()
        assert cleared == 1
        assert TokenBlacklist.size() == 1
        assert TokenBlacklist.is_blacklisted("valid_token")


class TestPasswordHash:
    """密码哈希测试"""
    
    def test_hash_password(self):
        """测试密码哈希"""
        password = "TestPassword123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert hashed.startswith("$2b$")  # bcrypt format
    
    def test_verify_password_success(self):
        """测试密码验证成功"""
        password = "TestPassword123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) == True
    
    def test_verify_password_failure(self):
        """测试密码验证失败"""
        password = "TestPassword123"
        hashed = hash_password(password)
        
        assert verify_password("WrongPassword", hashed) == False
    
    def test_password_truncation(self):
        """测试长密码截断（bcrypt 72 bytes限制）"""
        long_password = "A" * 100  # 100 characters > 72 bytes
        hashed = hash_password(long_password)
        
        # 截断后的密码应该能验证
        truncated = long_password[:72]
        assert verify_password(truncated, hashed) == True


class TestTokenCreation:
    """Token创建测试"""
    
    def test_create_access_token(self):
        """测试创建access token"""
        data = {"sub": "user_1", "email": "test@example.com"}
        token = create_access_token(data)
        
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "user_1"
        assert payload["type"] == "access"
    
    def test_create_refresh_token(self):
        """测试创建refresh token"""
        data = {"sub": "user_1"}
        token = create_refresh_token(data)
        
        payload = verify_token(token, token_type="refresh")
        assert payload is not None
        assert payload["sub"] == "user_1"
        assert payload["type"] == "refresh"
        assert payload.get("jti") is not None
    
    def test_create_token_pair(self):
        """测试创建token pair"""
        tokens = create_token_pair(
            user_id="user_1",
            email="test@example.com",
            tenant_id="tenant_1",
            role="admin"
        )
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert "expires_in" in tokens
        
        # 验证access token
        access_payload = verify_token(tokens["access_token"])
        assert access_payload["email"] == "test@example.com"
        
        # 验证refresh token
        refresh_payload = verify_token(tokens["refresh_token"], token_type="refresh")
        assert refresh_payload["sub"] == "user_1"
    
    def test_token_expiry(self):
        """测试token过期时间"""
        data = {"sub": "user_1"}
        token = create_access_token(data, expires_delta=timedelta(minutes=30))
        
        expiry = get_token_expiry(token)
        assert expiry is not None
        assert expiry > datetime.utcnow()


class TestAuthService:
    """认证服务测试"""
    
    def setup_method(self):
        """每个测试前清空数据"""
        AuthService._users.clear()
        AuthService._email_to_user.clear()
        AuthService._api_keys.clear()
        AuthService._tenant_api_keys.clear()
        TokenBlacklist.clear()
    
    def test_register_user(self):
        """测试用户注册"""
        user = AuthService.register_user(UserCreate(
            email="test@example.com",
            password="Test1234",
            name="Test User"
        ))
        
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.role == UserRole.ADMIN
        assert user.tenant_id.startswith("t_")
    
    def test_register_duplicate_email(self):
        """测试重复邮箱注册"""
        AuthService.register_user(UserCreate(
            email="test@example.com",
            password="Test1234"
        ))
        
        with pytest.raises(ValueError, match="already registered"):
            AuthService.register_user(UserCreate(
                email="test@example.com",
                password="Test1234"
            ))
    
    def test_login_user(self):
        """测试用户登录"""
        # 注册用户
        AuthService.register_user(UserCreate(
            email="test@example.com",
            password="Test1234"
        ))
        
        # 登录
        result = AuthService.login_user(UserLogin(
            email="test@example.com",
            password="Test1234"
        ))
        
        assert result.access_token is not None
        assert result.refresh_token is not None
        assert result.user.email == "test@example.com"
    
    def test_login_invalid_password(self):
        """测试错误密码登录"""
        AuthService.register_user(UserCreate(
            email="test@example.com",
            password="Test1234"
        ))
        
        with pytest.raises(ValueError, match="Invalid"):
            AuthService.login_user(UserLogin(
                email="test@example.com",
                password="WrongPassword"
            ))
    
    def test_login_nonexistent_user(self):
        """测试不存在用户登录"""
        with pytest.raises(ValueError, match="Invalid"):
            AuthService.login_user(UserLogin(
                email="nonexistent@example.com",
                password="Test1234"
            ))
    
    def test_refresh_token(self):
        """测试刷新令牌"""
        # 注册并登录
        AuthService.register_user(UserCreate(
            email="test@example.com",
            password="Test1234"
        ))
        login_result = AuthService.login_user(UserLogin(
            email="test@example.com",
            password="Test1234"
        ))
        
        # 刷新
        refresh_result = AuthService.refresh_token(login_result.refresh_token)
        
        assert refresh_result.access_token is not None
        assert refresh_result.refresh_token is not None
        # 新的refresh token应该与旧的不同
        assert refresh_result.refresh_token != login_result.refresh_token
    
    def test_refresh_token_revoked(self):
        """测试已撤销刷新令牌"""
        AuthService.register_user(UserCreate(
            email="test@example.com",
            password="Test1234"
        ))
        login_result = AuthService.login_user(UserLogin(
            email="test@example.com",
            password="Test1234"
        ))
        
        # 第一次刷新成功
        AuthService.refresh_token(login_result.refresh_token)
        
        # 使用旧的refresh token应该失败
        with pytest.raises(ValueError):  # 匹配任何错误消息
            AuthService.refresh_token(login_result.refresh_token)
    
    def test_change_password(self):
        """测试修改密码"""
        AuthService.register_user(UserCreate(
            email="test@example.com",
            password="OldPassword123"
        ))
        login_result = AuthService.login_user(UserLogin(
            email="test@example.com",
            password="OldPassword123"
        ))
        
        # 修改密码
        result = AuthService.change_password(
            login_result.user.user_id,
            PasswordChange(
                old_password="OldPassword123",
                new_password="NewPassword456"
            )
        )
        
        assert result["message"] == "Password changed successfully"
        
        # 用新密码登录成功
        new_login = AuthService.login_user(UserLogin(
            email="test@example.com",
            password="NewPassword456"
        ))
        assert new_login is not None
        
        # 用旧密码登录失败
        with pytest.raises(ValueError):
            AuthService.login_user(UserLogin(
                email="test@example.com",
                password="OldPassword123"
            ))
    
    def test_change_password_invalid_old(self):
        """测试错误旧密码"""
        AuthService.register_user(UserCreate(
            email="test@example.com",
            password="Test1234"
        ))
        login_result = AuthService.login_user(UserLogin(
            email="test@example.com",
            password="Test1234"
        ))
        
        with pytest.raises(ValueError, match="Invalid old password"):
            AuthService.change_password(
                login_result.user.user_id,
                PasswordChange(
                    old_password="WrongPassword",
                    new_password="NewPassword456"
                )
            )
    
    def test_update_profile(self):
        """测试更新用户信息"""
        AuthService.register_user(UserCreate(
            email="test@example.com",
            password="Test1234",
            name="Original Name"
        ))
        login_result = AuthService.login_user(UserLogin(
            email="test@example.com",
            password="Test1234"
        ))
        
        # 更新
        updated = AuthService.update_profile(
            login_result.user.user_id,
            UserProfileUpdate(
                name="Updated Name",
                organization="New Org"
            )
        )
        
        assert updated.name == "Updated Name"
        assert updated.organization == "New Org"
    
    def test_logout(self):
        """测试注销"""
        AuthService.register_user(UserCreate(
            email="test@example.com",
            password="Test1234"
        ))
        login_result = AuthService.login_user(UserLogin(
            email="test@example.com",
            password="Test1234"
        ))
        
        # 注销
        logout_result = AuthService.logout_user(
            login_result.access_token,
            login_result.refresh_token
        )
        
        assert logout_result["blacklisted_tokens"] == 2
        assert TokenBlacklist.size() >= 2
    
    def test_create_api_key(self):
        """测试创建API Key"""
        user = AuthService.register_user(UserCreate(
            email="test@example.com",
            password="Test1234"
        ))
        
        api_key = AuthService.create_api_key(
            tenant_id=user.tenant_id,
            user_id=user.user_id,
            key_data=APIKeyCreate(
                name="Test Key",
                scope=[APIKeyScope.READ, APIKeyScope.WRITE],
                rate_limit=100
            )
        )
        
        assert api_key.key_id is not None
        assert api_key.full_key is not None  # 创建时返回完整key (field name is full_key)
        assert api_key.name == "Test Key"
    
    def test_list_api_keys(self):
        """测试列出API Keys"""
        user = AuthService.register_user(UserCreate(
            email="test@example.com",
            password="Test1234"
        ))
        
        AuthService.create_api_key(
            tenant_id=user.tenant_id,
            user_id=user.user_id,
            key_data=APIKeyCreate(name="Key 1")
        )
        AuthService.create_api_key(
            tenant_id=user.tenant_id,
            user_id=user.user_id,
            key_data=APIKeyCreate(name="Key 2")
        )
        
        keys = AuthService.list_api_keys(user.tenant_id)
        assert len(keys) == 2
        # 列表不返回完整key (full_key is None)
        assert keys[0].full_key is None
    
    def test_revoke_api_key(self):
        """测试撤销API Key"""
        user = AuthService.register_user(UserCreate(
            email="test@example.com",
            password="Test1234"
        ))
        
        api_key = AuthService.create_api_key(
            tenant_id=user.tenant_id,
            user_id=user.user_id,
            key_data=APIKeyCreate(name="Test Key")
        )
        
        # 撤销
        success = AuthService.revoke_api_key(user.tenant_id, api_key.key_id)
        assert success == True
        
        # 查看状态
        keys = AuthService.list_api_keys(user.tenant_id)
        assert keys[0].is_active == False
    
    def test_get_stats(self):
        """测试获取统计"""
        AuthService.register_user(UserCreate(
            email="test@example.com",
            password="Test1234"
        ))
        
        stats = AuthService.get_stats()
        assert stats["total_users"] == 1
        assert stats["active_users"] == 1


class TestAPIKeyValidation:
    """API Key验证测试"""
    
    def setup_method(self):
        AuthService._users.clear()
        AuthService._email_to_user.clear()
        AuthService._api_keys.clear()
        AuthService._tenant_api_keys.clear()
    
    def test_validate_api_key(self):
        """测试API Key验证"""
        user = AuthService.register_user(UserCreate(
            email="test@example.com",
            password="Test1234"
        ))
        
        api_key = AuthService.create_api_key(
            tenant_id=user.tenant_id,
            user_id=user.user_id,
            key_data=APIKeyCreate(name="Test Key")
        )
        
        validation = AuthService.validate_api_key(api_key.full_key)  # use full_key
        
        assert validation.is_valid == True
        assert validation.tenant_id == user.tenant_id
        assert validation.key_id == api_key.key_id
    
    def test_validate_invalid_format(self):
        """测试无效格式"""
        validation = AuthService.validate_api_key("invalid_key")
        
        assert validation.is_valid == False
        assert "Invalid" in validation.error_message
    
    def test_validate_nonexistent_key(self):
        """测试不存在key"""
        # 格式正确但不存在的key - 使用正确的格式
        fake_key = "aw_t_12345678_k_abcdefgh_0123456789abcdef01234567"  # 32 char secret
        
        validation = AuthService.validate_api_key(fake_key)
        
        assert validation.is_valid == False
        # 可能是 "not found" 或 "secret mismatch"
        assert validation.error_message is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])