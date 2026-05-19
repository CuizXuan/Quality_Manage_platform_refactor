from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint

from app.models.base import Base


class SystemDictionary(Base):
    __tablename__ = "system_dictionaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(50), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    sort_order = Column(Integer, default=0)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        UniqueConstraint("category", "code", name="uix_category_code"),
    )