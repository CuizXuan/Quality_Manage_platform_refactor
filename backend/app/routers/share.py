# -*- coding: utf-8 -*-
"""
Phase 4 - 资产共享路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app.models.tenant import User
from app.services.auth_service import AuthService
from app.services.share_service import ShareService

router = APIRouter(prefix="/api/share", tags=["资产共享"])
security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    if not credentials:
        raise HTTPException(status_code=401, detail="未提供认证令牌")
    auth_service = AuthService(db)
    payload = auth_service.decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="令牌无效或已过期")
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


# ==================== 请求/响应模型 ====================

class ShareCreate(BaseModel):
    asset_type: str
    asset_id: int
    shared_to_tenant_id: Optional[int] = None
    shared_to_project_id: Optional[int] = None
    permission: str = "read"
    expires_days: Optional[int] = None


class ShareUpdate(BaseModel):
    shared_to_tenant_id: Optional[int] = None
    shared_to_project_id: Optional[int] = None
    permission: Optional[str] = None
    expires_days: Optional[int] = None


class ImportRequest(BaseModel):
    share_id: int
    target_project_id: int


class ShareResponse(BaseModel):
    id: int
    asset_type: str
    asset_id: int
    owner_tenant_id: int
    owner_project_id: Optional[int]
    shared_to_tenant_id: Optional[int]
    shared_to_project_id: Optional[int]
    permission: str
    owner_username: Optional[str]
    created_at: str
    expires_at: Optional[str]


class PageResponse(BaseModel):
    items: List[ShareResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==================== API ====================

@router.get("/assets", summary="获取共享资产列表")
def get_shared_assets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    asset_type: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取共享资产列表（包括收到的、发出的和公开的）"""
    share_service = ShareService(db)
    assets, total = share_service.get_shared_assets(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        asset_type=asset_type,
        keyword=keyword
    )
    
    total_pages = (total + page_size - 1) // page_size
    
    return PageResponse(
        items=[ShareResponse(**a) for a in assets],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/assets/received", summary="获取收到的共享")
def get_received_assets(
    project_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取收到的共享资产"""
    share_service = ShareService(db)
    assets, total = share_service.get_received_assets(
        tenant_id=current_user.tenant_id,
        project_id=project_id,
        page=page,
        page_size=page_size
    )
    
    total_pages = (total + page_size - 1) // page_size
    
    return PageResponse(
        items=[ShareResponse(**a) for a in assets],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/assets/sent", summary="获取发出的共享")
def get_sent_assets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取我发出的共享"""
    share_service = ShareService(db)
    assets, total = share_service.get_sent_assets(
        tenant_id=current_user.tenant_id,
        page=page,
        page_size=page_size
    )
    
    total_pages = (total + page_size - 1) // page_size
    
    return PageResponse(
        items=[ShareResponse(**a) for a in assets],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.post("/assets", summary="分享资产")
def create_share(
    request: ShareCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """分享资产给其他租户或项目"""
    share_service = ShareService(db)
    
    # 获取用户所在项目（简化处理，实际应该从请求中获取）
    from app.models.tenant import ProjectMember
    member = db.query(ProjectMember).filter(
        ProjectMember.user_id == current_user.id
    ).first()
    owner_project_id = member.project_id if member else None
    
    share, success, error = share_service.create_share(
        owner_tenant_id=current_user.tenant_id,
        owner_project_id=owner_project_id,
        user_id=current_user.id,
        asset_type=request.asset_type,
        asset_id=request.asset_id,
        shared_to_tenant_id=request.shared_to_tenant_id,
        shared_to_project_id=request.shared_to_project_id,
        permission=request.permission,
        expires_days=request.expires_days
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    return ShareResponse(
        id=share.id,
        asset_type=share.asset_type,
        asset_id=share.asset_id,
        owner_tenant_id=share.owner_tenant_id,
        owner_project_id=share.owner_project_id,
        shared_to_tenant_id=share.shared_to_tenant_id,
        shared_to_project_id=share.shared_to_project_id,
        permission=share.permission,
        owner_username=current_user.username,
        created_at=share.created_at.isoformat() if share.created_at else "",
        expires_at=share.expires_at.isoformat() if share.expires_at else None
    )


@router.put("/assets/{share_id}", summary="更新共享")
def update_share(
    share_id: int,
    request: ShareUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新共享设置"""
    share_service = ShareService(db)
    share, success, error = share_service.update_share(
        share_id=share_id,
        user_id=current_user.tenant_id,  # 使用租户ID
        shared_to_tenant_id=request.shared_to_tenant_id,
        shared_to_project_id=request.shared_to_project_id,
        permission=request.permission,
        expires_days=request.expires_days
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    return {"message": "更新成功"}


@router.delete("/assets/{share_id}", summary="取消分享")
def delete_share(
    share_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取消分享"""
    share_service = ShareService(db)
    success, error = share_service.delete_share(
        share_id=share_id,
        user_id=current_user.tenant_id
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    return {"message": "取消成功"}


@router.post("/assets/import", summary="导入共享资产")
def import_asset(
    request: ImportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """导入共享资产到本地"""
    share_service = ShareService(db)
    success, error = share_service.import_asset(
        share_id=request.share_id,
        user_id=current_user.id,
        target_project_id=request.target_project_id
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    return {"message": error or "导入成功"}
