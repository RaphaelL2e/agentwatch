"""
AgentWatch 团队协作存储层
Phase 2 功能扩展
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime


class TeamStorage(ABC):
    """
    团队存储抽象接口
    
    支持团队、成员、项目的 CRUD 操作
    """
    
    # ==================== 团队操作 ====================
    
    @abstractmethod
    def create_team(self, team_data: Dict[str, Any]) -> str:
        """创建团队，返回团队ID"""
        pass
    
    @abstractmethod
    def get_team(self, team_id: str) -> Optional[Dict[str, Any]]:
        """获取团队"""
        pass
    
    @abstractmethod
    def get_user_teams(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户所属的所有团队"""
        pass
    
    @abstractmethod
    def update_team(self, team_id: str, updates: Dict[str, Any]) -> bool:
        """更新团队"""
        pass
    
    @abstractmethod
    def delete_team(self, team_id: str) -> bool:
        """删除团队"""
        pass
    
    # ==================== 成员操作 ====================
    
    @abstractmethod
    def create_team_member(self, member_data: Dict[str, Any]) -> str:
        """创建团队成员"""
        pass
    
    @abstractmethod
    def get_team_member(self, team_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """获取团队成员"""
        pass
    
    @abstractmethod
    def get_team_member_by_id(self, member_id: str) -> Optional[Dict[str, Any]]:
        """通过成员ID获取"""
        pass
    
    @abstractmethod
    def get_team_members(self, team_id: str) -> List[Dict[str, Any]]:
        """获取团队所有成员"""
        pass
    
    @abstractmethod
    def update_team_member(self, member_id: str, updates: Dict[str, Any]) -> bool:
        """更新团队成员"""
        pass
    
    @abstractmethod
    def delete_team_member(self, member_id: str) -> bool:
        """删除团队成员"""
        pass
    
    # ==================== 项目操作 ====================
    
    @abstractmethod
    def create_project(self, project_data: Dict[str, Any]) -> str:
        """创建项目"""
        pass
    
    @abstractmethod
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """获取项目"""
        pass
    
    @abstractmethod
    def get_team_projects(self, team_id: str) -> List[Dict[str, Any]]:
        """获取团队所有项目"""
        pass
    
    @abstractmethod
    def update_project(self, project_id: str, updates: Dict[str, Any]) -> bool:
        """更新项目"""
        pass
    
    @abstractmethod
    def delete_project(self, project_id: str) -> bool:
        """删除项目"""
        pass
    
    @abstractmethod
    def get_traces_by_project(self, project_id: str, page: int, page_size: int) -> Dict[str, Any]:
        """获取项目的 traces"""
        pass
    
    # ==================== 用户操作 ====================
    
    @abstractmethod
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """通过邮箱获取用户"""
        pass
    
    # ==================== 统计操作 ====================
    
    @abstractmethod
    def get_team_stats(self, team_id: str, period_start: datetime = None, period_end: datetime = None) -> Dict[str, Any]:
        """获取团队统计"""
        pass


class MemoryTeamStorage(TeamStorage):
    """
    内存存储实现 - 用于开发测试
    """
    
    def __init__(self):
        self.teams: Dict[str, Dict] = {}
        self.team_members: Dict[str, Dict] = {}  # member_id -> member_data
        self.team_memberships: Dict[str, List[str]] = {}  # team_id -> [member_ids]
        self.user_teams: Dict[str, List[str]] = {}  # user_id -> [team_ids]
        self.projects: Dict[str, Dict] = {}
        self.team_projects: Dict[str, List[str]] = {}  # team_id -> [project_ids]
        self.users: Dict[str, Dict] = {}  # 模拟用户数据
    
    # ==================== 团队操作 ====================
    
    def create_team(self, team_data: Dict[str, Any]) -> str:
        team_id = team_data["id"]
        self.teams[team_id] = team_data
        self.team_memberships[team_id] = []
        self.team_projects[team_id] = []
        return team_id
    
    def get_team(self, team_id: str) -> Optional[Dict[str, Any]]:
        return self.teams.get(team_id)
    
    def get_user_teams(self, user_id: str) -> List[Dict[str, Any]]:
        team_ids = self.user_teams.get(user_id, [])
        return [self.teams[tid] for tid in team_ids if tid in self.teams]
    
    def update_team(self, team_id: str, updates: Dict[str, Any]) -> bool:
        if team_id not in self.teams:
            return False
        self.teams[team_id].update(updates)
        return True
    
    def delete_team(self, team_id: str) -> bool:
        if team_id not in self.teams:
            return False
        
        # 删除相关数据
        del self.teams[team_id]
        
        # 删除成员
        member_ids = self.team_memberships.get(team_id, [])
        for mid in member_ids:
            if mid in self.team_members:
                user_id = self.team_members[mid]["user_id"]
                if user_id in self.user_teams:
                    self.user_teams[user_id] = [tid for tid in self.user_teams[user_id] if tid != team_id]
                del self.team_members[mid]
        
        del self.team_memberships[team_id]
        
        # 删除项目
        project_ids = self.team_projects.get(team_id, [])
        for pid in project_ids:
            if pid in self.projects:
                del self.projects[pid]
        
        del self.team_projects[team_id]
        
        return True
    
    # ==================== 成员操作 ====================
    
    def create_team_member(self, member_data: Dict[str, Any]) -> str:
        member_id = member_data["id"]
        team_id = member_data["team_id"]
        user_id = member_data["user_id"]
        
        self.team_members[member_id] = member_data
        
        if team_id not in self.team_memberships:
            self.team_memberships[team_id] = []
        self.team_memberships[team_id].append(member_id)
        
        if user_id not in self.user_teams:
            self.user_teams[user_id] = []
        self.user_teams[user_id].append(team_id)
        
        return member_id
    
    def get_team_member(self, team_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        member_ids = self.team_memberships.get(team_id, [])
        for mid in member_ids:
            member = self.team_members.get(mid)
            if member and member["user_id"] == user_id:
                return member
        return None
    
    def get_team_member_by_id(self, member_id: str) -> Optional[Dict[str, Any]]:
        return self.team_members.get(member_id)
    
    def get_team_members(self, team_id: str) -> List[Dict[str, Any]]:
        member_ids = self.team_memberships.get(team_id, [])
        return [self.team_members[mid] for mid in member_ids if mid in self.team_members]
    
    def update_team_member(self, member_id: str, updates: Dict[str, Any]) -> bool:
        if member_id not in self.team_members:
            return False
        self.team_members[member_id].update(updates)
        return True
    
    def delete_team_member(self, member_id: str) -> bool:
        if member_id not in self.team_members:
            return False
        
        member = self.team_members[member_id]
        team_id = member["team_id"]
        user_id = member["user_id"]
        
        # 从团队成员列表移除
        if team_id in self.team_memberships:
            self.team_memberships[team_id] = [mid for mid in self.team_memberships[team_id] if mid != member_id]
        
        # 从用户团队列表移除
        if user_id in self.user_teams:
            self.user_teams[user_id] = [tid for tid in self.user_teams[user_id] if tid != team_id]
        
        del self.team_members[member_id]
        return True
    
    # ==================== 项目操作 ====================
    
    def create_project(self, project_data: Dict[str, Any]) -> str:
        project_id = project_data["id"]
        team_id = project_data["team_id"]
        
        self.projects[project_id] = project_data
        
        if team_id not in self.team_projects:
            self.team_projects[team_id] = []
        self.team_projects[team_id].append(project_id)
        
        return project_id
    
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        return self.projects.get(project_id)
    
    def get_team_projects(self, team_id: str) -> List[Dict[str, Any]]:
        project_ids = self.team_projects.get(team_id, [])
        return [self.projects[pid] for pid in project_ids if pid in self.projects]
    
    def update_project(self, project_id: str, updates: Dict[str, Any]) -> bool:
        if project_id not in self.projects:
            return False
        self.projects[project_id].update(updates)
        return True
    
    def delete_project(self, project_id: str) -> bool:
        if project_id not in self.projects:
            return False
        
        project = self.projects[project_id]
        team_id = project["team_id"]
        
        if team_id in self.team_projects:
            self.team_projects[team_id] = [pid for pid in self.team_projects[team_id] if pid != project_id]
        
        del self.projects[project_id]
        return True
    
    def get_traces_by_project(self, project_id: str, page: int, page_size: int) -> Dict[str, Any]:
        # TODO: 实现项目 traces 查询
        return {"traces": [], "total": 0, "page": page, "page_size": page_size}
    
    # ==================== 用户操作 ====================
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        # 模拟用户数据 - 实际应从 auth 系统获取
        for user_id, user in self.users.items():
            if user.get("email") == email:
                return user
        return None
    
    def set_user(self, user_id: str, user_data: Dict[str, Any]):
        """设置用户数据（用于测试）"""
        self.users[user_id] = user_data
    
    # ==================== 统计操作 ====================
    
    def get_team_stats(self, team_id: str, period_start: datetime = None, period_end: datetime = None) -> Dict[str, Any]:
        member_ids = self.team_memberships.get(team_id, [])
        project_ids = self.team_projects.get(team_id, [])
        
        return {
            "member_count": len(member_ids),
            "project_count": len(project_ids),
            "trace_count": 0,
            "total_cost": 0.0,
            "total_traces": 0,
            "running_traces": 0,
            "completed_traces": 0,
            "failed_traces": 0,
            "total_tokens": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "cost_by_provider": {},
            "cost_by_project": {},
            "active_members": len(member_ids),
            "member_stats": []
        }


# 全局团队存储实例
_team_storage: Optional[TeamStorage] = None


def get_team_storage() -> TeamStorage:
    """获取团队存储实例"""
    global _team_storage
    if _team_storage is None:
        _team_storage = MemoryTeamStorage()
    return _team_storage


def set_team_storage(storage: TeamStorage):
    """设置团队存储实例"""
    global _team_storage
    _team_storage = storage