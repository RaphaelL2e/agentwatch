-- AgentWatch ClickHouse 数据库初始化
-- 运行方式: docker exec -i agentwatch-clickhouse-1 clickhouse-client < init.sql

-- 创建数据库
CREATE DATABASE IF NOT EXISTS agentwatch;

-- Traces 表
CREATE TABLE IF NOT EXISTS agentwatch.traces (
    trace_id String,
    agent_id String,
    agent_name String,
    provider String,
    model String,
    status String,
    session_id String,
    user_id String,
    prompt String,
    total_input_tokens UInt64 DEFAULT 0,
    total_output_tokens UInt64 DEFAULT 0,
    total_tokens UInt64 DEFAULT 0,
    total_cost Float64 DEFAULT 0.0,
    duration_ms UInt64 DEFAULT 0,
    error_message String,
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now(),
    completed_at Nullable(DateTime),
    metadata String,  -- JSON 格式存储
    -- 索引字段
    INDEX idx_agent_id agent_id TYPE bloom_filter GRANULARITY 1,
    INDEX idx_provider provider TYPE bloom_filter GRANULARITY 1,
    INDEX idx_status status TYPE bloom_filter GRANULARITY 1,
    INDEX idx_created_at created_at TYPE minmax GRANULARITY 1
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(created_at)
ORDER BY (created_at, trace_id)
TTL created_at + INTERVAL 90 DAY  -- 90天后自动删除
SETTINGS index_granularity = 8192;

-- Trace Events 表
CREATE TABLE IF NOT EXISTS agentwatch.trace_events (
    trace_id String,
    event_id String,
    timestamp DateTime DEFAULT now(),
    event_type String,
    agent_name String,
    model String,
    input_tokens UInt64 DEFAULT 0,
    output_tokens UInt64 DEFAULT 0,
    latency_ms UInt64 DEFAULT 0,
    content String,
    metadata String,  -- JSON 格式存储
    -- 索引
    INDEX idx_event_type event_type TYPE bloom_filter GRANULARITY 1
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (trace_id, timestamp, event_id)
TTL timestamp + INTERVAL 90 DAY
SETTINGS index_granularity = 8192;

-- 成本汇总表 (物化视图)
CREATE TABLE IF NOT EXISTS agentwatch.cost_summary (
    day Date,
    provider String,
    model String,
    total_traces UInt64,
    total_tokens UInt64,
    total_cost Float64,
    avg_latency_ms Float64
) ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(day)
ORDER BY (day, provider, model);

-- 创建物化视图自动汇总
CREATE MATERIALIZED VIEW IF NOT EXISTS agentwatch.cost_summary_mv
TO agentwatch.cost_summary AS
SELECT
    toDate(created_at) as day,
    provider,
    model,
    count() as total_traces,
    sum(total_tokens) as total_tokens,
    sum(total_cost) as total_cost,
    avg(duration_ms) as avg_latency_ms
FROM agentwatch.traces
WHERE status = 'completed'
GROUP BY day, provider, model;

-- 查询示例
-- SELECT * FROM agentwatch.traces LIMIT 10;
-- SELECT * FROM agentwatch.cost_summary WHERE day >= today() - INTERVAL 7 DAY;