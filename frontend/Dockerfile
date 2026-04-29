# 构建阶段
FROM node:20-alpine as builder

WORKDIR /app

# 先复制 package.json 和 package-lock.json
COPY package*.json ./

# 安装依赖
RUN npm ci --legacy-peer-deps || npm install --legacy-peer-deps

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