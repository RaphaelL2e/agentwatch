"""
AgentWatch Backend
FastAPI 主入口 - 支持 WebSocket 实时推送
"""

import time
import asyncio
import json
from datetime import datetime, timedelta
from typing import Optional, List
from collections import defaultdict

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager

from models import (
    TraceCreate,
    TraceUpdate,
    TraceResponse,
    TraceListResponse,
    TraceEvent,
    CostSummary,
    HealthCheck,
    TraceStatus,
    AgentProvider,
)
from trace_service import TraceService

# 启动时间
START_TIME = time.time()


# Lifespan handler for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    print("🚀 AgentWatch Backend started!")
    print("   Version: 0.4.0")
    print("   Docs: http://localhost:8000/docs")
    print("   WebSocket: ws://localhost:8000/ws")
    yield
    # Shutdown
    print("👋 AgentWatch Backend shutting down...")


app = FastAPI(
    title="AgentWatch",
    description="AI Agent Security Monitoring Platform - Track, Debug, and Optimize Your AI Agents",
    version="0.4.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== WebSocket 管理 ====================

class ConnectionManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket):
        """接受新连接"""
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        print(f"📡 WebSocket connected. Total: {len(self.active_connections)}")
    
    async def disconnect(self, websocket: WebSocket):
        """断开连接"""
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        print(f"📡 WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """广播消息给所有连接"""
        if not self.active_connections:
            return
        
        async with self._lock:
            connections = list(self.active_connections)
        
        disconnected = []
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        
        # 清理断开的连接
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)
    
    async def send_to(self, websocket: WebSocket, message: dict):
        """发送消息给特定连接"""
        try:
            await websocket.send_json(message)
        except Exception:
            await self.disconnect(websocket)


manager = ConnectionManager()


# ==================== 基础端点 ====================


@app.get("/", tags=["Root"])
async def root():
    """API根路径"""
    return {
        "message": "AgentWatch API",
        "version": "0.4.0",
        "docs": "/docs",
        "status": "running",
        "websocket": "/ws",
    }


@app.get("/health", response_model=HealthCheck, tags=["Health"])
async def health():
    """健康检查"""
    stats = TraceService.get_stats()
    return HealthCheck(
        status="healthy",
        version="0.4.0",
        uptime_seconds=time.time() - START_TIME,
        database_connected=True,  # 内存存储总是连接
        traces_count=stats["total_traces"],
    )


@app.get("/stats", tags=["Stats"])
async def get_stats():
    """获取统计信息"""
    return TraceService.get_stats()


# ==================== Trace API ====================


@app.post("/api/v1/trace", response_model=TraceResponse, tags=["Trace"])
async def create_trace(trace_data: TraceCreate):
    """
    创建新的 Trace

    - **agent_id**: Agent唯一标识
    - **agent_name**: Agent名称
    - **provider**: AI提供商 (openai, anthropic, deepseek, google)
    - **model**: 使用的模型
    - **session_id**: 可选会话ID
    - **user_id**: 可选用户ID
    - **prompt**: 可选初始提示词
    """
    trace = TraceService.create_trace(trace_data)
    
    # 广播新 trace 事件
    await manager.broadcast({
        "type": "trace_created",
        "data": trace.model_dump(),
        "timestamp": datetime.utcnow().isoformat(),
    })
    
    return trace


@app.get("/api/v1/trace/{trace_id}", response_model=TraceResponse, tags=["Trace"])
async def get_trace(trace_id: str):
    """获取 Trace 详情"""
    trace = TraceService.get_trace(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
    return trace


@app.put("/api/v1/trace/{trace_id}", response_model=TraceResponse, tags=["Trace"])
async def update_trace(trace_id: str, update_data: TraceUpdate):
    """更新 Trace"""
    trace = TraceService.update_trace(trace_id, update_data)
    if not trace:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
    
    # 广播更新事件
    await manager.broadcast({
        "type": "trace_updated",
        "data": trace.model_dump(),
        "timestamp": datetime.utcnow().isoformat(),
    })
    
    return trace


@app.delete("/api/v1/trace/{trace_id}", tags=["Trace"])
async def delete_trace(trace_id: str):
    """删除 Trace"""
    success = TraceService.delete_trace(trace_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
    
    # 广播删除事件
    await manager.broadcast({
        "type": "trace_deleted",
        "data": {"trace_id": trace_id},
        "timestamp": datetime.utcnow().isoformat(),
    })
    
    return {"message": f"Trace {trace_id} deleted", "success": True}


@app.post(
    "/api/v1/trace/{trace_id}/event", response_model=TraceResponse, tags=["Trace"]
)
async def add_trace_event(trace_id: str, event: TraceEvent):
    """添加事件到 Trace"""
    trace = TraceService.add_event(trace_id, event)
    if not trace:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
    
    # 广播事件添加
    await manager.broadcast({
        "type": "trace_event",
        "data": {
            "trace_id": trace_id,
            "event": event.model_dump(),
            "trace": trace.model_dump(),
        },
        "timestamp": datetime.utcnow().isoformat(),
    })
    
    return trace


@app.get("/api/v1/traces", response_model=TraceListResponse, tags=["Trace"])
async def list_traces(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    agent_id: Optional[str] = Query(None, description="Agent ID过滤"),
    provider: Optional[str] = Query(None, description="提供商过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
):
    """
    列出 Traces

    支持多种过滤条件：
    - 按Agent ID
    - 按提供商
    - 按状态
    - 按时间范围
    """
    return TraceService.list_traces(
        page=page,
        page_size=page_size,
        agent_id=agent_id,
        provider=provider,
        status=status,
        start_time=start_time,
        end_time=end_time,
    )


# ==================== Cost API ====================


@app.get("/api/v1/cost/summary", response_model=list[CostSummary], tags=["Cost"])
async def get_cost_summary(
    provider: Optional[str] = Query(None, description="提供商过滤"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
):
    """
    获取成本汇总

    返回按 provider + model 分组的成本统计
    """
    return TraceService.get_cost_summary(
        provider=provider,
        start_time=start_time,
        end_time=end_time,
    )


@app.get("/api/v1/cost/models", tags=["Cost"])
async def get_model_costs():
    """获取各模型的Token成本配置"""
    return TraceService.TOKEN_COSTS


# ==================== Dashboard API ====================


@app.get("/api/v1/dashboard", tags=["Dashboard"])
async def get_dashboard():
    """
    获取 Dashboard 概览数据

    返回:
    - total_traces: 总 trace 数
    - running_traces: 运行中 trace 数
    - completed_traces: 已完成 trace 数
    - failed_traces: 失败 trace 数
    - total_cost: 总成本
    - avg_latency_ms: 平均延迟
    - provider_distribution: Provider 分布
    - model_distribution: Model 分布
    - recent_traces: 最近 traces
    """
    stats = TraceService.get_stats()

    # Provider 和 Model 分布
    provider_dist = {}
    model_dist = {}
    
    # 计算延迟分布
    latencies = []
    
    # 最近 traces
    recent = TraceService.list_traces(page=1, page_size=10)
    recent_traces = [t.model_dump() for t in recent.traces]

    for trace in TraceService.list_traces(page=1, page_size=1000).traces:
        provider = str(trace.provider)
        model = trace.model

        provider_dist[provider] = provider_dist.get(provider, 0) + 1
        model_dist[model] = model_dist.get(model, 0) + 1
        
        # 收集延迟数据
        if trace.duration_ms:
            latencies.append(trace.duration_ms)

    # 计算延迟分布
    latency_distribution = {}
    if latencies:
        buckets = [0, 100, 500, 1000, 2000, 5000, 10000]  # ms
        bucket_labels = ["<100ms", "100-500ms", "500ms-1s", "1-2s", "2-5s", "5-10s", ">10s"]
        
        for label in bucket_labels:
            latency_distribution[label] = 0
        
        for latency in latencies:
            for i, bucket in enumerate(buckets):
                if latency < bucket:
                    latency_distribution[bucket_labels[max(0, i-1)]] += 1
                    break
            else:
                latency_distribution[bucket_labels[-1]] += 1

    return {
        "total_traces": stats["total_traces"],
        "running_traces": stats["running_traces"],
        "completed_traces": stats["completed_traces"],
        "failed_traces": stats["failed_traces"],
        "total_cost": stats["total_cost"],
        "avg_latency_ms": stats.get("avg_latency_ms", 0),
        "provider_distribution": provider_dist,
        "model_distribution": model_dist,
        "latency_distribution": latency_distribution,
        "recent_traces": recent_traces,
    }


# ==================== Analytics API ====================


@app.get("/api/v1/analytics/timeline", tags=["Analytics"])
async def get_timeline(
    interval: str = Query("hour", description="时间间隔: minute, hour, day"),
    hours: int = Query(24, ge=1, le=168, description="查询时间范围(小时)"),
):
    """
    获取时间线数据
    
    用于绘制 trace 数量随时间变化的图表
    """
    end = datetime.utcnow()
    start = end - timedelta(hours=hours)
    
    # 获取所有 traces
    traces = TraceService.list_traces(
        page=1,
        page_size=10000,
        start_time=start,
        end_time=end,
    )
    
    # 按时间分组
    timeline_data = defaultdict(lambda: {"traces": 0, "cost": 0.0, "tokens": 0})
    
    for trace in traces.traces:
        if trace.created_at:
            # 根据间隔格式化时间
            if interval == "minute":
                key = trace.created_at.strftime("%Y-%m-%d %H:%M")
            elif interval == "day":
                key = trace.created_at.strftime("%Y-%m-%d")
            else:  # hour
                key = trace.created_at.strftime("%Y-%m-%d %H:00")
            
            timeline_data[key]["traces"] += 1
            timeline_data[key]["cost"] += trace.total_cost or 0
            timeline_data[key]["tokens"] += (trace.total_input_tokens or 0) + (trace.total_output_tokens or 0)
    
    # 转换为列表并排序
    result = [
        {
            "time": k,
            "traces": v["traces"],
            "cost": round(v["cost"], 6),
            "tokens": v["tokens"],
        }
        for k, v in sorted(timeline_data.items())
    ]
    
    return {"interval": interval, "data": result}


@app.get("/api/v1/analytics/providers", tags=["Analytics"])
async def get_provider_analytics():
    """
    获取 Provider 分析数据
    
    返回每个 provider 的详细统计
    """
    traces = TraceService.list_traces(page=1, page_size=10000)
    
    provider_stats = defaultdict(lambda: {
        "traces": 0,
        "total_cost": 0.0,
        "total_tokens": 0,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "avg_latency_ms": 0,
        "latencies": [],
        "models": set(),
        "success_count": 0,
        "failed_count": 0,
    })
    
    for trace in traces.traces:
        provider = str(trace.provider)
        stats = provider_stats[provider]
        
        stats["traces"] += 1
        stats["total_cost"] += trace.total_cost or 0
        stats["total_input_tokens"] += trace.total_input_tokens or 0
        stats["total_output_tokens"] += trace.total_output_tokens or 0
        stats["total_tokens"] += (trace.total_input_tokens or 0) + (trace.total_output_tokens or 0)
        
        if trace.model:
            stats["models"].add(trace.model)
        
        if trace.duration_ms:
            stats["latencies"].append(trace.duration_ms)
        
        if trace.status == "completed":
            stats["success_count"] += 1
        elif trace.status == "failed":
            stats["failed_count"] += 1
    
    # 计算平均延迟和成功率
    result = []
    for provider, stats in provider_stats.items():
        avg_latency = sum(stats["latencies"]) / len(stats["latencies"]) if stats["latencies"] else 0
        success_rate = stats["success_count"] / stats["traces"] * 100 if stats["traces"] > 0 else 0
        
        result.append({
            "provider": provider,
            "traces": stats["traces"],
            "total_cost": round(stats["total_cost"], 6),
            "total_tokens": stats["total_tokens"],
            "input_tokens": stats["total_input_tokens"],
            "output_tokens": stats["total_output_tokens"],
            "avg_latency_ms": round(avg_latency, 2),
            "success_rate": round(success_rate, 2),
            "models": list(stats["models"]),
        })
    
    return result


# ==================== Budget Tracking API ====================

# In-memory budget storage (in production, use database)
budget_config: dict = {
    "daily_limit": 10.0,  # $10 daily budget
    "monthly_limit": 100.0,  # $100 monthly budget
    "alert_threshold": 0.8,  # 80% alert threshold
    "providers_limits": {},  # Per-provider limits
}


@app.get("/api/v1/budget", tags=["Budget"])
async def get_budget_config():
    """
    获取预算配置
    
    返回当前的预算限制和告警阈值
    """
    stats = TraceService.get_stats()
    
    # Calculate current spending
    today_cost = stats.get("today_cost", 0.0)
    month_cost = stats.get("month_cost", 0.0)
    
    # Calculate budget status
    daily_usage_percent = (today_cost / budget_config["daily_limit"]) * 100 if budget_config["daily_limit"] > 0 else 0
    monthly_usage_percent = (month_cost / budget_config["monthly_limit"]) * 100 if budget_config["monthly_limit"] > 0 else 0
    
    # Determine alert status
    alerts = []
    if daily_usage_percent >= budget_config["alert_threshold"] * 100:
        alerts.append({
            "type": "daily_budget",
            "severity": "warning" if daily_usage_percent < 100 else "critical",
            "message": f"Daily budget {daily_usage_percent:.1f}% used",
            "current": today_cost,
            "limit": budget_config["daily_limit"],
        })
    if monthly_usage_percent >= budget_config["alert_threshold"] * 100:
        alerts.append({
            "type": "monthly_budget",
            "severity": "warning" if monthly_usage_percent < 100 else "critical",
            "message": f"Monthly budget {monthly_usage_percent:.1f}% used",
            "current": month_cost,
            "limit": budget_config["monthly_limit"],
        })
    
    return {
        "config": budget_config,
        "status": {
            "today_cost": today_cost,
            "month_cost": month_cost,
            "daily_usage_percent": round(daily_usage_percent, 2),
            "monthly_usage_percent": round(monthly_usage_percent, 2),
            "daily_remaining": round(budget_config["daily_limit"] - today_cost, 4),
            "monthly_remaining": round(budget_config["monthly_limit"] - month_cost, 4),
            "daily_over_budget": today_cost > budget_config["daily_limit"],
            "monthly_over_budget": month_cost > budget_config["monthly_limit"],
        },
        "alerts": alerts,
    }


@app.put("/api/v1/budget", tags=["Budget"])
async def update_budget_config(
    daily_limit: Optional[float] = Query(None, description="Daily budget limit in $"),
    monthly_limit: Optional[float] = Query(None, description="Monthly budget limit in $"),
    alert_threshold: Optional[float] = Query(None, description="Alert threshold (0-1)"),
):
    """
    更新预算配置
    
    - **daily_limit**: 每日预算限制 ($)
    - **monthly_limit**: 每月预算限制 ($)
    - **alert_threshold**: 告警阈值 (0-1, 如 0.8 表示 80%)
    """
    if daily_limit is not None:
        budget_config["daily_limit"] = daily_limit
    if monthly_limit is not None:
        budget_config["monthly_limit"] = monthly_limit
    if alert_threshold is not None:
        if alert_threshold < 0 or alert_threshold > 1:
            raise HTTPException(status_code=400, detail="alert_threshold must be between 0 and 1")
        budget_config["alert_threshold"] = alert_threshold
    
    return {"message": "Budget config updated", "config": budget_config}


@app.get("/api/v1/budget/history", tags=["Budget"])
async def get_budget_history(days: int = Query(7, ge=1, le=30, description="Number of days to analyze")):
    """
    获取预算历史
    
    返回过去 N 天的每日成本统计
    """
    traces = TraceService.list_traces(page=1, page_size=10000)
    
    # Group by day
    daily_costs = defaultdict(float)
    daily_traces = defaultdict(int)
    
    for trace in traces.traces:
        if trace.created_at:
            day_key = trace.created_at.strftime("%Y-%m-%d")
            daily_costs[day_key] += trace.total_cost or 0
            daily_traces[day_key] += 1
    
    # Build history
    history = []
    for day, cost in sorted(daily_costs.items(), reverse=True)[:days]:
        history.append({
            "date": day,
            "cost": round(cost, 6),
            "traces": daily_traces[day],
            "over_budget": cost > budget_config["daily_limit"],
        })
    
    return {
        "days": days,
        "daily_limit": budget_config["daily_limit"],
        "history": history,
        "total_cost": round(sum(d["cost"] for d in history), 4),
        "avg_daily_cost": round(sum(d["cost"] for d in history) / len(history), 4) if history else 0,
    }


@app.get("/api/v1/budget/providers", tags=["Budget"])
async def get_provider_budget_status():
    """
    获取各 Provider 的预算状态
    
    返回每个 Provider 的成本分布和建议
    """
    traces = TraceService.list_traces(page=1, page_size=10000)
    
    provider_costs = defaultdict(float)
    provider_traces = defaultdict(int)
    
    for trace in traces.traces:
        provider_costs[str(trace.provider)] += trace.total_cost or 0
        provider_traces[str(trace.provider)] += 1
    
    # DeepSeek savings calculation (DeepSeek is ~107x cheaper than GPT-4)
    DEEPSEEK_SAVINGS_FACTOR = 107
    
    suggestions = []
    total_openai_cost = provider_costs.get("openai", 0)
    total_deepseek_cost = provider_costs.get("deepseek", 0)
    
    if total_openai_cost > 0 and total_deepseek_cost == 0:
        potential_savings = total_openai_cost - total_openai_cost / DEEPSEEK_SAVINGS_FACTOR
        suggestions.append({
            "type": "switch_provider",
            "from": "openai",
            "to": "deepseek",
            "current_cost": round(total_openai_cost, 4),
            "potential_cost": round(total_openai_cost / DEEPSEEK_SAVINGS_FACTOR, 6),
            "savings": round(potential_savings, 4),
            "savings_percent": 99.1,  # ~99% savings
        })
    
    # Build provider status
    providers = []
    for provider, cost in provider_costs.items():
        provider_limit = budget_config["providers_limits"].get(provider, budget_config["monthly_limit"])
        providers.append({
            "provider": provider,
            "cost": round(cost, 6),
            "traces": provider_traces[provider],
            "limit": provider_limit,
            "usage_percent": round((cost / provider_limit) * 100, 2) if provider_limit > 0 else 0,
        })
    
    return {
        "providers": sorted(providers, key=lambda x: x["cost"], reverse=True),
        "suggestions": suggestions,
    }


# ==================== WebSocket 端点 ====================


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket 实时推送端点
    
    消息类型:
    - trace_created: 新 trace 创建
    - trace_updated: trace 更新
    - trace_deleted: trace 删除
    - trace_event: trace 事件添加
    - stats_update: 统计更新
    - ping/pong: 心跳
    """
    await manager.connect(websocket)
    
    try:
        # 发送欢迎消息
        await manager.send_to(websocket, {
            "type": "connected",
            "message": "Connected to AgentWatch real-time updates",
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        # 发送当前统计
        stats = TraceService.get_stats()
        await manager.send_to(websocket, {
            "type": "stats_update",
            "data": stats,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        while True:
            # 等待客户端消息
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await manager.send_to(websocket, {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                
                elif message.get("type") == "subscribe":
                    # 未来可扩展: 订阅特定 trace 或 agent
                    await manager.send_to(websocket, {
                        "type": "subscribed",
                        "channels": message.get("channels", ["all"]),
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                
                elif message.get("type") == "get_stats":
                    stats = TraceService.get_stats()
                    await manager.send_to(websocket, {
                        "type": "stats_update",
                        "data": stats,
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                    
            except json.JSONDecodeError:
                await manager.send_to(websocket, {
                    "type": "error",
                    "message": "Invalid JSON",
                    "timestamp": datetime.utcnow().isoformat(),
                })
                
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await manager.disconnect(websocket)


# ==================== 测试端点 ====================


@app.post("/api/v1/test/trace", response_model=TraceResponse, tags=["Test"])
async def create_test_trace():
    """创建测试 Trace（用于快速测试）"""
    trace_data = TraceCreate(
        agent_id="test-agent-001",
        agent_name="TestAgent",
        provider=AgentProvider.OPENAI,
        model="gpt-4o-mini",
        session_id="test-session",
        user_id="test-user",
        prompt="Hello, this is a test trace",
    )
    trace = TraceService.create_trace(trace_data)

    # 添加测试事件
    event1 = TraceEvent(
        event_id="ev_001",
        event_type="call",
        model="gpt-4o-mini",
        input_tokens=50,
        output_tokens=0,
        latency_ms=100,
        content="User prompt sent",
    )
    event2 = TraceEvent(
        event_id="ev_002",
        event_type="response",
        model="gpt-4o-mini",
        input_tokens=50,
        output_tokens=150,
        latency_ms=800,
        content="AI response received",
    )

    TraceService.add_event(trace.trace_id, event1)
    TraceService.add_event(trace.trace_id, event2)
    TraceService.update_trace(trace.trace_id, TraceUpdate(status=TraceStatus.COMPLETED))

    final_trace = TraceService.get_trace(trace.trace_id)
    
    # 广播测试事件
    await manager.broadcast({
        "type": "test_trace_created",
        "data": final_trace.model_dump(),
        "timestamp": datetime.utcnow().isoformat(),
    })
    
    return final_trace


# 开发运行: uvicorn main:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)