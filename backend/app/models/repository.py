from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base


class CodeRepository(Base):
    __tablename__ = "code_repository"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    url = Column(String(500), nullable=False)
    branch = Column(String(100), default="main")
    provider = Column(String(20), default="gitlab")  # github/gitlab/gitee/local
    access_token = Column(String(500), default="")
    local_path = Column(String(500), default="")
    last_sync_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index("idx_repo_name", "name"),
    )


class CodeFile(Base):
    __tablename__ = "code_file"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repository_id = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(200), nullable=False)
    package_path = Column(String(500), default="")
    language = Column(String(20), default="")  # python/java/javascript/go
    last_commit_hash = Column(String(64), default="")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index("idx_code_file_repo_path", "repository_id", "file_path"),
    )


class CodeMethod(Base):
    __tablename__ = "code_method"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(Integer, nullable=False)
    method_name = Column(String(200), nullable=False)
    class_name = Column(String(200), default="")
    line_start = Column(Integer, default=0)
    line_end = Column(Integer, default=0)
    complexity = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index("idx_method_file", "file_id"),
    )
