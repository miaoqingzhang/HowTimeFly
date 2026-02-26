"""
启动脚本
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import run_server


if __name__ == "__main__":
    run_server()
