# HowTimeFly 项目设计文档

## 项目概述

**目标**: 构建一个时间线媒体播放系统，能够读取飞牛NAS上的照片和视频，按时间顺序在电视盒子通过Web界面播放。

**核心挑战**:
- 处理大量媒体文件（>10,000个）
- 电视盒子浏览器兼容性不确定
- 需要高效的索引和检索机制

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         飞牛NAS (服务端)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   扫描服务       │  │   Web服务       │  │   缩略图服务     │ │
│  │  - 定时扫描      │  │  - REST API     │  │  - 后台生成      │ │
│  │  - 增量更新      │  │  - 静态文件     │  │  - 多尺寸        │ │
│  │  - EXIF提取      │  │  - WebSocket推送│  │  - 缓存管理      │ │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘ │
│           │                    │                    │           │
│           └────────────────────┼────────────────────┘           │
│                                │                                │
│                    ┌───────────▼────────────┐                   │
│                    │   数据层                │                   │
│                    │  ┌─────────────────┐   │                   │
│                    │  │  SQLite数据库   │   │                   │
│                    │  │  - media_items  │   │                   │
│                    │  │  - thumbnails   │   │                   │
│                    │  │  - playlists    │   │                   │
│                    │  └─────────────────┘   │                   │
│                    │  ┌─────────────────┐   │                   │
│                    │  │  文件系统       │   │                   │
│                    │  │  - 原始媒体      │   │                   │
│                    │  │  - 缩略图缓存    │   │                   │
│                    │  └─────────────────┘   │                   │
│                    └───────────────────────┘                   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │   电视盒子浏览器      │
                    │  ┌───────────────┐   │
                    │  │  Web播放器     │   │
                    │  │  - 时间线视图  │   │
                    │  │  - 幻灯片模式  │   │
                    │  │  - 视频播放    │   │
                    │  └───────────────┘   │
                    └─────────────────────┘
```

---

## 数据库设计

### 表结构

#### media_items (媒体文件表)
```sql
CREATE TABLE media_items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path       TEXT NOT NULL UNIQUE,     -- 文件绝对路径
    file_name       TEXT NOT NULL,             -- 文件名
    file_size       INTEGER NOT NULL,          -- 字节
    file_type       TEXT NOT NULL,             -- 'photo' | 'video'
    mime_type       TEXT,                      -- image/jpeg, video/mp4...

    -- 时间信息
    create_time     REAL NOT NULL,             -- EXIF创建时间戳
    modify_time     REAL NOT NULL,             -- 文件修改时间戳
    scan_time       REAL NOT NULL,             -- 扫描入库时间

    -- 媒体属性
    width           INTEGER,                   -- 宽度(像素)
    height          INTEGER,                   -- 高度(像素)
    duration        REAL,                      -- 视频时长(秒)
    orientation     INTEGER DEFAULT 1,         -- EXIF旋转角度

    -- 状态
    is_valid        BOOLEAN DEFAULT 1,         -- 文件是否有效
    is_hidden       BOOLEAN DEFAULT 0,         -- 是否隐藏
    thumbnail_id    INTEGER,                   -- 关联缩略图ID

    -- 扩展信息(JSON存储，避免频繁修改表结构)
    metadata        TEXT,                      -- JSON: camera, location, etc.

    FOREIGN KEY (thumbnail_id) REFERENCES thumbnails(id)
);

-- 索引优化
CREATE INDEX idx_media_create_time ON media_items(create_time);
CREATE INDEX idx_media_type ON media_items(file_type);
CREATE INDEX idx_media_path ON media_items(file_path);
```

#### thumbnails (缩略图表)
```sql
CREATE TABLE thumbnails (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    media_id        INTEGER NOT NULL,         -- 关联媒体ID
    size_type       TEXT NOT NULL,            -- 'small' | 'medium' | 'large'
    file_path       TEXT NOT NULL,            -- 缩略图文件路径
    width           INTEGER NOT NULL,
    height          INTEGER NOT NULL,
    file_size       INTEGER NOT NULL,
    created_at      REAL NOT NULL,

    FOREIGN KEY (media_id) REFERENCES media_items(id) ON DELETE CASCADE,
    UNIQUE(media_id, size_type)
);

CREATE INDEX idx_thumbnails_media ON thumbnails(media_id);
```

#### scan_history (扫描历史表)
```sql
CREATE TABLE scan_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time      REAL NOT NULL,
    end_time        REAL,
    status          TEXT NOT NULL,            -- 'running' | 'completed' | 'failed'
    items_added     INTEGER DEFAULT 0,
    items_updated   INTEGER DEFAULT 0,
    items_deleted   INTEGER DEFAULT 0,
    items_failed    INTEGER DEFAULT 0,
    error_message   TEXT
);

