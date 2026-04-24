"""
AgentWatch Backend
FastAPI骨架 - Day 2任务
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AgentWatch",
    description="AI Agent Security Monitoring Platform",
    version="0.1.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "AgentWatch API", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "0.1.0"}


# Trace API端点 - Day 2核心任务
@app.post("/api/v1/trace")
async def create_trace(trace_data: dict):
    """接收Agent执行trace数据"""
    # TODO: 存储到ClickHouse
    return {"trace_id": "pending", "status": "received"}


@app.get("/api/v1/trace/{trace_id}")
async def get_trace(trace_id: str):
    """获取trace详情"""
    # TODO: 从ClickHouse查询
    return {"trace_id": trace_id, "data": "pending"}


@app.get("/api/v1/traces")
async def list_traces(limit: int = 100):
    """列出最近traces"""
    # TODO: 从ClickHouse查询
    return {"traces": [], "count": 0}


# Agent监控端点
@app.get("/api/v1/agents")
async def list_agents():
    """列出活跃Agents"""
    return {"agents": [], "count": 0}


@app.get("/api/v1/agent/{agent_id}/metrics")
async def get_agent_metrics(agent_id: str):
    """获取Agent性能指标"""
    return {
        "agent_id": agent_id,
        "metrics": {
            "executions": 0,
            "success_rate": 0,
            "avg_latency": 0
        }
    }


# 安全监控端点 - 核心差异化功能
@app.get("/api/v1/security/alerts")
async def get_security_alerts():
    """获取安全告警"""
    return {"alerts": [], "count": 0}


@app.post("/api/v1/security/scan")
async def scan_dependencies(scan_request: dict):
    """扫描依赖安全"""
    # TODO: 实现供应链安全扫描
    return {"scan_id": "pending", "status": "scanning"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)