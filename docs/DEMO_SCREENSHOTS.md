# AgentWatch Demo 截图指南

## 截图准备

### 1. Dashboard 截图
- 启动后端: `cd backend && python main.py`
- 启动前端: `cd frontend && npm run dev`
- 访问: http://localhost:5173
- 创建一些测试数据: POST /api/v1/test/trace

### 2. Trace Detail 截图
- 点击一个 Trace 查看详情
- 展示 Token 使用、Events、Timeline

### 3. Cost Comparison 截图
- 访问 /costs 页面
- 展示 DeepSeek vs GPT-4o 的 89x 成本差异

## 关键截图

### Dashboard 主页
```
URL: http://localhost:5173/
展示内容:
- Total Traces 统计
- Completed/Running 状态
- Total Cost 累计
- Recent Traces 列表
```

### Trace 详情页
```
URL: http://localhost:5173/trace/{trace_id}
展示内容:
- Agent 名称和状态
- Provider 和 Model
- Token Usage（Input/Output/Total）
- Cost 计算
- Events 时间线
```

### Cost Comparison 页面
```
URL: http://localhost:5173/costs
展示内容:
- DeepSeek 89x cheaper than GPT-4o
- 各 Provider 成本对比表格
- Recommendations 建议
```

## HN 发布截图建议

**最佳截图组合：**
1. Dashboard 全屏（展示整体功能）
2. Cost Comparison（核心卖点：89x 成本差异）
3. Trace Detail（展示技术深度）

**截图尺寸：**
- 宽度: 1200px
- 高度: 800px
- 格式: PNG

## 自动生成 Demo 数据

```bash
# 创建多个测试 Trace
curl -X POST http://localhost:8000/api/v1/test/trace
curl -X POST http://localhost:8000/api/v1/test/trace
curl -X POST http://localhost:8000/api/v1/test/trace
curl -X POST http://localhost:8000/api/v1/test/trace
curl -X POST http://localhost:8000/api/v1/test/trace

# 创建不同 Provider 的 Trace
curl -X POST http://localhost:8000/api/v1/trace \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"agent_001","agent_name":"GPT-4 Agent","provider":"openai","model":"gpt-4o"}'

curl -X POST http://localhost:8000/api/v1/trace \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"agent_002","agent_name":"DeepSeek Agent","provider":"deepseek","model":"deepseek-chat"}'

curl -X POST http://localhost:8000/api/v1/trace \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"agent_003","agent_name":"Claude Agent","provider":"anthropic","model":"claude-3-sonnet"}'
```

---

**注意：** 截图需要在本地启动服务后手动拍摄，或使用 Playwright 自动截图。