"""
Storage Tests
Tests for Memory and SQLite storage implementations
"""

import sys
import os
import tempfile
import uuid
import pytest
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.memory import MemoryStorage
from storage.sqlite import SQLiteStorage
from models import (
    TraceCreate,
    TraceUpdate,
    TraceEvent,
    TraceStatus,
    AgentProvider,
)


def make_trace_create(**kwargs):
    """Helper to create TraceCreate with defaults"""
    defaults = {
        "agent_id": f"agent_{uuid.uuid4().hex[:8]}",
        "agent_name": "TestAgent",
        "provider": AgentProvider.OPENAI,
        "model": "gpt-4o",
    }
    defaults.update(kwargs)
    return TraceCreate(**defaults)


def make_trace_event(**kwargs):
    """Helper to create TraceEvent with defaults"""
    defaults = {
        "event_id": f"evt_{uuid.uuid4().hex[:8]}",
        "event_type": "call",
        "content": "test event",
        "input_tokens": 100,
        "output_tokens": 50,
        "latency_ms": 200,
    }
    defaults.update(kwargs)
    return TraceEvent(**defaults)


class TestMemoryStorage:
    """Memory Storage Tests"""

    def test_init_default(self):
        """Test default initialization"""
        storage = MemoryStorage()
        assert storage._traces == {}
        assert storage._max_size is None

    def test_init_with_max_size(self):
        """Test initialization with max_size"""
        storage = MemoryStorage(max_size=100)
        assert storage._max_size == 100

    def test_create_trace(self):
        """Test creating a trace"""
        storage = MemoryStorage()
        trace_data = make_trace_create()
        trace = storage.create_trace(trace_data)
        assert trace.trace_id is not None
        assert trace.agent_name == "TestAgent"
        assert trace.status == TraceStatus.RUNNING

    def test_create_trace_with_custom_id(self):
        """Test creating trace with custom ID"""
        storage = MemoryStorage()
        trace_data = make_trace_create(trace_id="custom_123")
        trace = storage.create_trace(trace_data)
        assert trace.trace_id == "custom_123"

    def test_get_trace(self):
        """Test getting a trace"""
        storage = MemoryStorage()
        trace_data = make_trace_create()
        created = storage.create_trace(trace_data)
        fetched = storage.get_trace(created.trace_id)
        assert fetched is not None
        assert fetched.trace_id == created.trace_id

    def test_get_trace_not_found(self):
        """Test getting non-existent trace"""
        storage = MemoryStorage()
        fetched = storage.get_trace("nonexistent")
        assert fetched is None

    def test_update_trace_status(self):
        """Test updating trace status"""
        storage = MemoryStorage()
        trace_data = make_trace_create()
        created = storage.create_trace(trace_data)
        update = TraceUpdate(status=TraceStatus.COMPLETED)
        updated = storage.update_trace(created.trace_id, update)
        assert updated.status == TraceStatus.COMPLETED
        assert updated.completed_at is not None

    def test_update_trace_with_events(self):
        """Test updating trace with events"""
        storage = MemoryStorage()
        trace_data = make_trace_create()
        created = storage.create_trace(trace_data)
        event = make_trace_event()
        update = TraceUpdate(events=[event])
        updated = storage.update_trace(created.trace_id, update)
        assert len(updated.events) == 1
        assert updated.total_input_tokens == 100
        assert updated.total_output_tokens == 50
        assert updated.total_tokens == 150

    def test_delete_trace(self):
        """Test deleting a trace"""
        storage = MemoryStorage()
        trace_data = make_trace_create()
        created = storage.create_trace(trace_data)
        result = storage.delete_trace(created.trace_id)
        assert result is True
        assert storage.get_trace(created.trace_id) is None

    def test_delete_trace_not_found(self):
        """Test deleting non-existent trace"""
        storage = MemoryStorage()
        result = storage.delete_trace("nonexistent")
        assert result is False

    def test_list_traces_pagination(self):
        """Test listing traces with pagination"""
        storage = MemoryStorage()
        # Create 5 traces
        for i in range(5):
            storage.create_trace(make_trace_create(agent_name=f"Agent{i}"))
        # Get page 1 with size 2
        result = storage.list_traces(page=1, page_size=2)
        assert len(result.traces) == 2
        assert result.total == 5
        assert result.has_more is True

    def test_list_traces_filter_provider(self):
        """Test filtering traces by provider"""
        storage = MemoryStorage()
        storage.create_trace(make_trace_create(provider=AgentProvider.OPENAI))
        storage.create_trace(make_trace_create(provider=AgentProvider.DEEPSEEK))
        result = storage.list_traces(provider="openai")
        assert len(result.traces) == 1
        assert result.traces[0].provider == AgentProvider.OPENAI

    def test_get_stats_empty(self):
        """Test getting stats when empty"""
        storage = MemoryStorage()
        stats = storage.get_stats()
        assert stats["total_traces"] == 0
        assert stats["total_cost"] == 0.0

    def test_get_stats_with_traces(self):
        """Test getting stats with traces"""
        storage = MemoryStorage()
        trace = storage.create_trace(make_trace_create())
        storage.update_trace(
            trace.trace_id,
            TraceUpdate(
                status=TraceStatus.COMPLETED,
                total_cost=0.05,
            )
        )
        stats = storage.get_stats()
        assert stats["total_traces"] == 1
        assert stats["total_cost"] == 0.05

    def test_get_cost_summary(self):
        """Test getting cost summary"""
        storage = MemoryStorage()
        trace = storage.create_trace(make_trace_create())
        storage.update_trace(
            trace.trace_id,
            TraceUpdate(
                status=TraceStatus.COMPLETED,
                total_tokens=1000,
                total_cost=0.05,
            )
        )
        summary = storage.get_cost_summary()
        assert len(summary) >= 1
        assert summary[0].provider == AgentProvider.OPENAI

    def test_eviction_with_max_size(self):
        """Test eviction when max_size is reached"""
        storage = MemoryStorage(max_size=3)
        # Create 5 traces
        ids = []
        for i in range(5):
            trace = storage.create_trace(make_trace_create(agent_name=f"Agent{i}"))
            ids.append(trace.trace_id)
        # Should have only 3 traces (oldest evicted)
        assert len(storage._traces) == 3
        # First 2 should be evicted
        assert storage.get_trace(ids[0]) is None
        assert storage.get_trace(ids[1]) is None


