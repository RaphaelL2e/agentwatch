# AgentWatch 部署指南

## 目录

1. [快速部署](#快速部署)
2. [Docker 部署](#docker-部署)
3. [生产配置](#生产配置)
4. [环境变量](#环境变量)
5. [安全配置](#安全配置)
6. [监控和日志](#监控和日志)

---

## 快速部署

### 本地开发

```bash
# 克隆仓库
git clone https://github.com/RaphaelL2e/agentwatch.git
cd agentwatch

# 后端
cd backend
pip install -r requirements.txt
python main.py

# 前端（可选）
cd frontend
npm install
npm run dev
```

### Docker Compose（推荐）

```bash
# 一键启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止
docker-compose down
```

服务地址：
- Backend API: http://localhost:8000
- Dashboard: http://localhost:3000
- API Docs: http://localhost:8000/docs

---

## Docker 部署

### 单容器部署

```bash
# 构建镜像
docker build -t agentwatch:latest .

# 运行
docker run -d \
  --name agentwatch \
  -p 8000:8000 \
  -e JWT_SECRET_KEY=your-secret-key \
  -v agentwatch-data:/data \
  agentwatch:latest
```

### Docker Compose 完整配置

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - STORAGE_TYPE=sqlite
      - DATABASE_PATH=/data/agentwatch.db
    volumes:
      - agentwatch-data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  agentwatch-data:
```

---

## 生产配置

### 环境变量

创建 `.env` 文件：

```bash
# .env
JWT_SECRET_KEY=your-secure-random-key-here
STORAGE_TYPE=sqlite
DATABASE_PATH=/data/agentwatch.db

# 可选
API_RATE_LIMIT=100
ACCESS_TOKEN_EXPIRE_HOURS=24
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### 生成安全密钥

```bash
# 生成 JWT 密钥
python -c "import secrets; print(secrets.token_hex(32))"
```

### HTTPS 配置（推荐）

使用 Nginx 反向代理：

```nginx
# /etc/nginx/sites-available/agentwatch
server {
    listen 443 ssl http2;
    server_name agentwatch.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 安全配置

### 认证系统

AgentWatch 支持两种认证模式：

1. **JWT Token** - 用于 Dashboard Web 界面
2. **API Key** - 用于 SDK/CLI 集成

#### API Key 格式

```
aw_t_xxxxxxxx_k_yyyyyyyy_secret
```

#### 使用 API Key

```python
from agentwatch import AgentWatch

aw = AgentWatch(
    api_url="https://agentwatch.yourdomain.com",
    api_key="aw_t_xxxxxxxx_k_yyyyyyyy_secret"
)
```

#### 权限范围

| Scope | 说明 |
|-------|------|
| `read` | 只读访问 |
| `write` | 创建/更新 traces |
| `admin` | 管理操作 |

### 防火墙配置

```bash
# 只开放必要端口
ufw allow 80/tcp
ufw allow 443/tcp
ufw deny 8000/tcp  # 内部端口
```

---

## 监控和日志

### 健康检查

```bash
# 检查后端状态
curl http://localhost:8000/health

# 返回
{"status": "ok", "version": "0.7.1", "uptime": 3600}
```

### 日志配置

Docker logs:

```bash
# 查看日志
docker-compose logs -f backend

# 日志级别
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

### Prometheus 监控（可选）

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'agentwatch'
    static_configs:
      - targets: ['localhost:8000']
```

---

## 数据备份

### SQLite 备份

```bash
# 每日备份
cp /data/agentwatch.db /backup/agentwatch-$(date +%Y%m%d).db

# 自动备份脚本
#!/bin/bash
BACKUP_DIR="/backup"
DB_FILE="/data/agentwatch.db"
DATE=$(date +%Y%m%d)

cp $DB_FILE $BACKUP_DIR/agentwatch-$DATE.db
# 保留最近 30 天
find $BACKUP_DIR -name "agentwatch-*.db" -mtime +30 -delete
```

---

## 升级指南

### 版本升级

```bash
# 停止服务
docker-compose down

# 备份数据
cp /data/agentwatch.db /backup/agentwatch-pre-upgrade.db

# 拉取最新代码
git pull origin main

# 重新构建
docker-compose build

# 启动
docker-compose up -d
```

---

## 故障排除

### 常见问题

#### 1. 连接失败

```bash
# 检查端口
lsof -i :8000

# 检查容器状态
docker-compose ps
```

#### 2. WebSocket 连接失败

检查 Nginx WebSocket 配置：

```nginx
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

#### 3. Token 验证失败

检查 JWT_SECRET_KEY 配置：

```bash
echo $JWT_SECRET_KEY
```

---

## 性能优化

### 内存存储 vs SQLite

| 场景 | 推荐 |
|------|------|
| 开发测试 | Memory |
| 小规模 (<10K traces) | SQLite |
| 大规模 (>100K traces) | PostgreSQL |

### 资源需求

| 组件 | CPU | 内存 |
|------|-----|------|
| Backend | 1 core | 512MB |
| Frontend | 0.5 core | 256MB |
| 总计 | 1.5 cores | 768MB |

---

## 参考链接

- [GitHub Repository](https://github.com/RaphaelL2e/agentwatch)
- [API Documentation](https://github.com/RaphaelL2e/agentwatch/blob/main/docs/API.md)
- [Architecture](https://github.com/RaphaelL2e/agentwatch/blob/main/docs/ARCHITECTURE.md)

---

**Made with ❤️ by RaphaelL2e**