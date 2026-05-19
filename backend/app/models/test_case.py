from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class TestCase(Base):
    """Test case for API testing."""
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_type = Column(String(20), nullable=False, default="api")  # 'functional' | 'api'
    folder_id = Column(Integer, nullable=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    method = Column(String(10), nullable=False, default="GET")
    url = Column(String(2000), nullable=False)
    query_params = Column(Text, default="{}")  # JSON string
    headers = Column(Text, default="{}")  # JSON string
    cookies = Column(Text, default="{}")  # JSON string
    auth_config = Column(Text, default="{}")  # JSON string
    body_type = Column(String(20), default="none")  # none, json, form, raw
    body = Column(Text, default="")
    expected_status = Column(Integer, nullable=True)
    source_debug_id = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    variants = relationship("CaseVariant", back_populates="test_case", cascade="all, delete-orphan")


class CaseVariant(Base):
    """Test case variant for different scenarios."""
    __tablename__ = "case_variants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("test_cases.id"), nullable=False)
    name = Column(String(200), nullable=False)
    variant_type = Column(String(50), nullable=False)  # normal, boundary, empty, missing_field, type_error, invalid_enum, overlong_field, auth_failed, permission_denied, response_schema, response_business_value, performance_threshold
    override_params = Column(Text, default="{}")  # JSON string
    override_headers = Column(Text, default="{}")  # JSON string
    override_body = Column(Text, default="")
    expected_status = Column(Integer, nullable=True)
    expected_schema = Column(Text, nullable=True)  # JSON string
    assertions = Column(Text, default="[]")  # JSON string
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    test_case = relationship("TestCase", back_populates="variants")
