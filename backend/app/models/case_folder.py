from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.models.base import Base


class CaseFolder(Base):
    """用例文件夹分类"""
    __tablename__ = "case_folders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_type = Column(String(20), nullable=False, default="api")  # 'functional' | 'api'
    parent_id = Column(Integer, nullable=True)
    name = Column(String(200), nullable=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)