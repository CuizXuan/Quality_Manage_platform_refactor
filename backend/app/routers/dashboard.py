# -*- coding: utf-8 -*-
"""
Phase 4 - 仪表盘路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List, Any
from app.database import get_db
from app.models.tenant import User
from app.services.auth_service import AuthService
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/dashboards", tags=["仪表盘"])
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

class DashboardCreate(BaseModel):
    name: str
    type: str  # personal/project/tenant/system
    layout_config: Optional[dict] = None


class DashboardUpdate(BaseModel):
    name: Optional[str] = None
    layout_config: Optional[dict] = None
    is_default: Optional[bool] = None


class WidgetCreate(BaseModel):
    widget_type: str
    title: Optional[str] = None
    config: Optional[dict] = None
    position: Optional[dict] = None


class WidgetUpdate(BaseModel):
    title: Optional[str] = None
    config: Optional[dict] = None
    position: Optional[dict] = None
    refresh_interval: Optional[int] = None


class DashboardResponse(BaseModel):
    id: int
    name: str
    type: str
    owner_id: Optional[int]
    is_default: bool
    layout_config: dict
    created_at: str
    updated_at: str
    widgets: Optional[List[dict]] = None


# ==================== API ====================

@router.get("", summary="获取仪表盘列表")
def get_dashboards(
    type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取仪表盘列表"""
    service = DashboardService(db)
    dashboards = service.get_dashboards(
        owner_id=current_user.id,
        dashboard_type=type
    )
    return {"items": dashboards}


@router.get("/{dashboard_id}", summary="获取仪表盘详情")
def get_dashboard(
    dashboard_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取仪表盘详情（含组件）"""
    service = DashboardService(db)
    dashboard = service.get_dashboard_by_id(dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="仪表盘不存在")
    return dashboard


@router.post("", summary="创建仪表盘")
def create_dashboard(
    request: DashboardCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建新仪表盘"""
    service = DashboardService(db)
    dashboard, success, error = service.create_dashboard(
        name=request.name,
        dashboard_type=request.type,
        owner_id=current_user.id,
        layout_config=request.layout_config
    )
    if not success:
        raise HTTPException(status_code=400, detail=error)
    return service.get_dashboard_by_id(dashboard.id)


@router.put("/{dashboard_id}", summary="更新仪表盘")
def update_dashboard(
    dashboard_id: int,
    request: DashboardUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新仪表盘"""
    service = DashboardService(db)
    dashboard, success, error = service.update_dashboard(
        dashboard_id=dashboard_id,
        name=request.name,
        layout_config=request.layout_config,
        is_default=request.is_default
    )
    if not success:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "更新成功"}


@router.delete("/{dashboard_id}", summary="删除仪表盘")
def delete_dashboard(
    dashboard_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除仪表盘"""
    service = DashboardService(db)
    success, error = service.delete_dashboard(dashboard_id)
    if not success:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "删除成功"}


# ==================== 组件管理 API ====================

@router.get("/{dashboard_id}/widgets", summary="获取组件列表")
def get_widgets(
    dashboard_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取仪表盘组件列表"""
    service = DashboardService(db)
    widgets = service.get_widgets(dashboard_id)
    return {"items": widgets}


@router.post("/{dashboard_id}/widgets", summary="添加组件")
def add_widget(
    dashboard_id: int,
    request: WidgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加组件到仪表盘"""
    service = DashboardService(db)
    widget, success, error = service.add_widget(
        dashboard_id=dashboard_id,
        widget_type=request.widget_type,
        title=request.title,
        config=request.config,
        position=request.position
    )
    if not success:
        raise HTTPException(status_code=400, detail=error)
    return service._widget_to_dict(widget)


@router.put("/widgets/{widget_id}", summary="更新组件")
def update_widget(
    widget_id: int,
    request: WidgetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新组件"""
    service = DashboardService(db)
    widget, success, error = service.update_widget(
        widget_id=widget_id,
        title=request.title,
        config=request.config,
        position=request.position,
        refresh_interval=request.refresh_interval
    )
    if not success:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "更新成功"}


@router.delete("/widgets/{widget_id}", summary="删除组件")
def delete_widget(
    widget_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除组件"""
    service = DashboardService(db)
    success, error = service.delete_widget(widget_id)
    if not success:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "删除成功"}
