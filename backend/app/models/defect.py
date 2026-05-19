from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Index, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base


class Defect(Base):
    __tablename__ = "defect"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, nullable=False, default=1)
    title = Column(String(500), nullable=False)
    description = Column(Text, default="")
    severity = Column(String(20), nullable=False, default="medium")  # critical/high/medium/low
    priority = Column(String(20), nullable=False, default="medium")  # urgent/high/medium/low
    status = Column(String(20), default="open")  # open/in_progress/resolved/closed/reopened
    defect_type = Column(String(30), default="functional")  # functional/performance/security/UI
    assignee = Column(String(100), default="")
    reporter = Column(String(100), nullable=False)
    execution_log_id = Column(Integer, nullable=True)
    case_id = Column(Integer, nullable=True)
    scenario_id = Column(Integer, nullable=True)
    environment = Column(String(50), default="")
    steps_to_reproduce = Column(Text, default="")
    expected_result = Column(Text, default="")
    actual_result = Column(Text, default="")
    resolution = Column(Text, default="")
    resolved_at = Column(DateTime, nullable=True)
    external_id = Column(String(100), default="")
    external_url = Column(String(500), default="")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index("idx_defect_status", "status"),
        Index("idx_defect_assignee", "assignee"),
        Index("idx_defect_case", "case_id"),
    )


class DefectAttachment(Base):
    __tablename__ = "defect_attachment"

    id = Column(Integer, primary_key=True, autoincrement=True)
    defect_id = Column(Integer, ForeignKey("defect.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String(200), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    file_type = Column(String(50), default="")
    uploaded_at = Column(DateTime, default=datetime.now)


class DefectComment(Base):
    __tablename__ = "defect_comment"

    id = Column(Integer, primary_key=True, autoincrement=True)
    defect_id = Column(Integer, ForeignKey("defect.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    author = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
