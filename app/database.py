"""
数据库操作
"""
import os
from pathlib import Path
from contextlib import contextmanager
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.models import Base


class Database:
    """数据库管理类"""

    def __init__(self, db_path: str):
        """初始化数据库

        Args:
            db_path: 数据库文件路径
        """
        # 确保目录存在
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.engine = create_engine(
            f"sqlite:///{db_path}",
            echo=False,  # 设置为True可以看到SQL语句
            connect_args={"check_same_thread": False}  # SQLite多线程支持
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

    def create_tables(self):
        """创建所有表"""
        Base.metadata.create_all(bind=self.engine)
        print(f"[OK] Database created: {self.engine.url}")

    def drop_tables(self):
        """删除所有表（慎用）"""
        Base.metadata.drop_all(bind=self.engine)
        print("[OK] Database tables dropped")

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """获取数据库会话（上下文管理器）

        Yields:
            Session: SQLAlchemy会话对象
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# 全局数据库实例
_db: Database | None = None


def init_database(db_path: str = "./data/database.db") -> Database:
    """初始化数据库

    Args:
        db_path: 数据库文件路径

    Returns:
        Database: 数据库实例
    """
    global _db
    _db = Database(db_path)
    _db.create_tables()
    return _db


def get_database() -> Database:
    """获取数据库实例"""
    if _db is None:
        raise RuntimeError("数据库未初始化，请先调用 init_database()")
    return _db


def get_session() -> Session:
    """快捷方式：获取数据库会话"""
    return get_database().get_session().__enter__()
