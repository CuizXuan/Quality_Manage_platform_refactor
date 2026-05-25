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

        # Check quality_foundation tables
        result = db.execute(text("PRAGMA table_info(quality_projects)"))
        columns = [row[1] for row in result.fetchall()]
        if not columns:
            db.execute(text("""CREATE TABLE IF NOT EXISTS quality_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(200) NOT NULL,
                code VARCHAR(50) NOT NULL UNIQUE,
                description TEXT DEFAULT '',
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )"""))

        result = db.execute(text("PRAGMA table_info(quality_versions)"))
        columns = [row[1] for row in result.fetchall()]
        if not columns:
            db.execute(text("""CREATE TABLE IF NOT EXISTS quality_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                name VARCHAR(200) NOT NULL,
                code VARCHAR(50) NOT NULL,
                status VARCHAR(20) DEFAULT 'planning',
                planned_release_at TIMESTAMP,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES quality_projects(id)
            )"""))

        result = db.execute(text("PRAGMA table_info(quality_iterations)"))
        columns = [row[1] for row in result.fetchall()]
        if not columns:
            db.execute(text("""CREATE TABLE IF NOT EXISTS quality_iterations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                version_id INTEGER NOT NULL,
                name VARCHAR(200) NOT NULL,
                status VARCHAR(20) DEFAULT 'planning',
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES quality_projects(id),
                FOREIGN KEY (version_id) REFERENCES quality_versions(id)
            )"""))

        result = db.execute(text("PRAGMA table_info(requirement_items)"))
        columns = [row[1] for row in result.fetchall()]
        if not columns:
            db.execute(text("""CREATE TABLE IF NOT EXISTS requirement_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                version_id INTEGER,
                iteration_id INTEGER,
                title VARCHAR(300) NOT NULL,
                description TEXT DEFAULT '',
                source_type VARCHAR(30),
                source_key VARCHAR(100),
                priority VARCHAR(10) DEFAULT 'P2',
                status VARCHAR(20) DEFAULT 'open',
                owner_id INTEGER,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES quality_projects(id),
                FOREIGN KEY (version_id) REFERENCES quality_versions(id),
                FOREIGN KEY (iteration_id) REFERENCES quality_iterations(id)
            )"""))

        # Add foreign key for requirement_id in test_cases if not exists
        result = db.execute(text("PRAGMA table_info(test_cases)"))
        columns = [row[1] for row in result.fetchall()]
        if 'requirement_id' not in columns:
            db.execute(text("ALTER TABLE test_cases ADD COLUMN requirement_id INTEGER"))
            db.execute(text("UPDATE test_cases SET requirement_id = NULL WHERE requirement_id IS NULL"))

        # Add quality foundation columns to test_cases
        if 'project_id' not in columns:
            db.execute(text("ALTER TABLE test_cases ADD COLUMN project_id INTEGER"))
            db.execute(text("UPDATE test_cases SET project_id = NULL WHERE project_id IS NULL"))

        if 'version_id' not in columns:
            db.execute(text("ALTER TABLE test_cases ADD COLUMN version_id INTEGER"))
            db.execute(text("UPDATE test_cases SET version_id = NULL WHERE version_id IS NULL"))

        if 'iteration_id' not in columns:
            db.execute(text("ALTER TABLE test_cases ADD COLUMN iteration_id INTEGER"))
            db.execute(text("UPDATE test_cases SET iteration_id = NULL WHERE iteration_id IS NULL"))

        # Add quality foundation columns to scenarios
        result = db.execute(text("PRAGMA table_info(scenarios)"))
        columns = [row[1] for row in result.fetchall()]
        if 'project_id' not in columns:
            db.execute(text("ALTER TABLE scenarios ADD COLUMN project_id INTEGER"))
            db.execute(text("UPDATE scenarios SET project_id = NULL WHERE project_id IS NULL"))

        if 'version_id' not in columns:
            db.execute(text("ALTER TABLE scenarios ADD COLUMN version_id INTEGER"))
            db.execute(text("UPDATE scenarios SET version_id = NULL WHERE version_id IS NULL"))

        if 'iteration_id' not in columns:
            db.execute(text("ALTER TABLE scenarios ADD COLUMN iteration_id INTEGER"))
            db.execute(text("UPDATE scenarios SET iteration_id = NULL WHERE iteration_id IS NULL"))

        # Add quality foundation columns to reports
        result = db.execute(text("PRAGMA table_info(reports)"))
        columns = [row[1] for row in result.fetchall()]
        if 'project_id' not in columns:
            db.execute(text("ALTER TABLE reports ADD COLUMN project_id INTEGER"))
            db.execute(text("UPDATE reports SET project_id = NULL WHERE project_id IS NULL"))

        if 'version_id' not in columns:
            db.execute(text("ALTER TABLE reports ADD COLUMN version_id INTEGER"))
            db.execute(text("UPDATE reports SET version_id = NULL WHERE version_id IS NULL"))

        if 'iteration_id' not in columns:
            db.execute(text("ALTER TABLE reports ADD COLUMN iteration_id INTEGER"))
            db.execute(text("UPDATE reports SET iteration_id = NULL WHERE iteration_id IS NULL"))

        # Add quality foundation columns to defects
        result = db.execute(text("PRAGMA table_info(defects)"))
        columns = [row[1] for row in result.fetchall()]
        if 'version_id' not in columns:
            db.execute(text("ALTER TABLE defects ADD COLUMN version_id INTEGER"))
            db.execute(text("UPDATE defects SET version_id = NULL WHERE version_id IS NULL"))

        if 'iteration_id' not in columns:
            db.execute(text("ALTER TABLE defects ADD COLUMN iteration_id INTEGER"))
            db.execute(text("UPDATE defects SET iteration_id = NULL WHERE iteration_id IS NULL"))

        if 'requirement_id' not in columns:
            db.execute(text("ALTER TABLE defects ADD COLUMN requirement_id INTEGER"))
            db.execute(text("UPDATE defects SET requirement_id = NULL WHERE requirement_id IS NULL"))

        # api_groups table
        result = db.execute(text("PRAGMA table_info(api_groups)"))
        columns = [row[1] for row in result.fetchall()]
        if not columns:
            db.execute(text("""CREATE TABLE IF NOT EXISTS api_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                name VARCHAR(200) NOT NULL,
                parent_id INTEGER,
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )"""))

        # api_definitions table
        result = db.execute(text("PRAGMA table_info(api_definitions)"))
        columns = [row[1] for row in result.fetchall()]
        if not columns:
            db.execute(text("""CREATE TABLE IF NOT EXISTS api_definitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                group_id INTEGER,
                name VARCHAR(200) NOT NULL,
                method VARCHAR(10) NOT NULL,
                path VARCHAR(500) NOT NULL,
                base_url VARCHAR(500),
                summary VARCHAR(500) DEFAULT '',
                description TEXT DEFAULT '',
                tags TEXT DEFAULT '[]',
                parameters TEXT DEFAULT '[]',
                request_body TEXT DEFAULT '{}',
                responses TEXT DEFAULT '{}',
                version VARCHAR(20) DEFAULT '1.0.0',
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES api_groups(id)
            )"""))

        # api_import_records table
        result = db.execute(text("PRAGMA table_info(api_import_records)"))
        columns = [row[1] for row in result.fetchall()]
        if not columns:
            db.execute(text("""CREATE TABLE IF NOT EXISTS api_import_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                source_type VARCHAR(20) NOT NULL,
                source_url VARCHAR(1000),
                status VARCHAR(20) DEFAULT 'pending',
                imported_count INTEGER DEFAULT 0,
                message TEXT DEFAULT '',
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )"""))

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
