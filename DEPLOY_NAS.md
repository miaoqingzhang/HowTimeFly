# HowTimeFly 飞牛OS/ARM NAS 部署指南

## 方法一：Docker 部署（推荐）

如果你的飞牛OS支持 Docker，这是最简单的部署方式。

### 1. 准备工作

在你的 NAS 上创建项目目录：

```bash
# SSH 连接到你的 NAS
ssh root@<你的NAS IP>

# 创建项目目录
mkdir -p /opt/howtimefly
cd /opt/howtimefly

# 上传项目文件到此目录
# 需要上传的文件和文件夹：
# - app/
# - frontend/
# - Dockerfile
# - docker-compose.yml
# - requirements.txt
# - config.yaml
```

### 2. 修改配置

编辑 `config.yaml`，设置你的媒体文件路径：

```yaml
scanner:
  paths:
    - "/volume1/photo"  # 修改为你的实际路径
  recursive: true
```

编辑 `docker-compose.yml`，修改媒体文件挂载路径：

```yaml
volumes:
  - /volume1/photo:/media:ro  # 修改为你的实际路径
```

### 3. 启动服务

```bash
docker-compose up -d
```

### 4. 查看日志

```bash
docker-compose logs -f
```

---

## 方法二：直接部署（使用脚本）

如果 Docker 不可用，使用部署脚本。

### 1. 上传项目文件

将整个项目文件夹上传到 NAS，例如到 `/tmp/howtimefly`

### 2. 运行部署脚本

```bash
cd /tmp/howtimefly
chmod +x deploy_nas.sh
sudo ./deploy_nas.sh
```

### 3. 配置媒体路径

```bash
nano /opt/howtimefly/config.yaml
```

修改 `scanner.paths` 为你的媒体文件路径。

### 4. 启动服务

```bash
systemctl start howtimefly
systemctl enable howtimefly  # 开机自启
```

---

## 方法三：手动部署

如果需要更多控制，可以手动部署。

### 1. 安装依赖

```bash
# 安装 Python 和依赖
apt-get update
apt-get install -y python3 python3-pip python3-venv ffmpeg libglib2.0-0
```

### 2. 创建虚拟环境

```bash
cd /opt/howtimefly
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. 创建配置文件

```bash
cat > config.yaml <<EOF
database:
  path: "/opt/howtimefly/data/database.db"

scanner:
  paths:
    - "/volume1/photo"  # 你的媒体路径
  recursive: true

server:
  host: "0.0.0.0"
  port: 8080
  reload: false
  debug: false
EOF
```

### 4. 创建 systemd 服务

```bash
cat > /etc/systemd/system/howtimefly.service <<EOF
[Unit]
Description=HowTimeFly Timeline Media Player
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/howtimefly
Environment="PATH=/opt/howtimefly/venv/bin:/usr/local/bin"
ExecStart=/opt/howtimefly/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
```

### 5. 启动服务

```bash
systemctl start howtimefly
systemctl enable howtimefly
```

---

## ARM 架构注意事项

如果你的 NAS 是 ARM 架构（如群晖、威联通等），需要注意：

### 1. OpenCV 安装

ARM 平台上安装 opencv-python 可能有问题，可以使用：

```bash
pip install opencv-python-headless
```

或者跳过视频缩略图功能，只使用图片缩略图。

### 2. 修改 requirements.txt

创建 `requirements-arm.txt`：

```
fastapi
uvicorn[standard]
sqlalchemy
pillow
piexif
pyyaml
opencv-python-headless
```

---

## 访问应用

部署完成后，在浏览器中访问：

```
http://<你的NAS IP>:8080
```

---

## 常见问题

### 1. 权限问题

确保有权限访问媒体文件目录：

```bash
chmod -R 755 /volume1/photo
```

### 2. 端口冲突

如果 8080 端口被占用，修改 `config.yaml` 中的端口配置。

### 3. 查看日志

```bash
# Docker 方式
docker-compose logs -f howtimefly

# systemd 方式
journalctl -u howtimefly -f
```

### 4. 重启服务

```bash
# Docker 方式
docker-compose restart

# systemd 方式
systemctl restart howtimefly
```

---

## 数据备份

重要数据位于 `data` 目录：

- `database.db` - 媒体数据库
- `thumbnails/` - 缩略图缓存

定期备份此目录：

```bash
tar -czf howtimefly-backup-$(date +%Y%m%d).tar.gz /opt/howtimefly/data
```
