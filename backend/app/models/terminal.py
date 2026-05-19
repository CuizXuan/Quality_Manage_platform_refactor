from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class DebugRequest(Base):
    """Terminal debug request draft."""
    __tablename__ = "terminal_debug_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    method = Column(String(10), nullable=False, default="GET")
    url = Column(String(2000), nullable=False)
    query_params = Column(Text, default="{}")  # JSON string
    headers = Column(Text, default="{}")  # JSON string
    cookies = Column(Text, default="{}")  # JSON string
    auth_config = Column(Text, default="{}")  # JSON string
    body_type = Column(String(20), default="none")  # none, json, form, raw
    body = Column(Text, default="")
    environment_id = Column(Integer, ForeignKey("platform_organizations.id"), nullable=True)
    status = Column(String(20), default="active")  # active, favorite
    source_type = Column(String(20), default="manual")  # manual, curl, fetch
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    results = relationship("DebugResult", back_populates="debug_request", cascade="all, delete-orphan")


class DebugResult(Base):
    """Terminal debug execution result."""
    __tablename__ = "terminal_debug_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    debug_request_id = Column(Integer, ForeignKey("terminal_debug_requests.id"), nullable=False)
    status_code = Column(Integer, default=0)
    response_headers = Column(Text, default="{}")  # JSON string
    response_body = Column(Text, default="")
    duration_ms = Column(Integer, default=0)
    error_message = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    debug_request = relationship("DebugRequest", back_populates="results")
