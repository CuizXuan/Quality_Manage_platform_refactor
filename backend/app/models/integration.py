from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from datetime import datetime
from app.models.base import Base


class IntegrationConfig(Base):
    __tablename__ = "integration_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    type = Column(String(30), nullable=False)  # jira/tapd/zentao/github_gitlab
    config = Column(Text, default="{}")  # JSON: url, api_key, project_key, etc.
    enabled = Column(Boolean, default=True)
    last_sync_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
