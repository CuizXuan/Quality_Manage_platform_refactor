"""
API 资产服务 — 接口定义分组、导入、生成用例
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.api_asset import ApiGroup, ApiDefinition, ApiImportRecord
from app.models.asset_trace import AssetTrace
from app.models.test_case import TestCase
from app.models.api_test_case import ApiTestCase
from app.schemas.api_asset import (
    ApiGroupCreate,
    ApiGroupUpdate,
    ApiDefinitionCreate,
    ApiDefinitionUpdate,
    ApiImportRequest,
)


def _loads(value: str, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


# ── ApiGroup ──────────────────────────────────────────────────────────────────

def list_groups(db: Session, project_id: Optional[int] = None, keyword: Optional[str] = None) -> List[ApiGroup]:
    query = db.query(ApiGroup)
    if project_id:
        query = query.filter(ApiGroup.project_id == project_id)
    if keyword:
        query = query.filter(ApiGroup.name.contains(keyword))
    return query.order_by(ApiGroup.sort_order.asc(), ApiGroup.id.asc()).all()


def create_group(db: Session, data: ApiGroupCreate) -> ApiGroup:
    group = ApiGroup(**data.model_dump())
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


def update_group(db: Session, group_id: int, data: ApiGroupUpdate) -> Optional[ApiGroup]:
    group = db.query(ApiGroup).filter(ApiGroup.id == group_id).first()
    if not group:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(group, key, value)
    db.commit()
    db.refresh(group)
    return group


def delete_group(db: Session, group_id: int) -> bool:
    group = db.query(ApiGroup).filter(ApiGroup.id == group_id).first()
    if not group:
        return False
    db.delete(group)
    db.commit()
    return True


# ── ApiDefinition ──────────────────────────────────────────────────────────────

def list_apis(
    db: Session,
    project_id: Optional[int] = None,
    group_id: Optional[int] = None,
    keyword: Optional[str] = None,
    method: Optional[str] = None,
    status: Optional[str] = None,
    tags: Optional[List[str]] = None,
    page: int = 1,
    page_size: int = 20,
) -> Tuple[List[ApiDefinition], int]:
    query = db.query(ApiDefinition)
    if project_id:
        query = query.filter(ApiDefinition.project_id == project_id)
    if group_id:
        query = query.filter(ApiDefinition.group_id == group_id)
    if keyword:
        query = query.filter(
            (ApiDefinition.name.contains(keyword)) | (ApiDefinition.path.contains(keyword))
        )
    if method:
        query = query.filter(ApiDefinition.method == method)
    if status:
        query = query.filter(ApiDefinition.status == status)
    if tags:
        # Filter by tags JSON array
        for tag in tags:
            query = query.filter(ApiDefinition.tags.contains(tag))

    total = query.count()
    offset = (page - 1) * page_size
    items = query.order_by(ApiDefinition.id.desc()).offset(offset).limit(page_size).all()
    return items, total


def get_api(db: Session, api_id: int) -> Optional[ApiDefinition]:
    return db.query(ApiDefinition).filter(ApiDefinition.id == api_id).first()


def list_services(db: Session, project_id: Optional[int] = None) -> List[Dict[str, Any]]:
    query = db.query(ApiDefinition)
    if project_id:
        query = query.filter(ApiDefinition.project_id == project_id)
    apis = query.order_by(ApiDefinition.id.desc()).all()
    services: Dict[str, Dict[str, Any]] = {}
    for api in apis:
        service_name = api.base_url or "default"
        if service_name not in services:
            services[service_name] = {
                "service_name": service_name,
                "api_count": 0,
                "latest_version": api.version or "1.0.0",
                "apis": [],
            }
        services[service_name]["api_count"] += 1
        services[service_name]["apis"].append(
            {
                "id": api.id,
                "name": api.name,
                "method": api.method,
                "path": api.path,
                "version": api.version or "1.0.0",
            }
        )
    return list(services.values())


def create_api(db: Session, data: ApiDefinitionCreate) -> ApiDefinition:
    payload = data.model_dump()
    for field in ("tags", "parameters", "request_body", "responses"):
        if field in payload and isinstance(payload[field], (dict, list)):
            payload[field] = json.dumps(payload[field])
    api = ApiDefinition(**payload)
    db.add(api)
    db.commit()
    db.refresh(api)
    return api


def update_api(db: Session, api_id: int, data: ApiDefinitionUpdate) -> Optional[ApiDefinition]:
    api = db.query(ApiDefinition).filter(ApiDefinition.id == api_id).first()
    if not api:
        return None
    updates = data.model_dump(exclude_unset=True)
    for field in ("tags", "parameters", "request_body", "responses"):
        if field in updates and isinstance(updates[field], (dict, list)):
            updates[field] = json.dumps(updates[field])
    for key, value in updates.items():
        setattr(api, key, value)
    db.commit()
    db.refresh(api)
    return api


def delete_api(db: Session, api_id: int) -> bool:
    api = db.query(ApiDefinition).filter(ApiDefinition.id == api_id).first()
    if not api:
        return False
    db.delete(api)
    db.commit()
    return True


def get_debug_payload(db: Session, api_id: int) -> Optional[Dict[str, Any]]:
    """Return payload for Terminal.vue to pre-fill."""
    api = db.query(ApiDefinition).filter(ApiDefinition.id == api_id).first()
    if not api:
        return None

    headers = {}
    params = {}
    body_type = "none"
    body = ""

    raw_params = _loads(api.parameters, [])
    if isinstance(raw_params, list):
        for p in raw_params:
            if p.get("in") == "header":
                headers[p.get("name", "")] = p.get("default", "")
            elif p.get("in") == "query":
                params[p.get("name", "")] = p.get("default", "")

    raw_body = _loads(api.request_body, {})
    if raw_body and isinstance(raw_body, dict):
        if raw_body.get("content"):
            content = raw_body["content"]
            if "application/json" in content:
                json_content = content["application/json"]
                # Prefer top-level example, then schema.example
                example = json_content.get("example")
                if example is None and "schema" in json_content:
                    example = json_content["schema"].get("example")
                if example is not None:
                    body_type = "json"
                    body = json.dumps(example, ensure_ascii=False) if isinstance(example, dict) else str(example)

    full_url = f"{api.base_url or ''}{api.path}"

    return {
        "api_id": api.id,
        "method": api.method,
        "url": full_url,
        "headers": headers,
        "query_params": params,
        "body_type": body_type,
        "body": body,
        "project_id": api.project_id,
        "source_type": api.source_type or "api_asset",
        "source_id": api.source_id or api.id,
        "version_tag": api.version_tag or api.version or "1.0.0",
    }


def diff_api_versions(db: Session, api_id: int) -> Optional[Dict[str, Any]]:
    current = get_api(db, api_id)
    if not current:
        return None
    previous = (
        db.query(ApiDefinition)
        .filter(
            ApiDefinition.path == current.path,
            ApiDefinition.method == current.method,
            ApiDefinition.id != current.id,
        )
        .order_by(ApiDefinition.id.desc())
        .first()
    )
    current_params = _loads(current.parameters, [])
    current_body = _loads(current.request_body, {})
    current_responses = _loads(current.responses, {})
    if not previous:
        return {
            "current_id": current.id,
            "previous_id": None,
            "changes": {
                "summary_changed": False,
                "parameter_delta": len(current_params),
                "response_code_delta": len(current_responses),
                "request_body_changed": bool(current_body),
            },
        }
    previous_params = _loads(previous.parameters, [])
    previous_body = _loads(previous.request_body, {})
    previous_responses = _loads(previous.responses, {})
    return {
        "current_id": current.id,
        "previous_id": previous.id,
        "changes": {
            "summary_changed": (current.summary or "") != (previous.summary or ""),
            "parameter_delta": len(current_params) - len(previous_params),
            "response_code_delta": len(current_responses) - len(previous_responses),
            "request_body_changed": current_body != previous_body,
        },
    }


def generate_baseline_from_api(db: Session, api_id: int) -> Optional[Dict[str, Any]]:
    api = get_api(db, api_id)
    if not api:
        return None
    generated_case = generate_case_from_api(db, api_id)
    if not generated_case:
        return None
    responses = _loads(api.responses, {})
    request_body = _loads(api.request_body, {})
    first_status = next(iter(responses.keys()), "200")
    return {
        "api_id": api.id,
        "test_case": {
            "id": generated_case.id,
            "name": generated_case.name,
            "auto_case_id": generated_case.auto_case_id,
        },
        "assertion_templates": [
            {
                "assertion_type": "status_code",
                "field": "status_code",
                "expected_value": first_status,
                "description": f"Expect status code {first_status}",
            }
        ],
        "scenario_draft": {
            "name": f"{api.name} baseline scenario",
            "description": f"Generated from API asset #{api.id}",
            "steps": [
                {
                    "case_id": generated_case.id,
                    "name": api.name,
                    "sort_order": 0,
                    "enabled": True,
                    "retry_count": 0,
                    "timeout_ms": 30000,
                    "failure_strategy": "stop",
                    "extract_rules": [],
                    "inject_rules": [],
                }
            ],
        },
        "request_has_body": bool(request_body),
    }


# ── OpenAPI Import ─────────────────────────────────────────────────────────────

def import_openapi(
    db: Session,
    source_type: str,
    source_url: Optional[str] = None,
    raw_content: Optional[str] = None,
    project_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Parse OpenAPI JSON and create ApiGroup + ApiDefinition records."""
    import httpx

    content = raw_content
    if source_type == "url" and source_url:
        try:
            resp = httpx.get(source_url, timeout=30)
            resp.raise_for_status()
            content = resp.text
        except Exception as e:
            raise ValueError(f"无法获取 OpenAPI 文档: {e}")

    if not content:
        raise ValueError("未提供内容")

    try:
        spec = json.loads(content)
    except json.JSONDecodeError:
        raise ValueError("OpenAPI JSON 解析失败")

    info = spec.get("info", {})
    title = info.get("title", "未命名 API")

    # Create root group
    root_group = ApiGroup(project_id=project_id, name=title, sort_order=0)
    db.add(root_group)
    db.commit()
    db.refresh(root_group)

    # Group paths by tags
    tag_groups: Dict[str, ApiGroup] = {title: root_group}
    paths = spec.get("paths", {})
    imported = 0
    skipped = 0

    for path, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        for method, operation in methods.items():
            if method.upper() not in ("GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"):
                continue

            if not isinstance(operation, dict):
                skipped += 1
                continue

            op_tags = operation.get("tags", [])
            group_name = op_tags[0] if op_tags else title
            if group_name not in tag_groups:
                g = ApiGroup(project_id=project_id, name=group_name, parent_id=root_group.id, sort_order=len(tag_groups))
                db.add(g)
                db.commit()
                db.refresh(g)
                tag_groups[group_name] = g
            group = tag_groups[group_name]

            summary = operation.get("summary", "")
            description = operation.get("description", "")
            parameters = operation.get("parameters", [])
            request_body = operation.get("requestBody", {})
            responses = operation.get("responses", {})

            api = ApiDefinition(
                project_id=project_id,
                group_id=group.id,
                name=summary or f"{method.upper()} {path}",
                method=method.upper(),
                path=path,
                base_url=spec.get("servers", [{}])[0].get("url", ""),
                summary=summary,
                description=description,
                tags=json.dumps(op_tags),
                parameters=json.dumps(parameters),
                request_body=json.dumps(request_body),
                responses=json.dumps(responses),
                version="1.0.0",
                status="active",
            )
            db.add(api)
            imported += 1

    # Record
    record = ApiImportRecord(
        project_id=project_id,
        source_type=source_type,
        source_url=source_url or "",
        status="success",
        imported_count=imported,
        message=f"导入成功: {imported} 个 API，{skipped} 个跳过",
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "total": imported + skipped,
        "imported": imported,
        "skipped": skipped,
        "groups_created": len(tag_groups),
        "message": record.message,
    }


