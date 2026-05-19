from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Index
from datetime import datetime
from app.models.base import Base


class ReportTemplate(Base):
    __tablename__ = "report_template"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    type = Column(String(20), default="html")  # html / pdf / markdown
    content = Column(Text, default="")
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index("idx_report_template_name", "name"),
        Index("idx_report_template_type", "type"),
    )
