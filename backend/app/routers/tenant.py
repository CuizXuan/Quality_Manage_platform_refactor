# -*- coding: utf-8 -*-
"""
Phase 4 - 租户与权限管理路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app.models.tenant import User, Tenant
from app.services.auth_service import AuthService
from app.services.rbac_service import RBACService

router = APIRouter(prefix="/api/tenant", tags=["租户与权限"])
security = HTTPBearer(auto_error=False)


# ==================== 依赖项 ====================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """获取当前用户"""
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


def require_permission(resource: str, action: str):
    """权限检查装饰器工厂"""
    def dependency(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
    ):
        if not credentials:
            raise HTTPException(status_code=401, detail="未提供认证令牌")
        auth_service = AuthService(db)
        payload = auth_service.decode_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="令牌无效或已过期")
        user_id = int(payload.get("sub"))
        rbac_service = RBACService(db)
        if not rbac_service.has_permission(user_id, resource, action):
            raise HTTPException(status_code=403, detail=f"没有 {resource}:{action} 权限")
        return payload
    return dependency


# ==================== 请求/响应模型 ====================

class RoleCreate(BaseModel):
    name: str
    description: str = ""


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class PermissionRequest(BaseModel):
    resource: str
    action: str
    scope: str = "all"


class RoleAssignRequest(BaseModel):
    user_id: int
    role_id: int


class UserStatusUpdate(BaseModel):
    status: str


class MessageResponse(BaseModel):
    message: str


# ==================== 角色管理 API ====================

@router.get("/roles", summary="获取角色列表")
def get_roles(
    tenant_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取角色列表"""
    rbac_service = RBACService(db)
    # 普通用户只能查看
    roles = rbac_service.get_roles(tenant_id=tenant_id)
    return [{"id": r.id, "name": r.name, "description": r.description, 
             "is_system": r.is_system, "tenant_id": r.tenant_id} for r in roles]


