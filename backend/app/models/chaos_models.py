# -*- coding: utf-8 -*-
"""
Phase 5 - 混沌工程相关数据模型
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


class ChaosExperiment(Base):
    """混沌实验表"""
    __tablename__ = "chaos_experiment"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    target_type = Column(String(50), nullable=False)  # service/pod/node/network
    target_id = Column(String(200), nullable=True)  # 目标标识
    hypothesis = Column(Text, nullable=True)  # 实验假设
    steady_state = Column(Text, nullable=True)  # JSON 稳态定义
    status = Column(String(20), default="draft")  # draft/running/paused/completed/aborted
    blast_radius = Column(Integer, default=0)  # 爆炸半径
    auto_rollback = Column(Boolean, default=True)
    rollback_condition = Column(Text, nullable=True)  # JSON
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    project = relationship("Project")
    faults = relationship("FaultInjection", back_populates="experiment")


class FaultInjection(Base):
    """故障注入表"""
    __tablename__ = "fault_injection"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(Integer, ForeignKey("chaos_experiment.id"), nullable=False)
    fault_type = Column(String(50), nullable=False)  # cpu/memory/network/disk/pod-kill/latency
    target_service = Column(String(200), nullable=True)
    fault_config = Column(Text, nullable=False)  # JSON 故障配置
    blast_radius = Column(Integer, default=0)
    status = Column(String(20), default="pending")  # pending/running/success/failed/rolled_back
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # 关系
    experiment = relationship("ChaosExperiment", back_populates="faults")
    metrics = relationship("ChaosMetric", back_populates="injection")


class FaultType(Base):
    """故障类型表"""
    __tablename__ = "fault_type"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    category = Column(String(50), nullable=True)  # resource/network/pod/application
    description = Column(Text, nullable=True)
    config_schema = Column(Text, nullable=True)  # JSON 配置 schema
    risk_level = Column(String(20), default="medium")  # low/medium/high/critical
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class ChaosMetric(Base):
    """混沌指标表"""
    __tablename__ = "chaos_metric"

    id = Column(Integer, primary_key=True, autoincrement=True)
    injection_id = Column(Integer, ForeignKey("fault_injection.id"), nullable=False)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=True)
    baseline_value = Column(Float, nullable=True)
    deviation = Column(Float, nullable=True)  # 偏差百分比
    timestamp = Column(DateTime, server_default=func.now())

    # 关系
    injection = relationship("FaultInjection", back_populates="metrics")


class ResilienceScore(Base):
    """韧性评分表"""
    __tablename__ = "resilience_score"

    id = Column(Integer, primary_key=True, autoincrement=True)
    target_type = Column(String(50), nullable=False)  # service/pod/node
    target_id = Column(String(200), nullable=False)
    score = Column(Float, default=0)  # 0-100
    metrics = Column(Text, nullable=True)  # JSON 各项指标
    weaknesses = Column(Text, nullable=True)  # JSON 弱点列表
    recommendations = Column(Text, nullable=True)  # JSON 改进建议
    evaluated_at = Column(DateTime, server_default=func.now())
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
