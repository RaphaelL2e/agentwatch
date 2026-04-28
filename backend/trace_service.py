"""
AgentWatch Trace 服务层
处理 Trace 数据的存储和查询

支持多种存储后端：
- memory: 内存存储（默认）
- clickhouse: ClickHouse（生产）
- postgres: PostgreSQL（待实现）
- mongodb: MongoDB（待实现）
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from collections import defaultdict

from models import (
    TraceCreate,
    TraceUpdate,
    TraceResponse,
    TraceListResponse,
    TraceStatus,
    TraceEvent,
    CostSummary,
    AgentProvider,
)
from storage import TraceStorage, StorageFactory, MemoryStorage


class TraceService:
    """Trace 服务 - 业务逻辑层"""
    
    # 存储实例（依赖注入）
    _storage: TraceStorage = None
    
    # Token 成本配置 (USD per 1K tokens)
    TOKEN_COSTS = {
        "openai": {
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        },
        "anthropic": {
            "claude-3-opus": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
            "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
            "claude-4.7": {"input": 0.003, "output": 0.015},
        },
        "deepseek": {
            "deepseek-v4": {
                "input": 0.00014,
                "output": 0.00028,
            },  # ¥0.3/M tokens ≈ $0.00014
            "deepseek-chat": {"input": 0.00007, "output": 0.00014},
        },
        "google": {
            "gemini-pro": {"input": 0.00025, "output": 0.0005},
            "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
        },
    }

    DEFAULT_COST = {"input": 0.001, "output": 0.002}  # 默认成本
    
    @classmethod
    def init_storage(cls, storage_type: str = "memory", **kwargs) -> None:
        """
        初始化存储
        
        Args:
            storage_type: 存储类型（memory, clickhouse 等）
            **kwargs: 存储配置参数
            
        Examples:
            # 内存存储
            TraceService.init_storage("memory")
            
            # ClickHouse 存储
            TraceService.init_storage(
                "clickhouse",
                host="localhost",
                port=9000
            )
        """
        cls._storage = StorageFactory.create(storage_type, **kwargs)
    
    @classmethod
    def get_storage(cls) -> TraceStorage:
        """获取存储实例（懒加载）"""
        if cls._storage is None:
            cls._storage = MemoryStorage()
        return cls._storage

    @staticmethod
    def generate_trace_id() -> str:
        """生成 Trace ID"""
        return f"tr_{uuid.uuid4().hex[:12]}"

    @staticmethod
    def calculate_cost(
        provider: str, model: str, input_tokens: int, output_tokens: int
    ) -> float:
        """计算成本"""
        provider_lower = provider.lower()
        model_lower = model.lower()

        costs = TraceService.TOKEN_COSTS.get(provider_lower, {})
        model_costs = costs.get(model_lower, TraceService.DEFAULT_COST)

        input_cost = (input_tokens / 1000) * model_costs["input"]
        output_cost = (output_tokens / 1000) * model_costs["output"]

        return input_cost + output_cost

    @staticmethod
    def create_trace(trace_data: TraceCreate) -> TraceResponse:
        """创建 Trace"""
        storage = TraceService.get_storage()
        
        # 添加成本计算逻辑
        trace = storage.create_trace(trace_data)
        
        return trace

    @staticmethod
    def get_trace(trace_id: str) -> Optional[TraceResponse]:
        """获取 Trace"""
        storage = TraceService.get_storage()
        return storage.get_trace(trace_id)

    @staticmethod
    def update_trace(
        trace_id: str, update_data: TraceUpdate
    ) -> Optional[TraceResponse]:
        """更新 Trace（包含成本计算）"""
        storage = TraceService.get_storage()
        
        trace = storage.get_trace(trace_id)
        if not trace:
            return None
        
        # 重新计算成本（如果 token 有变化）
        if update_data.events:
            # 获取更新后的 trace
            updated = storage.update_trace(trace_id, update_data)
            if updated and updated.total_tokens > 0:
                # 计算成本
                cost = TraceService.calculate_cost(
                    updated.provider,
                    updated.model,
                    updated.total_input_tokens,
                    updated.total_output_tokens
                )
                # 再次更新成本
                storage.update_trace(
                    trace_id,
                    TraceUpdate(total_cost=cost)
                )
        else:
            updated = storage.update_trace(trace_id, update_data)
        
        return updated

    @staticmethod
    def add_event(trace_id: str, event: TraceEvent) -> Optional[TraceResponse]:
        """添加事件到 Trace"""
        return TraceService.update_trace(trace_id, TraceUpdate(events=[event]))

    @staticmethod
    def list_traces(
        page: int = 1,
        page_size: int = 20,
        agent_id: Optional[str] = None,
        provider: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> TraceListResponse:
        """列出 Traces"""
        storage = TraceService.get_storage()
        return storage.list_traces(
            page=page,
            page_size=page_size,
            agent_id=agent_id,
            provider=provider,
            status=status,
            start_time=start_time,
            end_time=end_time,
        )

    @staticmethod
    def get_cost_summary(
        provider: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[CostSummary]:
        """获取成本汇总"""
        storage = TraceService.get_storage()
        return storage.get_cost_summary(
            provider=provider,
            start_time=start_time,
            end_time=end_time,
        )

    @staticmethod
    def delete_trace(trace_id: str) -> bool:
        """删除 Trace"""
        storage = TraceService.get_storage()
        return storage.delete_trace(trace_id)

    @staticmethod
    def get_stats() -> Dict[str, Any]:
        """获取统计信息"""
        storage = TraceService.get_storage()
        return storage.get_stats()
    
    @staticmethod
    def get_storage_info() -> Dict[str, Any]:
        """获取存储信息"""
        storage = TraceService.get_storage()
        return storage.health_check()
