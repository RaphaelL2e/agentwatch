# 构建阶段 - 使用 slim 避免 musl 兼容问题
FROM node:20-slim as builder

WORKDIR /app

# 先复制 package.json
COPY package*.json ./

# 安装 rollup 平台依赖（解决 npm optional deps bug）
RUN npm install --legacy-peer-deps && \
    npm install @rollup/rollup-linux-x64-gnu --save-optional

# 复制源代码
COPY . .

# 构建
RUN npm run build

# 生产镜像
FROM nginx:alpine

# 复制构建结果
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80