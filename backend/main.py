"""
AgentWatch Backend
FastAPI 主入口 - 支持 WebSocket 实时推送 + 认证系统
"""

import time
import asyncio
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from collections import defaultdict

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect, Depends
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

# Auth module (optional - gracefully handle if not available)
try:
    from auth.routes import router as auth_router
    from auth.middleware import verify_api_key, get_current_user
    AUTH_ENABLED=True
except ImportError:
    AUTH_ENABLED=False
    auth_router = None
    verify_api_key = None
    get_current_user = None

# Team API module (Phase 2 功能扩展)
try:
    from team_api import router as team_router
    TEAM_API_ENABLED=True
except ImportError:
    TEAM_API_ENABLED=False
    team_router = None

# 启动时间
START_TIME = time.time()


# Lifespan handler for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    print("🚀 AgentWatch Backend started!")
    print("   Version: 0.8.0")
    print("   Docs: http://localhost:8000/docs")
    print("   WebSocket: ws://localhost:8000/ws")
    if AUTH_ENABLED:
        print("   Auth: Enabled")
    # 启动实时推送后台任务
    await push_manager.start_background_push()
    print("📡 Real-time push enabled")
    yield
    # Shutdown
    await push_manager.stop_background_push()
    print("📡 Real-time push disabled")
    print("👋 AgentWatch Backend shutting down...")


