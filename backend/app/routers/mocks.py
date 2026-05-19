import json
import re
import time
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from app.database import get_db
from app.models.mock_rule import MockRule
from app.schemas.mock_rule import MockRuleCreate, MockRuleUpdate, MockRuleResponse

router = APIRouter(prefix="/api/mocks", tags=["Mocks"])
mock_entry_router = APIRouter(prefix="/mock", tags=["Mock Entry"])


def _parse_mock_rule(rule: MockRule) -> dict:
    return {
        "id": rule.id,
        "name": rule.name,
        "description": rule.description,
        "path": rule.path,
        "method": rule.method,
        "response_status": rule.response_status,
        "response_headers": json.loads(rule.response_headers or "{}"),
        "response_body": rule.response_body,
        "response_template_type": rule.response_template_type,
        "delay_ms": rule.delay_ms,
        "match_conditions": json.loads(rule.match_conditions or "[]"),
        "enabled": rule.enabled,
        "hit_count": rule.hit_count,
        "created_at": rule.created_at,
        "updated_at": rule.updated_at,
    }


# ---------- Mock 管理 API ----------

@router.get("")
def list_mock_rules(
    enabled: Optional[bool] = Query(None),
    method: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(MockRule)
    if enabled is not None:
        query = query.filter(MockRule.enabled == enabled)
    if method:
        query = query.filter(MockRule.method == method.upper())
    if keyword:
        query = query.filter(MockRule.name.contains(keyword))
    rules = query.order_by(desc(MockRule.created_at)).offset(skip).limit(limit).all()
    return {"code": 0, "data": [_parse_mock_rule(r) for r in rules]}


@router.post("")
def create_mock_rule(data: MockRuleCreate, db: Session = Depends(get_db)):
    rule = MockRule(
        name=data.name,
        description=data.description,
        path=data.path,
        method=data.method.upper(),
        response_status=data.response_status,
        response_headers=json.dumps(data.response_headers or {}),
        response_body=data.response_body or "",
        response_template_type=data.response_template_type,
        delay_ms=data.delay_ms,
        match_conditions=json.dumps([c.model_dump() for c in (data.match_conditions or [])]),
        enabled=data.enabled,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return {"code": 0, "data": _parse_mock_rule(rule)}


@router.get("/{rule_id}")
def get_mock_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(MockRule).filter(MockRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Mock rule not found")
    return {"code": 0, "data": _parse_mock_rule(rule)}


@router.put("/{rule_id}")
def update_mock_rule(rule_id: int, data: MockRuleUpdate, db: Session = Depends(get_db)):
    rule = db.query(MockRule).filter(MockRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Mock rule not found")
    for key, value in data.model_dump().items():
        if value is not None:
            if key in ("response_headers", "match_conditions"):
                setattr(rule, key, json.dumps(value))
            elif key == "method":
                setattr(rule, key, value.upper())
            else:
                setattr(rule, key, value)
    db.commit()
    db.refresh(rule)
    return {"code": 0, "data": _parse_mock_rule(rule)}


@router.delete("/{rule_id}")
def delete_mock_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(MockRule).filter(MockRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Mock rule not found")
    db.delete(rule)
    db.commit()
    return {"code": 0, "message": "deleted"}


@router.post("/{rule_id}/toggle")
def toggle_mock_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(MockRule).filter(MockRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Mock rule not found")
    rule.enabled = not rule.enabled
    db.commit()
    db.refresh(rule)
    return {"code": 0, "data": _parse_mock_rule(rule)}


# ---------- Mock 实际入口（ANY 方法）----------

def _match_condition(condition: dict, request: Request, body: str) -> bool:
    """检查单个匹配条件是否满足"""
    cond_type = condition.get("type", "")
    key = condition.get("key", "")
    operator = condition.get("operator", "equals")
    expected = condition.get("value", "")

    if cond_type == "header":
        actual = request.headers.get(key, "")
    elif cond_type == "query":
        actual = request.query_params.get(key, "")
    elif cond_type == "body":
        try:
            body_json = json.loads(body)
            actual = body_json.get(key, "") if isinstance(body_json, dict) else ""
        except json.JSONDecodeError:
            actual = ""
    elif cond_type == "cookie":
        actual = request.cookies.get(key, "")
    else:
        return True  # 未知类型默认匹配

    if operator == "equals":
        return str(actual) == str(expected)
    elif operator == "contains":
        return str(expected) in str(actual)
    elif operator == "regex":
        try:
            return bool(re.search(str(expected), str(actual)))
        except re.error:
            return False
    elif operator == "exists":
        return bool(actual)
    return True


def _apply_template(template: str, request: Request, body: str, params: dict) -> str:
    """使用 Jinja2 模板渲染响应体"""
    try:
        from jinja2 import Template
        tmpl = Template(template)
        context = {
            "method": request.method,
            "path": request.url.path,
            "query": dict(request.query_params),
            "headers": dict(request.headers),
            "body": body,
            "params": params,
        }
        return tmpl.render(**context)
    except Exception:
        return template


@mock_entry_router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def mock_entry(path: str, request: Request, db: Session = Depends(get_db)):
    """
    Mock 入口：匹配 path 和 method，返回对应规则的响应。
    支持 Jinja2 模板渲染。
    """
    # 查找匹配的规则
    query = db.query(MockRule).filter(
        MockRule.path == f"/{path}",
        MockRule.enabled == True,
    )
    rules = query.all()

    if not rules:
        # 尝试路径前缀匹配
        query = db.query(MockRule).filter(
            MockRule.path.endswith("{path}"),
            MockRule.enabled == True,
        )
        rules = query.all()

    matched_rule = None
    req_body = ""
    try:
        req_body = await request.body()
        req_body_str = req_body.decode("utf-8") if req_body else ""
    except Exception:
        req_body_str = ""

    for rule in rules:
        conditions = json.loads(rule.match_conditions or "[]")
        if not conditions:
            matched_rule = rule
            break
        if all(_match_condition(c, request, req_body_str) for c in conditions):
            matched_rule = rule
            break

    if not matched_rule:
        return JSONResponse(
            status_code=404,
            content={"error": "Mock rule not found", "path": f"/{path}"},
        )

    # 延迟
    if matched_rule.delay_ms > 0:
        time.sleep(matched_rule.delay_ms / 1000.0)

    # 模板渲染
    response_body = matched_rule.response_body
    if matched_rule.response_template_type == "jinja2":
        response_body = _apply_template(
            matched_rule.response_body,
            request,
            req_body_str,
            {},
        )

    # 响应头
    resp_headers = json.loads(matched_rule.response_headers or "{}")
    resp_headers["Content-Type"] = resp_headers.get("Content-Type", "application/json")

    # 更新命中计数
    matched_rule.hit_count += 1
    db.commit()

    return JSONResponse(
        status_code=matched_rule.response_status,
        content=json.loads(response_body) if response_body.startswith("{") or response_body.startswith("[") else {"data": response_body},
        headers=resp_headers,
    )
