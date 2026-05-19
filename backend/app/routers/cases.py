from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
import json
import functools
import time
import asyncio
import logging

logger = logging.getLogger(__name__)

from app.database import get_db
from app.models.case import TestCase
from app.models.environment import Environment
from app.models.execution_log import ExecutionLog
from app.schemas.case import TestCaseCreate, TestCaseUpdate, TestCaseResponse, RunCaseRequest, BatchDeleteRequest
from app.services.request_executor import RequestExecutor
from app.middleware.tenant_middleware import get_current_tenant_id

router = APIRouter(prefix="/api/cases", tags=["Cases"])


def get_tenant_id(request: Request) -> int:
    """从请求状态获取当前租户 ID"""
    tenant_id = get_current_tenant_id(request)
    if tenant_id is None:
        raise HTTPException(status_code=403, detail="需要租户权限")
    return tenant_id


@router.get("", response_model=List[TestCaseResponse])
def list_cases(
    folder: Optional[str] = Query(None),
    method: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    query = db.query(TestCase).filter(TestCase.tenant_id == tenant_id)
    if folder:
        query = query.filter(TestCase.folder_path == folder)
    if method:
        query = query.filter(TestCase.method == method.upper())
    if keyword:
        query = query.filter(or_(
            TestCase.name.contains(keyword),
            TestCase.url.contains(keyword),
        ))
    cases = query.order_by(TestCase.created_at.desc(), TestCase.id.desc()).offset(skip).limit(limit).all()
    return [_parse_case(c) for c in cases]


@router.post("", response_model=TestCaseResponse)
def create_case(
    data: TestCaseCreate,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    case = TestCase(
        tenant_id=tenant_id,
        name=data.name,
        description=data.description,
        method=data.method,
        url=data.url,
        headers=json.dumps(data.headers or {}),
        params=json.dumps(data.params or {}),
        body=data.body or "",
        body_type=data.body_type,
        request_body=data.request_body or "",
        response_body=data.response_body or "",
        auth_type=data.auth_type,
        auth_config=json.dumps(data.auth_config or {}),
        folder_path=data.folder_path,
        sort_order=data.sort_order,
        assertions=json.dumps([a.model_dump() for a in (data.assertions or [])]),
        pre_script=data.pre_script or "",
        post_script=data.post_script or "",
        timeout=data.timeout,
        follow_redirects=data.follow_redirects,
        verify_ssl=data.verify_ssl,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return _parse_case(case)


@router.get("/{case_id}", response_model=TestCaseResponse)
def get_case(case_id: int, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    case = db.query(TestCase).filter(TestCase.id == case_id, TestCase.tenant_id == tenant_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return _parse_case(case)


@router.put("/{case_id}", response_model=TestCaseResponse)
def update_case(case_id: int, data: TestCaseUpdate, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    case = db.query(TestCase).filter(TestCase.id == case_id, TestCase.tenant_id == tenant_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        if value is None:
            continue
        if key in ("headers", "params", "auth_config", "assertions"):
            setattr(case, key, json.dumps(value) if value else "{}")
        else:
            setattr(case, key, value)
    db.commit()
    db.refresh(case)
    return _parse_case(case)


@router.delete("/{case_id}")
def delete_case(case_id: int, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    case = db.query(TestCase).filter(TestCase.id == case_id, TestCase.tenant_id == tenant_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    db.delete(case)
    db.commit()
    return {"code": 0, "message": "deleted"}


@router.post("/{case_id}/duplicate", response_model=TestCaseResponse)
def duplicate_case(case_id: int, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    original = db.query(TestCase).filter(TestCase.id == case_id, TestCase.tenant_id == tenant_id).first()
    if not original:
        raise HTTPException(status_code=404, detail="Case not found")
    new_case = TestCase(
        tenant_id=tenant_id,
        name=f"{original.name}-复制",
        description=original.description,
        method=original.method,
        url=original.url,
        headers=original.headers,
        params=original.params,
        body=original.body,
        body_type=original.body_type,
        request_body=original.request_body,
        response_body=original.response_body,
        auth_type=original.auth_type,
        auth_config=original.auth_config,
        folder_path=original.folder_path,
        sort_order=original.sort_order + 1,
        assertions=original.assertions,
        pre_script=original.pre_script,
        post_script=original.post_script,
        timeout=original.timeout,
        follow_redirects=original.follow_redirects,
        verify_ssl=original.verify_ssl,
    )
    db.add(new_case)
    db.commit()
    db.refresh(new_case)
    return _parse_case(new_case)


@router.post("/batch-delete")
def batch_delete_cases(request_data: BatchDeleteRequest, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    ids = request_data.ids
    db.query(TestCase).filter(TestCase.id.in_(ids), TestCase.tenant_id == tenant_id).delete(synchronize_session=False)
    db.commit()
    return {"code": 0, "message": f"deleted {len(ids)} cases"}


@router.post("/{case_id}/run")
async def run_case(case_id: int, body: RunCaseRequest, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    logger.info(f"[run_case] start case_id={case_id}")

    case = db.query(TestCase).filter(TestCase.id == case_id, TestCase.tenant_id == tenant_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    logger.info(f"[run_case] found case: name={case.name}, url={case.url}")

    # 获取环境变量（需要 tenant 过滤）
    env_vars = {}
    env_id = body.environment_id
    if env_id:
        env = db.query(Environment).filter(Environment.id == env_id, Environment.tenant_id == tenant_id).first()
        if env:
            env_vars = json.loads(env.variables or "{}")
    else:
        # 使用默认环境
        env = db.query(Environment).filter(Environment.is_default == True, Environment.tenant_id == tenant_id).first()
        if env:
            env_id = env.id
            env_vars = json.loads(env.variables or "{}")

    case_data = _parse_case(case)

    # 执行用例
    executor = RequestExecutor()
    try:
        result = await asyncio.wait_for(
            executor.execute_case(case_data, env_vars, body.variables),
            timeout=30.0
        )
        logger.info(f"[run_case] executor.execute_case completed, result keys={result.keys() if isinstance(result, dict) else result}")
    except asyncio.TimeoutError:
        logger.error(f"[run_case] executor.execute_case TIMEOUT after 30s")
        raise HTTPException(status_code=504, detail="Execution timeout after 30s")
    except Exception as e:
        logger.error(f"[run_case] executor.execute_case exception: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"用例执行失败: {str(e)}")

    # 保存执行记录（带 tenant_id）
    log = ExecutionLog(
        tenant_id=tenant_id,
        case_id=case_id,
        scenario_id=None,
        scenario_step_id=None,
        execution_type="single",
        execution_id=result["execution_id"],
        request_url=case.url,
        request_method=case.method,
        request_headers=case.headers,
        request_body=case.body,
        response_status=result["response"]["status_code"],
        response_headers=json.dumps(result["response"]["headers"]),
        response_body=json.dumps(result["response"]["body"]) if isinstance(result["response"]["body"], (dict, list)) else str(result["response"]["body"]),
        response_size=result["response"]["size"],
        response_time_ms=result["response"]["time_ms"],
        status=result["status"],
        assertion_results=json.dumps(result["assertion_results"]),
        environment_id=env_id,
        triggered_by="user",
    )
    db.add(log)
    db.commit()

    return {"code": 0, "message": "success", "data": result}


def _safe_json(value, default):
    """Safely parse JSON, handling both list and dict stored as string.

    Ensures list-type fields never receive a dict (converts {} -> []).
    """
    if not value:
        return default
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            # Empty dict stored in a list-type field -> return empty list
            if isinstance(default, list):
                return []
            return parsed
        return default
    except (json.JSONDecodeError, TypeError):
        return default

def _parse_case(case: TestCase) -> dict:
    return {
        "id": case.id,
        "name": case.name,
        "description": case.description,
        "method": case.method,
        "url": case.url,
        "headers": _safe_json(case.headers, {}),
        "params": _safe_json(case.params, {}),
        "body": case.body,
        "body_type": case.body_type,
        "request_body": case.request_body or "",
        "response_body": case.response_body or "",
        "auth_type": case.auth_type,
        "auth_config": _safe_json(case.auth_config, {}),
        "folder_path": case.folder_path,
        "sort_order": case.sort_order,
        "assertions": _safe_json(case.assertions, []),
        "pre_script": case.pre_script,
        "post_script": case.post_script,
        "timeout": case.timeout,
        "follow_redirects": case.follow_redirects,
        "verify_ssl": case.verify_ssl,
        "created_at": case.created_at if case.created_at else None,
        "updated_at": case.updated_at if case.updated_at else None,
    }
