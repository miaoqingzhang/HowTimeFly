"""
文件扫描器 - 扫描目录并提取媒体信息
"""
import os
import time
from pathlib import Path
from typing import Generator, Optional
from dataclasses import dataclass

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import MediaItem, ScanHistory
from app.utils.exif import ExifExtractor
from app.utils.thumbnail import ensure_thumbnails_exist


@dataclass
class ScanProgress:
    """扫描进度"""
    total_files: int = 0
    processed_files: int = 0
    added_files: int = 0
    updated_files: int = 0
    deleted_files: int = 0
    failed_files: int = 0
    current_path: str = ""


class MediaScanner:
    """媒体文件扫描器"""

    # 支持的文件类型
    PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".heic"}
    VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv"}
    ALL_EXTENSIONS = PHOTO_EXTENSIONS | VIDEO_EXTENSIONS

    def __init__(self, session: Session, scan_paths: list[str], recursive: bool = True):
        """初始化扫描器

        Args:
            session: 数据库会话
            scan_paths: 要扫描的路径列表
            recursive: 是否递归扫描子目录
        """
        self.session = session
        self.scan_paths = scan_paths
        self.recursive = recursive
        self.progress = ScanProgress()
        self.scan_history: Optional[ScanHistory] = None

    def start_scan(self) -> ScanHistory:
        """开始扫描

        Returns:
            ScanHistory: 扫描历史记录
        """
        # 创建扫描历史记录
        self.scan_history = ScanHistory(
            start_time=time.time(),
            status="running"
        )
        self.session.add(self.scan_history)
        self.session.commit()

        print(f"\n{'='*50}")
        print(f"开始扫描媒体文件...")
        print(f"扫描路径: {self.scan_paths}")
        print(f"递归扫描: {self.recursive}")
        print(f"{'='*50}\n")

        # 收集所有需要扫描的文件
        all_files = list(self._collect_files())

        if not all_files:
            print("[WARN] No media files found")
            self._finish_scan(status="completed")
            return self.scan_history

        self.progress.total_files = len(all_files)

        # 获取数据库中现有的文件路径
        existing_paths = {
            path for (path,) in
            self.session.query(MediaItem.file_path).filter(
                MediaItem.file_path.in_(f[0] for f in all_files)
            ).all()
        }

        # 扫描每个文件
        for file_path, file_type in all_files:
            try:
                self._scan_file(file_path, file_type, file_path in existing_paths)
            except Exception as e:
                print(f"[FAIL] Scan failed {file_path}: {e}")
                self.progress.failed_files += 1

            self.progress.processed_files += 1

            # 每处理100个文件打印一次进度
            if self.progress.processed_files % 100 == 0:
                self._print_progress()

        # 检查已删除的文件
        self._check_deleted_files(all_files)

        # 完成扫描
        self._finish_scan(status="completed")

        return self.scan_history

    def _collect_files(self) -> Generator[tuple[str, str], None, None]:
        """收集所有需要扫描的文件

        Yields:
            tuple: (文件路径, 文件类型)
        """
        for scan_path in self.scan_paths:
            scan_path = os.path.abspath(scan_path)

            if not os.path.exists(scan_path):
                print(f"[WARN] Path not found: {scan_path}")
                continue

            if os.path.isfile(scan_path):
                # 单个文件
                ext = Path(scan_path).suffix.lower()
                if ext in self.ALL_EXTENSIONS:
                    file_type = "photo" if ext in self.PHOTO_EXTENSIONS else "video"
                    yield (scan_path, file_type)
            else:
                # 目录
                for root, dirs, files in os.walk(scan_path):
                    for filename in files:
                        file_path = os.path.join(root, filename)
                        ext = Path(file_path).suffix.lower()

                        if ext in self.ALL_EXTENSIONS:
                            file_type = "photo" if ext in self.PHOTO_EXTENSIONS else "video"
                            yield (file_path, file_type)

                    # 如果不递归，跳过子目录
                    if not self.recursive:
                        dirs.clear()

    def _scan_file(self, file_path: str, file_type: str, exists: bool):
        """扫描单个文件

        Args:
            file_path: 文件路径
            file_type: 文件类型 (photo/video)
            exists: 文件是否已存在于数据库
        """
        self.progress.current_path = file_path

        # 获取文件信息
        stat = os.stat(file_path)

        # 提取媒体信息
        media_info = ExifExtractor.get_media_info(file_path)

        # 获取创建时间（先尝试EXIF，没有则返回None）
        create_time = ExifExtractor.get_create_time(file_path, media_info, require_exif=True)

        # 如果没有EXIF时间，标记为待设置日期
        pending_date = create_time is None

        # 如果没有EXIF时间且不要求EXIF，使用文件时间作为占位
        if create_time is None:
            create_time = stat.st_mtime

        data = {
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "file_size": stat.st_size,
            "file_type": file_type,
            "mime_type": media_info.get("mime_type"),
            "create_time": create_time,
            "modify_time": stat.st_mtime,
            "scan_time": time.time(),
            "width": media_info.get("width"),
            "height": media_info.get("height"),
            "duration": media_info.get("duration"),
            "orientation": media_info.get("orientation", 1),
            "is_valid": True,
            "pending_date": pending_date,
        }

        if exists:
            # 更新现有记录
            item = self.session.query(MediaItem).filter_by(file_path=file_path).first()
            if item:
                # 检查是否需要更新
                if item.modify_time < stat.st_mtime:
                    for key, value in data.items():
                        setattr(item, key, value)
                    self.progress.updated_files += 1
                    # 重新生成缩略图
                    ensure_thumbnails_exist(self.session, item, "medium")
        else:
            # 插入新记录
            item = MediaItem(**data)
            self.session.add(item)
            self.session.flush()  # 获取 ID

            # 生成缩略图
            ensure_thumbnails_exist(self.session, item, "medium")

            if pending_date:
                self.progress.failed_files += 1  # 复用这个字段记录无日期文件
            else:
                self.progress.added_files += 1

        self.session.commit()

    def _check_deleted_files(self, current_files: list[tuple[str, str]]):
        """检查已删除的文件

        Args:
            current_files: 当前扫描到的文件列表
        """
        current_paths = {f[0] for f in current_files}

        # 查找数据库中存在但文件系统中不存在的记录
        deleted_items = self.session.query(MediaItem).filter(
            ~MediaItem.file_path.in_(current_paths)
        ).all()

        for item in deleted_items:
            print(f"[DEL] File removed: {item.file_path}")
            self.session.delete(item)
            self.progress.deleted_files += 1

        self.session.commit()

    def _print_progress(self):
        """打印扫描进度"""
        p = self.progress
        percent = p.processed_files / p.total_files * 100 if p.total_files > 0 else 0
        print(
            f"Progress: {p.processed_files}/{p.total_files} ({percent:.1f}%) | "
            f"+{p.added_files} ~{p.updated_files} -{p.deleted_files} pending_date:{p.failed_files}"
        )

    def _finish_scan(self, status: str):
        """完成扫描

        Args:
            status: 扫描状态
        """
        if self.scan_history:
            self.scan_history.end_time = time.time()
            self.scan_history.status = status
            self.scan_history.items_added = self.progress.added_files
            self.scan_history.items_updated = self.progress.updated_files
            self.scan_history.items_deleted = self.progress.deleted_files
            self.scan_history.items_failed = self.progress.failed_files
            self.session.commit()

        print(f"\n{'='*50}")
        print(f"Scan Complete!")
        print(f"  With EXIF date: {self.progress.added_files}")
        print(f"  Updated: {self.progress.updated_files}")
        print(f"  Deleted: {self.progress.deleted_files}")
        print(f"  Pending date (no EXIF): {self.progress.failed_files}")
        print(f"{'='*50}\n")


# ==================== 独立扫描函数 ====================

def scan_media(
    session: Session,
    paths: list[str],
    recursive: bool = True
) -> ScanHistory:
    """扫描媒体文件

    Args:
        session: 数据库会话
        paths: 要扫描的路径列表
        recursive: 是否递归扫描

    Returns:
        ScanHistory: 扫描历史记录
    """
    scanner = MediaScanner(session, paths, recursive)
    return scanner.start_scan()
