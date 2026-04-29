"""
AgentWatch 团队协作 API
Phase 2 功能扩展
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from datetime import datetime, timedelta
import uuid
import secrets

from team_models import (
    TeamCreate, TeamUpdate, TeamResponse, TeamListResponse,
    TeamMemberCreate, TeamMemberUpdate, TeamMemberResponse, TeamMemberListResponse,
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse,
    TeamStatsResponse, MemberRole, TeamStatus
)
from auth import get_current_user, UserResponse
from team_storage import get_team_storage

router = APIRouter(prefix="/api/v1", tags=["teams"])


# ==================== 团队管理 ====================

@router.post("/teams", response_model=TeamResponse)
async def create_team(
    team: TeamCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """创建团队"""
    storage = get_team_storage()
    
    # 检查用户已有团队数量限制
    existing_teams = storage.get_user_teams(current_user.id)
    if len(existing_teams) >= 10:  # Free tier 限制
        raise HTTPException(status_code=403, detail="Team limit reached (max 10)")
    
    team_id = str(uuid.uuid4())
    slug = team.slug or team.name.lower().replace(" ", "-").replace("_", "-")
    
    # 确保 slug 不重复
    existing_slugs = [t.get("slug") for t in existing_teams]
    if slug in existing_slugs:
        slug = f"{slug}-{secrets.token_hex(3)}"
    
    team_data = {
        "id": team_id,
        "name": team.name,
        "slug": slug,
        "description": team.description,
        "avatar_url": team.avatar_url,
        "status": TeamStatus.ACTIVE,
        "owner_id": current_user.id,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "settings": {"plan": "free", "limits": {"projects": 5, "members": 10}}
    }
    
    storage.create_team(team_data)
    
    # 自动将创建者加入团队
    member_data = {
        "id": str(uuid.uuid4()),
        "team_id": team_id,
        "user_id": current_user.id,
        "user_name": current_user.name,
        "user_email": current_user.email,
        "role": MemberRole.OWNER,
        "joined_at": datetime.utcnow(),
        "last_active": datetime.utcnow(),
        "trace_count": 0
    }
    storage.create_team_member(member_data)
    
    return TeamResponse(
        id=team_id,
        name=team.name,
        slug=slug,
        description=team.description,
        avatar_url=team.avatar_url,
        status=TeamStatus.ACTIVE,
        owner_id=current_user.id,
        member_count=1,
        project_count=0,
        trace_count=0,
        total_cost=0.0,
        created_at=team_data["created_at"],
        updated_at=team_data["updated_at"],
        settings=team_data["settings"]
    )


@router.get("/teams", response_model=TeamListResponse)
async def list_teams(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user)
):
    """获取用户所属团队列表"""
    storage = get_team_storage()
    teams = storage.get_user_teams(current_user.id)
    
    total = len(teams)
    start = (page - 1) * page_size
    end = start + page_size
    
    team_responses = []
    for t in teams[start:end]:
        # 获取团队统计
        stats = storage.get_team_stats(t["id"])
        team_responses.append(TeamResponse(
            id=t["id"],
            name=t["name"],
            slug=t["slug"],
            description=t.get("description"),
            avatar_url=t.get("avatar_url"),
            status=TeamStatus(t["status"]),
            owner_id=t["owner_id"],
            member_count=stats.get("member_count", 1),
            project_count=stats.get("project_count", 0),
            trace_count=stats.get("trace_count", 0),
            total_cost=stats.get("total_cost", 0.0),
            created_at=t["created_at"],
            updated_at=t["updated_at"],
            settings=t.get("settings", {})
        ))
    
    return TeamListResponse(
        teams=team_responses,
        total=total,
        page=page,
        page_size=page_size,
        has_more=end < total
    )


@router.get("/teams/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """获取团队详情"""
    storage = get_team_storage()
    
    # 检查权限
    member = storage.get_team_member(team_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a team member")
    
    team = storage.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    stats = storage.get_team_stats(team_id)
    
    return TeamResponse(
        id=team["id"],
        name=team["name"],
        slug=team["slug"],
        description=team.get("description"),
        avatar_url=team.get("avatar_url"),
        status=TeamStatus(team["status"]),
        owner_id=team["owner_id"],
        member_count=stats.get("member_count", 1),
        project_count=stats.get("project_count", 0),
        trace_count=stats.get("trace_count", 0),
        total_cost=stats.get("total_cost", 0.0),
        created_at=team["created_at"],
        updated_at=team["updated_at"],
        settings=team.get("settings", {})
    )


@router.patch("/teams/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: str,
    team_update: TeamUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """更新团队信息"""
    storage = get_team_storage()
    
    # 检查权限 (只有 owner/admin 可以更新)
    member = storage.get_team_member(team_id, current_user.id)
    if not member or member["role"] not in [MemberRole.OWNER, MemberRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    team = storage.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # 更新字段
    updates = team_update.model_dump(exclude_unset=True)
    updates["updated_at"] = datetime.utcnow()
    
    storage.update_team(team_id, updates)
    
    # 获取更新后的团队
    updated_team = storage.get_team(team_id)
    stats = storage.get_team_stats(team_id)
    
    return TeamResponse(
        id=updated_team["id"],
        name=updated_team["name"],
        slug=updated_team["slug"],
        description=updated_team.get("description"),
        avatar_url=updated_team.get("avatar_url"),
        status=TeamStatus(updated_team["status"]),
        owner_id=updated_team["owner_id"],
        member_count=stats.get("member_count", 1),
        project_count=stats.get("project_count", 0),
        trace_count=stats.get("trace_count", 0),
        total_cost=stats.get("total_cost", 0.0),
        created_at=updated_team["created_at"],
        updated_at=updated_team["updated_at"],
        settings=updated_team.get("settings", {})
    )


@router.delete("/teams/{team_id}")
async def delete_team(
    team_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """删除团队"""
    storage = get_team_storage()
    
    # 只有 owner 可以删除团队
    member = storage.get_team_member(team_id, current_user.id)
    if not member or member["role"] != MemberRole.OWNER:
        raise HTTPException(status_code=403, detail="Only team owner can delete")
    
    team = storage.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    storage.delete_team(team_id)
    
    return {"message": "Team deleted successfully"}


# ==================== 成员管理 ====================

@router.post("/teams/{team_id}/members", response_model=TeamMemberResponse)
async def add_team_member(
    team_id: str,
    member_create: TeamMemberCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """添加团队成员"""
    storage = get_team_storage()
    
    # 检查权限
    member = storage.get_team_member(team_id, current_user.id)
    if not member or member["role"] not in [MemberRole.OWNER, MemberRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    team = storage.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # 检查成员数量限制
    current_members = storage.get_team_members(team_id)
    member_limit = team.get("settings", {}).get("limits", {}).get("members", 10)
    if len(current_members) >= member_limit:
        raise HTTPException(status_code=403, detail=f"Member limit reached (max {member_limit})")
    
    # 查找用户
    user = storage.get_user_by_email(member_create.user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 检查是否已是成员
    existing = storage.get_team_member(team_id, user["id"])
    if existing:
        raise HTTPException(status_code=400, detail="User is already a team member")
    
    member_id = str(uuid.uuid4())
    member_data = {
        "id": member_id,
        "team_id": team_id,
        "user_id": user["id"],
        "user_name": user["name"],
        "user_email": user["email"],
        "role": member_create.role,
        "joined_at": datetime.utcnow(),
        "last_active": None,
        "trace_count": 0
    }
    
    storage.create_team_member(member_data)
    
    return TeamMemberResponse(
        id=member_id,
        team_id=team_id,
        user_id=user["id"],
        user_name=user["name"],
        user_email=user["email"],
        role=member_create.role,
        joined_at=member_data["joined_at"],
        last_active=None,
        trace_count=0
    )


@router.get("/teams/{team_id}/members", response_model=TeamMemberListResponse)
async def list_team_members(
    team_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """获取团队成员列表"""
    storage = get_team_storage()
    
    # 检查权限
    member = storage.get_team_member(team_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a team member")
    
    members = storage.get_team_members(team_id)
    
    member_responses = [
        TeamMemberResponse(
            id=m["id"],
            team_id=m["team_id"],
            user_id=m["user_id"],
            user_name=m["user_name"],
            user_email=m["user_email"],
            role=MemberRole(m["role"]),
            joined_at=m["joined_at"],
            last_active=m.get("last_active"),
            trace_count=m.get("trace_count", 0)
        )
        for m in members
    ]
    
    return TeamMemberListResponse(
        members=member_responses,
        total=len(members)
    )


@router.patch("/teams/{team_id}/members/{member_id}", response_model=TeamMemberResponse)
async def update_member_role(
    team_id: str,
    member_id: str,
    role_update: TeamMemberUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """更新成员角色"""
    storage = get_team_storage()
    
    # 检查权限
    member = storage.get_team_member(team_id, current_user.id)
    if not member or member["role"] not in [MemberRole.OWNER, MemberRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # 不能修改 owner 角色
    target_member = storage.get_team_member_by_id(member_id)
    if not target_member or target_member["team_id"] != team_id:
        raise HTTPException(status_code=404, detail="Member not found")
    
    if target_member["role"] == MemberRole.OWNER:
        raise HTTPException(status_code=403, detail="Cannot modify owner role")
    
    # 不能将角色提升到比当前用户更高
    if role_update.role in [MemberRole.OWNER, MemberRole.ADMIN] and member["role"] != MemberRole.OWNER:
        raise HTTPException(status_code=403, detail="Only owner can assign admin/owner roles")
    
    storage.update_team_member(member_id, {"role": role_update.role})
    
    updated = storage.get_team_member_by_id(member_id)
    
    return TeamMemberResponse(
        id=updated["id"],
        team_id=updated["team_id"],
        user_id=updated["user_id"],
        user_name=updated["user_name"],
        user_email=updated["user_email"],
        role=MemberRole(updated["role"]),
        joined_at=updated["joined_at"],
        last_active=updated.get("last_active"),
        trace_count=updated.get("trace_count", 0)
    )


@router.delete("/teams/{team_id}/members/{member_id}")
async def remove_team_member(
    team_id: str,
    member_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """移除团队成员"""
    storage = get_team_storage()
    
    # 检查权限
    member = storage.get_team_member(team_id, current_user.id)
    if not member or member["role"] not in [MemberRole.OWNER, MemberRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    target_member = storage.get_team_member_by_id(member_id)
    if not target_member or target_member["team_id"] != team_id:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # 不能移除 owner
    if target_member["role"] == MemberRole.OWNER:
        raise HTTPException(status_code=403, detail="Cannot remove team owner")
    
    storage.delete_team_member(member_id)
    
    return {"message": "Member removed successfully"}


# ==================== 项目管理 ====================

@router.post("/teams/{team_id}/projects", response_model=ProjectResponse)
async def create_project(
    team_id: str,
    project: ProjectCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """创建项目"""
    storage = get_team_storage()
    
    # 检查权限
    member = storage.get_team_member(team_id, current_user.id)
    if not member or member["role"] not in [MemberRole.OWNER, MemberRole.ADMIN, MemberRole.MEMBER]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    team = storage.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # 检查项目数量限制
    current_projects = storage.get_team_projects(team_id)
    project_limit = team.get("settings", {}).get("limits", {}).get("projects", 5)
    if len(current_projects) >= project_limit:
        raise HTTPException(status_code=403, detail=f"Project limit reached (max {project_limit})")
    
    project_id = str(uuid.uuid4())
    
    # 生成 API Key
    api_key_secret = secrets.token_hex(16)
    api_key = f"aw_t_{team_id[:8]}_p_{project_id[:8]}_{api_key_secret}"
    
    project_data = {
        "id": project_id,
        "name": project.name,
        "description": project.description,
        "team_id": team_id,
        "api_key_hash": api_key,  # 生产环境应该 hash 存储
        "created_by": current_user.id,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "settings": project.settings or {}
    }
    
    storage.create_project(project_data)
    
    return ProjectResponse(
        id=project_id,
        name=project.name,
        description=project.description,
        team_id=team_id,
        team_name=team["name"],
        api_key=api_key,  # 仅创建时返回
        is_active=True,
        trace_count=0,
        total_cost=0.0,
        created_at=project_data["created_at"],
        updated_at=project_data["updated_at"],
        settings=project_data["settings"]
    )


@router.get("/teams/{team_id}/projects", response_model=ProjectListResponse)
async def list_team_projects(
    team_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user)
):
    """获取团队项目列表"""
    storage = get_team_storage()
    
    # 检查权限
    member = storage.get_team_member(team_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a team member")
    
    team = storage.get_team(team_id)
    projects = storage.get_team_projects(team_id)
    
    total = len(projects)
    start = (page - 1) * page_size
    end = start + page_size
    
    project_responses = [
        ProjectResponse(
            id=p["id"],
            name=p["name"],
            description=p.get("description"),
            team_id=p["team_id"],
            team_name=team["name"],
            api_key=None,  # 列表不返回 API Key
            is_active=p.get("is_active", True),
            trace_count=p.get("trace_count", 0),
            total_cost=p.get("total_cost", 0.0),
            created_at=p["created_at"],
            updated_at=p["updated_at"],
            settings=p.get("settings", {})
        )
        for p in projects[start:end]
    ]
    
    return ProjectListResponse(
        projects=project_responses,
        total=total,
        page=page,
        page_size=page_size,
        has_more=end < total
    )


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """获取项目详情"""
    storage = get_team_storage()
    
    project = storage.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # 检查权限
    member = storage.get_team_member(project["team_id"], current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a team member")
    
    team = storage.get_team(project["team_id"])
    
    return ProjectResponse(
        id=project["id"],
        name=project["name"],
        description=project.get("description"),
        team_id=project["team_id"],
        team_name=team["name"],
        api_key=None,
        is_active=project.get("is_active", True),
        trace_count=project.get("trace_count", 0),
        total_cost=project.get("total_cost", 0.0),
        created_at=project["created_at"],
        updated_at=project["updated_at"],
        settings=project.get("settings", {})
    )


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """更新项目"""
    storage = get_team_storage()
    
    project = storage.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # 检查权限
    member = storage.get_team_member(project["team_id"], current_user.id)
    if not member or member["role"] not in [MemberRole.OWNER, MemberRole.ADMIN, MemberRole.MEMBER]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    updates = project_update.model_dump(exclude_unset=True)
    updates["updated_at"] = datetime.utcnow()
    
    storage.update_project(project_id, updates)
    
    updated = storage.get_project(project_id)
    team = storage.get_team(updated["team_id"])
    
    return ProjectResponse(
        id=updated["id"],
        name=updated["name"],
        description=updated.get("description"),
        team_id=updated["team_id"],
        team_name=team["name"],
        api_key=None,
        is_active=updated.get("is_active", True),
        trace_count=updated.get("trace_count", 0),
        total_cost=updated.get("total_cost", 0.0),
        created_at=updated["created_at"],
        updated_at=updated["updated_at"],
        settings=updated.get("settings", {})
    )


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """删除项目"""
    storage = get_team_storage()
    
    project = storage.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # 检查权限
    member = storage.get_team_member(project["team_id"], current_user.id)
    if not member or member["role"] not in [MemberRole.OWNER, MemberRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    storage.delete_project(project_id)
    
    return {"message": "Project deleted successfully"}


@router.get("/projects/{project_id}/traces")
async def get_project_traces(
    project_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user)
):
    """获取项目的 traces"""
    storage = get_team_storage()
    
    project = storage.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # 检查权限
    member = storage.get_team_member(project["team_id"], current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a team member")
    
    traces = storage.get_traces_by_project(project_id, page, page_size)
    
    return traces


# ==================== 团队统计 ====================

@router.get("/teams/{team_id}/stats", response_model=TeamStatsResponse)
async def get_team_stats(
    team_id: str,
    period: str = Query("7d", description="统计周期: 1d, 7d, 30d"),
    current_user: UserResponse = Depends(get_current_user)
):
    """获取团队统计"""
    storage = get_team_storage()
    
    # 检查权限
    member = storage.get_team_member(team_id, current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Not a team member")
    
    team = storage.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # 计算时间范围
    period_days = {"1d": 1, "7d": 7, "30d": 30}.get(period, 7)
    period_end = datetime.utcnow()
    period_start = period_end - timedelta(days=period_days)
    
    stats = storage.get_team_stats(team_id, period_start, period_end)
    
    return TeamStatsResponse(
        team_id=team_id,
        team_name=team["name"],
        total_traces=stats.get("total_traces", 0),
        running_traces=stats.get("running_traces", 0),
        completed_traces=stats.get("completed_traces", 0),
        failed_traces=stats.get("failed_traces", 0),
        total_cost=stats.get("total_cost", 0.0),
        cost_by_provider=stats.get("cost_by_provider", {}),
        cost_by_project=stats.get("cost_by_project", {}),
        total_tokens=stats.get("total_tokens", 0),
        input_tokens=stats.get("input_tokens", 0),
        output_tokens=stats.get("output_tokens", 0),
        period_start=period_start,
        period_end=period_end,
        active_members=stats.get("active_members", 0),
        member_stats=stats.get("member_stats", [])
    )