CREATE INDEX idx_scan_time ON scan_history(start_time DESC);
```

#### playlists (播放列表表)
```sql
CREATE TABLE playlists (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    description     TEXT,
    created_at      REAL NOT NULL,
    updated_at      REAL NOT NULL,
    is_auto         BOOLEAN DEFAULT 0         -- 是否自动生成的列表
);

CREATE TABLE playlist_items (
    playlist_id     INTEGER NOT NULL,
    media_id        INTEGER NOT NULL,
    position        INTEGER NOT NULL,

    PRIMARY KEY (playlist_id, media_id),
    FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
    FOREIGN KEY (media_id) REFERENCES media_items(id) ON DELETE CASCADE
);
```

---

## API接口设计

### 基础路径: `/api/v1`

### 媒体相关

```
GET    /media/timeline
       查询参数:
       - start_time: 开始时间戳 (可选)
       - end_time: 结束时间戳 (可选)
       - type: photo|video|all (默认: all)
       - limit: 返回数量 (默认: 50)
       - offset: 偏移量 (默认: 0)
       返回: 时间线排序的媒体列表

GET    /media/:id
       获取单个媒体详情

GET    /media/:id/file
       流式传输媒体文件
       查询参数:
       - download: 是否下载 (默认: false)

GET    /media/:id/thumbnail
       获取缩略图
       查询参数:
       - size: small|medium|large (默认: medium)
```

### 扫描相关

```
POST   /scan/start
       启动扫描任务
       Body: {
         paths: ["/path/to/media1", "/path/to/media2"],  // 扫描路径
         recursive: true,                                  // 是否递归
         generate_thumbnails: true                         // 是否生成缩略图
       }

GET    /scan/status
       获取当前扫描状态

POST   /scan/stop
       停止正在进行的扫描
```

### 播放相关

```
GET    /playlists
       获取所有播放列表

POST   /playlists
       创建播放列表
       Body: {
         name: "我的回忆",
         description: "...",
         media_ids: [1, 2, 3],
         date_range: { start: ..., end: ... }  // 可选：按时间范围
       }

GET    /playlists/:id
       获取播放列表详情

DELETE /playlists/:id
       删除播放列表

GET    /playlists/:id/play
       获取播放列表的流媒体地址
       返回: 可用于video src的m3u8或直接URL列表
```

### 系统相关

```
GET    /stats
       获取统计信息
       返回: {
         total_photos: 1234,
         total_videos: 56,
         total_size_gb: 45.6,
         date_range: { earliest: ..., latest: ... },
         last_scan: "2024-01-01T00:00:00Z"
       }

GET    /config
       获取系统配置

PUT    /config
       更新系统配置
```

---

## 核心功能设计

### 1. 扫描服务 (Scanner)

**职责**: 遍历指定目录，提取媒体信息并入库

**核心流程**:
```
1. 开始扫描 → 创建 scan_history 记录
2. 遍历目录 → 过滤支持的文件类型
3. 提取元数据:
   - 图片: PIL + Pillow 读取 EXIF
   - 视频: ffprobe (ffmpeg) 获取信息
4. 计算时间戳:
   优先级: EXIF DateTimeOriginal > 文件创建时间 > 文件修改时间
5. 数据库操作:
   - 新文件: INSERT
   - 已存在且更新: UPDATE
   - 数据库有但文件不存在: 标记删除
6. 触发缩略图生成任务
```

**文件类型支持**:
```
图片: .jpg, .jpeg, .png, .gif, .webp, .bmp, .heic
视频: .mp4, .mov, .avi, .mkv, .webm, .flv
```

**优化点**:
- 使用文件哈希(前8字节)快速判断是否修改
- 扫描时更新进度到数据库，支持断点续扫
- 支持增量扫描(只检查修改时间之后的文件)

### 2. 缩略图服务 (ThumbnailService)

**职责**: 后台生成和管理缩略图

**尺寸规范**:
| 尺寸类型 | 分辨率 | 用途 |
|---------|--------|------|
| small | 200x200 | 列表视图 |
| medium | 600x600 | 详情预览 |
| large | 1920x1080 | 全屏预览 |

**生成策略**:
```
1. 图片: PIL resize + 保持纵横比 + 居中裁剪
2. 视频: ffmpeg 截取第1帧或中间帧
3. 存储到 cache/thumbnails/{size_type}/{media_id}.jpg
4. 记录到 thumbnails 表
5. LRU清理: 限制总缓存大小(如10GB)
```

### 3. Web播放器 (Player)

**核心功能**:
- **时间线视图**: 按日期分组展示(年/月/日)
- **幻灯片模式**: 自动播放，可配置间隔
- **视频支持**: HLS流式播放大文件
- **响应式设计**: 适配各种屏幕尺寸

**兼容性策略**:
```javascript
// 特性检测
const supports = {
  template: !!document.createElement('template').content,
  picture: !!window.HTMLPictureElement,
  webrtc: !!RTCPeerConnection,
  hls: Hls.isSupported()  // HLS.js for old browsers
};

