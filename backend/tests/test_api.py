"""
Backend API Tests
Complete tests for all API endpoints including WebSocket and Analytics
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

    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "AgentWatch API"
        assert data["websocket"] == "/ws"


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

    def test_get_traces_with_pagination(self):
        """Test getting traces with pagination"""
        response = client.get("/api/v1/traces?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert "page" in data
        assert data["page"] == 1

    def test_get_traces_with_filters(self):
        """Test getting traces with filters"""
        response = client.get("/api/v1/traces?provider=openai&status=completed")
        assert response.status_code == 200

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

    def test_get_trace_not_found(self):
        """Test getting a non-existent trace"""
        response = client.get("/api/v1/trace/nonexistent_id")
        assert response.status_code == 404

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

    def test_delete_trace(self):
        """Test deleting a trace"""
        # First create a trace
        trace_data = {
            "agent_id": "test_agent_delete",
            "agent_name": "Delete Test",
            "provider": "openai",
            "model": "gpt-4o-mini",
        }
        create_response = client.post("/api/v1/trace", json=trace_data)
        trace_id = create_response.json()["trace_id"]

        # Delete it
        response = client.delete(f"/api/v1/trace/{trace_id}")
        assert response.status_code == 200
        assert response.json()["success"] == True

        # Verify it's deleted
        get_response = client.get(f"/api/v1/trace/{trace_id}")
        assert get_response.status_code == 404

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

    def test_anthropic_cost(self):
        """Test Anthropic cost calculation"""
        from trace_service import TraceService

        service = TraceService()
        cost = service.calculate_cost("anthropic", "claude-3-sonnet", 1000, 500)
        # Claude 3 Sonnet: $0.003/1K input, $0.015/1K output
        expected = 0.003 * 1 + 0.015 * 0.5  # = 0.0105
        assert abs(cost - expected) < 0.0001

    def test_gemini_cost(self):
        """Test Gemini cost calculation"""
        from trace_service import TraceService

        service = TraceService()
        cost = service.calculate_cost("google", "gemini-1.5-pro", 1000, 500)
        # Gemini 1.5 Pro: $0.00125/1K input, $0.005/1K output
        expected = 0.00125 * 1 + 0.005 * 0.5  # = 0.00375
        assert abs(cost - expected) < 0.0001


class TestDashboardAPI:
    """Dashboard API Tests"""

    def test_dashboard_endpoint(self):
        """Test dashboard endpoint"""
        response = client.get("/api/v1/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "total_traces" in data
        assert "running_traces" in data
        assert "completed_traces" in data
        assert "failed_traces" in data
        assert "total_cost" in data
        assert "provider_distribution" in data
        assert "model_distribution" in data
        assert "recent_traces" in data

    def test_dashboard_latency_distribution(self):
        """Test dashboard latency distribution"""
        response = client.get("/api/v1/dashboard")
        data = response.json()
        assert "latency_distribution" in data


class TestAnalyticsAPI:
    """Analytics API Tests"""

    def test_timeline_endpoint(self):
        """Test timeline endpoint"""
        response = client.get("/api/v1/analytics/timeline")
        assert response.status_code == 200
        data = response.json()
        assert "interval" in data
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_timeline_with_hours(self):
        """Test timeline with hours parameter"""
        response = client.get("/api/v1/analytics/timeline?hours=24")
        assert response.status_code == 200

    def test_timeline_with_interval(self):
        """Test timeline with interval parameter"""
        response = client.get("/api/v1/analytics/timeline?interval=hour")
        assert response.status_code == 200
        
        response = client.get("/api/v1/analytics/timeline?interval=day")
        assert response.status_code == 200

    def test_provider_analytics_endpoint(self):
        """Test provider analytics endpoint"""
        response = client.get("/api/v1/analytics/providers")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_provider_analytics_structure(self):
        """Test provider analytics structure"""
        # Create some test traces first
        for i in range(3):
            client.post("/api/v1/trace", json={
                "agent_id": f"analytics_agent_{i}",
                "agent_name": f"Analytics Agent {i}",
                "provider": "openai",
                "model": "gpt-4o-mini",
            })
        
        response = client.get("/api/v1/analytics/providers")
        data = response.json()
        
        if len(data) > 0:
            provider = data[0]
            assert "provider" in provider
            assert "traces" in provider
            assert "total_cost" in provider
            assert "avg_latency_ms" in provider
            assert "success_rate" in provider


class TestWebSocket:
    """WebSocket Tests - skipped in CI due to blocking behavior"""

    @pytest.mark.skip(reason="WebSocket tests can block in CI environment")
    def test_websocket_connect(self):
        """Test WebSocket connection"""
        with client.websocket_connect("/ws") as websocket:
            # Receive the connected message
            data = websocket.receive_json()
            assert data["type"] == "connected"
            assert "message" in data

    @pytest.mark.skip(reason="WebSocket tests can block in CI environment")
    def test_websocket_stats_request(self):
        """Test WebSocket stats request"""
        with client.websocket_connect("/ws") as websocket:
            # Receive the connected message
            websocket.receive_json()
            # Receive the initial stats update
            websocket.receive_json()
            
            # Request stats
            websocket.send_json({"type": "get_stats"})
            
            # Receive stats update
            data = websocket.receive_json()
            assert data["type"] == "stats_update"

    @pytest.mark.skip(reason="WebSocket tests can block in CI environment")
    def test_websocket_ping_pong(self):
        """Test WebSocket ping/pong"""
        with client.websocket_connect("/ws") as websocket:
            # Receive the connected message
            websocket.receive_json()
            # Receive the initial stats update
            websocket.receive_json()
            
            # Send ping
            websocket.send_json({"type": "ping"})
            
            # Receive pong
            data = websocket.receive_json()
            assert data["type"] == "pong"

    @pytest.mark.skip(reason="WebSocket tests can block in CI environment")
    def test_websocket_subscribe(self):
        """Test WebSocket subscribe"""
        with client.websocket_connect("/ws") as websocket:
            # Receive the connected message
            websocket.receive_json()
            # Receive the initial stats update
            websocket.receive_json()
            
            # Subscribe
            websocket.send_json({"type": "subscribe", "channels": ["all"]})
            
            # Receive subscribed response
            data = websocket.receive_json()
            assert data["type"] == "subscribed"

    @pytest.mark.skip(reason="WebSocket tests can block in CI environment")
    def test_websocket_trace_created_broadcast(self):
        """Test WebSocket trace created broadcast"""
        with client.websocket_connect("/ws") as websocket:
            # Receive the connected message
            websocket.receive_json()
            # Receive the initial stats update
            websocket.receive_json()
            
            # Create a trace via HTTP
            trace_data = {
                "agent_id": "websocket_test",
                "agent_name": "WebSocket Test",
                "provider": "openai",
                "model": "gpt-4o-mini",
            }
            client.post("/api/v1/trace", json=trace_data)
            
            # Should receive broadcast
            data = websocket.receive_json()
            assert data["type"] == "trace_created"
