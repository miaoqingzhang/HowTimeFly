"""
数据模型定义
"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session

Base = declarative_base()


# ==================== SQLAlchemy 表模型 ====================

class MediaItem(Base):
    """媒体文件表"""
    __tablename__ = "media_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_path = Column(String(512), nullable=False, unique=True, index=True)
    file_name = Column(String(256), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(16), nullable=False, index=True)  # 'photo' | 'video'
    mime_type = Column(String(64))

    # 时间信息
    create_time = Column(Float, nullable=False, index=True)  # EXIF创建时间戳
    modify_time = Column(Float, nullable=False)
    scan_time = Column(Float, nullable=False)

    # 媒体属性
    width = Column(Integer)
    height = Column(Integer)
    duration = Column(Float)  # 视频时长(秒)
    orientation = Column(Integer, default=1)

    # 状态
    is_valid = Column(Boolean, default=True)
    is_hidden = Column(Boolean, default=False)
    thumbnail_id = Column(Integer, ForeignKey("thumbnails.id"))
    pending_date = Column(Boolean, default=False)  # 标记是否需要手动设置日期

    # 扩展信息 (exif_data: JSON格式存储相机、地点等信息)
    exif_data = Column(Text)

    def to_dict(self):
        return {
            "id": self.id,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "mime_type": self.mime_type,
            "create_time": self.create_time,
            "modify_time": self.modify_time,
            "scan_time": self.scan_time,
            "width": self.width,
            "height": self.height,
            "duration": self.duration,
            "orientation": self.orientation,
            "is_valid": self.is_valid,
            "is_hidden": self.is_hidden,
            "thumbnail_id": self.thumbnail_id,
        }


class Thumbnail(Base):
    """缩略图表"""
    __tablename__ = "thumbnails"

    id = Column(Integer, primary_key=True, autoincrement=True)
    media_id = Column(Integer, ForeignKey("media_items.id", ondelete="CASCADE"), nullable=False, index=True)
    size_type = Column(String(16), nullable=False)  # 'small' | 'medium' | 'large'
    file_path = Column(String(512), nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    file_size = Column(Integer, nullable=False)
    created_at = Column(Float, nullable=False)

    __table_args__ = (
        # 如果支持UniqueConstraint
        # UniqueConstraint('media_id', 'size_type', name='uq_media_size'),
    )


class ScanHistory(Base):
    """扫描历史表"""
    __tablename__ = "scan_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    start_time = Column(Float, nullable=False, index=True)
    end_time = Column(Float)
    status = Column(String(16), nullable=False)  # 'running' | 'completed' | 'failed'
    items_added = Column(Integer, default=0)
    items_updated = Column(Integer, default=0)
    items_deleted = Column(Integer, default=0)
    items_failed = Column(Integer, default=0)
    error_message = Column(Text)


# ==================== Pydantic API模型 ====================

class MediaItemResponse(BaseModel):
    id: int
    file_name: str
    file_type: Literal["photo", "video"]
    create_time: float
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None
    thumbnail_url: Optional[str] = None
    file_url: str

    class Config:
        from_attributes = True


class TimelineResponse(BaseModel):
    items: list[MediaItemResponse | PendingMediaResponse]  # Accept both types
    total: int
    has_more: bool


class StatsResponse(BaseModel):
    total_photos: int
    total_videos: int
    total_size_mb: float
    date_range: dict[str, float]
    last_scan_time: Optional[float] = None


class ScanStartRequest(BaseModel):
    paths: list[str] = []
    recursive: bool = True
    generate_thumbnails: bool = True


class ScanStatusResponse(BaseModel):
    is_running: bool
    current_scan_id: Optional[int] = None
    status: str
    progress: Optional[dict] = None


class UpdateDateRequest(BaseModel):
    """更新媒体拍摄日期请求"""
    create_time: float  # Unix 时间戳


class BatchUpdateDateRequest(BaseModel):
    """批量更新日期请求"""
    item_ids: list[int]  # 要更新的媒体ID列表
    create_time: float   # 统一设置的拍摄时间


class PendingMediaResponse(BaseModel):
    """无日期媒体响应"""
    id: int
    file_name: str
    file_type: Literal["photo", "video"]
    file_path: str
    file_size: int
    width: Optional[int] = None
    height: Optional[int] = None
    create_time: Optional[float] = None  # 当前时间（可能是文件时间）
    thumbnail_url: Optional[str] = None
    file_url: str  # 添加 file_url 字段

    class Config:
        from_attributes = True
