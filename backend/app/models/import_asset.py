from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class ImportJob(Base):
    """Structured import job for OpenAPI/Postman/Apifox."""

    __tablename__ = "import_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, nullable=True)
    source_type = Column(String(20), nullable=False)
    source_name = Column(String(200), nullable=False, default="")
    source_ref = Column(String(1000), nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    total_count = Column(Integer, default=0)
    imported_count = Column(Integer, default=0)
    issue_count = Column(Integer, default=0)
    summary = Column(Text, default="{}")
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    issues = relationship(
        "ImportIssue",
        back_populates="job",
        cascade="all, delete-orphan",
        order_by="ImportIssue.id",
    )


class ImportIssue(Base):
    """Detected import issue item."""

    __tablename__ = "import_issues"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("import_jobs.id"), nullable=False)
    issue_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False, default="warning")
    endpoint_path = Column(String(500), default="")
    method = Column(String(10), default="")
    message = Column(Text, default="")
    details = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("ImportJob", back_populates="issues")
