from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base


class ExecutionLog(Base):
    __tablename__ = "execution_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, nullable=False, default=1)
    case_id = Column(Integer, ForeignKey("test_case.id", ondelete="SET NULL"), nullable=True)
    scenario_id = Column(Integer, ForeignKey("scenario.id", ondelete="SET NULL"), nullable=True)
    scenario_step_id = Column(Integer, nullable=True)
    execution_type = Column(String(20), default="single")
    execution_id = Column(String(50), default="")
    request_url = Column(Text, default="")
    request_method = Column(String(10), default="")
    request_headers = Column(Text, default="{}")
    request_body = Column(Text, default="")
    response_status = Column(Integer, default=0)
    response_headers = Column(Text, default="{}")
    response_body = Column(Text, default="")
    response_size = Column(Integer, default=0)
    response_time_ms = Column(Integer, default=0)
    status = Column(String(20), default="pending")
    error_message = Column(Text, default="")
    assertion_results = Column(Text, default="[]")
    environment_id = Column(Integer, ForeignKey("environment.id", ondelete="SET NULL"), nullable=True)
    triggered_by = Column(String(50), default="user")
    created_at = Column(DateTime, default=datetime.now)

    # Phase 5
    self_heal_logs = relationship("SelfHealLog", back_populates="failure_log")

    __table_args__ = (
        Index("idx_execution_log_case", "case_id"),
        Index("idx_execution_log_scenario", "scenario_id"),
        Index("idx_execution_log_created", "created_at"),
        Index("idx_execution_log_status", "status"),
    )
