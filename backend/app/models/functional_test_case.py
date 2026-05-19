from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class FunctionalTestCase(Base):
    """功能用例专用表"""
    __tablename__ = "functional_test_cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    testcase_id = Column(Integer, ForeignKey("test_cases.id"), unique=True, nullable=False)
    steps = Column(Text, default="[]")  # JSON array of steps
    test_data = Column(Text, default="{}")  # JSON object
    post_action = Column(Text, default="")
    expected_result = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    test_case = relationship("TestCase", back_populates="functional_case")