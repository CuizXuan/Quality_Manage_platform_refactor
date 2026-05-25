# doc-generator 文档生成模块数据模型
# DocGenerationTask: 生成任务记录
# DocGenerationRule: 生成规则（JSON格式）
# DocGenerationTemplate: 文档模板（.docx）
# DocGenerationHistory: 生成历史（元数据）

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, Boolean

from app.models.base import Base


class DocGenerationTask(Base):
    """文档生成任务"""
    __tablename__ = "docgen_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    task_type = Column(String(30), nullable=False)  # requirement_design | database_design | api_design
    status = Column(String(20), nullable=False, default="pending")  # pending | running | success | failed
    source_filename = Column(String(200), nullable=True)
    output_filename = Column(String(200), nullable=True)
    output_path = Column(String(500), nullable=True)
    message = Column(Text, default="")
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)


class DocGenerationRule(Base):
    """文档生成规则"""
    __tablename__ = "docgen_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    doc_type = Column(String(30), nullable=False)  # requirement_outline | requirement_detail | database_design | api_design
    filename = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)  # JSON规则内容
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DocGenerationTemplate(Base):
    """文档生成模板"""
    __tablename__ = "docgen_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    doc_type = Column(String(30), nullable=True)
    filename = Column(String(200), nullable=True)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)