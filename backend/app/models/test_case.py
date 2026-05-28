from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class TestCase(Base):
    """用例主表 - 存储公共字段"""
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    folder_id = Column(Integer, nullable=True)
    priority = Column(String(10), default="P2")  # P0/P1/P2/P3
    tags = Column(Text, default="[]")  # JSON array
    pre_condition = Column(Text, default="")
    case_type = Column(String(20), nullable=False)  # 'api' | 'functional'
    source_debug_id = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True)
    is_automated = Column(Boolean, default=False)
    auto_script_path = Column(String(1000), default="")
    auto_script_config = Column(Text, default="{}")
    auto_case_id = Column(String(100), default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # API 调试字段（终端保存时使用）
    method = Column(String(10), nullable=True)
    url = Column(String(2000), nullable=True)
    headers = Column(Text, default="{}")
    query_params = Column(Text, default="{}")
    cookies = Column(Text, default="{}")
    auth_config = Column(Text, default="{}")
    body_type = Column(String(20), default="none")
    body = Column(Text, default="")
    expected_status = Column(Integer, default=200)

    # 质量基础关联字段
    project_id = Column(Integer, nullable=True)
    version_id = Column(Integer, nullable=True)
    iteration_id = Column(Integer, nullable=True)
    requirement_id = Column(Integer, ForeignKey("requirement_items.id"), nullable=True)
    source_api_id = Column(Integer, nullable=True)

    variants = relationship("CaseVariant", back_populates="test_case", cascade="all, delete-orphan")
    api_case = relationship("ApiTestCase", back_populates="test_case", uselist=False)
    functional_case = relationship("FunctionalTestCase", back_populates="test_case", uselist=False)
    requirement = relationship("RequirementItem", back_populates="test_cases")


class CaseVariant(Base):
    """测试用例变体 - 用于不同场景"""
    __tablename__ = "case_variants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("test_cases.id"), nullable=False)
    name = Column(String(200), nullable=False)
    variant_type = Column(String(50), nullable=False)
    override_params = Column(Text, default="{}")
    override_headers = Column(Text, default="{}")
    override_body = Column(Text, default="")
    expected_status = Column(Integer, nullable=True)
    expected_schema = Column(Text, nullable=True)
    assertions = Column(Text, default="[]")
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    test_case = relationship("TestCase", back_populates="variants")
