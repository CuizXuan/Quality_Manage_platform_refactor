"""Operation Log Router — 日志查询 API"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.platform import OperationLog
from app.schemas.log import LogListResponse, LogResponse, LogQuery

router = APIRouter(prefix="/api/logs", tags=["logs"])


def _build_filter(query: LogQuery):
    kwargs = {}
    if query.keyword:
        kwargs["or"] = (
            OperationLog.username.ilike(f"%{query.keyword}%"),
            OperationLog.action.ilike(f"%{query.keyword}%"),
            OperationLog.detail.ilike(f"%{query.keyword}%"),
            OperationLog.module.ilike(f"%{query.keyword}%"),
        )
    if query.module:
        kwargs["module"] = query.module
    if query.action:
        kwargs["action"] = query.action
    if query.start_date:
        kwargs["created_at"] = OperationLog.created_at >= query.start_date
    if query.end_date:
        kwargs["created_at"] = OperationLog.created_at <= query.end_date
    return kwargs


@router.get("", response_model=LogListResponse)
def list_logs(query: LogQuery = Depends(), db: Session = Depends(get_db)):
    """分页 + 模糊搜索查询操作日志。"""
    filter_kwargs = _build_filter(query)
    q = db.query(OperationLog).filter(**filter_kwargs).order_by(OperationLog.created_at.desc())
    total = q.count()
    items = q.offset((query.page - 1) * query.page_size).limit(query.page_size).all()
    return LogListResponse(
        items=[LogResponse.model_validate(r) for r in items],
        total=total,
        page=query.page,
        page_size=query.page_size,
    )