app = FastAPI(
    title="AgentWatch",
    description="AI Agent Security Monitoring Platform - Track, Debug, and Optimize Your AI Agents",
    version="0.8.0",
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

# 注册认证路由
if AUTH_ENABLED and auth_router:
    app.include_router(auth_router)

# 注册团队协作路由 (Phase 2)
if TEAM_API_ENABLED and team_router:
    app.include_router(team_router)


# ==================== WebSocket 管理 ====================

from realtime import RealTimePushManager, AlertConfig

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

# 创建实时推送管理器
push_manager = RealTimePushManager(
    broadcast_func=manager.broadcast,
    get_stats_func=TraceService.get_stats,
    config=AlertConfig(
        cost_threshold=0.10,
        latency_threshold_ms=5000,
        failure_rate_threshold=0.3,
        token_threshold=100000,
    ),
)


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
    
    # 使用实时推送管理器广播（包含预警检查）
    await push_manager.push_trace_created(trace.model_dump())
    
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
    
    # 使用实时推送管理器广播
    await push_manager.push_trace_updated(trace.model_dump())
    
    return trace


@app.delete("/api/v1/trace/{trace_id}", tags=["Trace"])
async def delete_trace(trace_id: str):
    """删除 Trace"""
    success = TraceService.delete_trace(trace_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
    
    # 使用实时推送管理器广播
    await push_manager.push_trace_deleted(trace_id)
    
    return {"message": f"Trace {trace_id} deleted", "success": True}


@app.post(
    "/api/v1/trace/{trace_id}/event", response_model=TraceResponse, tags=["Trace"]
)
async def add_trace_event(trace_id: str, event: TraceEvent):
    """添加事件到 Trace"""
    trace = TraceService.add_event(trace_id, event)
    if not trace:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
    
    # 使用实时推送管理器广播
    await push_manager.push_trace_event(trace_id, event.model_dump(), trace.model_dump())
    
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




# ==================== DeepSeek Cost Comparison API ====================

# Model pricing data (per 1M tokens)
MODEL_PRICING = {
    "openai": {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    },
    "anthropic": {
        "claude-3-opus": {"input": 15.00, "output": 75.00},
        "claude-3-sonnet": {"input": 3.00, "output": 15.00},
        "claude-3-haiku": {"input": 0.25, "output": 1.25},
    },
    "deepseek": {
        "deepseek-chat": {"input": 0.14, "output": 0.28},
        "deepseek-coder": {"input": 0.14, "output": 0.28},
    },
    "google": {
        "gemini-pro": {"input": 0.50, "output": 1.50},
        "gemini-ultra": {"input": 2.50, "output": 10.00},
    },
}


@app.get("/api/v1/models/pricing", tags=["Cost Comparison"])
async def get_model_pricing():
    """获取所有模型的定价信息"""
    return MODEL_PRICING


@app.get("/api/v1/models/comparison", tags=["Cost Comparison"])
async def compare_model_costs(
    input_tokens: int = Query(10000, ge=100, description="输入token数量"),
    output_tokens: int = Query(5000, ge=100, description="输出token数量"),
    compare_to: str = Query("gpt-4o", description="对比基准模型"),
):
    """DeepSeek成本对比 - 107倍成本优势"""
    comparisons = []
    for provider, models in MODEL_PRICING.items():
        for model_name, pricing in models.items():
            input_cost = (pricing["input"] / 1_000_000) * input_tokens
            output_cost = (pricing["output"] / 1_000_000) * output_tokens
            total_cost = input_cost + output_cost
            comparisons.append({
                "provider": provider,
                "model": model_name,
                "total_cost": round(total_cost, 6),
            })
    
    # 计算省钱倍数
    base_cost = next((c["total_cost"] for c in comparisons if c["model"] == compare_to), None)
    if base_cost:
        for c in comparisons:
            c["savings_multiplier"] = round(base_cost / c["total_cost"], 1) if c["total_cost"] > 0 else 0
            c["savings_percent"] = round((1 - c["total_cost"] / base_cost) * 100, 1) if base_cost > 0 else 0
    
    comparisons.sort(key=lambda x: x["total_cost"])
    return {"base_cost": base_cost, "comparisons": comparisons}


@app.get("/api/v1/models/recommendation", tags=["Cost Comparison"])
async def get_model_recommendation(
    monthly_budget: float = Query(100.0, ge=10, description="月度预算($)"),
):
    """根据预算推荐最佳模型"""
    recommendations = []
    for provider, models in MODEL_PRICING.items():
        for model_name, pricing in models.items():
            monthly_cost = (pricing["input"] * 0.7 + pricing["output"] * 0.3)  # 假设每月1M tokens
            recommendations.append({
                "provider": provider,
                "model": model_name,
                "monthly_cost": round(monthly_cost, 2),
                "within_budget": monthly_cost <= monthly_budget,
            })
    
    recommendations.sort(key=lambda x: (-x["within_budget"], x["monthly_cost"]))
    return {"budget": monthly_budget, "recommendations": recommendations}


@app.get("/api/v1/models/performance", tags=["Cost Comparison"])
async def get_model_performance_comparison():
    """
    模型性能对比
    
    基于公开测试数据对比各模型性能和成本效率
    """
    # 简化的性能数据 (基于公开基准测试)
    performance_data = {
        "gpt-4o": {
            "mmlu": 86.4,
            "humaneval": 90.2,
            "math": 76.6,
            "speed": "fast",
            "cost_efficiency": 1.0,
        },
        "gpt-4o-mini": {
            "mmlu": 82.0,
            "humaneval": 87.0,
            "math": 70.0,
            "speed": "very_fast",
            "cost_efficiency": 16.7,
        },
        "claude-3-opus": {
            "mmlu": 86.8,
            "humaneval": 84.9,
            "math": 80.0,
            "speed": "medium",
            "cost_efficiency": 0.2,
        },
        "claude-3-sonnet": {
            "mmlu": 79.0,
            "humaneval": 73.0,
            "math": 43.0,
            "speed": "fast",
            "cost_efficiency": 1.0,
        },
        "deepseek-chat": {
            "mmlu": 75.0,
            "humaneval": 78.0,
            "math": 65.0,
            "speed": "fast",
            "cost_efficiency": 107.0,  # 107x cost advantage
        },
        "gemini-pro": {
            "mmlu": 71.8,
            "humaneval": 70.0,
            "math": 45.0,
            "speed": "fast",
            "cost_efficiency": 5.0,
        },
    }
    
    return {
        "models": performance_data,
        "benchmark_explanation": {
            "mmlu": "Massive Multitask Language Understanding - general knowledge",
            "humaneval": "HumanEval - code generation accuracy",
            "math": "Mathematical problem solving",
            "speed": "Response latency category",
            "cost_efficiency": "Relative cost efficiency (higher = better)",
        },
        "deepseek_analysis": {
            "cost_efficiency": 107.0,
            "performance_vs_gpt4o": "88-92% for most tasks",
            "recommendation": "Best choice for cost-sensitive production workloads",
        },
    }


# ==================== Data Export API ====================

import io
import csv
from fastapi.responses import StreamingResponse


@app.get("/api/v1/export/traces/json", tags=["Export"])
async def export_traces_json(
    provider: Optional[str] = Query(None, description="Provider filter"),
    status: Optional[str] = Query(None, description="Status filter"),
    start_time: Optional[datetime] = Query(None, description="Start time"),
    end_time: Optional[datetime] = Query(None, description="End time"),
    agent_id: Optional[str] = Query(None, description="Agent ID filter"),
):
    """
    Export traces as JSON file
    
    Returns all traces matching filters as a downloadable JSON file.
    """
    traces = TraceService.list_traces(
        page=1,
        page_size=10000,
        provider=provider,
        status=status,
        start_time=start_time,
        end_time=end_time,
        agent_id=agent_id,
    )
    
    # Convert to export format
    export_data = {
        "export_metadata": {
            "exported_at": datetime.utcnow().isoformat(),
            "total_traces": len(traces.traces),
            "filters": {
                "provider": provider,
                "status": status,
                "start_time": start_time.isoformat() if start_time else None,
                "end_time": end_time.isoformat() if end_time else None,
                "agent_id": agent_id,
            },
        },
        "traces": [t.model_dump() for t in traces.traces],
    }
    
    # Create JSON content
    json_content = json.dumps(export_data, indent=2, default=str)
    
    return StreamingResponse(
        iter([json_content]),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=agentwatch_traces_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        },
    )


@app.get("/api/v1/export/traces/csv", tags=["Export"])
async def export_traces_csv(
    provider: Optional[str] = Query(None, description="Provider filter"),
    status: Optional[str] = Query(None, description="Status filter"),
    start_time: Optional[datetime] = Query(None, description="Start time"),
    end_time: Optional[datetime] = Query(None, description="End time"),
    agent_id: Optional[str] = Query(None, description="Agent ID filter"),
):
    """
    Export traces as CSV file
    
    Returns all traces matching filters as a downloadable CSV file.
    Suitable for spreadsheet analysis.
    """
    traces = TraceService.list_traces(
        page=1,
        page_size=10000,
        provider=provider,
        status=status,
        start_time=start_time,
        end_time=end_time,
        agent_id=agent_id,
    )
    
    # Create CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header row
    headers = [
        "trace_id", "agent_id", "agent_name", "provider", "model",
        "status", "total_cost", "input_tokens", "output_tokens",
        "duration_ms", "created_at", "completed_at", "session_id", "user_id"
    ]
    writer.writerow(headers)
    
    # Data rows
    for trace in traces.traces:
        row = [
            trace.trace_id,
            trace.agent_id,
            trace.agent_name,
            str(trace.provider),
            trace.model,
            trace.status,
            trace.total_cost or 0,
            trace.total_input_tokens or 0,
            trace.total_output_tokens or 0,
            trace.duration_ms or 0,
            trace.created_at.isoformat() if trace.created_at else "",
            trace.completed_at.isoformat() if trace.completed_at else "",
            trace.session_id or "",
            trace.user_id or "",
        ]
        writer.writerow(row)
    
    csv_content = output.getvalue()
    output.close()
    
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=agentwatch_traces_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        },
    )


