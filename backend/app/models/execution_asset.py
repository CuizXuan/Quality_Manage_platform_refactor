from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class UnifiedRun(Base):
    """Unified execution record for case/scenario/plan runs."""

    __tablename__ = "execution_task_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_type = Column(String(20), nullable=False)
    target_type = Column(String(20), nullable=False)
    target_id = Column(Integer, nullable=False)
    project_id = Column(Integer, nullable=True)
    environment_id = Column(Integer, nullable=True)
    source_run_id = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    queue_status = Column(String(20), nullable=False, default="queued")
    summary = Column(Text, default="{}")
    created_by = Column(Integer, nullable=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = relationship(
        "UnifiedRunItem",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="UnifiedRunItem.sort_order",
    )
    artifacts = relationship(
        "RunArtifact",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="RunArtifact.id",
    )


class UnifiedRunItem(Base):
    """Expanded execution item under a unified run."""

    __tablename__ = "execution_run_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("execution_task_runs.id"), nullable=False)
    item_type = Column(String(20), nullable=False)
    item_id = Column(Integer, nullable=False)
    item_name = Column(String(200), default="")
    status = Column(String(20), nullable=False, default="pending")
    sort_order = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    summary = Column(Text, default="{}")

    run = relationship("UnifiedRun", back_populates="items")
    step_logs = relationship(
        "RunStepLog",
        back_populates="run_item",
        cascade="all, delete-orphan",
        order_by="RunStepLog.id",
    )


class RunStepLog(Base):
    """Detailed request/response/variable log entry."""

    __tablename__ = "execution_run_step_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_item_id = Column(Integer, ForeignKey("execution_run_items.id"), nullable=False)
    step_name = Column(String(200), default="")
    status = Column(String(20), nullable=False, default="pending")
    request_snapshot = Column(Text, default="{}")
    response_snapshot = Column(Text, default="{}")
    assertion_snapshot = Column(Text, default="[]")
    variable_snapshot = Column(Text, default="{}")
    error_message = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    run_item = relationship("UnifiedRunItem", back_populates="step_logs")


class RunArtifact(Base):
    """Execution artifact pointer."""

    __tablename__ = "execution_run_artifacts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("execution_task_runs.id"), nullable=False)
    artifact_type = Column(String(50), nullable=False)
    artifact_name = Column(String(200), nullable=False)
    payload = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)

    run = relationship("UnifiedRun", back_populates="artifacts")
