"""
AgentWatch Backend Tests
"""

import pytest
from fastapi.testclient import TestClient
import sys

sys.path.insert(0, ".")

from main import app


client = TestClient(app)


def test_health_check():
    """测试健康检查端点"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_stats():
    """测试统计端点"""
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_traces" in data
    assert "total_cost" in data


def test_create_trace():
    """测试创建 Trace"""
    response = client.post(
        "/api/v1/trace",
        json={
            "agent_id": "test-agent",
            "agent_name": "TestAgent",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "prompt": "Hello",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "trace_id" in data
    assert data["agent_name"] == "TestAgent"


def test_get_trace():
    """测试获取 Trace"""
    # 先创建一个 trace
    create_response = client.post(
        "/api/v1/trace",
        json={
            "agent_id": "test-agent-2",
            "agent_name": "TestAgent2",
            "provider": "openai",
            "model": "gpt-4o-mini",
        },
    )
    trace_id = create_response.json()["trace_id"]

    # 然后获取它
    response = client.get(f"/api/v1/trace/{trace_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["trace_id"] == trace_id


def test_dashboard():
    """测试 Dashboard"""
    response = client.get("/api/v1/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "total_traces" in data
    assert "provider_distribution" in data


def test_cost_models():
    """测试成本模型配置"""
    response = client.get("/api/v1/cost/models")
    assert response.status_code == 200
    data = response.json()
    assert "openai" in data
