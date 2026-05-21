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
    from app.services.dictionary_seed import seed_dictionaries

    Base.metadata.create_all(bind=engine)
    _run_migrations()
    db = Session(bind=engine)
    try:
        seed_platform(db)
        seed_dictionaries(db)
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
        # Check test_cases table columns
        result = db.execute(text("PRAGMA table_info(test_cases)"))
        columns = [row[1] for row in result.fetchall()]

        if 'case_type' not in columns:
            db.execute(text("ALTER TABLE test_cases ADD COLUMN case_type VARCHAR(20)"))
            db.execute(text("UPDATE test_cases SET case_type = 'api' WHERE case_type IS NULL"))

        if 'priority' not in columns:
            db.execute(text("ALTER TABLE test_cases ADD COLUMN priority VARCHAR(10)"))
            db.execute(text("UPDATE test_cases SET priority = 'P2' WHERE priority IS NULL"))

        if 'tags' not in columns:
            db.execute(text("ALTER TABLE test_cases ADD COLUMN tags TEXT"))
            db.execute(text("UPDATE test_cases SET tags = '[]' WHERE tags IS NULL"))

        if 'pre_condition' not in columns:
            db.execute(text("ALTER TABLE test_cases ADD COLUMN pre_condition TEXT"))
            db.execute(text("UPDATE test_cases SET pre_condition = '' WHERE pre_condition IS NULL"))

        if 'is_automated' not in columns:
            db.execute(text("ALTER TABLE test_cases ADD COLUMN is_automated BOOLEAN DEFAULT 0"))
            db.execute(text("UPDATE test_cases SET is_automated = 0 WHERE is_automated IS NULL"))

        if 'auto_script_path' not in columns:
            db.execute(text("ALTER TABLE test_cases ADD COLUMN auto_script_path VARCHAR(1000)"))
            db.execute(text("UPDATE test_cases SET auto_script_path = '' WHERE auto_script_path IS NULL"))

        if 'auto_script_config' not in columns:
            db.execute(text("ALTER TABLE test_cases ADD COLUMN auto_script_config TEXT"))
            db.execute(text("UPDATE test_cases SET auto_script_config = '{}' WHERE auto_script_config IS NULL"))

        if 'auto_case_id' not in columns:
            db.execute(text("ALTER TABLE test_cases ADD COLUMN auto_case_id VARCHAR(100)"))
            db.execute(text("UPDATE test_cases SET auto_case_id = '' WHERE auto_case_id IS NULL"))

        # Check scenarios table columns
        result = db.execute(text("PRAGMA table_info(scenarios)"))
        columns = [row[1] for row in result.fetchall()]
        if 'updated_at' not in columns:
            db.execute(text("ALTER TABLE scenarios ADD COLUMN updated_at TIMESTAMP"))
            db.execute(text("UPDATE scenarios SET updated_at = created_at WHERE updated_at IS NULL"))

        if 'scenario_type' not in columns:
            db.execute(text("ALTER TABLE scenarios ADD COLUMN scenario_type VARCHAR(50)"))
            db.execute(text("UPDATE scenarios SET scenario_type = 'functional' WHERE scenario_type IS NULL"))

        if 'priority' not in columns:
            db.execute(text("ALTER TABLE scenarios ADD COLUMN priority VARCHAR(10)"))
            db.execute(text("UPDATE scenarios SET priority = 'P2' WHERE priority IS NULL"))

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
