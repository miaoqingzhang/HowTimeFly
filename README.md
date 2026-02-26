# HowTimeFly - 时间线媒体播放系统

一个基于 Python + FastAPI 的媒体文件管理和时间线播放系统，专为飞牛NAS设计，可在电视盒子通过浏览器访问。

## 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 准备测试媒体文件

```bash
# 创建测试目录
mkdir test_media

# 将一些照片和视频复制到 test_media 目录
# 或者运行测试数据生成脚本
python scripts/create_test_data.py
```

### 3. 初始化数据库

```bash
python scripts/init_db.py
```

### 4. 扫描媒体文件

```bash
# 使用配置文件中的路径扫描
python scripts/scan.py

# 或指定自定义路径
python scripts/scan.py "D:\MyPhotos" "E:\MyVideos"
```

### 5. 生成缩略图（可选）

```bash
# 为所有媒体生成缩略图
python scripts/gen_thumbs.py

# 限制生成数量
python scripts/gen_thumbs.py --limit 50
```

### 6. 启动服务

```bash
python run.py
```

服务启动后访问: http://127.0.0.1:8080

## 目录结构

```
HowTimeFly/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 主应用
│   ├── models.py            # 数据模型
│   ├── database.py          # 数据库操作
│   ├── scanner.py           # 文件扫描器
│   ├── thumbnail.py         # 缩略图服务
│   └── utils/
│       └── exif.py          # EXIF 提取
├── frontend/
│   └── index.html           # Web 界面
├── scripts/
│   ├── init_db.py           # 初始化数据库
│   ├── scan.py              # 扫描脚本
│   └── gen_thumbs.py        # 生成缩略图
├── config.yaml              # 配置文件
├── requirements.txt         # 依赖清单
└── run.py                   # 启动脚本
```

## 配置文件 (config.yaml)

```yaml
# 扫描路径配置
scanner:
  paths:
    - "./test_media"      # 修改为你的媒体目录
    - "D:/Photos"
    - "E:/Videos"
  recursive: true

# 服务器配置
server:
  host: "0.0.0.0"         # 0.0.0.0 允许外部访问
  port: 8080
```

## API 接口

| 接口 | 说明 |
|------|------|
| `GET /` | Web 界面 |
| `GET /api/v1/stats` | 获取统计信息 |
| `GET /api/v1/media/timeline` | 获取时间线 |
| `GET /api/v1/media/{id}/file` | 获取媒体文件 |
| `GET /api/v1/media/{id}/thumbnail` | 获取缩略图 |
| `POST /api/v1/scan/start` | 开始扫描 |
| `GET /api/v1/scan/status` | 扫描状态 |

## 支持的文件格式

- **图片**: jpg, jpeg, png, gif, webp, bmp, heic
- **视频**: mp4, mov, avi, mkv, webm

## 技术栈

- **后端**: Python + FastAPI + SQLAlchemy + SQLite
- **前端**: 原生 HTML/CSS/JavaScript
- **图片处理**: Pillow
- **EXIF 提取**: piexif

## 电视盒子使用

1. 确保 HowTimeFly 服务运行在飞牛NAS上
2. 配置 `config.yaml` 中 `server.host` 为 `"0.0.0.0"`
3. 在电视盒子浏览器输入: `http://<NAS IP>:8080`

## 键盘快捷键

| 按键 | 功能 |
|------|------|
| ESC | 退出全屏/关闭查看器 |
| ← → | 上一张/下一张 |
| Enter | 打开选中项 |
