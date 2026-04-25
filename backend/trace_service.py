"""
AgentWatch Trace 服务层
处理 Trace 数据的存储和查询
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from collections import defaultdict

from models import (
    TraceCreate, TraceUpdate, TraceResponse, TraceListResponse,
    TraceStatus, TraceEvent, CostSummary, AgentProvider
)

# 内存存储（Day 2先用内存，后续迁移到ClickHouse）
_traces: Dict[str, TraceResponse] = {}
_trace_counter = defaultdict(int)  # 统计计数器


class TraceService:
    """Trace 服务"""
    
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
            "deepseek-v4": {"input": 0.00014, "output": 0.00028},  # ¥0.3/M tokens ≈ $0.00014
            "deepseek-chat": {"input": 0.00007, "output": 0.00014},
        },
        "google": {
            "gemini-pro": {"input": 0.00025, "output": 0.0005},
            "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
        },
    }
    
    DEFAULT_COST = {"input": 0.001, "output": 0.002}  # 默认成本
    
    @staticmethod
    def generate_trace_id() -> str:
        """生成 Trace ID"""
        return f"tr_{uuid.uuid4().hex[:12]}"
    
    @staticmethod
    def calculate_cost(provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
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
        now = datetime.utcnow()
        trace_id = trace_data.trace_id or TraceService.generate_trace_id()
        
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
            metadata=trace_data.metadata or {}
        )
        
        _traces[trace_id] = trace
        _trace_counter["total"] += 1
        _trace_counter[f"provider_{trace_data.provider}"] += 1
        
        return trace
    
    @staticmethod
    def get_trace(trace_id: str) -> Optional[TraceResponse]:
        """获取 Trace"""
        return _traces.get(trace_id)
    
    @staticmethod
    def update_trace(trace_id: str, update_data: TraceUpdate) -> Optional[TraceResponse]:
        """更新 Trace"""
        trace = _traces.get(trace_id)
        if not trace:
            return None
        
        # 更新字段
        if update_data.status:
            trace.status = update_data.status
            if update_data.status in [TraceStatus.COMPLETED, TraceStatus.FAILED, TraceStatus.TIMEOUT]:
                trace.completed_at = datetime.utcnow()
        
        if update_data.events:
            trace.events.extend(update_data.events)
            # 计算总 token
            total_input = sum(e.input_tokens for e in trace.events)
            total_output = sum(e.output_tokens for e in trace.events)
            trace.total_input_tokens = total_input
            trace.total_output_tokens = total_output
            trace.total_tokens = total_input + total_output
            trace.total_cost = TraceService.calculate_cost(
                trace.provider, trace.model, total_input, total_output
            )
            # 计算总延迟
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
        _traces[trace_id] = trace
        
        return trace
    
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
        # 过滤
        filtered = []
        for trace in _traces.values():
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
        
        # 按创建时间倒序排序
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
            has_more=end_idx < total
        )
    
    @staticmethod
    def get_cost_summary(
        provider: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[CostSummary]:
        """获取成本汇总"""
        # 按provider+model分组
        groups: Dict[str, Dict] = defaultdict(lambda: {
            "total_traces": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "latencies": [],
        })
        
        for trace in _traces.values():
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
            
            # 将字符串转换为 AgentProvider 枚举
            try:
                provider_enum = AgentProvider(provider_str)
            except ValueError:
                provider_enum = AgentProvider.CUSTOM
            
            summaries.append(CostSummary(
                provider=provider_enum,
                model=model,
                total_traces=data["total_traces"],
                total_tokens=data["total_tokens"],
                total_cost=data["total_cost"],
                avg_latency_ms=sum(data["latencies"]) / len(data["latencies"]) if data["latencies"] else 0,
                period_start=start_time or datetime.utcnow() - timedelta(days=30),
                period_end=end_time or datetime.utcnow(),
            ))
        
        return summaries
    
    @staticmethod
    def delete_trace(trace_id: str) -> bool:
        """删除 Trace"""
        if trace_id in _traces:
            del _traces[trace_id]
            _trace_counter["total"] -= 1
            return True
        return False
    
    @staticmethod
    def get_stats() -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_traces": _trace_counter["total"],
            "running_traces": len([t for t in _traces.values() if t.status == TraceStatus.RUNNING]),
            "completed_traces": len([t for t in _traces.values() if t.status == TraceStatus.COMPLETED]),
            "failed_traces": len([t for t in _traces.values() if t.status == TraceStatus.FAILED]),
            "total_cost": sum(t.total_cost for t in _traces.values()),
            "providers": dict(_trace_counter),
        }