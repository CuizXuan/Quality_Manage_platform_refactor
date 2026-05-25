from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class ApiGroup(Base):
    """API 分组"""
    __tablename__ = "api_groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, nullable=True)
    name = Column(String(200), nullable=False)
    parent_id = Column(Integer, nullable=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    apis = relationship("ApiDefinition", back_populates="group", cascade="all, delete-orphan")


class ApiDefinition(Base):
    """API 接口定义"""
    __tablename__ = "api_definitions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, nullable=True)
    group_id = Column(Integer, ForeignKey("api_groups.id"), nullable=True)
    name = Column(String(200), nullable=False)
    method = Column(String(10), nullable=False)
    path = Column(String(500), nullable=False)
    base_url = Column(String(500), nullable=True)
    summary = Column(String(500), default="")
    description = Column(Text, default="")
    tags = Column(Text, default="[]")
    parameters = Column(Text, default="[]")
    request_body = Column(Text, default="{}")
    responses = Column(Text, default="{}")
    version = Column(String(20), default="1.0.0")
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    group = relationship("ApiGroup", back_populates="apis")


class ApiImportRecord(Base):
    """OpenAPI 导入记录"""
    __tablename__ = "api_import_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, nullable=True)
    source_type = Column(String(20), nullable=False)
    source_url = Column(String(1000), nullable=True)
    status = Column(String(20), default="pending")
    imported_count = Column(Integer, default=0)
    message = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)