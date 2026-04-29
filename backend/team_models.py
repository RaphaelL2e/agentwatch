"""
AgentWatch 团队协作数据模型
Phase 2 功能扩展
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MemberRole(str, Enum):
    """团队成员角色"""
    OWNER = "owner"       # 团队创建者，最高权限
    ADMIN = "admin"       # 管理员，可管理成员和项目
    MEMBER = "member"     # 普通成员，可查看和使用
    VIEWER = "viewer"     # 观察者，只能查看


class TeamStatus(str, Enum):
    """团队状态"""
    ACTIVE = "active"
    SUSPENDED = "suspended"    # 超额使用暂停
    TRIAL = "trial"            # 试用期


class TeamCreate(BaseModel):
    """创建团队请求"""
    name: str = Field(..., min_length=2, max_length=50, description="团队名称")
    slug: Optional[str] = Field(None, min_length=2, max_length=30, description="团队标识符")
    description: Optional[str] = Field(None, max_length=200, description="团队描述")
    avatar_url: Optional[str] = Field(None, description="团队头像URL")


class TeamUpdate(BaseModel):
    """更新团队请求"""
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    avatar_url: Optional[str] = Field(None)
    settings: Optional[Dict[str, Any]] = None


class TeamResponse(BaseModel):
    """团队响应"""
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    status: TeamStatus
    owner_id: str
    member_count: int = Field(default=1)
    project_count: int = Field(default=0)
    trace_count: int = Field(default=0)
    total_cost: float = Field(default=0.0)
    created_at: datetime
    updated_at: datetime
    settings: Dict[str, Any] = Field(default_factory=dict)


class TeamListResponse(BaseModel):
    """团队列表响应"""
    teams: List[TeamResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class TeamMemberCreate(BaseModel):
    """添加团队成员请求"""
    user_email: str = Field(..., description="用户邮箱")
    role: MemberRole = Field(default=MemberRole.MEMBER, description="成员角色")


class TeamMemberUpdate(BaseModel):
    """更新成员角色请求"""
    role: MemberRole


class TeamMemberResponse(BaseModel):
    """团队成员响应"""
    id: str
    team_id: str
    user_id: str
    user_name: str
    user_email: str
    role: MemberRole
    joined_at: datetime
    last_active: Optional[datetime] = None
    trace_count: int = Field(default=0)


class TeamMemberListResponse(BaseModel):
    """团队成员列表响应"""
    members: List[TeamMemberResponse]
    total: int


class ProjectCreate(BaseModel):
    """创建项目请求"""
    name: str = Field(..., min_length=2, max_length=50, description="项目名称")
    description: Optional[str] = Field(None, max_length=200)
    team_id: str = Field(..., description="所属团队ID")
    settings: Optional[Dict[str, Any]] = None


class ProjectUpdate(BaseModel):
    """更新项目请求"""
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ProjectResponse(BaseModel):
    """项目响应"""
    id: str
    name: str
    description: Optional[str] = None
    team_id: str
    team_name: str
    api_key: Optional[str] = Field(None, description="项目API Key (仅创建时显示)")
    is_active: bool = Field(default=True)
    trace_count: int = Field(default=0)
    total_cost: float = Field(default=0.0)
    created_at: datetime
    updated_at: datetime
    settings: Dict[str, Any] = Field(default_factory=dict)


class ProjectListResponse(BaseModel):
    """项目列表响应"""
    projects: List[ProjectResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class TeamStatsResponse(BaseModel):
    """团队统计响应"""
    team_id: str
    team_name: str
    
    # Trace 统计
    total_traces: int
    running_traces: int
    completed_traces: int
    failed_traces: int
    
    # 成本统计
    total_cost: float
    cost_by_provider: Dict[str, float] = Field(default_factory=dict)
    cost_by_project: Dict[str, float] = Field(default_factory=dict)
    
    # Token 统计
    total_tokens: int
    input_tokens: int
    output_tokens: int
    
    # 时间范围
    period_start: datetime
    period_end: datetime
    
    # 成员活跃度
    active_members: int
    member_stats: List[Dict[str, Any]] = Field(default_factory=list)