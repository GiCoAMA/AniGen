# 使用官方轻量级 Python 3.12 镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 优先复制依赖文件，利用 Docker 缓存加速构建
COPY requirements.txt .

# 安装依赖（已添加清华源加速下载 🚀）
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir -r requirements.txt

# 复制代码到容器内
COPY . .