class TestSQLiteStorage:
    """SQLite Storage Tests"""

    def test_init_creates_db(self):
        """Test that initialization creates database"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = SQLiteStorage(path=db_path)
            assert os.path.exists(db_path)

    def test_init_no_auto_create(self):
        """Test initialization without auto_create"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = SQLiteStorage(path=db_path, auto_create=False)
            assert not os.path.exists(db_path)

    def test_create_trace(self):
        """Test creating a trace"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = SQLiteStorage(path=db_path)
            trace_data = make_trace_create()
            trace = storage.create_trace(trace_data)
            assert trace.trace_id is not None
            assert trace.agent_name == "TestAgent"
            assert trace.status == TraceStatus.RUNNING

    def test_get_trace(self):
        """Test getting a trace"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = SQLiteStorage(path=db_path)
            trace_data = make_trace_create(provider=AgentProvider.DEEPSEEK, model="deepseek-chat")
            created = storage.create_trace(trace_data)
            fetched = storage.get_trace(created.trace_id)
            assert fetched is not None
            assert fetched.trace_id == created.trace_id
            assert fetched.provider == AgentProvider.DEEPSEEK

    def test_update_trace(self):
        """Test updating a trace"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = SQLiteStorage(path=db_path)
            trace_data = make_trace_create()
            created = storage.create_trace(trace_data)
            event = make_trace_event(input_tokens=500, output_tokens=200, latency_ms=300)
            update = TraceUpdate(
                status=TraceStatus.COMPLETED,
                events=[event],
            )
            updated = storage.update_trace(created.trace_id, update)
            assert updated.status == TraceStatus.COMPLETED
            assert updated.total_tokens == 700
            assert updated.completed_at is not None

    def test_delete_trace(self):
        """Test deleting a trace"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = SQLiteStorage(path=db_path)
            trace_data = make_trace_create()
            created = storage.create_trace(trace_data)
            result = storage.delete_trace(created.trace_id)
            assert result is True
            assert storage.get_trace(created.trace_id) is None

    def test_list_traces(self):
        """Test listing traces"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = SQLiteStorage(path=db_path)
            # Create multiple traces
            for i in range(5):
                storage.create_trace(
                    make_trace_create(
                        agent_name=f"Agent{i}",
                        provider=AgentProvider.OPENAI if i % 2 == 0 else AgentProvider.DEEPSEEK,
                        model="gpt-4o" if i % 2 == 0 else "deepseek-chat",
                    )
                )
            result = storage.list_traces(page=1, page_size=3)
            assert len(result.traces) == 3
            assert result.total == 5
            assert result.has_more is True

    def test_list_traces_filter(self):
        """Test filtering traces"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = SQLiteStorage(path=db_path)
            storage.create_trace(make_trace_create(provider=AgentProvider.OPENAI))
            storage.create_trace(make_trace_create(provider=AgentProvider.DEEPSEEK))
            result = storage.list_traces(provider="deepseek")
            assert len(result.traces) == 1
            assert result.traces[0].provider == AgentProvider.DEEPSEEK

    def test_get_stats(self):
        """Test getting stats"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = SQLiteStorage(path=db_path)
            # Create and complete a trace
            trace = storage.create_trace(make_trace_create())
            storage.update_trace(
                trace.trace_id,
                TraceUpdate(
                    status=TraceStatus.COMPLETED,
                    total_cost=0.10,
                )
            )
            stats = storage.get_stats()
            assert stats["total_traces"] == 1
            assert stats["total_cost"] == 0.10

    def test_get_cost_summary(self):
        """Test getting cost summary"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = SQLiteStorage(path=db_path)
            trace = storage.create_trace(make_trace_create())
            storage.update_trace(
                trace.trace_id,
                TraceUpdate(
                    status=TraceStatus.COMPLETED,
                    total_tokens=2000,
                    total_cost=0.15,
                    duration_ms=500,
                )
            )
            summary = storage.get_cost_summary()
            assert len(summary) >= 1
            # Check the OpenAI summary
            openai_summary = next((s for s in summary if s.provider == AgentProvider.OPENAI), None)
            assert openai_summary is not None
            assert openai_summary.total_traces == 1
            assert openai_summary.total_tokens == 2000

    def test_persistence(self):
        """Test data persistence across connections"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            # Create storage and add trace
            storage1 = SQLiteStorage(path=db_path)
            trace_data = make_trace_create()
            created = storage1.create_trace(trace_data)
            trace_id = created.trace_id
            
            # Create new storage instance (simulates restart)
            storage2 = SQLiteStorage(path=db_path)
            fetched = storage2.get_trace(trace_id)
            assert fetched is not None
            assert fetched.agent_name == "TestAgent"

    def test_multiple_providers(self):
        """Test handling multiple providers"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = SQLiteStorage(path=db_path)
            
            # Create traces for different providers
            providers = [
                (AgentProvider.OPENAI, "gpt-4o"),
                (AgentProvider.ANTHROPIC, "claude-3-5-sonnet-20241022"),
                (AgentProvider.DEEPSEEK, "deepseek-chat"),
                (AgentProvider.GOOGLE, "gemini-1.5-pro"),
            ]
            
            for provider, model in providers:
                storage.create_trace(
                    make_trace_create(
                        agent_name=f"Agent_{provider.value}",
                        provider=provider,
                        model=model,
                    )
                )
            
            # Check stats
            stats = storage.get_stats()
            assert stats["total_traces"] == 4
            assert stats["providers"]["provider_openai"] == 1
            assert stats["providers"]["provider_deepseek"] == 1