@app.get("/api/v1/export/cost/summary", tags=["Export"])
async def export_cost_summary(
    format: str = Query("json", description="Export format: json or csv"),
    provider: Optional[str] = Query(None, description="Provider filter"),
    start_time: Optional[datetime] = Query(None, description="Start time"),
    end_time: Optional[datetime] = Query(None, description="End time"),
):
    """
    Export cost summary report
    
    Returns cost breakdown by provider and model.
    """
    cost_data = TraceService.get_cost_summary(
        provider=provider,
        start_time=start_time,
        end_time=end_time,
    )
    
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow(["provider", "model", "total_traces", "total_cost", "total_tokens", "avg_latency_ms"])
        
        # Data
        for item in cost_data:
            writer.writerow([
                str(item.provider),
                item.model,
                item.total_traces,
                item.total_cost,
                item.total_tokens,
                item.avg_latency_ms,
            ])
        
        csv_content = output.getvalue()
        output.close()
        
        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=agentwatch_cost_summary_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
            },
        )
    else:
        export_data = {
            "export_metadata": {
                "exported_at": datetime.utcnow().isoformat(),
                "filters": {
                    "provider": provider,
                    "start_time": start_time.isoformat() if start_time else None,
                    "end_time": end_time.isoformat() if end_time else None,
                },
            },
            "cost_summary": [item.model_dump() for item in cost_data],
        }
        
        json_content = json.dumps(export_data, indent=2, default=str)
        
        return StreamingResponse(
            iter([json_content]),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=agentwatch_cost_summary_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            },
        )


