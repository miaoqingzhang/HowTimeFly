"""
独立的扫描脚本 - 用于测试扫描功能
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_database, get_session
from app.scanner import scan_media


def main():
    import argparse

    parser = argparse.ArgumentParser(description="扫描媒体文件")
    parser.add_argument("paths", nargs="*", help="要扫描的路径（默认使用配置文件中的路径）")
    parser.add_argument("--recursive", "-r", action="store_true", default=True, help="递归扫描子目录")
    parser.add_argument("--no-recursive", action="store_false", dest="recursive", help="不递归扫描子目录")

    args = parser.parse_args()

    # 初始化数据库
    db = init_database()
    print("[OK] Database connected\n")

    # 获取扫描路径
    if args.paths:
        paths = args.paths
    else:
        # 使用配置文件中的路径
        try:
            import yaml
            with open("config.yaml", "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                paths = config.get("scanner", {}).get("paths", ["./test_media"])
        except:
            paths = ["./test_media"]

    print(f"扫描路径: {paths}")
    print(f"递归扫描: {args.recursive}\n")

    # 开始扫描
    scan_id = None
    with db.get_session() as session:
        result = scan_media(session, paths, args.recursive)
        scan_id = result.id

    print(f"\n[OK] Scan complete! ID: {scan_id}")


if __name__ == "__main__":
    main()
