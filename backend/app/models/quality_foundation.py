# =============================================================================
# Quality Foundation Models - 质量基础模型
# =============================================================================
# 包含：QualityProject（项目）、QualityVersion（版本）、QualityIteration（迭代）、
#       RequirementItem（需求）
# =============================================================================

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class QualityProject(Base):
    """质量项目 - 测试工作的顶层容器"""

    __tablename__ = "quality_projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    code = Column(String(50), nullable=False, unique=True)
    description = Column(Text, default="")
    status = Column(String(20), default="active")  # active|archived
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    versions = relationship("QualityVersion", back_populates="project", cascade="all, delete-orphan")
    iterations = relationship("QualityIteration", back_populates="project", cascade="all, delete-orphan")
    requirements = relationship("RequirementItem", back_populates="project", cascade="all, delete-orphan")


class QualityVersion(Base):
    """质量版本 - 属于项目的版本"""

    __tablename__ = "quality_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("quality_projects.id"), nullable=False)
    name = Column(String(200), nullable=False)
    code = Column(String(50), nullable=False)
    status = Column(String(20), default="planning")  # planning|development|testing|released|archived
    planned_release_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("QualityProject", back_populates="versions")
    iterations = relationship("QualityIteration", back_populates="version", cascade="all, delete-orphan")
    requirements = relationship("RequirementItem", back_populates="version", cascade="all, delete-orphan")


class QualityIteration(Base):
    """质量迭代 - 属于版本的迭代周期"""

    __tablename__ = "quality_iterations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("quality_projects.id"), nullable=False)
    version_id = Column(Integer, ForeignKey("quality_versions.id"), nullable=False)
    name = Column(String(200), nullable=False)
    status = Column(String(20), default="planning")  # planning|running|completed|cancelled
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("QualityProject", back_populates="iterations")
    version = relationship("QualityVersion", back_populates="iterations")
    requirements = relationship("RequirementItem", back_populates="iteration", cascade="all, delete-orphan")


class RequirementItem(Base):
    """需求项 - 归属迭代的具体需求"""

    __tablename__ = "requirement_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("quality_projects.id"), nullable=False)
    version_id = Column(Integer, ForeignKey("quality_versions.id"), nullable=True)
    iteration_id = Column(Integer, ForeignKey("quality_iterations.id"), nullable=True)
    title = Column(String(300), nullable=False)
    description = Column(Text, default="")
    source_type = Column(String(30), nullable=True)  # user_story|feature|bug|external
    source_key = Column(String(100), nullable=True)  # 外部系统ID如 JIRA-123
    priority = Column(String(10), default="P2")  # P0|P1|P2|P3
    status = Column(String(20), default="open")  # open|in_progress|tested|closed
    owner_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("QualityProject", back_populates="requirements")
    version = relationship("QualityVersion", back_populates="requirements")
    iteration = relationship("QualityIteration", back_populates="requirements")
    test_cases = relationship("TestCase", back_populates="requirement")
    defects = relationship("Defect", back_populates="requirement")