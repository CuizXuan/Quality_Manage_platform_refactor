# -*- coding: utf-8 -*-
"""
Phase 4 - 资产模板路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List, Any
from app.database import get_db
from app.models.tenant import User
from app.services.auth_service import AuthService
from app.services.template_service import TemplateService

router = APIRouter(prefix="/api/templates", tags=["资产模板"])
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

class TemplateCreate(BaseModel):
    name: str
    type: str
    content: Any
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: bool = False


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[Any] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None


class TemplateResponse(BaseModel):
    id: int
    name: str
    type: str
    content: Any
    description: Optional[str]
    tags: List[str]
    icon: Optional[str]
    usage_count: int
    tenant_id: Optional[int]
    is_public: bool
    created_at: str
    updated_at: str


class PageResponse(BaseModel):
    items: List[TemplateResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==================== API ====================

@router.get("", summary="获取模板列表")
def get_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type: Optional[str] = Query(None, alias="type"),
    keyword: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取模板列表（包括系统模板、公开模板和租户模板）"""
    template_service = TemplateService(db)
    templates, total = template_service.get_templates(
        tenant_id=current_user.tenant_id,
        page=page,
        page_size=page_size,
        template_type=type,
        keyword=keyword
    )
    
    total_pages = (total + page_size - 1) // page_size
    
    return PageResponse(
        items=[TemplateResponse(**t) for t in templates],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/market", summary="获取模板市场")
def get_template_market(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type: Optional[str] = Query(None, alias="type"),
    keyword: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取公开模板市场"""
    template_service = TemplateService(db)
    templates, total = template_service.get_template_market(
        page=page,
        page_size=page_size,
        template_type=type,
        keyword=keyword
    )
    
    total_pages = (total + page_size - 1) // page_size
    
    return PageResponse(
        items=[TemplateResponse(**t) for t in templates],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/mine", summary="获取我的模板")
def get_my_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取我创建的模板"""
    template_service = TemplateService(db)
    templates, total = template_service.get_my_templates(
        tenant_id=current_user.tenant_id,
        page=page,
        page_size=page_size
    )
    
    total_pages = (total + page_size - 1) // page_size
    
    return PageResponse(
        items=[TemplateResponse(**t) for t in templates],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{template_id}", summary="获取模板详情")
def get_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取模板详情"""
    template_service = TemplateService(db)
    template = template_service.get_template_by_id(template_id)
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    return TemplateResponse(**template)


@router.post("", summary="创建模板")
def create_template(
    request: TemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建新模板"""
    template_service = TemplateService(db)
    template, success, error = template_service.create_template(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        name=request.name,
        template_type=request.type,
        content=request.content,
        description=request.description,
        tags=request.tags,
        is_public=request.is_public
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    return TemplateResponse(**template_service.get_template_by_id(template.id))


@router.put("/{template_id}", summary="更新模板")
def update_template(
    template_id: int,
    request: TemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新模板"""
    template_service = TemplateService(db)
    template, success, error = template_service.update_template(
        template_id=template_id,
        user_id=current_user.tenant_id,
        name=request.name,
        description=request.description,
        content=request.content,
        tags=request.tags,
        is_public=request.is_public
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    return {"message": "更新成功"}


@router.delete("/{template_id}", summary="删除模板")
def delete_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除模板"""
    template_service = TemplateService(db)
    success, error = template_service.delete_template(
        template_id=template_id,
        user_id=current_user.tenant_id
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    return {"message": "删除成功"}


@router.post("/{template_id}/use", summary="使用模板")
def use_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """使用模板（获取模板内容）"""
    template_service = TemplateService(db)
    result, success, error = template_service.use_template(template_id)
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    return result
