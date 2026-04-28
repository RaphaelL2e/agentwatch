"""
AgentWatch 内存存储实现
默认存储方案，适合开发和测试环境

特点：
- 快速启动，无需外部依赖
- 数据存储在内存中，重启后丢失
- 适合本地开发和快速原型验证
- 性能最佳（零网络延迟）
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from collections import defaultdict

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


class MemoryStorage(TraceStorage):
    """
    内存存储实现
    
    使用 Python 字典存储数据，所有操作都在内存中完成。
    """
    
    def __init__(self, max_size: Optional[int] = None):
        """
        初始化内存存储
        
        Args:
            max_size: 最大存储数量（可选，超过时删除最旧的）
        """
        self._traces: Dict[str, TraceResponse] = {}
        self._counter: Dict[str, int] = defaultdict(int)
        self._max_size = max_size
    
    # ==================== CRUD 操作 ====================
    
    def create_trace(self, trace_data: TraceCreate) -> TraceResponse:
        """创建 Trace"""
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
        
        self._traces[trace_id] = trace
        self._counter["total"] += 1
        self._counter[f"provider_{trace_data.provider}"] += 1
        
        # 检查容量限制
        if self._max_size and len(self._traces) > self._max_size:
            self._evict_oldest()
        
        return trace
    
    def get_trace(self, trace_id: str) -> Optional[TraceResponse]:
        """获取 Trace"""
        return self._traces.get(trace_id)
    
    def update_trace(
        self, trace_id: str, update_data: TraceUpdate
    ) -> Optional[TraceResponse]:
        """更新 Trace"""
        trace = self._traces.get(trace_id)
        if not trace:
            return None
        
        # 更新状态
        if update_data.status:
            trace.status = update_data.status
            if update_data.status in [
                TraceStatus.COMPLETED,
                TraceStatus.FAILED,
                TraceStatus.TIMEOUT,
            ]:
                trace.completed_at = datetime.utcnow()
        
        # 更新事件
        if update_data.events:
            trace.events.extend(update_data.events)
            # 重新计算 Token 和成本
            total_input = sum(e.input_tokens for e in trace.events)
            total_output = sum(e.output_tokens for e in trace.events)
            trace.total_input_tokens = total_input
            trace.total_output_tokens = total_output
            trace.total_tokens = total_input + total_output
            trace.duration_ms = sum(e.latency_ms for e in trace.events)
        
        # 更新其他字段
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
        self._traces[trace_id] = trace
        
        return trace
    
    def delete_trace(self, trace_id: str) -> bool:
        """删除 Trace"""
        if trace_id in self._traces:
            trace = self._traces[trace_id]
            del self._traces[trace_id]
            self._counter["total"] -= 1
            self._counter[f"provider_{trace.provider}"] -= 1
            return True
        return False
    
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
        # 过滤
        filtered = []
        for trace in self._traces.values():
            if agent_id and trace.agent_id != agent_id:
                continue
            if provider and trace.provider != provider:
                continue
            if status and trace.status != status:
                continue
            if start_time and trace.created_at < start_time:
                continue
            if end_time and trace.created_at > end_time:
                continue
            filtered.append(trace)
        
        # 排序（最新的在前）
        filtered.sort(key=lambda t: t.created_at, reverse=True)
        
        # 分页
        total = len(filtered)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_traces = filtered[start_idx:end_idx]
        
        return TraceListResponse(
            traces=page_traces,
            total=total,
            page=page,
            page_size=page_size,
            has_more=end_idx < total,
        )
    
    def get_cost_summary(
        self,
        provider: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[CostSummary]:
        """获取成本汇总"""
        groups: Dict[str, Dict] = defaultdict(
            lambda: {
                "total_traces": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "latencies": [],
            }
        )
        
        for trace in self._traces.values():
            if trace.status != TraceStatus.COMPLETED:
                continue
            if provider and trace.provider != provider:
                continue
            if start_time and trace.created_at < start_time:
                continue
            if end_time and trace.created_at > end_time:
                continue
            
            key = f"{trace.provider}_{trace.model}"
            groups[key]["total_traces"] += 1
            groups[key]["total_tokens"] += trace.total_tokens
            groups[key]["total_cost"] += trace.total_cost
            groups[key]["latencies"].append(trace.duration_ms)
        
        summaries = []
        for key, data in groups.items():
            parts = key.split("_", 1)
            provider_str = parts[0]
            model = parts[1] if len(parts) > 1 else ""
            
            try:
                provider_enum = AgentProvider(provider_str)
            except ValueError:
                provider_enum = AgentProvider.CUSTOM
            
            summaries.append(
                CostSummary(
                    provider=provider_enum,
                    model=model,
                    total_traces=data["total_traces"],
                    total_tokens=data["total_tokens"],
                    total_cost=data["total_cost"],
                    avg_latency_ms=(
                        sum(data["latencies"]) / len(data["latencies"])
                        if data["latencies"]
                        else 0
                    ),
                    period_start=start_time or datetime.utcnow() - timedelta(days=30),
                    period_end=end_time or datetime.utcnow(),
                )
            )
        
        return summaries
    
    # ==================== 统计操作 ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_traces": self._counter["total"],
            "running_traces": len(
                [t for t in self._traces.values() if t.status == TraceStatus.RUNNING]
            ),
            "completed_traces": len(
                [t for t in self._traces.values() if t.status == TraceStatus.COMPLETED]
            ),
            "failed_traces": len(
                [t for t in self._traces.values() if t.status == TraceStatus.FAILED]
            ),
            "total_cost": sum(t.total_cost for t in self._traces.values()),
            "providers": dict(self._counter),
        }
    
    def get_count_by_provider(self) -> Dict[str, int]:
        """获取各 Provider 数量"""
        result = {}
        for key, count in self._counter.items():
            if key.startswith("provider_"):
                provider = key.replace("provider_", "")
                result[provider] = count
        return result
    
    # ==================== 事件操作 ====================
    
    def add_event(self, trace_id: str, event: TraceEvent) -> Optional[TraceResponse]:
        """添加事件"""
        return self.update_trace(trace_id, TraceUpdate(events=[event]))
    
    # ==================== 批量操作 ====================
    
    def bulk_create_traces(
        self, traces_data: List[TraceCreate]
    ) -> List[TraceResponse]:
        """批量创建"""
        results = []
        for data in traces_data:
            results.append(self.create_trace(data))
        return results
    
    def bulk_delete_traces(self, trace_ids: List[str]) -> int:
        """批量删除"""
        count = 0
        for trace_id in trace_ids:
            if self.delete_trace(trace_id):
                count += 1
        return count
    
    # ==================== 清理操作 ====================
    
    def clear_all(self) -> int:
        """清空所有"""
        count = len(self._traces)
        self._traces.clear()
        self._counter.clear()
        return count
    
    # ==================== 健康检查 ====================
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "status": "healthy",
            "type": "memory",
            "connection": "local",
            "metrics": {
                "total_traces": len(self._traces),
                "max_size": self._max_size,
                "usage": len(self._traces) / (self._max_size or 10000) * 100,
            },
        }
    
    # ==================== 私有方法 ====================
    
    def _generate_trace_id(self) -> str:
        """生成 Trace ID"""
        return f"tr_{uuid.uuid4().hex[:12]}"
    
    def _evict_oldest(self) -> None:
        """删除最旧的 Trace（容量管理）"""
        if not self._traces:
            return
        
        # 按创建时间排序，删除最旧的
        sorted_traces = sorted(
            self._traces.items(),
            key=lambda x: x[1].created_at
        )
        
        # 删除最旧的 10%
        to_remove = max(1, int(len(sorted_traces) * 0.1))
        for trace_id, _ in sorted_traces[:to_remove]:
            self.delete_trace(trace_id)


# 注册到工厂
StorageFactory.register("memory", MemoryStorage)