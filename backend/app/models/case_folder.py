from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base

class CaseFolder(Base):
    __tablename__ = "case_folders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    parent_id = Column(Integer, ForeignKey("case_folders.id"), nullable=True)
    sort_order = Column(Integer, default=0)
    tenant_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    children = relationship("CaseFolder", backref="parent", remote_side=[id], foreign_keys=[parent_id])
