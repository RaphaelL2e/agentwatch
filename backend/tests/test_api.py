"""
Backend API Tests
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestHealthAPI:
    """Health API Tests"""

    def test_health_check(self):
        """Test health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestStatsAPI:
    """Stats API Tests"""

    def test_stats_endpoint(self):
        """Test stats endpoint"""
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_traces" in data
        assert "total_cost" in data


class TestTraceAPI:
    """Trace API Tests"""

    def test_create_trace(self):
        """Test creating a trace"""
        trace_data = {
            "agent_id": "test_agent_001",
            "agent_name": "Test Agent",
            "provider": "openai",
            "model": "gpt-4o",
            "session_id": "test_session",
            "user_id": "test_user",
            "prompt": "Test prompt",
        }
        response = client.post("/api/v1/trace", json=trace_data)
        assert response.status_code == 200
        data = response.json()
        assert "trace_id" in data
        assert data["agent_name"] == "Test Agent"

    def test_create_test_trace(self):
        """Test creating a test trace"""
        response = client.post("/api/v1/test/trace")
        assert response.status_code == 200
        data = response.json()
        assert "trace_id" in data

    def test_get_traces(self):
        """Test getting traces list"""
        response = client.get("/api/v1/traces")
        assert response.status_code == 200
        data = response.json()
        assert "traces" in data
        assert "total" in data

    def test_get_trace_by_id(self):
        """Test getting a specific trace"""
        # First create a trace
        trace_data = {
            "agent_id": "test_agent_002",
            "agent_name": "Test Agent 2",
            "provider": "anthropic",
            "model": "claude-3-sonnet",
        }
        create_response = client.post("/api/v1/trace", json=trace_data)
        trace_id = create_response.json()["trace_id"]

        # Then get it
        response = client.get(f"/api/v1/trace/{trace_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["trace_id"] == trace_id

    def test_update_trace(self):
        """Test updating a trace"""
        # First create a trace
        trace_data = {
            "agent_id": "test_agent_003",
            "agent_name": "Test Agent 3",
            "provider": "deepseek",
            "model": "deepseek-chat",
        }
        create_response = client.post("/api/v1/trace", json=trace_data)
        trace_id = create_response.json()["trace_id"]

        # Update it
        update_data = {
            "status": "completed",
            "input_tokens": 1000,
            "output_tokens": 500,
        }
        response = client.put(f"/api/v1/trace/{trace_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    def test_add_event(self):
        """Test adding an event to a trace"""
        # First create a trace
        trace_data = {
            "agent_id": "test_agent_004",
            "agent_name": "Test Agent 4",
            "provider": "google",
            "model": "gemini-1.5-pro",
        }
        create_response = client.post("/api/v1/trace", json=trace_data)
        trace_id = create_response.json()["trace_id"]

        # Add event with all required fields
        event_data = {
            "event_id": "event_001",
            "event_type": "llm_call",
            "message": "Called GPT-4",
            "timestamp": "2026-04-27T00:00:00Z",
        }
        response = client.post(f"/api/v1/trace/{trace_id}/event", json=event_data)
        assert response.status_code == 200


class TestCostAPI:
    """Cost API Tests"""

    def test_cost_summary(self):
        """Test cost summary endpoint"""
        response = client.get("/api/v1/cost/summary")
        assert response.status_code == 200
        data = response.json()
        # Returns list of summaries by model
        assert isinstance(data, list)

    def test_cost_summary_by_provider(self):
        """Test cost summary by provider"""
        response = client.get("/api/v1/cost/summary?provider=openai")
        assert response.status_code == 200

    def test_model_costs(self):
        """Test model costs endpoint"""
        response = client.get("/api/v1/cost/models")
        assert response.status_code == 200
        data = response.json()
        # Should return a dict of model -> cost
        assert isinstance(data, dict)


class TestCostCalculation:
    """Cost Calculation Tests"""

    def test_openai_cost(self):
        """Test OpenAI cost calculation"""
        from trace_service import TraceService

        service = TraceService()
        cost = service.calculate_cost("openai", "gpt-4o", 1000, 500)
        # GPT-4o: $0.005/1K input, $0.015/1K output
        expected = 0.005 * 1 + 0.015 * 0.5  # = 0.0125
        assert abs(cost - expected) < 0.0001

    def test_deepseek_cost(self):
        """Test DeepSeek cost calculation"""
        from trace_service import TraceService

        service = TraceService()
        cost = service.calculate_cost("deepseek", "deepseek-chat", 1000, 500)
        # DeepSeek chat: $0.00007/1K input, $0.00014/1K output
        expected = 0.00007 * 1 + 0.00014 * 0.5  # = 0.00014
        assert abs(cost - expected) < 0.00001

    def test_deepseek_vs_openai_ratio(self):
        """Test DeepSeek vs OpenAI cost ratio"""
        from trace_service import TraceService

        service = TraceService()
        openai_cost = service.calculate_cost("openai", "gpt-4o", 1000, 500)
        deepseek_cost = service.calculate_cost("deepseek", "deepseek-chat", 1000, 500)
        ratio = openai_cost / deepseek_cost
        # Should be around 89x (0.0125 / 0.00014 = 89.28)
        assert ratio > 80
        assert ratio < 100
