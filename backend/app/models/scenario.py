from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base


class Scenario(Base):
    __tablename__ = "scenario"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, nullable=False, default=1)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    folder_path = Column(String(500), default="/")
    variables = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class ScenarioStep(Base):
    __tablename__ = "scenario_step"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scenario_id = Column(Integer, ForeignKey("scenario.id", ondelete="CASCADE"), nullable=False)
    case_id = Column(Integer, ForeignKey("test_case.id", ondelete="CASCADE"), nullable=False)
    step_order = Column(Integer, nullable=False)
    extract_rules = Column(Text, default="[]")
    skip_on_failure = Column(Boolean, default=True)
    retry_times = Column(Integer, default=0)
    retry_interval = Column(Integer, default=1000)
    enabled = Column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint("scenario_id", "step_order", name="idx_scenario_step_order"),
    )
