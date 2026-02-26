"""
缩略图生成服务
"""
import os
import time
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from PIL import Image
from sqlalchemy.orm import Session

from app.models import MediaItem, Thumbnail


@dataclass
class ThumbnailConfig:
    """缩略图配置"""
    enabled: bool = True
    output_dir: str = "./data/thumbnails"
    sizes: dict[str, int] = None

    def __post_init__(self):
        if self.sizes is None:
            self.sizes = {
                "small": 200,
                "medium": 600,
                "large": 1200,
            }


class ThumbnailService:
    """缩略图服务"""

    def __init__(self, session: Session, config: ThumbnailConfig):
        """初始化缩略图服务

        Args:
            session: 数据库会话
            config: 缩略图配置
        """
        self.session = session
        self.config = config

        # 确保输出目录存在
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)
        for size_type in self.config.sizes:
            Path(self.config.output_dir, size_type).mkdir(parents=True, exist_ok=True)

    def generate_for_media(self, media_id: int) -> list[Thumbnail]:
        """为指定媒体生成所有尺寸的缩略图

        Args:
            media_id: 媒体ID

        Returns:
            list[Thumbnail]: 生成的缩略图记录列表
        """
        media = self.session.query(MediaItem).get(media_id)
        if not media:
            raise ValueError(f"媒体不存在: {media_id}")

        if media.file_type != "photo":
            # 目前只支持图片缩略图
            print(f"[SKIP] Non-image media: {media.file_name}")
            return []

        thumbnails = []

        for size_type, size in self.config.sizes.items():
            try:
                thumb = self._generate_one(media, size_type, size)
                if thumb:
                    thumbnails.append(thumb)
            except Exception as e:
                print(f"[FAIL] Thumbnail failed {media.file_name} [{size_type}]: {e}")

        return thumbnails

    def _generate_one(self, media: MediaItem, size_type: str, size: int) -> Optional[Thumbnail]:
        """生成单个缩略图

        Args:
            media: 媒体对象
            size_type: 尺寸类型
            size: 目标尺寸

        Returns:
            Thumbnail: 缩略图记录
        """
        # 检查是否已存在
        existing = self.session.query(Thumbnail).filter_by(
            media_id=media.id,
            size_type=size_type
        ).first()

        if existing:
            # 检查文件是否存在
            if os.path.exists(existing.file_path):
                return existing
            else:
                self.session.delete(existing)

        # 生成缩略图文件
        thumb_filename = f"{media.id}_{size_type}.jpg"
        thumb_path = os.path.join(self.config.output_dir, size_type, thumb_filename)

        # 打开并处理图片
        with Image.open(media.file_path) as img:
            # 处理 EXIF 旋转
            from PIL import ImageOps
            img = ImageOps.exif_transpose(img)

            # 计算缩略图尺寸（保持纵横比）
            img.thumbnail((size, size), Image.Resampling.LANCZOS)

            # 保存为 JPEG
            img.save(thumb_path, "JPEG", quality=85, optimize=True)

        # 获取文件信息
        file_size = os.path.getsize(thumb_path)

        # 创建数据库记录
        thumb = Thumbnail(
            media_id=media.id,
            size_type=size_type,
            file_path=thumb_path,
            width=img.width,
            height=img.height,
            file_size=file_size,
            created_at=time.time()
        )
        self.session.add(thumb)
        self.session.commit()

        print(f"[OK] Thumbnail: {media.file_name} [{size_type}] -> {thumb_path}")
        return thumb

    def get_thumbnail_path(self, media_id: int, size_type: str = "medium") -> Optional[str]:
        """获取缩略图路径

        Args:
            media_id: 媒体ID
            size_type: 尺寸类型

        Returns:
            str: 缩略图文件路径，如果不存在返回 None
        """
        thumb = self.session.query(Thumbnail).filter_by(
            media_id=media_id,
            size_type=size_type
        ).first()

        if thumb and os.path.exists(thumb.file_path):
            return thumb.file_path

        return None

    def generate_all_pending(self, limit: Optional[int] = None) -> dict:
        """为所有没有缩略图的图片生成缩略图

        Args:
            limit: 限制生成的数量

        Returns:
            dict: 生成统计
        """
        # 查找没有缩略图的图片
        query = self.session.query(MediaItem).filter(
            MediaItem.file_type == "photo",
            MediaItem.is_valid == True
        )

        if limit:
            query = query.limit(limit)

        media_items = query.all()

        stats = {
            "total": len(media_items),
            "success": 0,
            "failed": 0,
        }

        for media in media_items:
            try:
                self.generate_for_media(media.id)
                stats["success"] += 1
            except Exception as e:
                print(f"[FAIL] Thumbnail failed {media.file_name}: {e}")
                stats["failed"] += 1

        return stats
