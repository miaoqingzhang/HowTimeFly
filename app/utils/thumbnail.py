"""
缩略图生成工具
"""
import os
import time
from pathlib import Path
from typing import Optional

from PIL import Image, ImageOps, ImageDraw
from sqlalchemy.orm import Session

from app.models import Thumbnail, MediaItem

# 尝试导入视频处理库
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

try:
    import ffmpeg
    FFMPEG_PYTHON_AVAILABLE = True
except ImportError:
    FFMPEG_PYTHON_AVAILABLE = False


class ThumbnailGenerator:
    """缩略图生成器"""

    # 缩略图尺寸定义
    SIZES = {
        "small": (150, 150),    # 小缩略图
        "medium": (400, 400),   # 中等缩略图
        "large": (1200, 1200),  # 大缩略图
    }

    def __init__(self, base_dir: str = "./data/thumbnails"):
        """初始化缩略图生成器

        Args:
            base_dir: 缩略图存储基础目录
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_thumbnail_path(self, media_id: int, size_type: str) -> Path:
        """获取缩略图存储路径

        Args:
            media_id: 媒体ID
            size_type: 尺寸类型

        Returns:
            Path: 缩略图文件路径
        """
        # 使用子目录组织: thumbnails/small/123.jpg
        size_dir = self.base_dir / size_type
        size_dir.mkdir(exist_ok=True)
        return size_dir / f"{media_id}.jpg"

    def generate_image_thumbnail(
        self,
        image_path: str,
        output_path: Path,
        size_type: str
    ) -> tuple[int, int, int]:
        """为图片生成缩略图

        Args:
            image_path: 原始图片路径
            output_path: 输出缩略图路径
            size_type: 尺寸类型 (small/medium/large)

        Returns:
            tuple: (width, height, file_size)
        """
        target_size = self.SIZES[size_type]

        try:
            with Image.open(image_path) as img:
                # 使用 ImageOps.exif_transpose 自动处理 EXIF 方向
                # 这个方法会自动检测并应用正确的旋转，避免双重旋转
                try:
                    img = ImageOps.exif_transpose(img)
                except Exception:
                    # 如果 EXIF 处理失败，继续使用原图
                    pass

                # 计算缩放比例，保持宽高比
                img.thumbnail(target_size, Image.Resampling.LANCZOS)

                # 保存缩略图
                img.save(output_path, "JPEG", quality=85, optimize=True)

                # 获取文件大小
                file_size = output_path.stat().st_size

                return img.width, img.height, file_size

        except Exception as e:
            print(f"[WARN] Thumbnail failed {image_path}: {e}")
            # 返回默认占位尺寸
            return target_size[0], target_size[1], 0

    def generate_video_thumbnail(
        self,
        video_path: str,
        output_path: Path,
        size_type: str
    ) -> tuple[int, int, int]:
        """为视频生成缩略图

        Args:
            video_path: 视频文件路径
            output_path: 输出缩略图路径
            size_type: 尺寸类型

        Returns:
            tuple: (width, height, file_size)
        """
        target_size = self.SIZES[size_type]

        # 方法1: 使用 OpenCV (优先，因为它不需要外部命令行工具)
        if OPENCV_AVAILABLE:
            try:
                cap = cv2.VideoCapture(video_path)
                if cap.isOpened():
                    # 读取第一帧
                    ret, frame = cap.read()
                    cap.release()

                    if ret:
                        # 转换 BGR 到 RGB
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        img = Image.fromarray(frame_rgb)

                        # 缩放到目标尺寸
                        img.thumbnail(target_size, Image.Resampling.LANCZOS)
                        img.save(output_path, "JPEG", quality=85, optimize=True)

                        file_size = output_path.stat().st_size
                        return img.width, img.height, file_size
            except Exception as e:
                print(f"[WARN] OpenCV thumbnail failed {video_path}: {e}")

        # 方法2: 使用 ffmpeg-python (需要 ffmpeg 命令行工具)
        if FFMPEG_PYTHON_AVAILABLE:
            try:
                (
                    ffmpeg
                    .input(video_path, ss="0:0:0")  # 从第0秒开始
                    .output(str(output_path), vframes=1, **{
                        "vf": f"scale={target_size[0]}:{target_size[1]}:force_original_aspect_ratio=decrease",
                        "format": "image2",
                    })
                    .overwrite_output()
                    .run(quiet=True)
                )

                # 验证输出文件
                if output_path.exists():
                    with Image.open(output_path) as img:
                        file_size = output_path.stat().st_size
                        return img.width, img.height, file_size
            except Exception as e:
                print(f"[WARN] ffmpeg thumbnail failed {video_path}: {e}")

        # 都失败，创建视频占位图（带播放按钮）
        self._create_placeholder(output_path, target_size[0], target_size[1], is_video=True)
        return target_size[0], target_size[1], output_path.stat().st_size

    def _create_placeholder(self, output_path: Path, width: int, height: int, is_video: bool = False):
        """创建占位图

        Args:
            output_path: 输出路径
            width: 宽度
            height: 高度
            is_video: 是否为视频占位图
        """
        from PIL import ImageDraw, ImageFont

        # 创建背景
        img = Image.new("RGB", (width, height), color="#3a3a3a")
        draw = ImageDraw.Draw(img)

        if is_video:
            # 绘制播放按钮（三角形）
            margin = min(width, height) // 4
            play_box = (
                margin, margin,
                width - margin, height - margin
            )

            # 播放按钮三角形
            triangle_points = [
                (play_box[0] + play_box[2] * 0.35, play_box[1]),  # 左上
                (play_box[0] + play_box[2] * 0.35, play_box[3]),  # 左下
                (play_box[2], (play_box[1] + play_box[3]) / 2),    # 右中
            ]
            draw.polygon(triangle_points, fill="#ffffff")

            # 边框
            draw.rectangle(play_box, outline="#666666", width=2)

        img.save(output_path, "JPEG", quality=85)

    def _get_orientation(self, img: Image.Image) -> int:
        """获取图片方向

        Args:
            img: PIL Image 对象

        Returns:
            int: 方向值 (1-8)
        """
        try:
            exif = img._getexif()
            if exif:
                orientation_key = None
                # 查找 Orientation 标签
                for tag, value in exif.items():
                    if tag in ExifTags.TAGS and ExifTags.TAGS[tag] == "Orientation":
                        return value
        except Exception:
            pass
        return 1  # 默认方向

    def _apply_orientation(self, img: Image.Image, orientation: int) -> Image.Image:
        """应用图片方向旋转

        Args:
            img: PIL Image 对象
            orientation: 方向值

        Returns:
            Image: 旋转后的图片
        """
        # EXIF 方向值对应的旋转操作
        orientation_ops = {
            1: lambda x: x,  # 正常
            2: lambda x: x.transpose(Image.FLIP_LEFT_RIGHT),
            3: lambda x: x.rotate(180),
            4: lambda x: x.rotate(180).transpose(Image.FLIP_LEFT_RIGHT),
            5: lambda x: x.rotate(-90, expand=True).transpose(Image.FLIP_LEFT_RIGHT),
            6: lambda x: x.rotate(-90, expand=True),
            7: lambda x: x.rotate(90, expand=True).transpose(Image.FLIP_LEFT_RIGHT),
            8: lambda x: x.rotate(90, expand=True),
        }

        op = orientation_ops.get(orientation, lambda x: x)
        return op(img)

    def generate_for_media(
        self,
        session: Session,
        media: MediaItem,
        sizes: list[str] = None
    ) -> list[Thumbnail]:
        """为媒体文件生成所有尺寸的缩略图

        Args:
            session: 数据库会话
            media: 媒体对象
            sizes: 要生成的尺寸列表，默认生成全部

        Returns:
            list: 生成的缩略图对象列表
        """
        if sizes is None:
            sizes = ["small", "medium", "large"]

        thumbnails = []

        for size_type in sizes:
            # 检查是否已存在
            existing = session.query(Thumbnail).filter_by(
                media_id=media.id,
                size_type=size_type
            ).first()

            if existing:
                # 检查文件是否存在
                if Path(existing.file_path).exists():
                    thumbnails.append(existing)
                    continue
                else:
                    # 文件不存在，删除记录重新生成
                    session.delete(existing)
                    session.commit()

            # 生成新缩略图
            output_path = self._get_thumbnail_path(media.id, size_type)

            if media.file_type == "photo":
                width, height, file_size = self.generate_image_thumbnail(
                    media.file_path,
                    output_path,
                    size_type
                )
            elif media.file_type == "video":
                width, height, file_size = self.generate_video_thumbnail(
                    media.file_path,
                    output_path,
                    size_type
                )
            else:
                continue

            # 保存到数据库
            thumbnail = Thumbnail(
                media_id=media.id,
                size_type=size_type,
                file_path=str(output_path.absolute()),
                width=width,
                height=height,
                file_size=file_size,
                created_at=time.time()
            )
            session.add(thumbnail)
            thumbnails.append(thumbnail)

        session.commit()
        return thumbnails


# ==================== 便捷函数 ====================

def generate_thumbnails_for_media(
    session: Session,
    media: MediaItem,
    sizes: list[str] = None
) -> list[Thumbnail]:
    """为媒体文件生成缩略图

    Args:
        session: 数据库会话
        media: 媒体对象
        sizes: 要生成的尺寸列表

    Returns:
        list: 生成的缩略图对象列表
    """
    generator = ThumbnailGenerator()
    return generator.generate_for_media(session, media, sizes)


def ensure_thumbnails_exist(
    session: Session,
    media: MediaItem,
    size_type: str = "medium"
) -> Optional[Thumbnail]:
    """确保指定尺寸的缩略图存在，不存在则生成

    Args:
        session: 数据库会话
        media: 媒体对象
        size_type: 尺寸类型

    Returns:
        Thumbnail: 缩略图对象，如果生成失败返回 None
    """
    # 先检查是否已存在
    thumb = session.query(Thumbnail).filter_by(
        media_id=media.id,
        size_type=size_type
    ).first()

    if thumb and Path(thumb.file_path).exists():
        return thumb

    # 不存在，生成
    generator = ThumbnailGenerator()
    thumbnails = generator.generate_for_media(session, media, [size_type])

    return thumbnails[0] if thumbnails else None
