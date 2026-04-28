"""
AgentWatch ClickHouse 存储实现
生产环境推荐方案，适合大规模数据存储

特点：
- 高性能 OLAP 数据库
- 支持海量 Trace 数据存储
- 高效的时间范围查询
- 实时聚合分析能力
- 数据持久化，重启不丢失

ClickHouse 表结构：

CREATE TABLE traces (
    trace_id String,
    agent_id String,
    agent_name String,
    provider String,
    model String,
    status String,
    session_id String,
    user_id String,
    prompt String,
    events Array(Map(String, String)),
    total_input_tokens UInt64,
    total_output_tokens UInt64,
    total_tokens UInt64,
    total_cost Float64,
    duration_ms UInt64,
    error_message String,
    metadata Map(String, String),
    created_at DateTime,
    updated_at DateTime,
    completed_at Nullable(DateTime)
) ENGINE = MergeTree()
ORDER BY (created_at, trace_id)
PARTITION BY toYYYYMM(created_at);

"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

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


class ClickHouseStorage(TraceStorage):
    """
    ClickHouse 存储实现
    
    需要安装 clickhouse-driver:
    pip install clickhouse-driver
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 9000,
        database: str = "agentwatch",
        user: str = "default",
        password: str = "",
        table: str = "traces",
    ):
        """
        初始化 ClickHouse 存储
        
        Args:
            host: ClickHouse 主机
            port: 端口（Native 协议默认 9000）
            database: 数据库名
            user: 用户名
            password: 密码
            table: 表名
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.table = table
        
        # 延迟连接（避免启动时失败）
        self._client = None
        self._connected = False
    
    def _connect(self) -> None:
        """连接到 ClickHouse"""
        if self._connected:
            return
        
        try:
            from clickhouse_driver import Client
            self._client = Client(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
            )
            self._connected = True
        except ImportError:
            raise ImportError(
                "clickhouse-driver not installed. "
                "Run: pip install clickhouse-driver"
            )
    
    def _ensure_table(self) -> None:
        """确保表存在"""
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.table} (
            trace_id String,
            agent_id String,
            agent_name String,
            provider String,
            model String,
            status String,
            session_id String,
            user_id String,
            prompt String,
            events String,  -- JSON 存储
            total_input_tokens UInt64,
            total_output_tokens UInt64,
            total_tokens UInt64,
            total_cost Float64,
            duration_ms UInt64,
            error_message String,
            metadata String,  -- JSON 存储
            created_at DateTime,
            updated_at DateTime,
            completed_at Nullable(DateTime)
        ) ENGINE = MergeTree()
        ORDER BY (created_at, trace_id)
        PARTITION BY toYYYYMM(created_at)
        """
        self._client.execute(create_sql)
    
    # ==================== CRUD 操作 ====================
    
    def create_trace(self, trace_data: TraceCreate) -> TraceResponse:
        """创建 Trace"""
        self._connect()
        
        now = datetime.utcnow()
        trace_id = trace_data.trace_id or self._generate_trace_id()
        
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
        
        # 插入到 ClickHouse
        import json
        self._client.execute(
            f"""
            INSERT INTO {self.table} VALUES
            """,
            [{
                'trace_id': trace_id,
                'agent_id': trace.agent_id or '',
                'agent_name': trace.agent_name,
                'provider': trace.provider,
                'model': trace.model,
                'status': trace.status.value,
                'session_id': trace.session_id or '',
                'user_id': trace.user_id or '',
                'prompt': trace.prompt or '',
                'events': json.dumps([]),
                'total_input_tokens': 0,
                'total_output_tokens': 0,
                'total_tokens': 0,
                'total_cost': 0.0,
                'duration_ms': 0,
                'error_message': '',
                'metadata': json.dumps(trace.metadata),
                'created_at': now,
                'updated_at': now,
                'completed_at': None,
            }]
        )
        
        return trace
    
    def get_trace(self, trace_id: str) -> Optional[TraceResponse]:
        """获取 Trace"""
        self._connect()
        
        result = self._client.execute(
            f"""
            SELECT * FROM {self.table}
            WHERE trace_id = '{trace_id}'
            LIMIT 1
            """
        )
        
        if not result:
            return None
        
        return self._row_to_trace(result[0])
    
    def update_trace(
        self, trace_id: str, update_data: TraceUpdate
    ) -> Optional[TraceResponse]:
        """更新 Trace（ClickHouse 使用 ALTER TABLE）"""
        # ClickHouse 不支持直接 UPDATE，需要先删除再插入
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
        
        # 其他字段更新...
        trace.updated_at = datetime.utcnow()
        
        # 删除旧数据，插入新数据
        self._client.execute(
            f"""
            ALTER TABLE {self.table}
            DELETE WHERE trace_id = '{trace_id}'
            """
        )
        
        # 重新插入（使用 create_trace 的逻辑）
        import json
        self._client.execute(
            f"""
            INSERT INTO {self.table} VALUES
            """,
            [self._trace_to_row(trace)]
        )
        
        return trace
    
    def delete_trace(self, trace_id: str) -> bool:
        """删除 Trace"""
        self._connect()
        
        self._client.execute(
            f"""
            ALTER TABLE {self.table}
            DELETE WHERE trace_id = '{trace_id}'
            """
        )
        return True
    
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
        self._connect()
        
        where_clauses = []
        if agent_id:
            where_clauses.append(f"agent_id = '{agent_id}'")
        if provider:
            where_clauses.append(f"provider = '{provider}'")
        if status:
            where_clauses.append(f"status = '{status}'")
        if start_time:
            where_clauses.append(f"created_at >= '{start_time.isoformat()}'")
        if end_time:
            where_clauses.append(f"created_at <= '{end_time.isoformat()}'")
        
        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # 获取总数
        count_result = self._client.execute(
            f"SELECT count() FROM {self.table} {where_sql}"
        )
        total = count_result[0][0] if count_result else 0
        
        # 分页查询
        offset = (page - 1) * page_size
        results = self._client.execute(
            f"""
            SELECT * FROM {self.table}
            {where_sql}
            ORDER BY created_at DESC
            LIMIT {page_size}
            OFFSET {offset}
            """
        )
        
        traces = [self._row_to_trace(row) for row in results]
        
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
        """获取成本汇总（ClickHouse 高效聚合）"""
        self._connect()
        
        where_clauses = ["status = 'completed'"]
        if provider:
            where_clauses.append(f"provider = '{provider}'")
        if start_time:
            where_clauses.append(f"created_at >= '{start_time.isoformat()}'")
        if end_time:
            where_clauses.append(f"created_at <= '{end_time.isoformat()}'")
        
        where_sql = "WHERE " + " AND ".join(where_clauses)
        
        # ClickHouse 聚合查询
        results = self._client.execute(
            f"""
            SELECT
                provider,
                model,
                count() as total_traces,
                sum(total_tokens) as total_tokens,
                sum(total_cost) as total_cost,
                avg(duration_ms) as avg_latency_ms
            FROM {self.table}
            {where_sql}
            GROUP BY provider, model
            """
        )
        
        summaries = []
        for row in results:
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
                    total_tokens=tokens,
                    total_cost=cost,
                    avg_latency_ms=latency,
                    period_start=start_time or datetime.utcnow() - timedelta(days=30),
                    period_end=end_time or datetime.utcnow(),
                )
            )
        
        return summaries
    
    # ==================== 统计操作 ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        self._connect()
        
        results = self._client.execute(
            f"""
            SELECT
                count() as total,
                countIf(status = 'running') as running,
                countIf(status = 'completed') as completed,
                countIf(status = 'failed') as failed,
                sum(total_cost) as total_cost
            FROM {self.table}
            """
        )
        
        if results:
            total, running, completed, failed, cost = results[0]
        else:
            total, running, completed, failed, cost = 0, 0, 0, 0, 0.0
        
        # Provider 分布
        provider_results = self._client.execute(
            f"""
            SELECT provider, count() as cnt
            FROM {self.table}
            GROUP BY provider
            """
        )
        
        providers = {"total": total}
        for provider, cnt in provider_results:
            providers[f"provider_{provider}"] = cnt
        
        return {
            "total_traces": total,
            "running_traces": running,
            "completed_traces": completed,
            "failed_traces": failed,
            "total_cost": cost,
            "providers": providers,
        }
    
    def get_count_by_provider(self) -> Dict[str, int]:
        """获取各 Provider 数量"""
        self._connect()
        
        results = self._client.execute(
            f"""
            SELECT provider, count() as cnt
            FROM {self.table}
            GROUP BY provider
            """
        )
        
        return {provider: cnt for provider, cnt in results}
    
    # ==================== 其他方法（简化实现） ====================
    
    def add_event(self, trace_id: str, event: TraceEvent) -> Optional[TraceResponse]:
        """添加事件"""
        return self.update_trace(trace_id, TraceUpdate(events=[event]))
    
    def bulk_create_traces(self, traces_data: List[TraceCreate]) -> List[TraceResponse]:
        """批量创建"""
        results = []
        for data in traces_data:
            results.append(self.create_trace(data))
        return results
    
    def bulk_delete_traces(self, trace_ids: List[str]) -> int:
        """批量删除"""
        if not trace_ids:
            return 0
        
        self._client.execute(
            f"""
            ALTER TABLE {self.table}
            DELETE WHERE trace_id IN ({','.join(f"'{id}'" for id in trace_ids)})
            """
        )
        return len(trace_ids)
    
    def clear_all(self) -> int:
        """清空所有"""
        stats = self.get_stats()
        self._client.execute(f"TRUNCATE TABLE {self.table}")
        return stats["total_traces"]
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            self._connect()
            self._client.execute("SELECT 1")
            return {
                "status": "healthy",
                "type": "clickhouse",
                "connection": f"{self.host}:{self.port}",
                "database": self.database,
                "table": self.table,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "type": "clickhouse",
                "error": str(e),
            }
    
    # ==================== 私有方法 ====================
    
    def _generate_trace_id(self) -> str:
        """生成 Trace ID"""
        return f"tr_{uuid.uuid4().hex[:12]}"
    
    def _row_to_trace(self, row: tuple) -> TraceResponse:
        """数据库行转换为 TraceResponse"""
        import json
        
        (trace_id, agent_id, agent_name, provider, model, status,
         session_id, user_id, prompt, events_json,
         total_input, total_output, total, cost, duration,
         error, metadata_json, created, updated, completed) = row
        
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
            events=json.loads(events_json) if events_json else [],
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            total_tokens=total,
            total_cost=cost,
            duration_ms=duration,
            error_message=error,
            metadata=json.loads(metadata_json) if metadata_json else {},
            created_at=created,
            updated_at=updated,
            completed_at=completed,
        )
    
    def _trace_to_row(self, trace: TraceResponse) -> Dict[str, Any]:
        """TraceResponse 转换为数据库行"""
        import json
        
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


# 注册到工厂
StorageFactory.register("clickhouse", ClickHouseStorage)