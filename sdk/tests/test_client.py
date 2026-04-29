"""
Tests for AgentWatch SDK client
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import httpx

from agentwatch.client import AgentWatch, AgentWatchConfig, TraceContext


class TestAgentWatchConfig:
    """Tests for AgentWatchConfig"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = AgentWatchConfig()
        assert config.api_url == "http://localhost:8000"
        assert config.api_key is None
        assert config.timeout == 30.0
        assert config.auto_start == True
    
    def test_custom_config(self):
        """Test custom configuration values"""
        config = AgentWatchConfig(
            api_url="https://api.example.com",
            api_key="test_key",
            timeout=60.0,
            auto_start=False
        )
        assert config.api_url == "https://api.example.com"
        assert config.api_key == "test_key"
        assert config.timeout == 60.0
        assert config.auto_start == False


class TestAgentWatch:
    """Tests for AgentWatch client"""
    
    @patch('httpx.Client')
    def test_init_default(self, mock_client):
        """Test default initialization"""
        aw = AgentWatch()
        assert aw.config.api_url == "http://localhost:8000"
        assert aw.config.api_key is None
        mock_client.assert_called_once_with(timeout=30.0)
    
    @patch('httpx.Client')
    def test_init_custom_url(self, mock_client):
        """Test initialization with custom URL"""
        aw = AgentWatch(api_url="https://custom.api.com")
        assert aw.config.api_url == "https://custom.api.com"
    
    @patch('httpx.Client')
    def test_init_with_api_key(self, mock_client):
        """Test initialization with API key"""
        aw = AgentWatch(api_key="test_key")
        assert aw.config.api_key == "test_key"
    
    @patch('httpx.Client')
    def test_init_with_config(self, mock_client):
        """Test initialization with config object"""
        config = AgentWatchConfig(api_url="https://config.api.com", timeout=45.0)
        aw = AgentWatch(config=config)
        assert aw.config.api_url == "https://config.api.com"
        assert aw.config.timeout == 45.0
    
    @patch('httpx.Client')
    def test_get_headers_no_key(self, mock_client):
        """Test headers without API key"""
        aw = AgentWatch()
        headers = aw._get_headers()
        assert headers == {"Content-Type": "application/json"}
        assert "Authorization" not in headers
    
    @patch('httpx.Client')
    def test_get_headers_with_key(self, mock_client):
        """Test headers with API key"""
        aw = AgentWatch(api_key="test_key")
        headers = aw._get_headers()
        assert headers["Authorization"] == "Bearer test_key"
    
    @patch('httpx.Client')
    def test_close(self, mock_client):
        """Test close method"""
        aw = AgentWatch()
        aw.close()
        aw._client.close.assert_called_once()
    
    @patch('httpx.Client')
    def test_context_manager(self, mock_client):
        """Test context manager"""
        with AgentWatch() as aw:
            assert aw is not None
        aw._client.close.assert_called_once()


class TestAgentWatchRequest:
    """Tests for HTTP request methods"""
    
    @patch('httpx.Client')
    def test_health_check_success(self, mock_client):
        """Test health check success"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy"}
        mock_response.raise_for_status = Mock()
        mock_client.return_value.get.return_value = mock_response
        
        aw = AgentWatch()
        result = aw.health_check()
        assert result == {"status": "healthy"}
    
    @patch('httpx.Client')
    def test_get_stats_success(self, mock_client):
        """Test get stats success"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"total_traces": 10}
        mock_response.raise_for_status = Mock()
        mock_client.return_value.get.return_value = mock_response
        
        aw = AgentWatch()
        result = aw.get_stats()
        assert result == {"total_traces": 10}
    
    @patch('httpx.Client')
    def test_list_traces_success(self, mock_client):
        """Test list traces success"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"traces": [], "total": 0}
        mock_response.raise_for_status = Mock()
        mock_client.return_value.get.return_value = mock_response
        
        aw = AgentWatch()
        result = aw.list_traces(page=1, page_size=10)
        assert result == {"traces": [], "total": 0}


class TestTraceContext:
    """Tests for TraceContext"""
    
    def test_init(self):
        """Test TraceContext initialization"""
        mock_client = Mock()
        trace = TraceContext(
            trace_id="test_trace_123",
            agent_id="agent_001",
            agent_name="TestAgent",
            provider="openai",
            model="gpt-4o",
            client=mock_client
        )
        assert trace.trace_id == "test_trace_123"
        assert trace.agent_id == "agent_001"
        assert trace.agent_name == "TestAgent"
        assert trace.provider == "openai"
        assert trace.model == "gpt-4o"
        assert trace._status == "running"
        assert trace._total_input_tokens == 0
        assert trace._total_output_tokens == 0
    
    def test_context_manager_enter_exit(self):
        """Test TraceContext as context manager"""
        mock_client = Mock()
        mock_client._request.return_value = {}
        
        trace = TraceContext(
            trace_id="test_trace",
            agent_id="agent",
            agent_name="Test",
            provider="openai",
            model="gpt-4o",
            client=mock_client
        )
        
        with trace as t:
            assert t == trace
        
        # Should call PUT to complete
        mock_client._request.assert_called()


class TestAgentWatchDecorators:
    """Tests for decorators"""
    
    def test_extract_tokens_with_usage_attr(self):
        """Test token extraction from object with usage attribute"""
        from agentwatch.decorators import _extract_tokens
        
        mock_trace = Mock()
        mock_result = Mock()
        mock_result.usage = Mock()
        mock_result.usage.prompt_tokens = 100
        mock_result.usage.completion_tokens = 200
        
        _extract_tokens(mock_trace, mock_result)
        mock_trace.log_tokens.assert_called_once_with(input=100, output=200)
    
    def test_extract_tokens_with_dict_usage(self):
        """Test token extraction from dict with usage key"""
        from agentwatch.decorators import _extract_tokens
        
        mock_trace = Mock()
        mock_result = {"usage": {"prompt_tokens": 50, "completion_tokens": 75}}
        
        _extract_tokens(mock_trace, mock_result)
        mock_trace.log_tokens.assert_called_once_with(input=50, output=75)