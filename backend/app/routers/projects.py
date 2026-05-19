# -*- coding: utf-8 -*-
"""
Phase 4 - 项目管理路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app.models.tenant import User, Project, ProjectMember
from app.services.auth_service import AuthService
from app.services.project_service import ProjectService

router = APIRouter(prefix="/api/projects", tags=["项目管理"])
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


# ==================== 请求/响应模型 ====================

class ProjectCreate(BaseModel):
    name: str
    key: str
    description: str = ""
    repository_id: Optional[int] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    avatar: Optional[str] = None
    status: Optional[str] = None
    repository_id: Optional[int] = None


class ProjectMemberCreate(BaseModel):
    user_id: int
    role: str


class ProjectMemberUpdate(BaseModel):
    role: str


class ProjectMemberResponse(BaseModel):
    id: int
    user_id: int
    username: str
    email: str
    avatar: Optional[str]
    role: str
    created_at: str


class ProjectResponse(BaseModel):
    id: int
    tenant_id: int
    name: str
    key: str
    description: str
    avatar: Optional[str]
    status: str
    repository_id: Optional[int]
    created_by: int
    created_at: str
    updated_at: str
    member_count: int = 0
    version_count: int = 0

    class Config:
        from_attributes = True


class PageResponse(BaseModel):
    items: List[ProjectResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str


# ==================== 项目 CRUD ====================

@router.get("", response_model=PageResponse, summary="获取项目列表")
def get_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str = Query(None),
    status: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的项目列表"""
    project_service = ProjectService(db)
    
    # 获取用户参与的项目列表（带分页）
    projects, total = project_service.get_projects(
        tenant_id=current_user.tenant_id,
        page=page,
        page_size=page_size,
        keyword=keyword,
        status=status
    )
    
    # 如果用户不是超级管理员，只返回其参与的项目
    user_roles = project_service.rbac_service.get_user_roles(current_user.id)
    if "SuperAdmin" not in user_roles and "TenantAdmin" not in user_roles:
        user_project_ids = [p.id for p in project_service.get_user_projects(current_user.id)]
        projects = [p for p in projects if p.id in user_project_ids]
        total = len(projects)
    
    # 获取每个项目的统计信息
    items = []
    for p in projects:
        stats = project_service.get_project_stats(p.id)
        items.append(ProjectResponse(
            id=p.id,
            tenant_id=p.tenant_id,
            name=p.name,
            key=p.key,
            description=p.description or "",
            avatar=p.avatar,
            status=p.status,
            repository_id=p.repository_id,
            created_by=p.created_by,
            created_at=p.created_at.isoformat() if p.created_at else "",
            updated_at=p.updated_at.isoformat() if p.updated_at else "",
            member_count=stats["member_count"] if stats else 0,
            version_count=stats["version_count"] if stats else 0
        ))
    
    total_pages = (total + page_size - 1) // page_size
    
    return PageResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.post("", response_model=ProjectResponse, summary="创建项目")
