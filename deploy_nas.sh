#!/bin/bash
# HowTimeFly 飞牛OS 部署脚本

set -e

echo "=== HowTimeFly 飞牛OS 部署脚本 ==="
echo ""

# 配置变量
INSTALL_DIR="/opt/howtimefly"
SERVICE_NAME="howtimefly"
MEDIA_DIR="/media/photos"  # 修改为你的媒体文件目录
PORT=8080

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then
    echo "请使用 sudo 运行此脚本"
    exit 1
fi

# 检查 Python 版本
echo "检查 Python 版本..."
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3"
    echo "请先安装 Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
echo "Python 版本: $PYTHON_VERSION"

if [ "$(echo "$PYTHON_VERSION 3.8" | awk '{print ($1 < $2)}')" -eq 1 ]; then
    echo "错误: Python 版本需要 3.8 或更高"
    exit 1
fi

# 安装依赖
echo ""
echo "安装系统依赖..."
apt-get update
apt-get install -y python3-pip python3-venv libglib2.0-0 ffmpeg

# 创建安装目录
echo ""
echo "创建安装目录: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/data"
mkdir -p "$INSTALL_DIR/logs"

# 复制文件
echo ""
echo "复制应用文件..."
cp -r app "$INSTALL_DIR/"
cp -r frontend "$INSTALL_DIR/"
cp requirements.txt "$INSTALL_DIR/"
cp run.py "$INSTALL_DIR/"
cp config.yaml "$INSTALL_DIR/" 2>/dev/null || true

# 创建虚拟环境
echo ""
echo "创建 Python 虚拟环境..."
cd "$INSTALL_DIR"
python3 -m venv venv
source venv/bin/activate

# 安装 Python 依赖
echo ""
echo "安装 Python 依赖..."
pip install --upgrade pip
pip install -r requirements.txt

# 创建配置文件
echo ""
echo "创建配置文件..."
cat > "$INSTALL_DIR/config.yaml" <<EOF
# HowTimeFly 配置文件

# 数据库配置
database:
  path: "${INSTALL_DIR}/data/database.db"

# 媒体扫描路径
scanner:
  paths:
    - "${MEDIA_DIR}"
  recursive: true

# 服务器配置
server:
  host: "0.0.0.0"
  port: ${PORT}
  reload: false
  debug: false
EOF

# 创建 systemd 服务文件
echo ""
echo "创建 systemd 服务..."
cat > "/etc/systemd/system/${SERVICE_NAME}.service" <<EOF
[Unit]
Description=HowTimeFly Timeline Media Player
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${INSTALL_DIR}
Environment="PATH=${INSTALL_DIR}/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=${INSTALL_DIR}/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
Restart=always
RestartSec=10
StandardOutput=append:${INSTALL_DIR}/logs/app.log
StandardError=append:${INSTALL_DIR}/logs/error.log

[Install]
WantedBy=multi-user.target
EOF

# 重载 systemd
systemctl daemon-reload

# 创建启动脚本
cat > "$INSTALL_DIR/start.sh" <<EOF
#!/bin/bash
cd "$INSTALL_DIR"
source venv/bin/activate
python3 -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
EOF
chmod +x "$INSTALL_DIR/start.sh"

# 设置权限
chmod -R 755 "$INSTALL_DIR"

echo ""
echo "=== 安装完成 ==="
echo ""
echo "配置文件: $INSTALL_DIR/config.yaml"
echo "日志目录: $INSTALL_DIR/logs"
echo "媒体目录: $MEDIA_DIR"
echo ""
echo "使用命令管理服务:"
echo "  启动: systemctl start $SERVICE_NAME"
echo "  停止: systemctl stop $SERVICE_NAME"
echo "  重启: systemctl restart $SERVICE_NAME"
echo "  状态: systemctl status $SERVICE_NAME"
echo "  开机自启: systemctl enable $SERVICE_NAME"
echo ""
echo "访问地址: http://<你的NAS IP>:${PORT}"
echo ""
echo "请先编辑配置文件设置媒体目录，然后启动服务:"
echo "  nano $INSTALL_DIR/config.yaml"
echo "  systemctl start $SERVICE_NAME"
