# -*- coding: utf-8 -*-
"""
Phase 5 - 测试数据工厂相关数据模型
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


class DataMaskRule(Base):
    """数据脱敏规则表"""
    __tablename__ = "data_mask_rule"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    field_pattern = Column(String(500), nullable=False)  # 正则或 JSONPath
    mask_type = Column(String(50), nullable=False)  # phone/email/id_card/bank_card/password/token/custom
    mask_config = Column(Text, nullable=True)  # JSON 配置
    enabled = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class DataGenTemplate(Base):
    """数据生成模板表"""
    __tablename__ = "data_gen_template"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    template_type = Column(String(50), nullable=False)  # user/order/product/card
    schema = Column(Text, nullable=False)  # JSON 数据结构
    generation_rules = Column(Text, nullable=True)  # JSON 生成规则
    usage_count = Column(Integer, default=0)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class DataSnapshot(Base):
    """数据快照表"""
    __tablename__ = "data_snapshot"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    source_type = Column(String(50), nullable=False)  # database/table/api
    source_id = Column(String(200), nullable=True)
    data_content = Column(Text, nullable=True)  # 快照数据
    size_bytes = Column(Integer, default=0)
    record_count = Column(Integer, default=0)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=True)


class DataCloneTask(Base):
    """数据克隆任务表"""
    __tablename__ = "data_clone_task"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=True)
    source_env_id = Column(Integer, ForeignKey("environment.id"), nullable=True)
    target_env_id = Column(Integer, ForeignKey("environment.id"), nullable=True)
    tables = Column(Text, nullable=True)  # JSON 要克隆的表列表
    clone_type = Column(String(50), default="full")  # full/partial/mask
    mask_rules = Column(Text, nullable=True)  # JSON 应用的脱敏规则
    status = Column(String(20), default="pending")  # pending/running/completed/failed
    progress = Column(Integer, default=0)  # 0-100
    error_message = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
