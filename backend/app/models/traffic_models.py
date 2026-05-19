# -*- coding: utf-8 -*-
"""
Phase 5 - 全链路压测相关数据模型
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


class TrafficRecord(Base):
    """流量录制表"""
    __tablename__ = "traffic_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    source = Column(String(50), nullable=False)  # nginx/envoy/kubernetes/custom
    filter_rules = Column(Text, nullable=True)  # JSON
    traffic_data = Column(Text, nullable=True)  # 流量数据存储路径
    request_count = Column(Integer, default=0)
    unique_apis = Column(Integer, default=0)
    time_range_start = Column(DateTime, nullable=True)
    time_range_end = Column(DateTime, nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    environment_id = Column(Integer, ForeignKey("environment.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String(20), default="pending")  # pending/recording/completed/stopped
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    project = relationship("Project")
    replays = relationship("TrafficReplay", back_populates="record")


class TrafficReplay(Base):
    """流量回放表"""
    __tablename__ = "traffic_replay"

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(Integer, ForeignKey("traffic_record.id"), nullable=False)
    replay_config = Column(Text, nullable=True)  # JSON
    status = Column(String(20), default="pending")  # pending/running/completed/failed
    total_requests = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    diff_count = Column(Integer, default=0)
    target_environment_id = Column(Integer, ForeignKey("environment.id"), nullable=True)
    enable_shadow = Column(Boolean, default=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    record = relationship("TrafficRecord", back_populates="replays")
    diff_reports = relationship("DiffReport", back_populates="replay")


class TrafficTag(Base):
    """流量标签表"""
    __tablename__ = "traffic_tag"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tag_name = Column(String(100), nullable=False)
    tag_value = Column(String(200), nullable=False)
    match_rules = Column(Text, nullable=True)  # JSON
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class DiffReport(Base):
    """Diff 报告表"""
    __tablename__ = "diff_report"

    id = Column(Integer, primary_key=True, autoincrement=True)
    replay_id = Column(Integer, ForeignKey("traffic_replay.id"), nullable=False)
    diff_type = Column(String(20), nullable=True)  # status/body/header/latency
    diff_details = Column(Text, nullable=True)  # JSON
    request_info = Column(Text, nullable=True)  # JSON
    original_response = Column(Text, nullable=True)  # JSON
    replay_response = Column(Text, nullable=True)  # JSON
    is_match = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    replay = relationship("TrafficReplay", back_populates="diff_reports")


class CompareResult(Base):
    """对比结果表"""
    __tablename__ = "compare_result"

    id = Column(Integer, primary_key=True, autoincrement=True)
    replay_id = Column(Integer, ForeignKey("traffic_replay.id"), nullable=False)
    request_signature = Column(String(100), nullable=True)  # 请求签名
    original_resp = Column(Text, nullable=True)  # JSON
    replay_resp = Column(Text, nullable=True)  # JSON
    is_match = Column(Boolean, default=True)
    diff_fields = Column(Text, nullable=True)  # JSON
    latency_diff_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
