# AgentWatch API v2 规划文档

## 概述

API v2 将在现有 v1 API 基础上，提供更强的查询能力、批量操作支持、实时推送增强和多租户架构。

**发布时间**: Month 3 (Week 9-12)
**当前版本**: v1 (v0.5.0)
**目标版本**: v2.0.0

---

## 核心改进

### 1. 批量操作 API

**痛点**: v1 需要逐个创建/更新 Trace，效率低

**v2 解决方案**:

```
POST /api/v2/traces/bulk
{
  "traces": [
    {"agent_name": "agent1", "provider": "openai", "model": "gpt-4o"},
    {"agent_name": "agent2", "provider": "deepseek", "model": "deepseek-chat"},
    ...
  ]
}

Response:
{
  "created": 10,
  "failed": 0,
  "trace_ids": ["tr_001", "tr_002", ...],
  "errors": []
}
```

**批量更新**:
```
PUT /api/v2/traces/bulk
{
  "updates": [
    {"trace_id": "tr_001", "status": "completed"},
    {"trace_id": "tr_002", "status": "failed", "error": "..."},
    ...
  ]
}
```

**批量删除**:
```
DELETE /api/v2/traces/bulk
{
  "trace_ids": ["tr_001", "tr_002", ...]
}
```

---

### 2. 高级查询 API

**痛点**: v1 查询能力有限，不支持复杂过滤

**v2 解决方案**: 

```
POST /api/v2/traces/search
{
  "query": {
    "filters": [
      {"field": "provider", "operator": "eq", "value": "openai"},
      {"field": "status", "operator": "in", "values": ["completed", "running"]},
      {"field": "total_cost", "operator": "gt", "value": 0.5},
      {"field": "created_at", "operator": "between", "start": "2026-04-01", "end": "2026-04-30"}
    ],
    "sort": [{"field": "total_cost", "order": "desc"}],
    "pagination": {"page": 1, "page_size": 50},
    "aggregations": [
      {"type": "sum", "field": "total_cost"},
      {"type": "avg", "field": "duration_ms"},
      {"type": "count", "group_by": "provider"}
    ]
  }
}

Response:
{
  "traces": [...],
  "total": 1000,
  "aggregations": {
    "sum_total_cost": 150.5,
    "avg_duration_ms": 250,
    "count_by_provider": {"openai": 500, "deepseek": 400, "claude": 100}
  }
}
```

**支持的 operator**:
- `eq` - 等于
- `ne` - 不等于
- `gt` / `gte` - 大于/大于等于
- `lt` / `lte` - 小于/小于等于
- `in` - 在列表中
- `between` - 区间
- `like` - 模糊匹配
- `regex` - 正则匹配

---

### 3. 实时推送增强

**痛点**: v1 WebSocket 只支持 trace_created 事件

**v2 解决方案**:

**订阅配置**:
```
WS /api/v2/ws/subscribe
{
  "channels": [
    "traces.created",
    "traces.updated",
    "traces.completed",
    "alerts.cost_threshold",
    "alerts.error_rate",
    "stats.hourly"
  ],
  "filters": {
    "provider": ["openai", "deepseek"],
    "agent_id": "agent_001"
  }
}
```

**推送事件类型**:
- `traces.created` - 新 Trace 创建
- `traces.updated` - Trace 更新
- `traces.completed` - Trace 完成
- `traces.failed` - Trace 失败
- `alerts.cost_threshold` - 成本超阈值告警
- `alerts.error_rate` - 错误率告警
- `stats.hourly` - 每小时统计汇总

**推送数据结构**:
```json
{
  "event": "traces.completed",
  "timestamp": "2026-04-29T10:00:00Z",
  "data": {
    "trace_id": "tr_001",
    "total_cost": 0.15,
    "duration_ms": 1200,
    "provider": "deepseek"
  },
  "stats": {
    "hourly_cost": 5.2,
    "total_traces_today": 150
  }
}
```

---

### 4. 多租户架构

**痛点**: v1 单租户，无法区分不同团队/项目

**v2 解决方案**:

**租户隔离**:
- 每个 API Key 对应一个租户
- Trace 数据按 tenant_id 隔离
- Dashboard 按租户聚合显示

**租户管理 API**:
```
POST /api/v2/tenants
{
  "name": "Team Alpha",
  "plan": "pro",
  "limits": {
    "max_traces_per_month": 100000,
    "max_api_keys": 10
  }
}

GET /api/v2/tenants/{tenant_id}/usage
{
  "month": "2026-04",
  "traces_created": 5000,
  "storage_used_mb": 120,
  "api_calls": 15000
}
```

**计划类型**:
- `free` - 1K traces/month
- `pro` - 100K traces/month
- `enterprise` - 无限制

---

### 5. 成本分析增强

**痛点**: v1 只提供基础成本汇总

