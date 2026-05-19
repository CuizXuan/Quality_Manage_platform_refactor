from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Index
from sqlalchemy.orm import declarative_base
from datetime import datetime
from app.models.base import Base


class TestCase(Base):
    __tablename__ = "test_case"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, nullable=False, default=1)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    method = Column(String(10), nullable=False, default="GET")
    url = Column(Text, nullable=False, default="")
    headers = Column(Text, default="{}")
    params = Column(Text, default="{}")
    body = Column(Text, default="")
    body_type = Column(String(20), default="json")
    request_body = Column(Text, default="")
    response_body = Column(Text, default="")
    auth_type = Column(String(20), default="none")
    auth_config = Column(Text, default="{}")
    folder_path = Column(String(500), default="/")
    sort_order = Column(Integer, default=0)
    assertions = Column(Text, default="[]")
    pre_script = Column(Text, default="")
    post_script = Column(Text, default="")
    timeout = Column(Integer, default=30)
    follow_redirects = Column(Boolean, default=True)
    verify_ssl = Column(Boolean, default=True)
    # Phase 3: 用例-代码关联字段
    code_file_id = Column(Integer, nullable=True)
    code_method_id = Column(Integer, nullable=True)
    coverage_threshold = Column(Integer, nullable=True)
    unit_test_path = Column(String(500), default="")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index("idx_test_case_folder", "folder_path"),
        Index("idx_test_case_method", "method"),
    )
