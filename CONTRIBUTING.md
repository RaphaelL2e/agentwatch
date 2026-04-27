# Contributing to AgentWatch

感谢你对 AgentWatch 的关注！我们欢迎任何形式的贡献。

## 🤔 如何贡献

### 报告 Bug

如果你发现了 bug，请通过 [GitHub Issues](https://github.com/RaphaelL2e/agentwatch/issues) 提交报告。

**Bug 报告模板：**
```markdown
**描述问题**
清楚地描述遇到了什么问题。

**复现步骤**
1. 执行 '...'
2. 点击 '...'
3. 看到错误 '...'

**预期行为**
描述你期望发生什么。

**实际行为**
描述实际发生了什么。

**环境信息**
- OS: [e.g. macOS, Linux]
- Python version: [e.g. 3.11]
- AgentWatch version: [e.g. 0.1.0]
```

### 提出新功能

如果你有新功能建议，请在 Issues 中提交。

**功能请求模板：**
```markdown
**功能描述**
清楚地描述你希望添加的功能。

**为什么需要这个功能？**
解释这个功能的用途和价值。

**实现建议**
如果有的话，提供实现思路或参考。
```

### 提交代码

1. **Fork 仓库**
   ```bash
   git clone https://github.com/YOUR_USERNAME/agentwatch.git
   cd agentwatch
   ```

2. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **开发**
   - 确保代码风格一致（遵循 PEP 8）
   - 添加必要的测试
   - 更新相关文档

4. **测试**
   ```bash
   # 后端测试
   cd backend
   pytest
   
   # 前端测试
   cd frontend
   npm test
   ```

5. **提交**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

6. **推送**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **创建 Pull Request**
   - 在 GitHub 上创建 PR
   - 描述你的更改
   - 等待审核

## 📝 代码规范

### Python 代码

- 遵循 [PEP 8](https://peps.python.org/pep-0008/) 风格指南
- 使用 [Black](https://github.com/psf/black) 格式化代码
- 使用类型注解（Type Hints）
- 函数和类添加 docstring

**示例：**
```python
def calculate_cost(
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int
) -> float:
    """Calculate the cost for a given provider and token usage.
    
    Args:
        provider: The LLM provider name (e.g. "openai")
        model: The model name (e.g. "gpt-4o")
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
    
    Returns:
        The calculated cost in USD
    """
    # Implementation
    pass
```

### TypeScript/React 代码

- 使用 TypeScript 类型
- 组件使用函数式组件
- 遵循 Airbnb React 风格指南

**示例：**
```typescript
interface TraceCardProps {
  id: string;
  agentName: string;
  startTime: Date;
  status: 'running' | 'completed' | 'failed';
}

const TraceCard: React.FC<TraceCardProps> = ({ id, agentName, startTime, status }) => {
  // Implementation
};
```

### Commit 消息

遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型：**
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

**示例：**
```
feat(sdk): add DeepSeek provider support

Add DeepSeek API cost calculation and adapter.
Support DeepSeek v4 pricing model.

Closes #123
```

## 🧪 测试规范

### 单元测试

- 每个新功能必须有对应的单元测试
- 测试覆盖率目标：> 80%
- 使用 pytest（后端）和 Jest（前端）

**Python 测试示例：**
```python
import pytest
from agentwatch.client import AgentWatch

def test_calculate_cost_openai():
    """Test OpenAI cost calculation."""
    aw = AgentWatch()
    cost = aw.calculate_cost("openai", "gpt-4o", 1000, 500)
    assert cost == 0.0125  # $0.005*1 + $0.015*0.5
```

### 集成测试

- 重要功能流程需要有集成测试
- 使用 Docker Compose 进行本地集成测试

## 📚 文档规范

- 新功能需要更新 README.md
- API 变化需要更新 API 文档
- SDK 使用方式需要更新 SDK README

## 🏆 贡献者奖励

- 首批贡献者将在 README 中永久展示
- 重要贡献者将获得后续付费版本永久折扣
- 核心贡献者有机会成为项目 Collaborator

## 💬 获取帮助

- GitHub Issues：提交问题或建议
- GitHub Discussions：讨论想法和方案
- Email: raphaellee.work@gmail.com

## 📜 许可证

本项目采用 Apache 2.0 许可证。你的贡献将同样受此许可证保护。

---

再次感谢你的关注和贡献！让我们一起打造最好的 AI Agent 监控平台 🚀