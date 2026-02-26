"""
初始化数据库脚本
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_database
from app.models import Base


def main():
    print("正在初始化数据库...")

    db_path = "./data/database.db"
    db = init_database(db_path)

    # 确保表已创建
    db.create_tables()

    print(f"[OK] Database initialized: {db_path}")
    print("\n可以使用以下命令启动服务:")
    print("  python run.py")


if __name__ == "__main__":
    main()
