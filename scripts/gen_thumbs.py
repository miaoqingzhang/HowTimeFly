"""
生成缩略图脚本
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_database, get_session
from app.thumbnail import ThumbnailService, ThumbnailConfig
from app.models import MediaItem


def main():
    import argparse

    parser = argparse.ArgumentParser(description="生成缩略图")
    parser.add_argument("--limit", "-n", type=int, default=None, help="限制生成的数量")
    parser.add_argument("--media-id", "-m", type=int, help="为指定媒体ID生成缩略图")

    args = parser.parse_args()

    # 初始化数据库
    db = init_database()
    print("[OK] Database connected\n")

    # 创建缩略图服务
    config = ThumbnailConfig(
        enabled=True,
        output_dir="./data/thumbnails"
    )

    with db.get_session() as session:
        service = ThumbnailService(session, config)

        if args.media_id:
            # 为指定媒体生成
            print(f"为媒体 {args.media_id} 生成缩略图...")
            service.generate_for_media(args.media_id)
        else:
            # 批量生成
            limit = args.limit
            print(f"开始生成缩略图... (限制: {limit or '无'})\n")

            stats = service.generate_all_pending(limit)

            print(f"\n[OK] Generation complete!")
            print(f"  成功: {stats['success']}")
            print(f"  失败: {stats['failed']}")


if __name__ == "__main__":
    main()
