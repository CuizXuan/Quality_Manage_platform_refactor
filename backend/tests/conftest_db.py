# -*- coding: utf-8 -*-
"""
数据库fixture配置
"""
import pytest
import sys
import os
from pathlib import Path

# 添加项目根目录到path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.database import Base, get_db
from app.main import app

# 导入所有模型以注册到 Base.metadata
from app.models import *


# 测试数据库路径 - 使用项目相对路径
BACKEND_DIR = Path(__file__).parent.parent
TEST_DATABASE_PATH = BACKEND_DIR / "data" / "api_debug.db"
DATABASE_URL = f"sqlite:///{TEST_DATABASE_PATH}"

# 创建测试用数据库引擎
@pytest.fixture(scope="session")
def engine():
    """创建数据库引擎"""
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    return engine


@pytest.fixture(scope="session")
def TestingSessionLocal(engine):
    """创建会话工厂"""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session(engine, TestingSessionLocal):
    """为每个测试提供独立的数据库会话"""
    # 创建表
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # 清理数据（但不删除表）
        with engine.connect() as conn:
            for table in reversed(Base.metadata.sorted_tables):
                conn.execute(table.delete())
            conn.commit()


@pytest.fixture(scope="function")
def override_get_db(db_session):
    """覆盖应用的get_db依赖"""
    def _override():
        try:
            yield db_session
        finally:
            pass
    return _override
