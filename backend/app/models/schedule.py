from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from datetime import datetime
from app.models.base import Base


class Schedule(Base):
    __tablename__ = "schedule"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, nullable=False, default=1)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    target_type = Column(String(20), nullable=False)  # case / scenario
    target_id = Column(Integer, nullable=False)
    cron_expression = Column(String(100), nullable=False)
    environment_id = Column(Integer, ForeignKey("environment.id", ondelete="SET NULL"), nullable=True)
    enabled = Column(Boolean, default=True)
    notify_on = Column(String(20), default="never")  # never / always / failure
    notify_channels = Column(Text, default="[]")  # JSON array
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    run_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
