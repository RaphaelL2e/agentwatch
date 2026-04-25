"""
AgentWatch ClickHouse 客户端
连接和操作 ClickHouse 数据库
"""

import os
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio

# ClickHouse 驱动（后续添加）
# from clickhouse_driver import Client

from models import (
    TraceCreate, TraceUpdate, TraceResponse, TraceListResponse,
    TraceStatus, TraceEvent, CostSummary
)


class ClickHouseClient:
    """
    ClickHouse 客户端
    
    Day 2: 使用内存存储作为过渡
    Day 3+: 连接真实 ClickHouse
    """
    
    def __init__(self):
        self.host = os.getenv("CLICKHOUSE_HOST", "localhost")
        self.port = int(os.getenv("CLICKHOUSE_PORT", "9000"))
        self.database = "agentwatch"
        self._client = None
        self._connected = False
        
    def connect(self):
        """连接 ClickHouse"""
        # TODO: 实现真实连接
        # self._client = Client(host=self.host, port=self.port, database=self.database)
        # self._connected = True
        print(f"📍 ClickHouse configured: {self.host}:{self.port}/{self.database}")
        self._connected = True  # Day 2 模拟连接
        return self
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._connected
    
    def close(self):
        """关闭连接"""
        if self._client:
            self._client.disconnect()
        self._connected = False


# 全局客户端实例
clickhouse_client = ClickHouseClient()


def init_clickhouse():
    """初始化 ClickHouse 连接"""
    return clickhouse_client.connect()


def get_clickhouse() -> ClickHouseClient:
    """获取 ClickHouse 客户端"""
    if not clickhouse_client.is_connected():
        clickhouse_client.connect()
    return clickhouse_client


# ==================== SQL 辅助函数 ====================

def trace_to_row(trace: TraceResponse) -> Dict[str, Any]:
    """将 Trace 对象转换为 ClickHouse 行"""
    return {
        "trace_id": trace.trace_id,
        "agent_id": trace.agent_id,
        "agent_name": trace.agent_name,
        "provider": trace.provider.value if hasattr(trace.provider, 'value') else str(trace.provider),
        "model": trace.model,
        "status": trace.status.value if hasattr(trace.status, 'value') else str(trace.status),
        "session_id": trace.session_id or "",
        "user_id": trace.user_id or "",
        "prompt": trace.prompt or "",
        "total_input_tokens": trace.total_input_tokens,
        "total_output_tokens": trace.total_output_tokens,
        "total_tokens": trace.total_tokens,
        "total_cost": trace.total_cost,
        "duration_ms": trace.duration_ms,
        "error_message": trace.error_message or "",
        "created_at": trace.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": trace.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
        "completed_at": trace.completed_at.strftime("%Y-%m-%d %H:%M:%S") if trace.completed_at else None,
        "metadata": json.dumps(trace.metadata),
    }


def event_to_row(trace_id: str, event: TraceEvent) -> Dict[str, Any]:
    """将 Event 对象转换为 ClickHouse 行"""
    return {
        "trace_id": trace_id,
        "event_id": event.event_id,
        "timestamp": event.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "event_type": event.event_type,
        "agent_name": event.agent_name or "",
        "model": event.model or "",
        "input_tokens": event.input_tokens,
        "output_tokens": event.output_tokens,
        "latency_ms": event.latency_ms,
        "content": event.content or "",
        "metadata": json.dumps(event.metadata or {}),
    }


# ==================== 查询构建器 ====================

class TraceQueryBuilder:
    """Trace 查询 SQL 构建器"""
    
    @staticmethod
    def insert_trace(trace: TraceResponse) -> str:
        """构建插入 Trace SQL"""
        row = trace_to_row(trace)
        columns = ", ".join(row.keys())
        values = ", ".join([f"'{v}'" if isinstance(v, str) else str(v) for v in row.values()])
        return f"INSERT INTO agentwatch.traces ({columns}) VALUES ({values})"
    
    @staticmethod
    def insert_event(trace_id: str, event: TraceEvent) -> str:
        """构建插入 Event SQL"""
        row = event_to_row(trace_id, event)
        columns = ", ".join(row.keys())
        values = ", ".join([f"'{v}'" if isinstance(v, str) else str(v) for v in row.values()])
        return f"INSERT INTO agentwatch.trace_events ({columns}) VALUES ({values})"
    
    @staticmethod
    def select_trace(trace_id: str) -> str:
        """构建查询 Trace SQL"""
        return f"SELECT * FROM agentwatch.traces WHERE trace_id = '{trace_id}' LIMIT 1"
    
    @staticmethod
    def select_traces(
        page: int = 1,
        page_size: int = 20,
        agent_id: Optional[str] = None,
        provider: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> str:
        """构建查询 Traces SQL"""
        where_clauses = []
        
        if agent_id:
            where_clauses.append(f"agent_id = '{agent_id}'")
        if provider:
            where_clauses.append(f"provider = '{provider}'")
        if status:
            where_clauses.append(f"status = '{status}'")
        if start_time:
            where_clauses.append(f"created_at >= '{start_time.strftime('%Y-%m-%d %H:%M:%S')}'")
        if end_time:
            where_clauses.append(f"created_at <= '{end_time.strftime('%Y-%m-%d %H:%M:%S')}'")
        
        where = " AND ".join(where_clauses) if where_clauses else "1=1"
        offset = (page - 1) * page_size
        
        return f"""
        SELECT * FROM agentwatch.traces 
        WHERE {where}
        ORDER BY created_at DESC
        LIMIT {page_size}
        OFFSET {offset}
        """
    
    @staticmethod
    def count_traces(
        agent_id: Optional[str] = None,
        provider: Optional[str] = None,
        status: Optional[str] = None,
    ) -> str:
        """构建统计 Traces SQL"""
        where_clauses = []
        
        if agent_id:
            where_clauses.append(f"agent_id = '{agent_id}'")
        if provider:
            where_clauses.append(f"provider = '{provider}'")
        if status:
            where_clauses.append(f"status = '{status}'")
        
        where = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        return f"SELECT count() as total FROM agentwatch.traces WHERE {where}"
    
    @staticmethod
    def cost_summary(
        provider: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> str:
        """构建成本汇总 SQL"""
        where_clauses = ["status = 'completed'"]
        
        if provider:
            where_clauses.append(f"provider = '{provider}'")
        if start_time:
            where_clauses.append(f"created_at >= '{start_time.strftime('%Y-%m-%d %H:%M:%S')}'")
        if end_time:
            where_clauses.append(f"created_at <= '{end_time.strftime('%Y-%m-%d %H:%M:%S')}'")
        
        where = " AND ".join(where_clauses)
        
        return f"""
        SELECT 
            provider,
            model,
            count() as total_traces,
            sum(total_tokens) as total_tokens,
            sum(total_cost) as total_cost,
            avg(duration_ms) as avg_latency_ms
        FROM agentwatch.traces
        WHERE {where}
        GROUP BY provider, model
        ORDER BY total_cost DESC
        """