"""
AgentWatch 存储层抽象接口
支持多种数据库实现的统一接口设计

设计原则：
- Repository Pattern（仓储模式）
- 依赖倒置原则（DIP）
- 开闭原则（OCP）- 易于扩展新实现
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime

from models import (
    TraceResponse,
    TraceListResponse,
    CostSummary,
    TraceCreate,
    TraceUpdate,
    TraceEvent,
)


class TraceStorage(ABC):
    """
    Trace 存储抽象接口
    
    所有存储实现必须继承此接口并实现所有方法。
    支持：Memory、ClickHouse、PostgreSQL、MongoDB、SQLite 等
    """
    
    # ==================== CRUD 操作 ====================
    
    @abstractmethod
    def create_trace(self, trace_data: TraceCreate) -> TraceResponse:
        """
        创建新的 Trace
        
        Args:
            trace_data: Trace 创建数据
            
        Returns:
            TraceResponse: 创建成功的 Trace 对象
        """
        pass
    
    @abstractmethod
    def get_trace(self, trace_id: str) -> Optional[TraceResponse]:
        """
        获取单个 Trace
        
        Args:
            trace_id: Trace ID
            
        Returns:
            TraceResponse 或 None
        """
        pass
    
    @abstractmethod
    def update_trace(
        self, trace_id: str, update_data: TraceUpdate
    ) -> Optional[TraceResponse]:
        """
        更新 Trace
        
        Args:
            trace_id: Trace ID
            update_data: 更新数据
            
        Returns:
            更新后的 Trace 或 None（如果不存在）
        """
        pass
    
    @abstractmethod
    def delete_trace(self, trace_id: str) -> bool:
        """
        删除 Trace
        
        Args:
            trace_id: Trace ID
            
        Returns:
            是否删除成功
        """
        pass
    
    # ==================== 查询操作 ====================
    
    @abstractmethod
    def list_traces(
        self,
        page: int = 1,
        page_size: int = 20,
        agent_id: Optional[str] = None,
        provider: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> TraceListResponse:
        """
        列出 Traces（支持过滤和分页）
        
        Args:
            page: 页码
            page_size: 每页数量
            agent_id: Agent ID 过滤
            provider: Provider 过滤
            status: 状态过滤
            start_time: 开始时间过滤
            end_time: 结束时间过滤
            
        Returns:
            TraceListResponse: 分页结果
        """
        pass
    
    @abstractmethod
    def get_cost_summary(
        self,
        provider: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[CostSummary]:
        """
        获取成本汇总
        
        Args:
            provider: Provider 过滤
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            CostSummary 列表
        """
        pass
    
    # ==================== 统计操作 ====================
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计数据字典，包含：
            - total_traces: 总数
            - running_traces: 运行中
            - completed_traces: 已完成
            - failed_traces: 已失败
            - total_cost: 总成本
            - providers: Provider 统计
        """
        pass
    
    @abstractmethod
    def get_count_by_provider(self) -> Dict[str, int]:
        """
        获取各 Provider 的 Trace 数量
        
        Returns:
            Provider -> 数量 的字典
        """
        pass
    
    # ==================== 事件操作 ====================
    
    @abstractmethod
    def add_event(self, trace_id: str, event: TraceEvent) -> Optional[TraceResponse]:
        """
        添加事件到 Trace
        
        Args:
            trace_id: Trace ID
            event: 事件数据
            
        Returns:
            更新后的 Trace 或 None
        """
        pass
    
    # ==================== 批量操作 ====================
    
    @abstractmethod
    def bulk_create_traces(
        self, traces_data: List[TraceCreate]
    ) -> List[TraceResponse]:
        """
        批量创建 Traces
        
        Args:
            traces_data: Trace 创建数据列表
            
        Returns:
            创建成功的 Trace 列表
        """
        pass
    
    @abstractmethod
    def bulk_delete_traces(self, trace_ids: List[str]) -> int:
        """
        批量删除 Traces
        
        Args:
            trace_ids: Trace ID 列表
            
        Returns:
            删除的数量
        """
        pass
    
    # ==================== 清理操作 ====================
    
    @abstractmethod
    def clear_all(self) -> int:
        """
        清空所有数据（谨慎使用！）
        
        Returns:
            清除的数量
        """
        pass
    
    # ==================== 健康检查 ====================
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        存储健康检查
        
        Returns:
            健康状态信息，包含：
            - status: healthy/unhealthy
            - type: 存储类型
            - connection: 连接状态
            - metrics: 存储指标（可选）
        """
        pass


class StorageFactory:
    """
    存储工厂
    
    用于创建不同类型的存储实现
    """
    
    _registry: Dict[str, type] = {}
    
    @classmethod
    def register(cls, name: str, storage_class: type) -> None:
        """
        注册存储实现
        
        Args:
            name: 存储类型名称（如 'memory', 'clickhouse'）
            storage_class: 存储类
        """
        cls._registry[name] = storage_class
    
    @classmethod
    def create(cls, name: str, **kwargs) -> TraceStorage:
        """
        创建存储实例
        
        Args:
            name: 存储类型名称
            **kwargs: 存储配置参数
            
        Returns:
            TraceStorage 实例
            
        Raises:
            ValueError: 未注册的存储类型
        """
        if name not in cls._registry:
            raise ValueError(f"Unknown storage type: {name}. "
                           f"Available: {list(cls._registry.keys())}")
        
        return cls._registry[name](**kwargs)
    
    @classmethod
    def list_available(cls) -> List[str]:
        """
        列出可用的存储类型
        
        Returns:
            可用存储类型列表
        """
        return list(cls._registry.keys())


# 存储配置类型
StorageConfig = Dict[str, Any]

"""
存储配置示例：

Memory 存储配置（默认）：
{
    "type": "memory",
    "max_size": 10000,  # 最大存储数量（可选）
}

ClickHouse 存储配置：
{
    "type": "clickhouse",
    "host": "localhost",
    "port": 9000,
    "database": "agentwatch",
    "user": "default",
    "password": "",
    "table": "traces",
}

PostgreSQL 存储配置：
{
    "type": "postgres",
    "host": "localhost",
    "port": 5432,
    "database": "agentwatch",
    "user": "postgres",
    "password": "password",
}

SQLite 存储配置：
{
    "type": "sqlite",
    "path": "/data/agentwatch.db",
}

MongoDB 存储配置：
{
    "type": "mongodb",
    "uri": "mongodb://localhost:27017",
    "database": "agentwatch",
    "collection": "traces",
}
"""