from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Index
from datetime import datetime
from app.models.base import Base


class QualityGate(Base):
    __tablename__ = "quality_gate"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    rules = Column(Text, default="[]")  # JSON array of gate rules
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class QualityGateResult(Base):
    __tablename__ = "quality_gate_result"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gate_id = Column(Integer, nullable=False)
    trigger_type = Column(String(20), default="manual")  # commit/pr/deploy/schedule/manual
    trigger_ref = Column(String(200), default="")
    status = Column(String(20), nullable=False)  # passed/failed/warning
    rule_results = Column(Text, default="[]")  # JSON array of per-rule results
    summary = Column(Text, default="")
    triggered_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        Index("idx_gate_result_gate", "gate_id"),
    )
