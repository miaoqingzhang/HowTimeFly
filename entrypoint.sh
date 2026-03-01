#!/bin/bash
# HowTimeFly 容器启动脚本
# 支持通过环境变量动态配置扫描路径

set -e

echo "=========================================="
echo "    HowTimeFly - 时间线媒体播放系统"
echo "=========================================="

# 配置文件路径
CONFIG_FILE="/app/config.yaml"

# 如果配置文件不存在，创建默认配置
if [ ! -f "$CONFIG_FILE" ]; then
    echo "创建默认配置文件..."
    cat > "$CONFIG_FILE" << 'EOF'
# 服务器配置
server:
  host: "0.0.0.0"
  port: 8080
  debug: false
  reload: false

# 扫描路径配置 (可通过环境变量覆盖)
scanner:
  paths:
    - "/media"
  recursive: true
  file_types:
    photo:
      - ".jpg"
      - ".jpeg"
      - ".png"
      - ".gif"
      - ".webp"
    video:
      - ".mp4"
      - ".mov"
      - ".avi"
      - ".mkv"

# 数据库配置
database:
  path: "./data/database.db"

# 缩略图配置
thumbnails:
  enabled: true
  output_dir: "./data/thumbnails"
  sizes:
    small: 200
    medium: 600
    large: 1200

# 日志配置
logging:
  level: "INFO"
EOF
fi

# ============ 环境变量覆盖配置 ============
echo "检查环境变量配置..."

# SCAN_PATHS - 扫描路径 (支持多个，用冒号分隔)
if [ -n "$SCAN_PATHS" ]; then
    echo "配置扫描路径: $SCAN_PATHS"
    # 将路径转换为 YAML 列表格式
    IFS=':' read -ra PATHS <<< "$SCAN_PATHS"
    python3 /app/app/update_config.py "$CONFIG_FILE" "scanner.paths" "${PATHS[@]}"
fi

# SCAN_RECURSIVE - 是否递归扫描
if [ -n "$SCAN_RECURSIVE" ]; then
    echo "配置递归扫描: $SCAN_RECURSIVE"
    python3 /app/app/update_config.py "$CONFIG_FILE" "scanner.recursive" "$SCAN_RECURSIVE"
fi

# TZ - 时区 (由 Docker 自动处理，这里仅显示)
if [ -n "$TZ" ]; then
    echo "时区设置: $TZ"
fi

# ============ 显示最终配置 ============
echo ""
echo "最终扫描配置:"
python3 /app/app/show_config.py "$CONFIG_FILE"
echo ""

# ============ 启动应用 ============
echo "启动 HowTimeFly 服务..."
echo "=========================================="
exec uvicorn app.main:app --host 0.0.0.0 --port 8080
