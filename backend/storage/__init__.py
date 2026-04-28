"""
AgentWatch Storage 模块
支持多种数据库实现的存储层

Available Storage Types:
- memory: 内存存储（默认，适合开发）
- sqlite: SQLite 存储（轻量级，适合单机）
- clickhouse: ClickHouse 存储（生产推荐）

Usage:
    from storage import StorageFactory
    
    # 创建内存存储
    storage = StorageFactory.create("memory")
    
    # 创建 SQLite 存储
    storage = StorageFactory.create("sqlite", path="agentwatch.db")
    
    # 创建 ClickHouse 存储
    storage = StorageFactory.create(
        "clickhouse",
        host="localhost",
        port=9000,
        database="agentwatch"
    )
"""

from storage.base import TraceStorage, StorageFactory, StorageConfig
from storage.memory import MemoryStorage
from storage.sqlite import SQLiteStorage
from storage.clickhouse import ClickHouseStorage

# 导出所有
__all__ = [
    "TraceStorage",
    "StorageFactory",
    "StorageConfig",
    "MemoryStorage",
    "SQLiteStorage",
    "ClickHouseStorage",
]

# 默认存储
DefaultStorage = MemoryStorage