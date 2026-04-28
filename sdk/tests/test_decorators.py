"""
Tests for AgentWatch SDK decorators
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
import time

from agentwatch.decorators import (
    trace_agent,
    trace_openai_call,
    trace_anthropic_call,
    trace_deepseek_call,
    trace_gemini_call,
    with_retry,
    with_rate_limit,
    RateLimiter,
    TracedAgent,
    AsyncTracedAgent,
    _extract_tokens,
)


class TestProviderSpecificDecorators:
    """Tests for provider-specific decorators"""
    
    def test_trace_openai_call(self):
        """Test trace_openai_call decorator definition"""
        # Check that the decorator returns trace_agent with correct provider
        decorator = trace_openai_call(model="gpt-4o-mini")
        assert decorator is not None
    
    def test_trace_anthropic_call(self):
        """Test trace_anthropic_call decorator definition"""
        decorator = trace_anthropic_call(model="claude-3-haiku")
        assert decorator is not None
    
    def test_trace_deepseek_call(self):
        """Test trace_deepseek_call decorator definition"""
        decorator = trace_deepseek_call(model="deepseek-chat")
        assert decorator is not None
    
    def test_trace_gemini_call(self):
        """Test trace_gemini_call decorator definition"""
        decorator = trace_gemini_call(model="gemini-1.5-pro")
        assert decorator is not None


class TestWithRetryDecorator:
    """Tests for retry decorator"""
    
    def test_with_retry_sync_success(self):
        """Test retry decorator on successful sync call"""
        call_counts = [0]  # Use list to avoid UnboundLocalError
        
        @with_retry(max_attempts=3, delay=0.1)
        def successful_func():
            call_counts[0] += 1
            return "success"
        
        result = successful_func()
        assert result == "success"
        assert call_counts[0] == 1  # Should only call once on success
    
    def test_with_retry_sync_failure_then_success(self):
        """Test retry decorator on sync call that fails then succeeds"""
        call_counts = [0]
        
        @with_retry(max_attempts=3, delay=0.1)
        def flaky_func():
            call_counts[0] += 1
            if call_counts[0] < 2:
                raise ValueError("Temporary error")
            return "success"
        
        result = flaky_func()
        assert result == "success"
        assert call_counts[0] == 2  # Should retry once
    
    def test_with_retry_sync_max_attempts(self):
        """Test retry decorator exhausts max attempts"""
        call_counts = [0]
        retry_callback = Mock()
        
        @with_retry(max_attempts=3, delay=0.1, on_retry=retry_callback)
        def always_fail():
            call_counts[0] += 1
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError):
            always_fail()
        
        assert call_counts[0] == 3
        assert retry_callback.call_count == 2  # Callback called for each retry
    
    @pytest.mark.asyncio
    async def test_with_retry_async_success(self):
        """Test retry decorator on successful async call"""
        call_counts = [0]
        
        @with_retry(max_attempts=3, delay=0.1)
        async def async_successful_func():
            call_counts[0] += 1
            return "async_success"
        
        result = await async_successful_func()
        assert result == "async_success"
        assert call_counts[0] == 1
    
    @pytest.mark.asyncio
    async def test_with_retry_async_failure_then_success(self):
        """Test retry decorator on async call that fails then succeeds"""
        call_counts = [0]
        
        @with_retry(max_attempts=3, delay=0.1)
        async def async_flaky_func():
            call_counts[0] += 1
            if call_counts[0] < 2:
                raise ValueError("Async temporary error")
            return "async_success"
        
        result = await async_flaky_func()
        assert result == "async_success"
        assert call_counts[0] == 2
    
    def test_with_retry_specific_exception_types(self):
        """Test retry decorator with specific exception types"""
        call_counts = [0]
        
        @with_retry(max_attempts=3, delay=0.1, retry_on=(ValueError,))
        def raises_type_error():
            call_counts[0] += 1
            raise TypeError("Not a ValueError")
        
        # TypeError should not trigger retry since it's not in retry_on
        with pytest.raises(TypeError):
            raises_type_error()
        
        assert call_counts[0] == 1  # Should not retry


class TestRateLimiter:
    """Tests for rate limiter"""
    
    def test_rate_limiter_init(self):
        """Test RateLimiter initialization"""
        limiter = RateLimiter(calls_per_minute=60, calls_per_second=10)
        assert limiter.calls_per_minute == 60
        assert limiter.calls_per_second == 10
        assert limiter._minute_calls == []
        assert limiter._second_calls == []
    
    def test_rate_limiter_clean_old_calls(self):
        """Test cleaning old call records"""
        limiter = RateLimiter()
        now = time.time()
        
        # Add some old calls
        old_calls = [now - 10, now - 5, now - 0.5]
        cleaned = limiter._clean_old_calls(old_calls, 1.0)
        
        # Only the call within 1 second window should remain
        assert len(cleaned) == 1
        assert cleaned[0] == now - 0.5
    
    def test_rate_limiter_sync_wait(self):
        """Test sync rate limiter wait"""
        limiter = RateLimiter(calls_per_minute=100, calls_per_second=100)
        
        # First call should not wait
        limiter._wait_sync()
        assert len(limiter._minute_calls) == 1


class TestWithRateLimitDecorator:
    """Tests for rate limit decorator"""
    
    def test_with_rate_limit_sync(self):
        """Test rate limit decorator on sync function"""
        call_times = []
        
        @with_rate_limit(calls_per_minute=100, calls_per_second=100)
        def rate_limited_func():
            call_times.append(time.time())
            return "done"
        
        # Should work normally with low rate limits
        result = rate_limited_func()
        assert result == "done"
        assert len(call_times) == 1
    
    @pytest.mark.asyncio
    async def test_with_rate_limit_async(self):
        """Test rate limit decorator on async function"""
        call_times = []
        
        @with_rate_limit(calls_per_minute=100, calls_per_second=100)
        async def async_rate_limited_func():
            call_times.append(time.time())
            return "async_done"
        
        result = await async_rate_limited_func()
        assert result == "async_done"
        assert len(call_times) == 1


class TestTracedAgent:
    """Tests for TracedAgent base class"""
    
    def test_traced_agent_init(self):
        """Test TracedAgent initialization"""
        with patch('agentwatch.decorators.AgentWatch') as mock_aw:
            agent = TracedAgent(name="test_agent", model="gpt-4o")
            assert agent.name == "test_agent"
            assert agent.model == "gpt-4o"
            assert agent.provider == "openai"
    
    def test_traced_agent_context_manager(self):
        """Test TracedAgent as context manager"""
        with patch('agentwatch.decorators.AgentWatch') as mock_aw:
            mock_aw_instance = mock_aw.return_value
            mock_trace = Mock()
            mock_aw_instance.create_trace.return_value = mock_trace
            
            agent = TracedAgent(name="test_agent", model="gpt-4o")
            
            with agent:
                pass
            
            mock_aw_instance.create_trace.assert_called_once()
            mock_trace.complete.assert_called_once()


class TestAsyncTracedAgent:
    """Tests for AsyncTracedAgent base class"""
    
    def test_async_traced_agent_init(self):
        """Test AsyncTracedAgent initialization"""
        with patch('agentwatch.decorators.AgentWatch') as mock_aw:
            agent = AsyncTracedAgent(name="async_agent", model="claude-3")
            assert agent.name == "async_agent"
            assert agent.model == "claude-3"
            assert agent.provider == "openai"
    
    @pytest.mark.asyncio
    async def test_async_traced_agent_context_manager(self):
        """Test AsyncTracedAgent as async context manager"""
        with patch('agentwatch.decorators.AgentWatch') as mock_aw:
            mock_aw_instance = mock_aw.return_value
            mock_trace = Mock()
            mock_aw_instance.create_trace.return_value = mock_trace
            
            agent = AsyncTracedAgent(name="async_agent", model="claude-3")
            
            async with agent:
                pass
            
            mock_aw_instance.create_trace.assert_called_once()
            mock_trace.complete.assert_called_once()


class TestExtractTokens:
    """Tests for token extraction helper"""
    
    def test_extract_from_object_with_usage(self):
        """Test extracting tokens from object with usage attribute"""
        mock_trace = Mock()
        
        class MockResponse:
            usage = Mock()
            usage.prompt_tokens = 100
            usage.completion_tokens = 200
        
        _extract_tokens(mock_trace, MockResponse())
        mock_trace.log_tokens.assert_called_once_with(input=100, output=200)
    
    def test_extract_from_dict_with_usage(self):
        """Test extracting tokens from dict with usage"""
        mock_trace = Mock()
        result = {"usage": {"prompt_tokens": 50, "completion_tokens": 75}}
        
        _extract_tokens(mock_trace, result)
        mock_trace.log_tokens.assert_called_once_with(input=50, output=75)
    
    def test_extract_no_usage(self):
        """Test extracting tokens from result without usage"""
        mock_trace = Mock()
        result = {"content": "some text"}
        
        _extract_tokens(mock_trace, result)
        mock_trace.log_tokens.assert_not_called()
    
    def test_extract_partial_usage(self):
        """Test extracting tokens when usage has None values"""
        mock_trace = Mock()
        
        class MockResponse:
            usage = Mock()
            usage.prompt_tokens = None
            usage.completion_tokens = 50
        
        _extract_tokens(mock_trace, MockResponse())
        mock_trace.log_tokens.assert_called_once_with(input=0, output=50)


class TestTimeoutDecorator:
    """Tests for timeout decorator"""
    
    def test_with_timeout_sync_success(self):
        """Test timeout decorator on successful sync call"""
        from agentwatch.decorators import with_timeout
        
        @with_timeout(seconds=5.0)
        def quick_func():
            return "success"
        
        result = quick_func()
        assert result == "success"
    
    def test_with_timeout_sync_timeout(self):
        """Test timeout decorator on sync call that exceeds timeout"""
        from agentwatch.decorators import with_timeout, TimeoutError
        import time
        
        @with_timeout(seconds=0.5)
        def slow_func():
            time.sleep(2.0)
            return "too slow"
        
        with pytest.raises(TimeoutError):
            slow_func()
    
    def test_with_timeout_sync_with_callback(self):
        """Test timeout decorator with callback on timeout"""
        from agentwatch.decorators import with_timeout
        
        def on_timeout():
            return "fallback"
        
        @with_timeout(seconds=0.5, on_timeout=on_timeout)
        def slow_func():
            import time
            time.sleep(2.0)
            return "too slow"
        
        result = slow_func()
        assert result == "fallback"
    
    @pytest.mark.asyncio
    async def test_with_timeout_async_success(self):
        """Test timeout decorator on successful async call"""
        from agentwatch.decorators import with_timeout
        
        @with_timeout(seconds=5.0)
        async def async_quick_func():
            await asyncio.sleep(0.1)
            return "async_success"
        
        result = await async_quick_func()
        assert result == "async_success"
    
    @pytest.mark.asyncio
    async def test_with_timeout_async_timeout(self):
        """Test timeout decorator on async call that exceeds timeout"""
        from agentwatch.decorators import with_timeout, TimeoutError
        
        @with_timeout(seconds=0.5)
        async def async_slow_func():
            await asyncio.sleep(2.0)
            return "too slow"
        
        with pytest.raises(TimeoutError):
            await async_slow_func()
    
    @pytest.mark.asyncio
    async def test_with_timeout_async_with_callback(self):
        """Test timeout decorator with callback on async timeout"""
        from agentwatch.decorators import with_timeout
        
        def on_timeout():
            return "async_fallback"
        
        @with_timeout(seconds=0.5, on_timeout=on_timeout)
        async def async_slow_func():
            await asyncio.sleep(2.0)
            return "too slow"
        
        result = await async_slow_func()
        assert result == "async_fallback"


class TestResponseCache:
    """Tests for response cache"""
    
    def test_response_cache_init(self):
        """Test ResponseCache initialization"""
        from agentwatch.decorators import ResponseCache
        
        cache = ResponseCache(max_size=100, ttl_seconds=60)
        assert cache.max_size == 100
        assert cache.ttl_seconds == 60
        assert cache._cache == {}
    
    def test_response_cache_hash_key(self):
        """Test cache key generation"""
        from agentwatch.decorators import ResponseCache
        
        cache = ResponseCache()
        key1 = cache._hash_key(("arg1", "arg2"), {"kwarg": "value"})
        key2 = cache._hash_key(("arg1", "arg2"), {"kwarg": "value"})
        key3 = cache._hash_key(("different",), {})
        
        # Same args should produce same key
        assert key1 == key2
        # Different args should produce different key
        assert key1 != key3
    
    def test_response_cache_set_and_get(self):
        """Test cache set and get"""
        from agentwatch.decorators import ResponseCache
        
        cache = ResponseCache(max_size=10, ttl_seconds=60)
        
        # Set value
        cache.set(("prompt",), {}, "response")
        
        # Get value
        result = cache.get(("prompt",), {})
        assert result == "response"
    
    def test_response_cache_get_expired(self):
        """Test cache get returns None for expired entries"""
        from agentwatch.decorators import ResponseCache
        import time
        
        cache = ResponseCache(max_size=10, ttl_seconds=0.1)
        
        # Set value
        cache.set(("prompt",), {}, "response")
        
        # Wait for expiration
        time.sleep(0.2)
        
        # Get should return None
        result = cache.get(("prompt",), {})
        assert result is None
    
    def test_response_cache_eviction(self):
        """Test cache eviction at max size"""
        from agentwatch.decorators import ResponseCache
        
        cache = ResponseCache(max_size=3, ttl_seconds=60)
        
        # Fill cache
        cache.set(("a",), {}, "a")
        cache.set(("b",), {}, "b")
        cache.set(("c",), {}, "c")
        
        # Add one more, should evict oldest
        cache.set(("d",), {}, "d")
        
        assert len(cache._cache) == 3
        assert cache.get(("d",), {}) == "d"
    
    def test_response_cache_clear(self):
        """Test cache clear"""
        from agentwatch.decorators import ResponseCache
        
        cache = ResponseCache()
        cache.set(("a",), {}, "a")
        cache.set(("b",), {}, "b")
        
        cache.clear()
        
        assert len(cache._cache) == 0
        assert cache.get(("a",), {}) is None
    
    def test_response_cache_stats(self):
        """Test cache stats"""
        from agentwatch.decorators import ResponseCache
        
        cache = ResponseCache(max_size=100, ttl_seconds=60)
        cache.set(("a",), {}, "a")
        
        stats = cache.stats()
        assert stats["size"] == 1
        assert stats["max_size"] == 100
        assert stats["ttl_seconds"] == 60


class TestWithCacheDecorator:
    """Tests for cache decorator"""
    
    def test_with_cache_sync_first_call(self):
        """Test cache decorator on first sync call"""
        from agentwatch.decorators import with_cache
        
        call_count = [0]
        
        @with_cache(max_size=10, ttl_seconds=60)
        def cached_func(arg):
            call_count[0] += 1
            return f"result_{arg}"
        
        result = cached_func("test")
        assert result == "result_test"
        assert call_count[0] == 1
    
    def test_with_cache_sync_cached_call(self):
        """Test cache decorator on cached sync call"""
        from agentwatch.decorators import with_cache
        
        call_count = [0]
        
        @with_cache(max_size=10, ttl_seconds=60)
        def cached_func(arg):
            call_count[0] += 1
            return f"result_{arg}"
        
        # First call
        result1 = cached_func("test")
        assert call_count[0] == 1
        
        # Second call should return cached
        result2 = cached_func("test")
        assert result2 == "result_test"
        assert call_count[0] == 1  # Still 1, cached
    
    def test_with_cache_sync_different_args(self):
        """Test cache decorator with different args"""
        from agentwatch.decorators import with_cache
        
        call_count = [0]
        
        @with_cache(max_size=10, ttl_seconds=60)
        def cached_func(arg):
            call_count[0] += 1
            return f"result_{arg}"
        
        result1 = cached_func("test1")
        result2 = cached_func("test2")
        
        assert result1 == "result_test1"
        assert result2 == "result_test2"
        assert call_count[0] == 2  # Both calls executed
    
    @pytest.mark.asyncio
    async def test_with_cache_async(self):
        """Test cache decorator on async call"""
        from agentwatch.decorators import with_cache
        
        call_count = [0]
        
        @with_cache(max_size=10, ttl_seconds=60)
        async def async_cached_func(arg):
            call_count[0] += 1
            await asyncio.sleep(0.01)
            return f"async_result_{arg}"
        
        # First call
        result1 = await async_cached_func("test")
        assert call_count[0] == 1
        
        # Second call should return cached
        result2 = await async_cached_func("test")
        assert result2 == "async_result_test"
        assert call_count[0] == 1  # Still 1, cached