"""
EXIF 信息提取工具
"""
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image, ExifTags
import piexif


class ExifExtractor:
    """EXIF 信息提取器"""

    # EXIF 标签到名称的映射
    DATETIME_TAGS = [
        "DateTimeOriginal",
        "DateTime",
        "DateTimeDigitized",
    ]

    @staticmethod
    def get_image_info(file_path: str) -> dict:
        """获取图片信息

        Args:
            file_path: 图片文件路径

        Returns:
            dict: 包含 width, height, create_time, orientation 等信息
        """
        result = {
            "width": None,
            "height": None,
            "create_time": None,
            "orientation": 1,
            "mime_type": None,
        }

        try:
            # 使用 PIL 打开图片
            with Image.open(file_path) as img:
                result["width"] = img.width
                result["height"] = img.height
                result["mime_type"] = f"image/{img.format.lower()}" if img.format else None

                # 获取 EXIF 信息
                exif_data = img._getexif()
                if exif_data:
                    # 构建可读的 EXIF 字典
                    exif = {
                        ExifTags.TAGS.get(tag, tag): value
                        for tag, value in exif_data.items()
                        if tag in ExifTags.TAGS
                    }

                    # 提取方向
                    result["orientation"] = exif.get("Orientation", 1)

                    # 提取创建时间
                    for tag in ExifExtractor.DATETIME_TAGS:
                        if tag in exif:
                            dt_str = exif[tag]
                            # 格式: "YYYY:MM:DD HH:MM:SS"
                            try:
                                dt = datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
                                result["create_time"] = dt.timestamp()
                                break
                            except (ValueError, TypeError):
                                continue

        except Exception as e:
            print(f"[WARN] EXIF read failed {file_path}: {e}")

        return result

    @staticmethod
    def get_video_info(file_path: str) -> dict:
        """获取视频信息

        Args:
            file_path: 视频文件路径

        Returns:
            dict: 包含 width, height, duration, create_time 等信息
        """
        result = {
            "width": None,
            "height": None,
            "duration": None,
            "create_time": None,
            "mime_type": None,
        }

        # 根据扩展名猜测 MIME 类型
        ext = Path(file_path).suffix.lower()
        mime_map = {
            ".mp4": "video/mp4",
            ".mov": "video/quicktime",
            ".avi": "video/x-msvideo",
            ".mkv": "video/x-matroska",
            ".webm": "video/webm",
        }
        result["mime_type"] = mime_map.get(ext)

        # 尝试使用 ffmpeg 提取视频元数据
        try:
            import ffmpeg
            probe = ffmpeg.probe(file_path)

            # 获取视频流信息
            video_stream = None
            for stream in probe.get("streams", []):
                if stream.get("codec_type") == "video":
                    video_stream = stream
                    break

            if video_stream:
                result["width"] = int(video_stream.get("width"))
                result["height"] = int(video_stream.get("height"))

            # 获取时长
            format_info = probe.get("format", {})
            duration = format_info.get("duration")
            if duration:
                result["duration"] = float(duration)

            # 获取创建时间 (优先级最高)
            # 尝试多个可能的时间字段
            creation_time = (
                video_stream.get("tags", {}).get("creation_time") if video_stream else None
            ) or format_info.get("tags", {}).get("creation_time")

            if creation_time:
                try:
                    # ISO 8601 格式: "2024-01-15T10:30:00.000000Z"
                    dt = datetime.fromisoformat(creation_time.replace("Z", "+00:00"))
                    result["create_time"] = dt.timestamp()
                except (ValueError, TypeError) as e:
                    print(f"[WARN] Failed to parse video creation time: {e}")

        except ImportError:
            # ffmpeg-python 未安装，静默跳过
            pass
        except Exception as e:
            print(f"[WARN] ffmpeg probe failed for {file_path}: {e}")

        return result

    @staticmethod
    def get_media_info(file_path: str) -> dict:
        """获取媒体文件信息（自动判断类型）

        Args:
            file_path: 媒体文件路径

        Returns:
            dict: 媒体信息
        """
        ext = Path(file_path).suffix.lower()

        photo_exts = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".heic"}
        video_exts = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv"}

        if ext in photo_exts:
            info = ExifExtractor.get_image_info(file_path)
            info["file_type"] = "photo"
            return info
        elif ext in video_exts:
            info = ExifExtractor.get_video_info(file_path)
            info["file_type"] = "video"
            return info
        else:
            return {"file_type": "unknown"}

    @staticmethod
    def get_create_time(file_path: str, media_info: dict | None = None, require_exif: bool = False) -> float | None:
        """获取媒体文件的创建时间

        优先级: EXIF DateTimeOriginal > 文件创建时间 > 文件修改时间

        Args:
            file_path: 文件路径
            media_info: 已提取的媒体信息
            require_exif: 是否要求必须有EXIF时间（True时没有EXIF返回None）

        Returns:
            float | None: Unix 时间戳，如果 require_exif=True 且无EXIF则返回 None
        """
        # 1. 优先使用 EXIF 时间
        if media_info and media_info.get("create_time"):
            return media_info["create_time"]

        # 2. 如果要求必须有EXIF时间，返回None
        if require_exif:
            return None

        # 3. 使用文件系统时间（降级方案）
        stat = os.stat(file_path)
        # Windows: st_ctime 是创建时间
        # Linux: st_ctime 是状态改变时间，st_mtime 是修改时间
        # 这里统一用 st_mtime 作为备选
        return stat.st_mtime
