# =============================================================================
# Test Plan Models - 测试计划模型
# =============================================================================
# 包含：TestPlan（测试计划）、TestSuite（测试套件）、TestSuiteItem（套件项）、TestPlanRun（计划执行记录）
# =============================================================================

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class TestPlan(Base):
    """测试计划"""

    __tablename__ = "test_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, nullable=True)
    version_id = Column(Integer, nullable=True)
    iteration_id = Column(Integer, nullable=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    status = Column(String(20), default="draft")  # draft|active|archived
    owner_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    suites = relationship("TestSuite", back_populates="plan", cascade="all, delete-orphan", order_by="TestSuite.sort_order")
    runs = relationship("TestPlanRun", back_populates="plan", cascade="all, delete-orphan")


class TestSuite(Base):
    """测试套件"""

    __tablename__ = "test_suites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey("test_plans.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    sort_order = Column(Integer, nullable=False, default=0)

    plan = relationship("TestPlan", back_populates="suites")
    items = relationship("TestSuiteItem", back_populates="suite", cascade="all, delete-orphan", order_by="TestSuiteItem.sort_order")


class TestSuiteItem(Base):
    """测试套件项 - 套件中的用例或场景"""

    __tablename__ = "test_suite_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    suite_id = Column(Integer, ForeignKey("test_suites.id"), nullable=False)
    item_type = Column(String(20), nullable=False)  # case|scenario
    item_id = Column(Integer, nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)

    suite = relationship("TestSuite", back_populates="items")


class TestPlanRun(Base):
    """测试计划执行记录"""

    __tablename__ = "test_plan_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey("test_plans.id"), nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending|running|passed|failed|stopped
    total = Column(Integer, default=0)
    passed = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    skipped = Column(Integer, default=0)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    summary = Column(Text, default="{}")  # JSON object

    plan = relationship("TestPlan", back_populates="runs")