FROM python:3.14-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用文件
COPY app/ ./app/
COPY frontend/ ./frontend/
COPY run.py .

# 设置辅助脚本执行权限
RUN chmod +x /app/update_config.py /app/show_config.py

# 复制并设置启动脚本权限
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# 创建数据目录
RUN mkdir -p /app/data

# 暴露端口
EXPOSE 8080

# 启动命令 - 使用 entrypoint 脚本
ENTRYPOINT ["/app/entrypoint.sh"]
