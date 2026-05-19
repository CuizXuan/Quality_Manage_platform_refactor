from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Index
from datetime import datetime
from app.models.base import Base


class MockRule(Base):
    __tablename__ = "mock_rule"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    path = Column(String(500), nullable=False)
    method = Column(String(10), default="GET")
    response_status = Column(Integer, default=200)
    response_headers = Column(Text, default="{}")  # JSON object
    response_body = Column(Text, default="")
    response_template_type = Column(String(20), default="none")  # none / jinja2
    delay_ms = Column(Integer, default=0)
    match_conditions = Column(Text, default="[]")  # JSON array
    enabled = Column(Boolean, default=True)
    hit_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index("idx_mock_rule_path_method", "path", "method"),
    )