@router.get("/roles/{role_id}", summary="获取角色详情")
def get_role(
    role_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取角色详情"""
    rbac_service = RBACService(db)
    role = rbac_service.get_role_by_id(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    perms = rbac_service.get_role_permissions(role_id)
    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "is_system": role.is_system,
        "tenant_id": role.tenant_id,
        "permissions": [{"resource": p.resource, "action": p.action, "scope": p.scope} for p in perms]
    }


@router.post("/roles", summary="创建角色")
def create_role(
    request: RoleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建角色（需要 team:manage_roles 权限）"""
    rbac_service = RBACService(db)
    if not rbac_service.has_permission(current_user.id, "team", "manage_roles"):
        raise HTTPException(status_code=403, detail="没有管理角色权限")
    # 检查名称唯一性
    existing = rbac_service.get_role_by_name(request.name, current_user.tenant_id)
    if existing:
        raise HTTPException(status_code=400, detail="角色名称已存在")
    role = rbac_service.create_role(request.name, request.description, current_user.tenant_id)
    return {"id": role.id, "name": role.name, "description": role.description}


@router.put("/roles/{role_id}", summary="更新角色")
def update_role(
    role_id: int,
    request: RoleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新角色"""
    rbac_service = RBACService(db)
    if not rbac_service.has_permission(current_user.id, "team", "manage_roles"):
        raise HTTPException(status_code=403, detail="没有管理角色权限")
    role = rbac_service.update_role(role_id, request.name, request.description)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在或系统角色不可修改")
    return {"id": role.id, "name": role.name, "description": role.description}


@router.delete("/roles/{role_id}", summary="删除角色")
def delete_role(
    role_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除角色"""
    rbac_service = RBACService(db)
    if not rbac_service.has_permission(current_user.id, "team", "manage_roles"):
        raise HTTPException(status_code=403, detail="没有管理角色权限")
    success = rbac_service.delete_role(role_id)
    if not success:
        raise HTTPException(status_code=404, detail="角色不存在或系统角色不可删除")
    return {"message": "删除成功"}


# ==================== 权限管理 API ====================

@router.post("/roles/{role_id}/permissions", summary="为角色添加权限")
def add_permission(
    role_id: int,
    request: PermissionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """为角色添加权限"""
    rbac_service = RBACService(db)
    if not rbac_service.has_permission(current_user.id, "team", "manage_roles"):
        raise HTTPException(status_code=403, detail="没有管理角色权限")
    perm = rbac_service.add_permission(role_id, request.resource, request.action, request.scope)
    if not perm:
        raise HTTPException(status_code=404, detail="角色不存在")
    return {"resource": perm.resource, "action": perm.action, "scope": perm.scope}


@router.delete("/roles/{role_id}/permissions", summary="移除角色权限")
def remove_permission(
    role_id: int,
    resource: str,
    action: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """移除角色权限"""
    rbac_service = RBACService(db)
    if not rbac_service.has_permission(current_user.id, "team", "manage_roles"):
        raise HTTPException(status_code=403, detail="没有管理角色权限")
    success = rbac_service.remove_permission(role_id, resource, action)
    if not success:
        raise HTTPException(status_code=404, detail="权限不存在")
    return {"message": "删除成功"}


@router.put("/roles/{role_id}/permissions", summary="批量设置角色权限")
def set_permissions(
    role_id: int,
    permissions: List[PermissionRequest],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量设置角色权限"""
    rbac_service = RBACService(db)
    if not rbac_service.has_permission(current_user.id, "team", "manage_roles"):
        raise HTTPException(status_code=403, detail="没有管理角色权限")
    perm_list = [(p.resource, p.action, p.scope) for p in permissions]
    success = rbac_service.set_role_permissions(role_id, perm_list)
    if not success:
        raise HTTPException(status_code=404, detail="角色不存在或系统角色不可修改")
    return {"message": "设置成功"}


# ==================== 用户角色管理 API ====================

@router.get("/users/{user_id}/roles", summary="获取用户角色")
def get_user_roles(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户角色列表"""
    rbac_service = RBACService(db)
    # 只有管理员或用户本人可以查看
    if current_user.id != user_id and not rbac_service.has_permission(current_user.id, "team", "manage_users"):
        raise HTTPException(status_code=403, detail="没有查看权限")
    roles = rbac_service.get_user_roles(user_id)
    return [{"id": r.id, "name": r.name, "description": r.description} for r in roles]


@router.post("/users/roles", summary="为用户分配角色")
def assign_role(
    request: RoleAssignRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """为用户分配角色"""
    rbac_service = RBACService(db)
    if not rbac_service.has_permission(current_user.id, "team", "manage_users"):
        raise HTTPException(status_code=403, detail="没有管理用户权限")
    # 验证用户和角色存在
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    role = rbac_service.get_role_by_id(request.role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    rbac_service.assign_role_to_user(request.user_id, request.role_id)
    return {"message": "分配成功"}


@router.delete("/users/{user_id}/roles/{role_id}", summary="移除用户角色")
def remove_user_role(
    user_id: int,
    role_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """移除用户角色"""
    rbac_service = RBACService(db)
    if not rbac_service.has_permission(current_user.id, "team", "manage_users"):
        raise HTTPException(status_code=403, detail="没有管理用户权限")
    success = rbac_service.remove_role_from_user(user_id, role_id)
    if not success:
        raise HTTPException(status_code=404, detail="关联不存在")
    return {"message": "移除成功"}


# ==================== 用户管理 API ====================

@router.get("/users", summary="获取用户列表")
def get_users(
    tenant_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户列表"""
    rbac_service = RBACService(db)
    if not rbac_service.has_permission(current_user.id, "team", "manage_users"):
        raise HTTPException(status_code=403, detail="没有管理用户权限")
    query = db.query(User)
    if tenant_id:
        query = query.filter(User.tenant_id == tenant_id)
    users = query.all()
    return [{
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "status": u.status,
        "tenant_id": u.tenant_id,
        "created_at": u.created_at.isoformat() if u.created_at else None
    } for u in users]


@router.put("/users/{user_id}/status", summary="更新用户状态")
def update_user_status(
    user_id: int,
    request: UserStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户状态"""
    rbac_service = RBACService(db)
    if not rbac_service.has_permission(current_user.id, "team", "manage_users"):
        raise HTTPException(status_code=403, detail="没有管理用户权限")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.status = request.status
    db.commit()
    return {"message": "更新成功"}
