from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class ApiTestCase(Base):
    """接口用例专用表"""
    __tablename__ = "api_test_cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    testcase_id = Column(Integer, ForeignKey("test_cases.id"), unique=True, nullable=False)
    method = Column(String(10), default="GET")
    url = Column(String(2000), nullable=False)
    headers = Column(Text, default="{}")
    params = Column(Text, default="{}")
    body_type = Column(String(20), default="none")
    body = Column(Text, default="")
    auth_config = Column(Text, default="{}")
    expected_status = Column(Integer, default=200)
    assertions = Column(Text, default="[]")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    test_case = relationship("TestCase", back_populates="api_case")