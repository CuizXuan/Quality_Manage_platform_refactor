# =============================================================================
# Scenario Models - 场景编排模型
# =============================================================================
# 包含：Scenario（场景）、ScenarioStep（场景步骤）、ExecutionRun（执行记录）
# =============================================================================

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class Scenario(Base):
    """场景 - 编排多个用例/步骤的集合"""

    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    status = Column(String(20), default="draft")  # draft|active|archived
    version = Column(Integer, default=1)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    steps = relationship(
        "ScenarioStep",
        back_populates="scenario",
        cascade="all, delete-orphan",
        order_by="ScenarioStep.sort_order",
    )


class ScenarioStep(Base):
    """场景步骤 - 场景中的单个步骤"""

    __tablename__ = "scenario_steps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"), nullable=False)
    case_id = Column(Integer, nullable=False)
    variant_id = Column(Integer, nullable=True)  # optional variant
    name = Column(String(200), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    enabled = Column(Integer, nullable=False, default=True)
    retry_count = Column(Integer, nullable=False, default=0)
    timeout_ms = Column(Integer, nullable=False, default=30000)
    failure_strategy = Column(String(20), nullable=False, default="stop")
    # stop|continue|retry|skip
    extract_rules = Column(Text, default="[]")  # JSON array
    inject_rules = Column(Text, default="[]")  # JSON array

    scenario = relationship("Scenario", back_populates="steps")


class ExecutionRun(Base):
    """执行记录 - 记录一次执行的历史"""

    __tablename__ = "execution_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_type = Column(String(20), nullable=False)  # case|scenario
    target_id = Column(Integer, nullable=False)
    environment_id = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    # pending|running|passed|failed|stopped
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    summary = Column(Text, default="{}")  # JSON object
