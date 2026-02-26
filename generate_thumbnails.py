"""
为现有媒体生成缩略图
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from app.database import init_database, get_session
from app.models import MediaItem
from app.utils.thumbnail import ensure_thumbnails_exist


def generate_all_thumbnails():
    """为所有媒体文件生成缩略图"""
    # 初始化数据库
    db = init_database("./data/database.db")

    session = get_session()

    try:
        # 获取所有媒体
        media_items = session.query(MediaItem).filter_by(is_valid=True).all()

        print(f"Found {len(media_items)} media items")
        print("Generating thumbnails...\n")

        for i, item in enumerate(media_items, 1):
            print(f"[{i}/{len(media_items)}] Processing: {item.file_name}")

            try:
                # 生成 medium 尺寸的缩略图
                thumb = ensure_thumbnails_exist(session, item, "medium")

                if thumb:
                    print(f"  [OK] Thumbnail created: {thumb.width}x{thumb.height}")
                else:
                    print(f"  [FAIL] Failed to create thumbnail")

            except Exception as e:
                print(f"  [FAIL] Error: {e}")

        print("\nDone!")

    finally:
        session.close()


if __name__ == "__main__":
    generate_all_thumbnails()