**v2 解决方案**:

**成本预测 API**:
```
GET /api/v2/cost/predict
{
  "provider": "deepseek",
  "estimated_tokens": 1000000,
  "time_period": "month"
}

Response:
{
  "estimated_cost": 11.0,
  "confidence": 0.95,
  "based_on": {
    "historical_avg_cost_per_token": 0.000011,
    "sample_size": 5000
  }
}
```

**成本优化建议**:
```
GET /api/v2/cost/optimization
{
  "current_provider": "openai",
  "monthly_tokens": 500000
}

Response:
{
  "recommendations": [
    {
      "type": "switch_provider",
      "target": "deepseek",
      "potential_savings": 99.1,
      "savings_per_month": 1165
    },
    {
      "type": "reduce_tokens",
      "target": 400000,
      "potential_savings": 20,
      "savings_per_month": 233
    }
  ]
}
```

---

### 6. Agent 管理 API

**新增功能**: Agent 注册和配置管理

```
POST /api/v2/agents
{
  "agent_id": "agent_001",
  "name": "MyAgent",
  "description": "Code generation agent",
  "default_provider": "deepseek",
  "default_model": "deepseek-chat",
  "config": {
    "max_tokens": 2000,
    "temperature": 0.7
  }
}

GET /api/v2/agents/{agent_id}/stats
{
  "total_traces": 500,
  "avg_cost": 0.02,
  "avg_latency_ms": 350,
  "error_rate": 0.02,
  "most_used_model": "deepseek-chat"
}
```

---

## API 端点汇总

### v1 vs v2 对比

| 功能 | v1 | v2 |
|------|----|----|
| 创建 Trace | POST /trace | POST /traces, POST /traces/bulk |
| 查询 Trace | GET /trace/{id} | GET /traces/{id}, POST /traces/search |
| 更新 Trace | PUT /trace/{id} | PUT /traces/{id}, PUT /traces/bulk |
| 删除 Trace | DELETE /trace/{id} | DELETE /traces/{id}, DELETE /traces/bulk |
| 成本汇总 | GET /cost/summary | GET /cost/summary, GET /cost/predict |
| WebSocket | WS /ws | WS /ws/v2, 多通道订阅 |
| 健康检查 | GET /health | GET /health, GET /status |
| Agent 管理 | - | GET/POST /agents |
| 租户管理 | - | GET/POST /tenants |

---

## 实施计划

### Phase 1: 批量操作 (Week 9)

**任务**:
1. 实现 `bulk_create_traces` API
2. 实现 `bulk_update_traces` API
3. 实现 `bulk_delete_traces` API
4. 添加批量操作测试
5. 更新 SDK 支持批量操作

**工作量**: 3-5 天

### Phase 2: 高级查询 (Week 10)

**任务**:
1. 设计查询 DSL
2. 实现 `search_traces` API
3. 添加聚合计算逻辑
4. 优化 ClickHouse 查询性能
5. 添加查询测试

**工作量**: 4-6 天

### Phase 3: WebSocket 增强 (Week 11)

**任务**:
1. 设计多通道订阅协议
2. 实现告警推送机制
3. 实现统计推送机制
4. 添加推送测试
5. 更新前端 WebSocket 客户端

**工作量**: 3-4 天

### Phase 4: 多租户架构 (Week 12)

**任务**:
1. 设计租户数据模型
2. 实现租户隔离逻辑
3. 实现租户管理 API
4. 实现用量统计 API
5. 添加租户测试

**工作量**: 5-7 天

---

## 兼容性

**策略**: v1 API 保留，v2 API 并行运行

**迁移路径**:
- SDK 自动检测 API 版本
- 提供 v1 → v2 迁移指南
- Dashboard 同时支持两个版本

---

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| API 变更导致 SDK 不兼容 | 高 | SDK 版本化，保持向后兼容 |
| 多租户数据隔离复杂 | 中 | 使用 tenant_id 作为查询条件，测试隔离完整性 |
| WebSocket 推送延迟 | 中 | 使用消息队列缓冲，批量推送优化 |
| ClickHouse 查询性能 | 中 | 添加索引，优化查询语句 |

---

## 成功指标

| 指标 | 目标 |
|------|------|
| API 响应时间 | < 100ms (批量操作 < 500ms) |
| WebSocket 推送延迟 | < 50ms |
| 批量操作吞吐 | 1000 traces/请求 |
| 多租户隔离 | 100% 数据隔离验证 |
| SDK 兼容性 | v1 SDK 继续工作 |

---

## 下一步

1. ✅ 确认 API v2 规划文档
2. 开始 Phase 1: 批量操作 API 实现
3. 更新 PROGRESS.md 添加 Week 9-12 计划

---

*Created: 2026-04-29*
*Author: AgentWatch Team*