"""
AgentWatch SDK Trace 模块
Trace 上下文和数据结构
"""

import time
import uuid
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TraceEvent:
    """Trace 事件"""

    event_id: str
    event_type: str  # call, response, error, tool_use
    timestamp: datetime = field(default_factory=datetime.utcnow)
    model: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TraceData:
    """Trace 数据结构"""

    trace_id: str
    agent_id: str
    agent_name: str
    provider: str
    model: str
    status: str = "running"  # running, completed, failed, timeout
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    prompt: Optional[str] = None
    events: List[TraceEvent] = field(default_factory=list)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    duration_ms: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class TraceBuilder:
    """
    Trace 构建器

    用于构建复杂的 Trace 数据

    使用示例:
        trace = TraceBuilder("my_agent", "gpt-4o")
            .with_prompt("Hello")
            .with_session("session_123")
            .build()
    """

    def __init__(self, agent_name: str, model: str, provider: str = "openai"):
        self._agent_id = f"agent_{uuid.uuid4().hex[:8]}"
        self._agent_name = agent_name
        self._provider = provider
        self._model = model
        self._trace_id = f"tr_{uuid.uuid4().hex[:12]}"

        self._session_id: Optional[str] = None
        self._user_id: Optional[str] = None
        self._prompt: Optional[str] = None
        self._metadata: Dict[str, Any] = {}

    def with_agent_id(self, agent_id: str) -> "TraceBuilder":
        """设置 Agent ID"""
        self._agent_id = agent_id
        return self

    def with_session(self, session_id: str) -> "TraceBuilder":
        """设置会话 ID"""
        self._session_id = session_id
        return self

    def with_user(self, user_id: str) -> "TraceBuilder":
        """设置用户 ID"""
        self._user_id = user_id
        return self

    def with_prompt(self, prompt: str) -> "TraceBuilder":
        """设置提示词"""
        self._prompt = prompt
        return self

    def with_metadata(self, metadata: Dict[str, Any]) -> "TraceBuilder":
        """设置元数据"""
        self._metadata = metadata
        return self

    def build(self) -> TraceData:
        """构建 Trace 数据"""
        return TraceData(
            trace_id=self._trace_id,
            agent_id=self._agent_id,
            agent_name=self._agent_name,
            provider=self._provider,
            model=self._model,
            session_id=self._session_id,
            user_id=self._user_id,
            prompt=self._prompt,
            metadata=self._metadata,
        )

    def build_dict(self) -> Dict[str, Any]:
        """构建字典格式（用于 API 请求）"""
        return {
            "trace_id": self._trace_id,
            "agent_id": self._agent_id,
            "agent_name": self._agent_name,
            "provider": self._provider,
            "model": self._model,
            "session_id": self._session_id,
            "user_id": self._user_id,
            "prompt": self._prompt,
            "metadata": self._metadata,
        }
