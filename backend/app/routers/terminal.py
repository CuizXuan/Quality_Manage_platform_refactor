import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.platform import PlatformUser
from app.routers.platform_auth import get_current_platform_user
from app.schemas.terminal import (
    DebugHistoryItem,
    DebugHistoryResponse,
    DebugRequestCreate,
    DebugRequestResponse,
    DebugResponse,
    ImportDocumentItem,
    ImportDocumentRequest,
    ImportDocumentResponse,
)
from app.services.terminal_service import TerminalService

router = APIRouter(prefix="/api/terminal", tags=["终端调试"])


def build_request_response(req, result=None) -> DebugRequestResponse:
    latest_result = None
    if result:
        latest_result = DebugResponse(
            id=result.id,
            status_code=result.status_code,
            response_headers=json.loads(result.response_headers) if result.response_headers else {},
            response_body=result.response_body,
            duration_ms=result.duration_ms,
            error_message=result.error_message or "",
            created_at=result.created_at.isoformat() if result.created_at else "",
        )
    return DebugRequestResponse(
        id=req.id,
        method=req.method,
        url=req.url,
        query_params=json.loads(req.query_params) if req.query_params else {},
        headers=json.loads(req.headers) if req.headers else {},
        cookies=json.loads(req.cookies) if req.cookies else {},
        auth_config=json.loads(req.auth_config) if req.auth_config else {},
        body_type=req.body_type or "none",
        body=req.body or "",
        status=req.status or "active",
        source_type=req.source_type or "manual",
        created_at=req.created_at.isoformat() if req.created_at else "",
        latest_result=latest_result,
    )


@router.post("/debug", response_model=DebugRequestResponse)
def debug_request(
    request: DebugRequestCreate,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    """Send a debug request and return the response."""
    service = TerminalService(db)
    req = service.create_debug_request(
        method=request.method,
        url=request.url,
        query_params=request.query_params,
        headers=request.headers,
        cookies=request.cookies,
        auth_config=request.auth_config,
        body_type=request.body_type,
        body=request.body,
        environment_id=request.environment_id,
        created_by=current_user.id,
        source_type="manual",
    )
    result = service.execute_debug(req.id)
    return build_request_response(req, result)


@router.get("/history", response_model=DebugHistoryResponse)
def get_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    """Get debug history for current user."""
    service = TerminalService(db)
    requests, total = service.get_history(
        page=page,
        page_size=page_size,
        created_by=current_user.id,
    )
    items = []
    for req in requests:
        latest_result = None
        if req.results:
            latest_result = sorted(req.results, key=lambda r: r.created_at, reverse=True)[0]
        items.append(
            DebugHistoryItem(
                id=req.id,
                method=req.method,
                url=req.url,
                status=req.status or "active",
                status_code=latest_result.status_code if latest_result else None,
                duration_ms=latest_result.duration_ms if latest_result else None,
                created_at=req.created_at.isoformat() if req.created_at else "",
            )
        )
    return DebugHistoryResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/history/{request_id}", response_model=DebugRequestResponse)
def get_request(
    request_id: int,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    """Get a specific debug request with its latest result."""
    service = TerminalService(db)
    req = service.get_request_with_result(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    latest_result = None
    if req.results:
        latest_result = sorted(req.results, key=lambda r: r.created_at, reverse=True)[0]
    return build_request_response(req, latest_result)


@router.post("/history/{request_id}/favorite")
def toggle_favorite(
    request_id: int,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    """Toggle favorite status of a debug request."""
    service = TerminalService(db)
    try:
        req = service.toggle_favorite(request_id)
        return {"id": req.id, "status": req.status}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/history/{request_id}")
def delete_request(
    request_id: int,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    """Delete a debug request."""
    service = TerminalService(db)
    if not service.delete_request(request_id):
        raise HTTPException(status_code=404, detail="Request not found")
    return {"message": "Deleted successfully"}


@router.post("/import-document", response_model=ImportDocumentResponse)
def import_document(
    request: ImportDocumentRequest,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    service = TerminalService(db)
    try:
      items = service.import_openapi_document(
          source_url=request.source_url or "",
          raw_content=request.raw_content or "",
      )
    except Exception as e:
      raise HTTPException(status_code=400, detail=str(e))

    return ImportDocumentResponse(
        items=[ImportDocumentItem(**item) for item in items],
        total=len(items),
    )
