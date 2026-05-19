from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# 计算 backend 目录的绝对路径
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BACKEND_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "api_debug.db")

# 默认使用绝对路径
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

os.makedirs(DATA_DIR, exist_ok=True)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app.models import Base
    Base.metadata.create_all(bind=engine)
    # 初始化内置角色
    _seed_roles()


def _seed_roles():
    """初始化内置系统角色"""
    from sqlalchemy.orm import Session
    from app.models.tenant import Role

    db = Session(bind=engine)
    try:
        # 检查是否已有角色数据
        existing = db.query(Role).first()
        if existing:
            return  # 已有数据，跳过

        system_roles = [
            {"name": "Viewer", "description": "只读访问", "is_system": True},
            {"name": "Admin", "description": "管理员", "is_system": True},
            {"name": "Editor", "description": "编辑者", "is_system": True},
            {"name": "SuperAdmin", "description": "超级管理员", "is_system": True},
        ]

        for role_data in system_roles:
            role = Role(**role_data)
            db.add(role)

        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
