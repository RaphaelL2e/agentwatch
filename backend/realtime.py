"""
WebSocket 实时推送增强模块
- 定时统计推送
- 成本预警推送
- 延迟预警推送
- Agent性能预警
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


class AlertType(str, Enum):
    COST_SPIKE = "cost_spike"
    HIGH_LATENCY = "high_latency"
    AGENT_FAILURE = "agent_failure"
    RATE_LIMIT = "rate_limit"
    TOKEN_OVERFLOW = "token_overflow"


@dataclass
class AlertConfig:
    """预警配置"""
    cost_threshold: float = 0.10  # 单次trace成本超过$0.10预警
    latency_threshold_ms: float = 5000  # 延迟超过5秒预警
    failure_rate_threshold: float = 0.3  # 失败率超过30%预警
    token_threshold: int = 100000  # 单次token超过100K预警


@dataclass
class WebSocketStats:
    """WebSocket连接统计"""
    total_connections: int = 0
    messages_sent: int = 0
    alerts_sent: int = 0
    last_broadcast: Optional[datetime] = None


class RealTimePushManager:
    """实时推送管理器"""
    
    def __init__(
        self,
        broadcast_func: Callable,
        get_stats_func: Callable,
        config: AlertConfig = AlertConfig(),
    ):
        self.broadcast = broadcast_func
        self.get_stats = get_stats_func
        self.config = config
        self.stats = WebSocketStats()
        self._running = False
        self._push_interval = 5  # 5秒推送一次统计
        self._background_task: Optional[asyncio.Task] = None
        
        # 预警历史（避免重复推送）
        self._alert_history: Dict[str, datetime] = {}
        self._alert_cooldown = 60  # 同类型预警60秒冷却
    
    async def start_background_push(self):
        """启动后台定时推送"""
        if self._running:
            return
        
        self._running = True
        self._background_task = asyncio.create_task(self._push_loop())
        print("📡 Real-time push started")
    
    async def stop_background_push(self):
        """停止后台推送"""
        self._running = False
        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass
        print("📡 Real-time push stopped")
    
    async def _push_loop(self):
        """定时推送循环"""
        while self._running:
            try:
                # 推送统计更新
                stats = self.get_stats()
                await self.broadcast({
                    "type": "stats_update",
                    "data": stats,
                    "timestamp": datetime.utcnow().isoformat(),
                })
                
                self.stats.messages_sent += 1
                self.stats.last_broadcast = datetime.utcnow()
                
                # 检查预警条件
                await self._check_alerts(stats)
                
                await asyncio.sleep(self._push_interval)
                
            except Exception as e:
                print(f"Push loop error: {e}")
                await asyncio.sleep(1)
    
    async def _check_alerts(self, stats: dict):
        """检查预警条件"""
        # 成本预警
        if stats.get("total_cost", 0) > self.config.cost_threshold * 10:
            await self._send_alert(
                AlertType.COST_SPIKE,
                {
                    "total_cost": stats["total_cost"],
                    "threshold": self.config.cost_threshold * 10,
                    "message": f"Total cost ${stats['total_cost']:.4f} exceeded threshold",
                }
            )
        
        # 失败率预警
        success_rate = stats.get("success_rate", 1.0)
        if success_rate < (1 - self.config.failure_rate_threshold):
            await self._send_alert(
                AlertType.AGENT_FAILURE,
                {
                    "success_rate": success_rate,
                    "threshold": self.config.failure_rate_threshold,
                    "message": f"Success rate {success_rate:.1%} below threshold",
                }
            )
    
    async def _send_alert(self, alert_type: AlertType, data: dict):
        """发送预警"""
        # 检查冷却时间
        alert_key = alert_type.value
        if alert_key in self._alert_history:
            elapsed = (datetime.utcnow() - self._alert_history[alert_key]).total_seconds()
            if elapsed < self._alert_cooldown:
                return  # 冷静期，不重复推送
        
        self._alert_history[alert_key] = datetime.utcnow()
        
        await self.broadcast({
            "type": "alert",
            "alert_type": alert_type.value,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        self.stats.alerts_sent += 1
        print(f"⚠️ Alert sent: {alert_type.value}")
    
    async def push_trace_created(self, trace: dict):
        """推送新trace创建"""
        await self.broadcast({
            "type": "trace_created",
            "data": trace,
            "timestamp": datetime.utcnow().isoformat(),
        })
        self.stats.messages_sent += 1
        
        # 检查单trace预警
        cost = trace.get("total_cost", 0)
        if cost > self.config.cost_threshold:
            await self._send_alert(
                AlertType.COST_SPIKE,
                {
                    "trace_id": trace.get("trace_id"),
                    "cost": cost,
                    "threshold": self.config.cost_threshold,
                    "message": f"Single trace cost ${cost:.4f} exceeded threshold",
                }
            )
        
        # 检查延迟预警
        latency = trace.get("latency_ms", 0)
        if latency > self.config.latency_threshold_ms:
            await self._send_alert(
                AlertType.HIGH_LATENCY,
                {
                    "trace_id": trace.get("trace_id"),
                    "latency_ms": latency,
                    "threshold": self.config.latency_threshold_ms,
                    "message": f"Trace latency {latency}ms exceeded threshold",
                }
            )
        
        # 检查token预警
        tokens = trace.get("total_input_tokens", 0) + trace.get("total_output_tokens", 0)
        if tokens > self.config.token_threshold:
            await self._send_alert(
                AlertType.TOKEN_OVERFLOW,
                {
                    "trace_id": trace.get("trace_id"),
                    "tokens": tokens,
                    "threshold": self.config.token_threshold,
                    "message": f"Trace tokens {tokens} exceeded threshold",
                }
            )
    
    async def push_trace_updated(self, trace: dict):
        """推送trace更新"""
        await self.broadcast({
            "type": "trace_updated",
            "data": trace,
            "timestamp": datetime.utcnow().isoformat(),
        })
        self.stats.messages_sent += 1
    
    async def push_trace_deleted(self, trace_id: str):
        """推送trace删除"""
        await self.broadcast({
            "type": "trace_deleted",
            "data": {"trace_id": trace_id},
            "timestamp": datetime.utcnow().isoformat(),
        })
        self.stats.messages_sent += 1
    
    async def push_trace_event(self, trace_id: str, event: dict, trace: dict):
        """推送trace事件"""
        await self.broadcast({
            "type": "trace_event",
            "data": {
                "trace_id": trace_id,
                "event": event,
                "trace": trace,
            },
            "timestamp": datetime.utcnow().isoformat(),
        })
        self.stats.messages_sent += 1
    
    def get_push_stats(self) -> WebSocketStats:
        """获取推送统计"""
        return self.stats


# 导出
__all__ = [
    "RealTimePushManager",
    "AlertConfig",
    "AlertType",
    "WebSocketStats",
]