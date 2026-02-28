"""
HowTimeFly - Web 服务主入口
"""
import os
import time
import yaml
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Query

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session

from app.database import init_database, get_database, get_session
from app.models import (
    MediaItem, Thumbnail, ScanHistory,
    MediaItemResponse, TimelineResponse, StatsResponse,
    ScanStartRequest, ScanStatusResponse, UpdateDateRequest,
    BatchUpdateDateRequest, PendingMediaResponse
)
from app.scanner import scan_media


# ==================== 配置加载 ====================

def load_config(config_path: str = "config.yaml") -> dict:
    """加载配置文件"""
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


# ==================== FastAPI 应用 ====================

# 加载配置
config = load_config()

# 初始化数据库
db_config = config.get("database", {"path": "./data/database.db"})
db = init_database(db_config["path"])

# 创建 FastAPI 应用
app = FastAPI(
    title="HowTimeFly",
    description="时间线媒体播放系统",
    version="0.1.0"
)

# ==================== 静态文件服务 ====================

# 创建静态文件目录
static_dir = Path(__file__).parent.parent / "static"
static_dir.mkdir(exist_ok=True)
music_dir = static_dir / "music"
music_dir.mkdir(exist_ok=True)

# 挂载静态文件
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# ==================== 依赖项 ====================

def get_db():
    """获取数据库会话"""
    session = get_session()
    try:
        yield session
    finally:
        session.close()


# ==================== API 路由 ====================

