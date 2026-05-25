# =============================================================================
# Report Models - 报告/缺陷/质量门禁模型
# =============================================================================
# 包含：Report（测试报告）、Defect（缺陷）、QualityGate（质量门禁规则）
# =============================================================================

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship

from app.models.base import Base


class Report(Base):
    """测试报告 - 记录一次测试执行的完整报告"""

    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    report_type = Column(String(20), nullable=False)  # execution | scenario | suite
    target_id = Column(Integer, nullable=True)  # 执行记录ID或场景ID
    target_name = Column(String(200), nullable=True)
    environment = Column(String(50), nullable=True)
    summary = Column(JSON, default=dict)  # {total, passed, failed, skipped, pass_rate}
    metrics = Column(JSON, default=dict)  # 详细指标
    executed_at = Column(DateTime, default=datetime.utcnow)
    duration_ms = Column(Integer, nullable=True)
    triggered_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 质量基础关联字段
    project_id = Column(Integer, nullable=True)
    version_id = Column(Integer, nullable=True)
    iteration_id = Column(Integer, nullable=True)


class Defect(Base):
    """缺陷 - 记录测试发现的缺陷，支持状态流转"""

    __tablename__ = "defects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(300), nullable=False)
    description = Column(Text, default="")
    severity = Column(String(10), nullable=False, default="medium")  # critical | high | medium | low
    priority = Column(String(10), nullable=False, default="P2")  # P0 P1 P2 P3
    status = Column(String(20), nullable=False, default="open")  # open | confirmed | fixed | verified | closed
    defect_type = Column(String(30), nullable=False, default="functional")  # functional | api | performance | security
    project_id = Column(Integer, nullable=True)
    case_id = Column(Integer, nullable=True)
    execution_id = Column(Integer, nullable=True)
    assigned_to = Column(Integer, nullable=True)
    reported_by = Column(Integer, nullable=True)
    opened_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)
    fixed_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    tags = Column(JSON, default=list)  # ["登录", "支付"]
    attachments = Column(JSON, default=list)  # [{"name": "...", "url": "..."}]

    # 质量基础关联字段
    version_id = Column(Integer, nullable=True)
    iteration_id = Column(Integer, nullable=True)
    requirement_id = Column(Integer, ForeignKey("requirement_items.id"), nullable=True)

    requirement = relationship("RequirementItem", back_populates="defects")


class QualityGate(Base):
    """质量门禁规则 - 定义质量门禁条件和阈值"""

    __tablename__ = "quality_gates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    gate_type = Column(String(20), nullable=False)  # execution | scheduled | pre_deploy
    enabled = Column(Integer, nullable=False, default=True)
    # 门禁条件（JSON数组）
    conditions = Column(JSON, default=list)  # [{"metric": "pass_rate", "operator": ">=", "threshold": 95}]
    # 质量门禁等级
    gate_level = Column(String(20), nullable=False, default="warning")  # blocking | warning | info
    scope_filter = Column(JSON, default=dict)  # {"project_id": 1, "environment": "prod"}
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_evaluated_at = Column(DateTime, nullable=True)
    last_result = Column(String(20), nullable=True)  # pass | fail | warning | skipped
