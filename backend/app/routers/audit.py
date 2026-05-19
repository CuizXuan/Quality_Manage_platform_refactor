# -*- coding: utf-8 -*-
"""
Phase 5 - 审计日志 API
"""
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
from datetime import datetime, timedelta
from typing import Optional
from app.database import get_db
from app.models.audit_models import AuditLog, SecurityEvent

router = APIRouter(prefix="/api/audit", tags=["审计日志 (Phase 5)"])


def get_db_session():
    db_gen = get_db()
    return next(db_gen)


@router.get("/logs")
async def get_audit_logs(
    req: Request,
    operation: Optional[str] = None,
    user_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    is_sensitive: Optional[bool] = None,
    page: int = 1,
    page_size: int = 50,
):
    """查询审计日志"""
    db = get_db_session()
    try:
        query = db.query(AuditLog)

        # 租户隔离（如果不是超级管理员）
        req_user_id = getattr(req.state, "user_id", None)
        req_tenant_id = getattr(req.state, "tenant_id", None)
        is_admin = getattr(req.state, "is_superadmin", False)

        if not is_admin and req_user_id:
            # 普通用户只看自己的操作
            query = query.filter(AuditLog.user_id == req_user_id)
        elif req_tenant_id:
            # 租户管理员看租户内所有操作
            query = query.filter(AuditLog.tenant_id == req_tenant_id)

        # 筛选条件
        if operation:
            query = query.filter(AuditLog.operation == operation)

        if user_id:
            query = query.filter(AuditLog.user_id == user_id)

        if is_sensitive is not None:
            query = query.filter(AuditLog.is_sensitive == is_sensitive)

        if start_date:
            try:
                start = datetime.fromisoformat(start_date)
                query = query.filter(AuditLog.created_at >= start)
            except ValueError:
                pass

        if end_date:
            try:
                end = datetime.fromisoformat(end_date)
                query = query.filter(AuditLog.created_at <= end)
            except ValueError:
                pass

        # 排序
        query = query.order_by(desc(AuditLog.created_at))

        # 分页
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [_serialize_audit(a) for a in items],
        }
    finally:
        db.close()


@router.get("/logs/{log_id}")
async def get_audit_log_detail(
    log_id: int,
    req: Request,
):
    """获取审计日志详情"""
    db = get_db_session()
    try:
        log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
        if not log:
            return {"error": "Log not found"}

        return _serialize_audit(log)
    finally:
        db.close()


@router.get("/stats/overview")
async def get_audit_stats(
    req: Request,
    days: int = 7,
):
    """获取审计统计概览"""
    db = get_db_session()
    try:
        since = datetime.now() - timedelta(days=days)

        # 操作类型统计
        op_stats = (
            db.query(AuditLog.operation, func.count(AuditLog.id).label("count"))
            .filter(AuditLog.created_at >= since)
            .group_by(AuditLog.operation)
            .order_by(desc("count"))
            .limit(10)
            .all()
        )

        # 每日请求量趋势（兼容 SQLite: strftime，PostgreSQL/MySQL: func.date）
        if "sqlite" in str(db.bind.dialect):
            date_expr = func.strftime('%Y-%m-%d', AuditLog.created_at).label("date")
            date_group = func.strftime('%Y-%m-%d', AuditLog.created_at)
        else:
            date_expr = func.date(AuditLog.created_at).label("date")
            date_group = func.date(AuditLog.created_at)

        daily_stats = (
            db.query(
                date_expr,
                func.count(AuditLog.id).label("count"),
            )
            .filter(AuditLog.created_at >= since)
            .group_by(date_group)
            .order_by("date")
            .all()
        )

        # 高敏感操作统计
        sensitive_count = (
            db.query(func.count(AuditLog.id))
            .filter(AuditLog.created_at >= since)
            .filter(AuditLog.is_sensitive == True)
            .scalar()
        )

        return {
            "period_days": days,
            "operation_stats": [{"operation": op, "count": cnt} for op, cnt in op_stats],
            "daily_trend": [{"date": str(d), "count": c} for d, c in daily_stats],
            "sensitive_operations": sensitive_count or 0,
        }
    finally:
        db.close()


@router.get("/security/events")
async def get_security_events(
    req: Request,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    resolved: Optional[bool] = None,
    page: int = 1,
    page_size: int = 20,
):
    """查询安全事件"""
    db = get_db_session()
    try:
        query = db.query(SecurityEvent)

        if event_type:
            query = query.filter(SecurityEvent.event_type == event_type)
        if severity:
            query = query.filter(SecurityEvent.severity == severity)
        if resolved is not None:
            query = query.filter(SecurityEvent.resolved == resolved)

        query = query.order_by(desc(SecurityEvent.created_at))

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [_serialize_security_event(e) for e in items],
        }
    finally:
        db.close()


@router.post("/security/events/{event_id}/resolve")
async def resolve_security_event(
    event_id: int,
    req: Request,
    notes: str = "",
):
    """标记安全事件已处理"""
    db = get_db_session()
    try:
        event = db.query(SecurityEvent).filter(SecurityEvent.id == event_id).first()
        if not event:
            return {"error": "Event not found"}

        event.resolved = True
        event.resolved_by = getattr(req.state, "user_id", None)
        event.resolved_at = datetime.now()
        event.resolution_notes = notes

        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


def _serialize_audit(log: AuditLog) -> dict:
    return {
        "id": log.id,
        "method": log.method,
        "path": log.path,
        "operation": log.operation,
        "user_id": log.user_id,
        "tenant_id": log.tenant_id,
        "client_ip": log.client_ip,
        "status_code": log.status_code,
        "duration_ms": log.duration_ms,
        "is_sensitive": log.is_sensitive,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }


def _serialize_security_event(event: SecurityEvent) -> dict:
    return {
        "id": event.id,
        "event_type": event.event_type,
        "severity": event.severity,
        "user_id": event.user_id,
        "client_ip": event.client_ip,
        "details": event.details,
        "resolved": event.resolved,
        "resolved_at": event.resolved_at.isoformat() if event.resolved_at else None,
        "created_at": event.created_at.isoformat() if event.created_at else None,
    }
