from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
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
    from app.services.platform_seed import seed_platform

    Base.metadata.create_all(bind=engine)
    _run_migrations()
    db = Session(bind=engine)
    try:
        seed_platform(db)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _run_migrations():
    """Run one-time migrations for schema changes that require ALTER TABLE."""
    from sqlalchemy import text

    db = Session(bind=engine)
    try:
        # Check if test_cases.case_type column exists
        result = db.execute(text("PRAGMA table_info(test_cases)"))
        columns = [row[1] for row in result.fetchall()]

        if 'case_type' not in columns:
            db.execute(text("ALTER TABLE test_cases ADD COLUMN case_type VARCHAR(20) DEFAULT 'api'"))
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
