from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.models.base import Base


class AssetTrace(Base):
    """Trace between imported/debugged assets and downstream test assets."""

    __tablename__ = "asset_traces"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_type = Column(String(30), nullable=False)
    source_id = Column(Integer, nullable=False)
    target_type = Column(String(30), nullable=False)
    target_id = Column(Integer, nullable=False)
    relation_type = Column(String(30), nullable=False, default="derived")
    project_id = Column(Integer, nullable=True)
    version_tag = Column(String(50), default="")
    trace_metadata = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)