def export_openapi(db: Session, project_id: Optional[int] = None) -> Dict[str, Any]:
    """Export all APIs as OpenAPI 3.0 dict."""
    apis = db.query(ApiDefinition)
    if project_id:
        apis = apis.filter(ApiDefinition.project_id == project_id)
    apis = apis.all()

    paths: Dict[str, Dict[str, Any]] = {}
    for api in apis:
        if api.path not in paths:
            paths[api.path] = {}
        op = {
            "summary": api.summary or api.name,
            "description": api.description or "",
            "tags": _loads(api.tags, []),
            "parameters": _loads(api.parameters, []),
            "requestBody": _loads(api.request_body, {}),
            "responses": _loads(api.responses, {}),
        }
        paths[api.path][api.method.lower()] = op

    return {
        "openapi": "3.0.0",
        "info": {"title": "API 资产导出", "version": "1.0.0"},
        "paths": paths,
    }


# ── Generate Case ──────────────────────────────────────────────────────────────

def generate_case_from_api(db: Session, api_id: int) -> Optional[TestCase]:
    """Create an API test case from an ApiDefinition."""
    api = db.query(ApiDefinition).filter(ApiDefinition.id == api_id).first()
    if not api:
        return None

    import uuid
    auto_case_id = f"APICASE-{uuid.uuid4().hex[:8].upper()}"

    # Extract headers/query/body BEFORE creating TestCase so we can use them
    debug = get_debug_payload(db, api.id) or {}
    headers_for_case = debug.get("headers", {})
    query_params_for_case = debug.get("query_params", {})
    body_type_for_case = debug.get("body_type", "none")
    body_for_case = debug.get("body", "")

    case = TestCase(
        name=api.summary or api.name,
        description=api.description or "",
        case_type="api",
        method=api.method,
        url=f"{api.base_url or ''}{api.path}",
        headers=json.dumps(headers_for_case, ensure_ascii=False),
        query_params=json.dumps(query_params_for_case, ensure_ascii=False),
        cookies=json.dumps({}),
        auth_config=json.dumps({}),
        body_type=body_type_for_case,
        body=body_for_case,
        auto_case_id=auto_case_id,
        project_id=api.project_id,
        source_api_id=api.id,
        source_type=api.source_type or "api_asset",
        source_id=api.id,
        version_tag=api.version_tag or api.version or "1.0.0",
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    api_case = ApiTestCase(
        testcase_id=case.id,
        url=f"{api.base_url or ''}{api.path}",
        method=api.method,
        headers=json.dumps(headers_for_case),
        params=json.dumps(query_params_for_case),
        body_type=body_type_for_case,
        body=body_for_case,
        assertions="[]",
    )
    db.add(api_case)
    db.flush()
    db.add(
        AssetTrace(
            source_type=api.source_type or "api_asset",
            source_id=api.id,
            target_type="test_case",
            target_id=case.id,
            relation_type="generated_baseline",
            project_id=api.project_id,
            version_tag=api.version_tag or api.version or "1.0.0",
            trace_metadata=json.dumps({"api_name": api.name, "case_name": case.name}, ensure_ascii=False),
        )
    )
    db.commit()
    db.refresh(case)

    return case
