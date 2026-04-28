"""
AgentWatch SQLite 存储实现
轻量级数据库，适合单机部署和开发测试

特点：
- 单文件数据库，无需额外服务
- 零配置，自动创建数据库
- 支持 SQL 查询和索引
- 数据持久化，重启不丢失
- Python 内置支持（sqlite3）
"""

import uuid
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

from storage.base import TraceStorage, StorageFactory
from models import (
    TraceResponse,
    TraceListResponse,
    CostSummary,
    TraceCreate,
    TraceUpdate,
    TraceEvent,
    TraceStatus,
    AgentProvider,
)


class SQLiteStorage(TraceStorage):
    """
    SQLite 存储实现
    
    使用 SQLite 数据库存储 Trace 数据。
    适合单机部署、边缘设备、IoT场景。
    """
    
    # 创建表的 SQL
    CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS traces (
        trace_id TEXT PRIMARY KEY,
        agent_id TEXT,
        agent_name TEXT NOT NULL,
        provider TEXT NOT NULL,
        model TEXT NOT NULL,
        status TEXT NOT NULL,
        session_id TEXT,
        user_id TEXT,
        prompt TEXT,
        events TEXT,  -- JSON array
        total_input_tokens INTEGER DEFAULT 0,
        total_output_tokens INTEGER DEFAULT 0,
        total_tokens INTEGER DEFAULT 0,
        total_cost REAL DEFAULT 0.0,
        duration_ms INTEGER DEFAULT 0,
        error_message TEXT,
        metadata TEXT,  -- JSON object
        created_at TIMESTAMP NOT NULL,
        updated_at TIMESTAMP NOT NULL,
        completed_at TIMESTAMP
    );
    
    -- 索引优化查询性能
    CREATE INDEX IF NOT EXISTS idx_traces_created_at ON traces(created_at);
    CREATE INDEX IF NOT EXISTS idx_traces_provider ON traces(provider);
    CREATE INDEX IF NOT EXISTS idx_traces_status ON traces(status);
    CREATE INDEX IF NOT EXISTS idx_traces_agent_id ON traces(agent_id);
    """
    
    def __init__(
        self,
        path: str = "agentwatch.db",
        auto_create: bool = True,
    ):
        """
        初始化 SQLite 存储
        
        Args:
            path: 数据库文件路径（默认 agentwatch.db）
            auto_create: 是否自动创建数据库和表
        """
        self.path = Path(path)
        self._conn: Optional[sqlite3.Connection] = None
        
        if auto_create:
            self._init_db()
    
    def _init_db(self) -> None:
        """初始化数据库"""
        # 确保目录存在
        self.path.parent.mkdir(parents=True, exist_ok=True)
        
        # 创建连接
        self._conn = sqlite3.connect(
            str(self.path),
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        
        # 启用外键约束
        self._conn.execute("PRAGMA foreign_keys = ON")
        
        # 创建表和索引
        self._conn.executescript(self.CREATE_TABLE_SQL)
        self._conn.commit()
    
    def _get_conn(self) -> sqlite3.Connection:
        """获取数据库连接"""
        if self._conn is None:
            self._init_db()
        return self._conn
    
    def _row_to_trace(self, row: tuple) -> TraceResponse:
        """数据库行转换为 TraceResponse"""
        (
            trace_id, agent_id, agent_name, provider, model, status,
            session_id, user_id, prompt, events_json,
            total_input, total_output, total, cost, duration,
            error, metadata_json, created, updated, completed
        ) = row
        
        events = []
        if events_json:
            try:
                events_data = json.loads(events_json)
                events = [TraceEvent(**e) for e in events_data]
            except:
                pass
        
        metadata = {}
        if metadata_json:
            try:
                metadata = json.loads(metadata_json)
            except:
                pass
        
        return TraceResponse(
            trace_id=trace_id,
            agent_id=agent_id,
            agent_name=agent_name,
            provider=provider,
            model=model,
            status=TraceStatus(status),
            session_id=session_id,
            user_id=user_id,
            prompt=prompt,
            events=events,
            total_input_tokens=total_input or 0,
            total_output_tokens=total_output or 0,
            total_tokens=total or 0,
            total_cost=cost or 0.0,
            duration_ms=duration or 0,
            error_message=error,
            metadata=metadata,
            created_at=created,
            updated_at=updated,
            completed_at=completed,
        )
    
    def _trace_to_dict(self, trace: TraceResponse) -> Dict:
        """TraceResponse 转换为数据库字典"""
        return {
            'trace_id': trace.trace_id,
            'agent_id': trace.agent_id or '',
            'agent_name': trace.agent_name,
            'provider': trace.provider,
            'model': trace.model,
            'status': trace.status.value,
            'session_id': trace.session_id or '',
            'user_id': trace.user_id or '',
            'prompt': trace.prompt or '',
            'events': json.dumps([e.dict() for e in trace.events]),
            'total_input_tokens': trace.total_input_tokens,
            'total_output_tokens': trace.total_output_tokens,
            'total_tokens': trace.total_tokens,
            'total_cost': trace.total_cost,
            'duration_ms': trace.duration_ms,
            'error_message': trace.error_message or '',
            'metadata': json.dumps(trace.metadata),
            'created_at': trace.created_at,
            'updated_at': trace.updated_at,
            'completed_at': trace.completed_at,
        }
    
    # ==================== CRUD 操作 ====================
    
    def create_trace(self, trace_data: TraceCreate) -> TraceResponse:
        """创建 Trace"""
        conn = self._get_conn()
        now = datetime.utcnow()
        trace_id = trace_data.trace_id or f"tr_{uuid.uuid4().hex[:12]}"
        
        trace = TraceResponse(
            trace_id=trace_id,
            agent_id=trace_data.agent_id,
            agent_name=trace_data.agent_name,
            provider=trace_data.provider,
            model=trace_data.model,
            status=TraceStatus.RUNNING,
            session_id=trace_data.session_id,
            user_id=trace_data.user_id,
            prompt=trace_data.prompt,
            events=[],
            created_at=now,
            updated_at=now,
            metadata=trace_data.metadata or {},
        )
        
        conn.execute(
            """
            INSERT INTO traces (
                trace_id, agent_id, agent_name, provider, model, status,
                session_id, user_id, prompt, events,
                total_input_tokens, total_output_tokens, total_tokens, total_cost, duration_ms,
                error_message, metadata, created_at, updated_at, completed_at
            ) VALUES (
                :trace_id, :agent_id, :agent_name, :provider, :model, :status,
                :session_id, :user_id, :prompt, :events,
                :total_input_tokens, :total_output_tokens, :total_tokens, :total_cost, :duration_ms,
                :error_message, :metadata, :created_at, :updated_at, :completed_at
            )
            """,
            self._trace_to_dict(trace)
        )
        conn.commit()
        
        return trace
    
    def get_trace(self, trace_id: str) -> Optional[TraceResponse]:
        """获取 Trace"""
        conn = self._get_conn()
        
        cursor = conn.execute(
            """
            SELECT * FROM traces WHERE trace_id = ?
            """,
            (trace_id,)
        )
        
        row = cursor.fetchone()
        if row is None:
            return None
        
        return self._row_to_trace(row)
    
    def update_trace(
        self, trace_id: str, update_data: TraceUpdate
    ) -> Optional[TraceResponse]:
        """更新 Trace"""
        trace = self.get_trace(trace_id)
        if not trace:
            return None
        
        # 应用更新
        if update_data.status:
            trace.status = update_data.status
            if update_data.status in [
                TraceStatus.COMPLETED,
                TraceStatus.FAILED,
                TraceStatus.TIMEOUT,
            ]:
                trace.completed_at = datetime.utcnow()
        
        if update_data.events:
            trace.events.extend(update_data.events)
            total_input = sum(e.input_tokens for e in trace.events)
            total_output = sum(e.output_tokens for e in trace.events)
            trace.total_input_tokens = total_input
            trace.total_output_tokens = total_output
            trace.total_tokens = total_input + total_output
            trace.duration_ms = sum(e.latency_ms for e in trace.events)
        
        if update_data.total_tokens:
            trace.total_tokens = update_data.total_tokens
        
        if update_data.total_cost:
            trace.total_cost = update_data.total_cost
        
        if update_data.duration_ms:
            trace.duration_ms = update_data.duration_ms
        
        if update_data.error_message:
            trace.error_message = update_data.error_message
        
        if update_data.metadata:
            trace.metadata.update(update_data.metadata)
        
        trace.updated_at = datetime.utcnow()
        
        # 更新数据库
        conn = self._get_conn()
        conn.execute(
            """
            UPDATE traces SET
                status = :status,
                events = :events,
                total_input_tokens = :total_input_tokens,
                total_output_tokens = :total_output_tokens,
                total_tokens = :total_tokens,
                total_cost = :total_cost,
                duration_ms = :duration_ms,
                error_message = :error_message,
                metadata = :metadata,
                updated_at = :updated_at,
                completed_at = :completed_at
            WHERE trace_id = :trace_id
            """,
            self._trace_to_dict(trace)
        )
        conn.commit()
        
        return trace
    
    def delete_trace(self, trace_id: str) -> bool:
        """删除 Trace"""
        conn = self._get_conn()
        
        cursor = conn.execute(
            "DELETE FROM traces WHERE trace_id = ?",
            (trace_id,)
        )
        conn.commit()
        
        return cursor.rowcount > 0
    
    # ==================== 查询操作 ====================
    
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
        """列出 Traces"""
        conn = self._get_conn()
        
        # 构建查询条件
        conditions = []
        params = []
        
        if agent_id:
            conditions.append("agent_id = ?")
            params.append(agent_id)
        
        if provider:
            conditions.append("provider = ?")
            params.append(provider)
        
        if status:
            conditions.append("status = ?")
            params.append(status)
        
        if start_time:
            conditions.append("created_at >= ?")
            params.append(start_time)
        
        if end_time:
            conditions.append("created_at <= ?")
            params.append(end_time)
        
        where_sql = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        # 获取总数
        count_cursor = conn.execute(
            f"SELECT COUNT(*) FROM traces {where_sql}",
            params
        )
        total = count_cursor.fetchone()[0]
        
        # 分页查询
        offset = (page - 1) * page_size
        cursor = conn.execute(
            f"""
            SELECT * FROM traces
            {where_sql}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            params + [page_size, offset]
        )
        
        traces = [self._row_to_trace(row) for row in cursor.fetchall()]
        
        return TraceListResponse(
            traces=traces,
            total=total,
            page=page,
            page_size=page_size,
            has_more=offset + page_size < total,
        )
    
    def get_cost_summary(
        self,
        provider: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[CostSummary]:
        """获取成本汇总"""
        conn = self._get_conn()
        
        conditions = ["status = 'completed'"]
        params = []
        
        if provider:
            conditions.append("provider = ?")
            params.append(provider)
        
        if start_time:
            conditions.append("created_at >= ?")
            params.append(start_time)
        
        if end_time:
            conditions.append("created_at <= ?")
            params.append(end_time)
        
        where_sql = "WHERE " + " AND ".join(conditions)
        
        # SQLite 聚合查询
        cursor = conn.execute(
            f"""
            SELECT
                provider,
                model,
                COUNT(*) as total_traces,
                SUM(total_tokens) as total_tokens,
                SUM(total_cost) as total_cost,
                AVG(duration_ms) as avg_latency_ms
            FROM traces
            {where_sql}
            GROUP BY provider, model
            """,
            params
        )
        
        summaries = []
        for row in cursor.fetchall():
            provider_str, model, traces, tokens, cost, latency = row
            
            try:
                provider_enum = AgentProvider(provider_str)
            except ValueError:
                provider_enum = AgentProvider.CUSTOM
            
            summaries.append(
                CostSummary(
                    provider=provider_enum,
                    model=model,
                    total_traces=traces,
                    total_tokens=tokens or 0,
                    total_cost=cost or 0.0,
                    avg_latency_ms=latency or 0,
                    period_start=start_time or datetime.utcnow() - timedelta(days=30),
                    period_end=end_time or datetime.utcnow(),
                )
            )
        
        return summaries
    
    # ==================== 统计操作 ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        conn = self._get_conn()
        
        cursor = conn.execute(
            """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                SUM(total_cost) as total_cost
            FROM traces
            """
        )
        
        row = cursor.fetchone()
        total, running, completed, failed, cost = row
        
        # Provider 分布
        provider_cursor = conn.execute(
            """
            SELECT provider, COUNT(*) as cnt
            FROM traces
            GROUP BY provider
            """
        )
        
        providers = {"total": total or 0}
        for provider, cnt in provider_cursor.fetchall():
            providers[f"provider_{provider}"] = cnt
        
        return {
            "total_traces": total or 0,
            "running_traces": running or 0,
            "completed_traces": completed or 0,
            "failed_traces": failed or 0,
            "total_cost": cost or 0.0,
            "providers": providers,
        }
    
    def get_count_by_provider(self) -> Dict[str, int]:
        """获取各 Provider 数量"""
        conn = self._get_conn()
        
        cursor = conn.execute(
            """
            SELECT provider, COUNT(*) as cnt
            FROM traces
            GROUP BY provider
            """
        )
        
        return {provider: cnt for provider, cnt in cursor.fetchall()}
    
    # ==================== 事件操作 ====================
    
    def add_event(self, trace_id: str, event: TraceEvent) -> Optional[TraceResponse]:
        """添加事件"""
        return self.update_trace(trace_id, TraceUpdate(events=[event]))
    
    # ==================== 批量操作 ====================
    
    def bulk_create_traces(self, traces_data: List[TraceCreate]) -> List[TraceResponse]:
        """批量创建"""
        results = []
        for data in traces_data:
            results.append(self.create_trace(data))
        return results
    
    def bulk_delete_traces(self, trace_ids: List[str]) -> int:
        """批量删除"""
        conn = self._get_conn()
        
        cursor = conn.execute(
            """
            DELETE FROM traces WHERE trace_id IN (
                SELECT value FROM json_each(?)
            )
            """,
            (json.dumps(trace_ids),)
        )
        conn.commit()
        
        return cursor.rowcount
    
    # ==================== 清理操作 ====================
    
    def clear_all(self) -> int:
        """清空所有数据"""
        conn = self._get_conn()
        
        cursor = conn.execute("DELETE FROM traces")
        conn.commit()
        
        return cursor.rowcount
    
    # ==================== 健康检查 ====================
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            conn = self._get_conn()
            cursor = conn.execute("SELECT COUNT(*) FROM traces")
            count = cursor.fetchone()[0]
            
            return {
                "status": "healthy",
                "type": "sqlite",
                "path": str(self.path),
                "metrics": {
                    "total_traces": count,
                    "file_size": self.path.stat().st_size if self.path.exists() else 0,
                },
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "type": "sqlite",
                "error": str(e),
            }
    
    # ==================== SQLite 特有方法 ====================
    
    def vacuum(self) -> None:
        """清理数据库文件空间"""
        conn = self._get_conn()
        conn.execute("VACUUM")
        conn.commit()
    
    def get_db_size(self) -> int:
        """获取数据库文件大小"""
        return self.path.stat().st_size if self.path.exists() else 0
    
    def export_to_json(self, output_path: str) -> int:
        """导出数据到 JSON 文件"""
        traces = self.list_traces(page=1, page_size=10000)
        
        with open(output_path, 'w') as f:
            json.dump([t.dict() for t in traces.traces], f, indent=2)
        
        return traces.total
    
    def close(self) -> None:
        """关闭数据库连接"""
        if self._conn:
            self._conn.close()
            self._conn = None


# 注册到工厂
StorageFactory.register("sqlite", SQLiteStorage)