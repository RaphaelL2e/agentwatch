"""
AgentWatch 数据模型
基于 Pydantic v2
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TraceStatus(str, Enum):
    """Trace 状态枚举"""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class AgentProvider(str, Enum):
    """Agent 提供商枚举"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    GOOGLE = "google"
    CUSTOM = "custom"


class TraceEvent(BaseModel):
    """单个 Trace 事件"""
    event_id: str = Field(..., description="事件ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: str = Field(..., description="事件类型: call, response, error, tool_use")
    agent_name: Optional[str] = Field(None, description="Agent名称")
    model: Optional[str] = Field(None, description="使用的模型")
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    latency_ms: int = Field(default=0, ge=0, description="延迟(毫秒)")
    content: Optional[str] = Field(None, description="事件内容摘要")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class TraceCreate(BaseModel):
    """创建 Trace 请求"""
    trace_id: Optional[str] = Field(None, description="Trace ID，不提供则自动生成")
    agent_id: str = Field(..., description="Agent ID")
    agent_name: str = Field(..., description="Agent 名称")
    provider: AgentProvider = Field(..., description="AI提供商")
    model: str = Field(..., description="使用的模型")
    session_id: Optional[str] = Field(None, description="会话ID")
    user_id: Optional[str] = Field(None, description="用户ID")
    prompt: Optional[str] = Field(None, description="初始提示词")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class TraceUpdate(BaseModel):
    """更新 Trace 请求"""
    status: Optional[TraceStatus] = None
    events: Optional[List[TraceEvent]] = None
    total_tokens: Optional[int] = None
    total_cost: Optional[float] = None
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TraceResponse(BaseModel):
    """Trace 响应"""
    trace_id: str
    agent_id: str
    agent_name: str
    provider: AgentProvider
    model: str
    status: TraceStatus
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    prompt: Optional[str] = None
    events: List[TraceEvent] = Field(default_factory=list)
    total_input_tokens: int = Field(default=0)
    total_output_tokens: int = Field(default=0)
    total_tokens: int = Field(default=0)
    total_cost: float = Field(default=0.0, description="成本(USD)")
    duration_ms: int = Field(default=0)
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TraceListResponse(BaseModel):
    """Trace 列表响应"""
    traces: List[TraceResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class CostSummary(BaseModel):
    """成本汇总"""
    provider: AgentProvider
    model: str
    total_traces: int
    total_tokens: int
    total_cost: float
    avg_latency_ms: float
    period_start: datetime
    period_end: datetime


class HealthCheck(BaseModel):
    """健康检查响应"""
    status: str
    version: str
    uptime_seconds: float
    database_connected: bool
    traces_count: int