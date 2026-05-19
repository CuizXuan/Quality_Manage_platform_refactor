from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.execution_log import ExecutionLog
from app.middleware.tenant_middleware import get_current_tenant_id
import json

router = APIRouter(prefix="/api/logs", tags=["Logs"])


def get_tenant_id(request: Request):
    tenant_id = get_current_tenant_id(request)
    if tenant_id is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="需要租户权限")
    return tenant_id


@router.get("")
def list_logs(
    request: Request,
    case_id: Optional[int] = Query(None),
    scenario_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    query = db.query(ExecutionLog).filter(ExecutionLog.tenant_id == tenant_id)
    if case_id:
        query = query.filter(ExecutionLog.case_id == case_id)
    if scenario_id:
        query = query.filter(ExecutionLog.scenario_id == scenario_id)
    if status:
        query = query.filter(ExecutionLog.status == status)
    logs = query.order_by(ExecutionLog.created_at.desc()).offset(skip).limit(limit).all()
    return [_parse_log(l) for l in logs]


@router.get("/{log_id}")
def get_log(request: Request, log_id: int, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    log = db.query(ExecutionLog).filter(
        ExecutionLog.id == log_id,
        ExecutionLog.tenant_id == tenant_id
    ).first()
    if not log:
        return {"error": "not found"}
    return _parse_log(log)


@router.delete("/{log_id}")
def delete_log(request: Request, log_id: int, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    log = db.query(ExecutionLog).filter(
        ExecutionLog.id == log_id,
        ExecutionLog.tenant_id == tenant_id
    ).first()
    if log:
        db.delete(log)
        db.commit()
    return {"code": 0, "message": "deleted"}


@router.delete("/batch-delete")
def batch_delete_logs(request: Request, ids: List[int] = Query(...), db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    db.query(ExecutionLog).filter(
        ExecutionLog.id.in_(ids),
        ExecutionLog.tenant_id == tenant_id
    ).delete(synchronize_session=False)
    db.commit()
    return {"code": 0, "message": f"deleted {len(ids)} logs"}


def _parse_log(log: ExecutionLog) -> dict:
    return {
        "id": log.id,
        "case_id": log.case_id,
        "scenario_id": log.scenario_id,
        "scenario_step_id": log.scenario_step_id,
        "execution_type": log.execution_type,
        "execution_id": log.execution_id,
        "request_url": log.request_url,
        "request_method": log.request_method,
        "request_headers": json.loads(log.request_headers or "{}"),
        "request_body": log.request_body,
        "response_status": log.response_status,
        "response_headers": json.loads(log.response_headers or "{}"),
        "response_body": log.response_body,
        "response_size": log.response_size,
        "response_time_ms": log.response_time_ms,
        "status": log.status,
        "error_message": log.error_message,
        "assertion_results": json.loads(log.assertion_results or "[]"),
        "environment_id": log.environment_id,
        "triggered_by": log.triggered_by,
        "created_at": log.created_at,
    }
