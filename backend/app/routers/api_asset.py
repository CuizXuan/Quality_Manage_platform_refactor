from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.platform import PlatformUser
from app.routers.platform_auth import get_current_platform_user
from app.services import api_asset_service as service
from app.schemas.api_asset import (
    ApiGroupCreate,
    ApiGroupUpdate,
    ApiGroupResponse,
    ApiGroupListResponse,
    ApiDefinitionCreate,
    ApiDefinitionUpdate,
    ApiDefinitionResponse,
    ApiDefinitionListResponse,
    ApiImportRequest,
    DebugPayloadResponse,
    OpenApiImportResult,
)
from app.services.log_service import LogService

router = APIRouter(prefix="/api/assets", tags=["API资产"])


# ── ApiGroup ──────────────────────────────────────────────────────────────────

@router.get("/groups", response_model=ApiGroupListResponse)
def list_groups(
    project_id: Optional[int] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    groups = service.list_groups(db, project_id, keyword)
    return ApiGroupListResponse(
        items=[ApiGroupResponse(
            id=g.id,
            project_id=g.project_id,
            name=g.name,
            parent_id=g.parent_id,
            sort_order=g.sort_order or 0,
            created_at=g.created_at.isoformat() if g.created_at else "",
            updated_at=g.updated_at.isoformat() if g.updated_at else "",
        ) for g in groups],
        total=len(groups),
        page=1,
        page_size=len(groups),
    )


@router.post("/groups", response_model=ApiGroupResponse)
def create_group(
    data: ApiGroupCreate,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    result = service.create_group(db, data)
    LogService(db, current_user.id, current_user.username).log_crud("创建", "API分组", result.name, result.id)
    return ApiGroupResponse(
        id=result.id,
        project_id=result.project_id,
        name=result.name,
        parent_id=result.parent_id,
        sort_order=result.sort_order or 0,
        created_at=result.created_at.isoformat() if result.created_at else "",
        updated_at=result.updated_at.isoformat() if result.updated_at else "",
    )


@router.put("/groups/{group_id}", response_model=ApiGroupResponse)
def update_group(
    group_id: int,
    data: ApiGroupUpdate,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    result = service.update_group(db, group_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="分组不存在")
    LogService(db, current_user.id, current_user.username).log_crud("更新", "API分组", result.name, result.id)
    return ApiGroupResponse(
        id=result.id,
        project_id=result.project_id,
        name=result.name,
        parent_id=result.parent_id,
        sort_order=result.sort_order or 0,
        created_at=result.created_at.isoformat() if result.created_at else "",
        updated_at=result.updated_at.isoformat() if result.updated_at else "",
    )


@router.delete("/groups/{group_id}")
def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    if not service.delete_group(db, group_id):
        raise HTTPException(status_code=404, detail="分组不存在")
    LogService(db, current_user.id, current_user.username).log_crud("删除", "API分组", None, group_id)
    return {"success": True}


# ── ApiDefinition ──────────────────────────────────────────────────────────────

@router.get("/apis", response_model=ApiDefinitionListResponse)
def list_apis(
    project_id: Optional[int] = None,
    group_id: Optional[int] = None,
    keyword: Optional[str] = None,
    method: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    items, total = service.list_apis(db, project_id, group_id, keyword, method, status, page=page, page_size=page_size)
    return ApiDefinitionListResponse(
        items=[_serialize_api(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/apis/{api_id}", response_model=ApiDefinitionResponse)
def get_api(
    api_id: int,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    result = service.get_api(db, api_id)
    if not result:
        raise HTTPException(status_code=404, detail="API 不存在")
    return _serialize_api(result)


@router.post("/apis", response_model=ApiDefinitionResponse)
def create_api(
    data: ApiDefinitionCreate,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    result = service.create_api(db, data)
    LogService(db, current_user.id, current_user.username).log_crud("创建", "API定义", result.name, result.id)
    return _serialize_api(result)


@router.put("/apis/{api_id}", response_model=ApiDefinitionResponse)
def update_api(
    api_id: int,
    data: ApiDefinitionUpdate,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    result = service.update_api(db, api_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="API 不存在")
    LogService(db, current_user.id, current_user.username).log_crud("更新", "API定义", result.name, result.id)
    return _serialize_api(result)


@router.delete("/apis/{api_id}")
def delete_api(
    api_id: int,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    if not service.delete_api(db, api_id):
        raise HTTPException(status_code=404, detail="API 不存在")
    LogService(db, current_user.id, current_user.username).log_crud("删除", "API定义", None, api_id)
    return {"success": True}


@router.get("/apis/{api_id}/debug-payload", response_model=DebugPayloadResponse)
def get_debug_payload(
    api_id: int,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    result = service.get_debug_payload(db, api_id)
    if not result:
        raise HTTPException(status_code=404, detail="API 不存在")
    return result


# ── Import / Export ──────────────────────────────────────────────────────────────

@router.post("/import/openapi", response_model=OpenApiImportResult)
def import_openapi(
    request: ApiImportRequest,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    try:
        result = service.import_openapi(
            db,
            source_type=request.source_type,
            source_url=request.source_url,
            raw_content=request.raw_content,
            project_id=request.project_id,
        )
        LogService(db, current_user.id, current_user.username).log(
            "导入", "OpenAPI", f"导入 {result['imported']} 个 API"
        )
        return OpenApiImportResult(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/export/openapi")
def export_openapi(
    project_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    return service.export_openapi(db, project_id)


# ── Generate Case ──────────────────────────────────────────────────────────────

@router.post("/apis/{api_id}/generate-case")
def generate_case(
    api_id: int,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    case = service.generate_case_from_api(db, api_id)
    if not case:
        raise HTTPException(status_code=404, detail="API 不存在")
    LogService(db, current_user.id, current_user.username).log_crud("生成", "测试用例", case.name, case.id)
    return {"id": case.id, "name": case.name, "auto_case_id": case.auto_case_id}


# ── Helpers ─────────────────────────────────────────────────────────────────────

def _serialize_api(api) -> ApiDefinitionResponse:
    import json as _json
    tags = []
    parameters = []
    request_body = {}
    responses = {}
    try:
        tags = _json.loads(api.tags) if api.tags else []
    except Exception:
        pass
    try:
        parameters = _json.loads(api.parameters) if api.parameters else []
    except Exception:
        pass
    try:
        request_body = _json.loads(api.request_body) if api.request_body else {}
    except Exception:
        pass
    try:
        responses = _json.loads(api.responses) if api.responses else {}
    except Exception:
        pass
    return ApiDefinitionResponse(
        id=api.id,
        project_id=api.project_id,
        group_id=api.group_id,
        name=api.name,
        method=api.method,
        path=api.path,
        base_url=api.base_url,
        summary=api.summary or "",
        description=api.description or "",
        tags=tags,
        parameters=parameters,
        request_body=request_body,
        responses=responses,
        version=api.version or "1.0.0",
        status=api.status or "active",
        created_at=api.created_at.isoformat() if api.created_at else "",
        updated_at=api.updated_at.isoformat() if api.updated_at else "",
    )