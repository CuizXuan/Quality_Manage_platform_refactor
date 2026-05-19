# -*- coding: utf-8 -*-
"""
Phase 5 - 审计日志数据模型
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Index, JSON
from sqlalchemy.sql import func
from app.models.base import Base


class AuditLog(Base):
    """审计日志表"""
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    method = Column(String(10), nullable=False)
    path = Column(String(500), nullable=False)
    operation = Column(String(100), nullable=False)
    user_id = Column(Integer)
    tenant_id = Column(Integer)
    client_ip = Column(String(45))
    status_code = Column(Integer)
    duration_ms = Column(Integer)
    request_body = Column(Text)  # 已脱敏
    response_size = Column(Integer)
    error_message = Column(Text)
    is_sensitive = Column(Boolean, default=False)  # 高敏感操作
    user_agent = Column(String(500))
    created_at = Column(DateTime, server_default=func.now())

    # 索引
    __table_args__ = (
        Index("ix_audit_user_time", "user_id", "created_at"),
        Index("ix_audit_operation", "operation", "created_at"),
        Index("ix_audit_tenant_time", "tenant_id", "created_at"),
        Index("ix_audit_sensitive", "is_sensitive", "created_at"),
    )


class SecurityEvent(Base):
    """安全事件表"""
    __tablename__ = "security_event"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(50), nullable=False)  # login_failed/brute_force/suspicious_access
    severity = Column(String(20), nullable=False)  # low/medium/high/critical
    user_id = Column(Integer)
    client_ip = Column(String(45))
    user_agent = Column(String(500))
    details = Column(JSON)  # 事件详情
    resolved = Column(Boolean, default=False)
    resolved_by = Column(Integer)
    resolved_at = Column(DateTime)
    resolution_notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_security_event_type_time", "event_type", "created_at"),
        Index("ix_security_event_user", "user_id", "created_at"),
    )