@app.get("/api/v1/export/analytics/report", tags=["Export"])
async def export_analytics_report(
    format: str = Query("json", description="Export format: json or csv"),
    days: int = Query(7, ge=1, le=30, description="Number of days to include"),
):
    """
    Export comprehensive analytics report
    
    Includes:
    - Overall statistics
    - Provider breakdown
    - Model performance
    - Daily trends
    """
    stats = TraceService.get_stats()
    traces = TraceService.list_traces(page=1, page_size=10000)
    
    # Daily breakdown
    daily_data = defaultdict(lambda: {"traces": 0, "cost": 0.0, "tokens": 0})
    for trace in traces.traces:
        if trace.created_at:
            day_key = trace.created_at.strftime("%Y-%m-%d")
            daily_data[day_key]["traces"] += 1
            daily_data[day_key]["cost"] += trace.total_cost or 0
            daily_data[day_key]["tokens"] += (trace.total_input_tokens or 0) + (trace.total_output_tokens or 0)
    
    # Provider breakdown
    provider_stats = defaultdict(lambda: {"traces": 0, "cost": 0.0, "tokens": 0})
    for trace in traces.traces:
        provider_stats[str(trace.provider)]["traces"] += 1
        provider_stats[str(trace.provider)]["cost"] += trace.total_cost or 0
        provider_stats[str(trace.provider)]["tokens"] += (trace.total_input_tokens or 0) + (trace.total_output_tokens or 0)
    
    # Build report
    report = {
        "export_metadata": {
            "exported_at": datetime.utcnow().isoformat(),
            "report_days": days,
        },
        "overall_stats": stats,
        "daily_trends": [
            {"date": k, "traces": v["traces"], "cost": round(v["cost"], 4), "tokens": v["tokens"]}
            for k, v in sorted(daily_data.items(), reverse=True)[:days]
        ],
        "provider_breakdown": [
            {"provider": k, "traces": v["traces"], "cost": round(v["cost"], 4), "tokens": v["tokens"]}
            for k, v in sorted(provider_stats.items(), key=lambda x: x[1]["cost"], reverse=True)
        ],
    }
    
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Overall stats
        writer.writerow(["=== OVERALL STATS ==="])
        writer.writerow(["metric", "value"])
        for key, value in stats.items():
            writer.writerow([key, value])
        
        writer.writerow([])
        writer.writerow(["=== DAILY TRENDS ==="])
        writer.writerow(["date", "traces", "cost", "tokens"])
        for day in report["daily_trends"]:
            writer.writerow([day["date"], day["traces"], day["cost"], day["tokens"]])
        
        writer.writerow([])
        writer.writerow(["=== PROVIDER BREAKDOWN ==="])
        writer.writerow(["provider", "traces", "cost", "tokens"])
        for provider in report["provider_breakdown"]:
            writer.writerow([provider["provider"], provider["traces"], provider["cost"], provider["tokens"]])
        
        csv_content = output.getvalue()
        output.close()
        
        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=agentwatch_analytics_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
            },
        )
    else:
        json_content = json.dumps(report, indent=2, default=str)
        
        return StreamingResponse(
            iter([json_content]),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=agentwatch_analytics_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            },
        )


# 开发运行: uvicorn main:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)