// 根据能力降级
if (!supports.hls && videoType === 'video/mp4') {
  // 直接播放
} else if (supports.hls) {
  // 使用HLS
}
```

---

## 目录结构

```
HowTimeFly/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI入口
│   ├── api/                    # API路由
│   │   ├── __init__.py
│   │   ├── media.py
│   │   ├── scan.py
│   │   ├── playlist.py
│   │   └── system.py
│   ├── core/                   # 核心业务逻辑
│   │   ├── __init__.py
│   │   ├── scanner.py          # 扫描服务
│   │   ├── thumbnail.py        # 缩略图服务
│   │   └── database.py         # 数据库操作
│   ├── models/                 # 数据模型
│   │   ├── __init__.py
│   │   └── schemas.py          # Pydantic模型
│   └── utils/                  # 工具函数
│       ├── __init__.py
│       ├── exif.py             # EXIF提取
│       └── video.py            # 视频处理
├── frontend/                   # 前端资源
│   ├── index.html
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── img/
│   └── dist/                   # 构建输出(如果使用构建工具)
├── data/                       # 数据目录
│   ├── database.db             # SQLite数据库
│   ├── thumbnails/             # 缩略图缓存
│   │   ├── small/
│   │   ├── medium/
│   │   └── large/
│   └── logs/                   # 日志文件
├── tests/                      # 测试
├── docs/                       # 文档
├── requirements.txt            # Python依赖
├── config.yaml                 # 配置文件
└── run.py                      # 启动脚本
```

---

## 配置文件 (config.yaml)

```yaml
# 服务器配置
server:
  host: "0.0.0.0"
  port: 8080
  debug: false

# 数据库配置
database:
  path: "./data/database.db"

# 扫描配置
scanner:
  paths:
    - "/mnt/media/photos"
    - "/mnt/media/videos"
  recursive: true
  interval_hours: 24  # 定时扫描间隔
  file_types:
    photo:
      - ".jpg"
      - ".jpeg"
      - ".png"
      - ".gif"
      - ".webp"
      - ".heic"
    video:
      - ".mp4"
      - ".mov"
      - ".avi"
      - ".mkv"
      - ".webm"

# 缩略图配置
thumbnails:
  enabled: true
  concurrent_workers: 4
  cache_size_gb: 10
  sizes:
    small: 200
    medium: 600
    large: 1920

# 播放器配置
player:
  slideshow_interval: 5    # 秒
  video_streaming: true    # 是否启用流式传输
  preload_count: 3         # 预加载数量

# 日志配置
logging:
  level: "INFO"
  file: "./data/logs/app.log"
  max_size_mb: 100
  backup_count: 5
```

---

## 性能优化策略

### 1. 数据库优化
- **时间索引**: create_time字段建立索引
- **分页查询**: 使用LIMIT + OFFSET，前端虚拟滚动
- **连接池**: 使用SQLAlchemy连接池

### 2. 缓存策略
- **缩略图缓存**: 磁盘缓存 + HTTP缓存头
- **API响应**: Redis缓存热点数据(可选)
- **浏览器缓存**: 设置合理的Cache-Control

### 3. 流式传输
- **视频**: 使用Range请求支持分段加载
- **HLS转换**: 大视频自动转码为m3u8(可选)

### 4. 懒加载
- **图片**: IntersectionObserver监听可视区域
- **预加载**: 提前加载相邻几项

---

## 部署方案

### 开发环境
```bash
# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python -m app.init_db

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

### 生产环境

#### 方案1: systemd服务
```ini
# /etc/systemd/system/howtimefly.service
[Unit]
Description=HowTimeFly Media Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/HowTimeFly
ExecStart=/opt/HowTimeFly/venv/bin/gunicorn \
    -w 4 -k uvicorn.workers.UvicornWorker \
    -b 0.0.0.0:8080 app.main:app
Restart=always

[Install]
WantedBy=multi-user.target
```

#### 方案2: Docker容器
```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    ffmpeg libexif-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8080

CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8080", "app.main:app"]
```

---

## 后续扩展方向

1. **人脸识别**: 自动识别并按人物分组
2. **地点聚合**: 从EXIF提取GPS，按地点展示
3. **AI分类**: 自动分类(风景、人像、美食等)
4. **移动端适配**: 响应式设计或独立App
5. **分享功能**: 生成分享链接
6. **备份同步**: 与云存储同步
7. **多用户支持**: 用户隔离和权限管理

---

## 技术依赖

```
# 后端核心
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
alembic==1.13.1

# 数据处理
pillow==10.2.0
piexif==1.1.3
python-magic==0.4.27

# 视频处理
ffmpeg-python==0.2.0

# 工具库
pyyaml==6.0.1
python-dotenv==1.0.1
aiofiles==23.2.1

# 前端(开发时)
hls.js==1.4.12  # CDN引入
```