def create_project(
    request: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建新项目"""
    project_service = ProjectService(db)
    
    project, success, error = project_service.create_project(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        name=request.name,
        key=request.key,
        description=request.description,
        repository_id=request.repository_id
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    stats = project_service.get_project_stats(project.id)
    
    return ProjectResponse(
        id=project.id,
        tenant_id=project.tenant_id,
        name=project.name,
        key=project.key,
        description=project.description or "",
        avatar=project.avatar,
        status=project.status,
        repository_id=project.repository_id,
        created_by=project.created_by,
        created_at=project.created_at.isoformat() if project.created_at else "",
        updated_at=project.updated_at.isoformat() if project.updated_at else "",
        member_count=stats["member_count"] if stats else 0,
        version_count=stats["version_count"] if stats else 0
    )


@router.get("/{project_id}", response_model=ProjectResponse, summary="获取项目详情")
def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取项目详情"""
    project_service = ProjectService(db)
    project = project_service.get_project_by_id(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 检查是否有权限访问
    if project.tenant_id != current_user.tenant_id:
        user_projects = project_service.get_user_projects(current_user.id)
        if project.id not in [p.id for p in user_projects]:
            raise HTTPException(status_code=403, detail="没有访问此项目的权限")
    
    stats = project_service.get_project_stats(project_id)
    
    return ProjectResponse(
        id=project.id,
        tenant_id=project.tenant_id,
        name=project.name,
        key=project.key,
        description=project.description or "",
        avatar=project.avatar,
        status=project.status,
        repository_id=project.repository_id,
        created_by=project.created_by,
        created_at=project.created_at.isoformat() if project.created_at else "",
        updated_at=project.updated_at.isoformat() if project.updated_at else "",
        member_count=stats["member_count"] if stats else 0,
        version_count=stats["version_count"] if stats else 0
    )


@router.put("/{project_id}", response_model=ProjectResponse, summary="更新项目")
def update_project(
    project_id: int,
    request: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新项目"""
    project_service = ProjectService(db)
    
    # 构建更新参数
    update_data = {}
    if request.name is not None:
        update_data["name"] = request.name
    if request.description is not None:
        update_data["description"] = request.description
    if request.avatar is not None:
        update_data["avatar"] = request.avatar
    if request.status is not None:
        update_data["status"] = request.status
    if request.repository_id is not None:
        update_data["repository_id"] = request.repository_id
    
    project, success, error = project_service.update_project(
        project_id=project_id,
        user_id=current_user.id,
        **update_data
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    stats = project_service.get_project_stats(project_id)
    
    return ProjectResponse(
        id=project.id,
        tenant_id=project.tenant_id,
        name=project.name,
        key=project.key,
        description=project.description or "",
        avatar=project.avatar,
        status=project.status,
        repository_id=project.repository_id,
        created_by=project.created_by,
        created_at=project.created_at.isoformat() if project.created_at else "",
        updated_at=project.updated_at.isoformat() if project.updated_at else "",
        member_count=stats["member_count"] if stats else 0,
        version_count=stats["version_count"] if stats else 0
    )


@router.delete("/{project_id}", response_model=MessageResponse, summary="删除项目")
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除项目（软删除）"""
    project_service = ProjectService(db)
    success, error = project_service.delete_project(project_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    return MessageResponse(message="删除成功")


# ==================== 项目成员管理 ====================

@router.get("/{project_id}/members", response_model=List[ProjectMemberResponse], 
           summary="获取项目成员列表")
def get_members(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取项目成员列表"""
    project_service = ProjectService(db)
    project = project_service.get_project_by_id(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    members = project_service.get_members(project_id)
    
    return [
        ProjectMemberResponse(
            id=m["id"],
            user_id=m["user_id"],
            username=m["username"],
            email=m["email"],
            avatar=m["avatar"],
            role=m["role"],
            created_at=m["created_at"].isoformat() if m["created_at"] else ""
        ) for m in members
    ]


@router.post("/{project_id}/members", response_model=ProjectMemberResponse, 
            summary="添加项目成员")
def add_member(
    project_id: int,
    request: ProjectMemberCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加项目成员"""
    project_service = ProjectService(db)
    
    member, success, error = project_service.add_member(
        project_id=project_id,
        user_id=current_user.id,
        target_user_id=request.user_id,
        role=request.role
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    # 获取成员信息
    from app.models.tenant import User
    user = db.query(User).filter(User.id == request.user_id).first()
    
    return ProjectMemberResponse(
        id=member.id,
        user_id=user.id,
        username=user.username,
        email=user.email,
        avatar=user.avatar,
        role=member.role,
        created_at=member.created_at.isoformat() if member.created_at else ""
    )


@router.put("/{project_id}/members/{user_id}", response_model=MessageResponse, 
           summary="更新成员角色")
def update_member(
    project_id: int,
    user_id: int,
    request: ProjectMemberUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新项目成员角色"""
    project_service = ProjectService(db)
    
    success, error = project_service.update_member_role(
        project_id=project_id,
        user_id=current_user.id,
        target_user_id=user_id,
        new_role=request.role
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    return MessageResponse(message="更新成功")


@router.delete("/{project_id}/members/{user_id}", response_model=MessageResponse, 
              summary="移除项目成员")
def remove_member(
    project_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """移除项目成员"""
    project_service = ProjectService(db)
    
    success, error = project_service.remove_member(
        project_id=project_id,
        user_id=current_user.id,
        target_user_id=user_id
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    return MessageResponse(message="移除成功")