@app.get("/", response_class=HTMLResponse)
async def index():
    """主页"""
    html_path = Path(__file__).parent.parent / "frontend" / "index.html"
    if html_path.exists():
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>HowTimeFly</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            h1 { color: #333; }
            .info { background: #f0f0f0; padding: 20px; border-radius: 8px; }
            .api-list { margin-top: 20px; }
            .api-list li { margin: 5px 0; }
            code { background: #e0e0e0; padding: 2px 6px; border-radius: 4px; }
        </style>
    </head>
    <body>
        <h1>🎬 HowTimeFly</h1>
        <div class="info">
            <p>时间线媒体播放系统正在运行...</p>
            <p>请访问 <a href="/docs">API 文档</a> 查看可用接口</p>
        </div>
        <div class="api-list">
            <h3>快速开始:</h3>
            <ol>
                <li>将照片/视频放入配置的扫描目录</li>
                <li>访问 <code>POST /api/v1/scan/start</code> 开始扫描</li>
                <li>访问 <code>GET /api/v1/media/timeline</code> 查看时间线</li>
            </ol>
        </div>
    </body>
    </html>
    """)


@app.get("/api/v1/stats", response_model=StatsResponse)
async def get_stats(db: Session = Depends(get_db)):
    """获取统计信息"""
    # 统计照片和视频数量
    photo_count = db.query(MediaItem).filter_by(file_type="photo", is_valid=True).count()
    video_count = db.query(MediaItem).filter_by(file_type="video", is_valid=True).count()

    # 计算总大小
    from sqlalchemy import func
    total_size = db.query(func.sum(MediaItem.file_size)).filter(
        MediaItem.is_valid == True
    ).scalar() or 0

    # 获取时间范围
    from sqlalchemy import func
    time_range = db.query(
        func.min(MediaItem.create_time).label("min"),
        func.max(MediaItem.create_time).label("max")
    ).filter(MediaItem.is_valid == True).first()

    # 获取最后扫描时间
    last_scan = db.query(ScanHistory).order_by(
        ScanHistory.start_time.desc()
    ).first()

    return StatsResponse(
        total_photos=photo_count,
        total_videos=video_count,
        total_size_mb=total_size / 1024 / 1024,
        date_range={
            "earliest": time_range.min or 0,
            "latest": time_range.max or 0,
        },
        last_scan_time=last_scan.start_time if last_scan else None
    )


@app.get("/api/v1/media/timeline", response_model=TimelineResponse)
async def get_timeline(
    start_time: Optional[float] = Query(None, description="开始时间戳"),
    end_time: Optional[float] = Query(None, description="结束时间戳"),
    file_type: Optional[str] = Query("all", description="文件类型: photo/video/all"),
    sort: str = Query("desc", description="排序方式: asc(正序/早→晚)/desc(倒序/晚→早)"),
    limit: int = Query(50, ge=1, le=500, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: Session = Depends(get_db)
):
    """获取时间线媒体列表"""
    query = db.query(MediaItem).filter(
        MediaItem.is_valid == True,
        MediaItem.pending_date == False  # 只返回有日期的文件
    )

    # 时间范围过滤
    if start_time is not None:
        query = query.filter(MediaItem.create_time >= start_time)
    if end_time is not None:
        query = query.filter(MediaItem.create_time <= end_time)

    # 类型过滤
    if file_type in ("photo", "video"):
        query = query.filter(MediaItem.file_type == file_type)

    # 排序和分页
    if sort == "asc":
        query = query.order_by(MediaItem.create_time.asc())
    else:
        query = query.order_by(MediaItem.create_time.desc())

    # 先获取项目
    items = query.offset(offset).limit(limit).all()

    # 然后获取总数（使用单独的查询）
    from sqlalchemy import func
    base_query = db.query(MediaItem).filter(
        MediaItem.is_valid == True,
        MediaItem.pending_date == False
    )
    if start_time is not None:
        base_query = base_query.filter(MediaItem.create_time >= start_time)
    if end_time is not None:
        base_query = base_query.filter(MediaItem.create_time <= end_time)
    if file_type in ("photo", "video"):
        base_query = base_query.filter(MediaItem.file_type == file_type)
    total = base_query.count()

    # 构建响应
    result_items = []
    for item in items:
        # 获取缩略图URL
        thumb = db.query(Thumbnail).filter_by(media_id=item.id, size_type="medium").first()
        thumbnail_url = f"/api/v1/media/{item.id}/thumbnail?size=medium" if thumb else None

        result_items.append(MediaItemResponse(
            id=item.id,
            file_name=item.file_name,
            file_type=item.file_type,
            create_time=item.create_time,
            width=item.width,
            height=item.height,
            duration=item.duration,
            thumbnail_url=thumbnail_url,
            file_url=f"/api/v1/media/{item.id}/file"
        ))

    return TimelineResponse(
        items=result_items,
        total=total,
        has_more=offset + len(items) < total
    )


@app.get("/api/v1/media/pending", response_model=TimelineResponse)
async def get_pending_media(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """获取待设置日期的媒体列表"""
    query = db.query(MediaItem).filter(MediaItem.pending_date == True)

    total = query.count()
    items = query.order_by(MediaItem.modify_time.desc()).offset(offset).limit(limit).all()

    result_items = []
    for item in items:
        thumb = db.query(Thumbnail).filter_by(media_id=item.id, size_type="medium").first()
        thumbnail_url = f"/api/v1/media/{item.id}/thumbnail?size=medium" if thumb else None

        result_items.append(PendingMediaResponse(
            id=item.id,
            file_name=item.file_name,
            file_type=item.file_type,
            file_path=item.file_path,
            file_size=item.file_size,
            width=item.width,
            height=item.height,
            create_time=item.create_time,
            thumbnail_url=thumbnail_url,
            file_url=f"/api/v1/media/{item.id}/file"
        ))

    return TimelineResponse(
        items=result_items,
        total=total,
        has_more=offset + len(items) < total
    )


@app.get("/api/v1/media/{media_id}", response_model=MediaItemResponse)
async def get_media(media_id: int, db: Session = Depends(get_db)):
    """获取单个媒体详情"""
    item = db.query(MediaItem).filter_by(id=media_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="媒体不存在")

    thumb = db.query(Thumbnail).filter_by(media_id=item.id, size_type="medium").first()
    thumbnail_url = f"/api/v1/media/{item.id}/thumbnail?size=medium" if thumb else None

    return MediaItemResponse(
        id=item.id,
        file_name=item.file_name,
        file_type=item.file_type,
        create_time=item.create_time,
        width=item.width,
        height=item.height,
        duration=item.duration,
        thumbnail_url=thumbnail_url,
        file_url=f"/api/v1/media/{item.id}/file"
    )


@app.get("/api/v1/media/{media_id}/file")
async def get_media_file(media_id: int, db: Session = Depends(get_db)):
    """获取媒体文件"""
    item = db.query(MediaItem).filter_by(id=media_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="媒体不存在")

    if not os.path.exists(item.file_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    # 获取 MIME 类型
    mime_type = item.mime_type or "application/octet-stream"

    return FileResponse(
        item.file_path,
        media_type=mime_type,
        filename=item.file_name
    )


@app.get("/api/v1/media/{media_id}/thumbnail")
async def get_thumbnail(
    media_id: int,
    size: str = Query("medium", description="缩略图尺寸: small/medium/large"),
    db: Session = Depends(get_db)
):
    """获取缩略图"""
    thumb = db.query(Thumbnail).filter_by(media_id=media_id, size_type=size).first()

    if not thumb or not os.path.exists(thumb.file_path):
        # 返回默认占位图
        return HTMLResponse(content="""
        <svg xmlns="http://www.w3.org/2000/svg" width="200" height="200">
            <rect width="200" height="200" fill="#ccc"/>
            <text x="100" y="100" text-anchor="middle" dominant-baseline="middle" font-size="14">No Thumbnail</text>
        </svg>
        """, media_type="image/svg+xml")

    return FileResponse(thumb.file_path, media_type="image/jpeg")


@app.put("/api/v1/media/{media_id}/date")
async def update_media_date(
    media_id: int,
    request: UpdateDateRequest,
    db: Session = Depends(get_db)
):
    """手动设置媒体的拍摄日期"""
    item = db.query(MediaItem).filter_by(id=media_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="媒体不存在")

    # 更新拍摄时间
    item.create_time = request.create_time
    item.pending_date = False  # 清除待处理标记
    item.scan_time = time.time()
    db.commit()

    return {
        "id": item.id,
        "file_name": item.file_name,
        "create_time": item.create_time,
        "create_date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(item.create_time))
    }


@app.put("/api/v1/media/batch-date")
async def batch_update_date(
    request: BatchUpdateDateRequest,
    db: Session = Depends(get_db)
):
    """批量设置媒体拍摄日期"""
    items = db.query(MediaItem).filter(MediaItem.id.in_(request.item_ids)).all()

    updated_count = 0
    for item in items:
        item.create_time = request.create_time
        item.pending_date = False  # 清除待处理标记
        item.scan_time = time.time()
        updated_count += 1

    db.commit()

    return {
        "updated_count": updated_count,
        "create_date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(request.create_time))
    }


@app.post("/api/v1/scan/start", response_model=ScanStatusResponse)
async def start_scan(request: ScanStartRequest, db: Session = Depends(get_db)):
    """开始扫描"""
    # 检查是否有正在运行的扫描
    running_scan = db.query(ScanHistory).filter_by(status="running").first()
    if running_scan:
        return ScanStatusResponse(
            is_running=True,
            current_scan_id=running_scan.id,
            status="已有扫描任务正在运行",
            progress={"total": 0, "processed": 0}
        )

    # 获取扫描路径
    paths = request.paths or config.get("scanner", {}).get("paths", ["./test_media"])

    # 在后台执行扫描
    import threading
    def scan_task():
        try:
            scan_media(get_session(), paths, request.recursive)
        except Exception as e:
            print(f"扫描失败: {e}")

    thread = threading.Thread(target=scan_task, daemon=True)
    thread.start()

    return ScanStatusResponse(
        is_running=True,
        status="扫描任务已启动",
        progress={"total": 0, "processed": 0}
    )


@app.get("/api/v1/scan/status", response_model=ScanStatusResponse)
async def get_scan_status(db: Session = Depends(get_db)):
    """获取扫描状态"""
    running_scan = db.query(ScanHistory).filter_by(status="running").first()

    if running_scan:
        return ScanStatusResponse(
            is_running=True,
            current_scan_id=running_scan.id,
            status="扫描中...",
            progress={"total": 0, "processed": 0}
        )

    # 获取最后一次扫描
    last_scan = db.query(ScanHistory).order_by(
        ScanHistory.start_time.desc()
    ).first()

    if last_scan:
        return ScanStatusResponse(
            is_running=False,
            current_scan_id=last_scan.id,
            status=f"上次扫描: {last_scan.status}",
            progress={
                "total": last_scan.items_added + last_scan.items_updated,
                "processed": last_scan.items_added + last_scan.items_updated,
                "added": last_scan.items_added,
                "updated": last_scan.items_updated,
            }
        )

    return ScanStatusResponse(
        is_running=False,
        status="尚未进行扫描",
        progress=None
    )


# ==================== 启动服务器 ====================

def run_server():
    """启动服务器"""
    import uvicorn

    server_config = config.get("server", {})
    host = server_config.get("host", "127.0.0.1")
    port = server_config.get("port", 8080)
    reload = server_config.get("reload", False)
    debug = server_config.get("debug", False)

    print(f"""
    ╔═══════════════════════════════════════════════════════╗
    ║           HowTimeFly - 时间线媒体播放系统               ║
    ╠═══════════════════════════════════════════════════════╣
    ║  服务地址: http://{host}:{port}                       ║
    ║  API 文档: http://{host}:{port}/docs                  ║
    ╚═══════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="debug" if debug else "info"
    )


if __name__ == "__main__":
    run_server()
