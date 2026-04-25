"""
AgentWatch Backend
FastAPI 主入口 - Day 2完整实现
"""

import time
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from models import (
    TraceCreate, TraceUpdate, TraceResponse, TraceListResponse,
    TraceEvent, CostSummary, HealthCheck, TraceStatus, AgentProvider
)
from trace_service import TraceService

# 启动时间
START_TIME = time.time()

app = FastAPI(
    title="AgentWatch",
    description="AI Agent Security Monitoring Platform - Track, Debug, and Optimize Your AI Agents",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 基础端点 ====================

@app.get("/", tags=["Root"])
async def root():
    """API根路径"""
    return {
        "message": "AgentWatch API",
        "version": "0.2.0",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health", response_model=HealthCheck, tags=["Health"])
async def health():
    """健康检查"""
    stats = TraceService.get_stats()
    return HealthCheck(
        status="healthy",
        version="0.2.0",
        uptime_seconds=time.time() - START_TIME,
        database_connected=True,  # 内存存储总是连接
        traces_count=stats["total_traces"]
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
    return TraceService.create_trace(trace_data)


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
    return trace


@app.delete("/api/v1/trace/{trace_id}", tags=["Trace"])
async def delete_trace(trace_id: str):
    """删除 Trace"""
    success = TraceService.delete_trace(trace_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
    return {"message": f"Trace {trace_id} deleted", "success": True}


@app.post("/api/v1/trace/{trace_id}/event", response_model=TraceResponse, tags=["Trace"])
async def add_trace_event(trace_id: str, event: TraceEvent):
    """添加事件到 Trace"""
    trace = TraceService.add_event(trace_id, event)
    if not trace:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
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
    
    return TraceService.get_trace(trace.trace_id)


# ==================== 启动事件 ====================

@app.on_event("startup")
async def startup_event():
    """启动事件"""
    print("🚀 AgentWatch Backend started!")
    print(f"   Version: 0.2.0")
    print(f"   Docs: http://localhost:8000/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """关闭事件"""
    print("👋 AgentWatch Backend shutting down...")


# 开发运行: uvicorn main:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)