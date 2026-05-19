from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.platform import (
    Organization,
    PlatformMenu,
    PlatformPermission,
    PlatformRole,
    PlatformUser,
    PlatformUserRole,
)
from app.routers.platform_auth import build_user_response, get_current_platform_user
from app.schemas.platform import (
    MenuCreate,
    MenuResponse,
    MenuUpdate,
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
    RoleCreate,
    RoleResponse,
    RoleUpdate,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.services.platform_auth import PlatformAuthService

router = APIRouter(prefix="/api/system", tags=["平台系统管理"])


@router.get("/users", response_model=list[UserResponse])
def list_users(
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    users = db.query(PlatformUser).order_by(PlatformUser.id.asc()).all()
    return [build_user_response(user, db) for user in users]


@router.post("/users", response_model=UserResponse)
def create_user(
    request: UserCreate,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    existing = db.query(PlatformUser).filter(
        or_(PlatformUser.username == request.username, PlatformUser.email == request.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名或邮箱已存在")

    user = PlatformUser(
        username=request.username,
        email=request.email,
        password_hash=PlatformAuthService.hash_password(request.password),
        display_name=request.display_name or request.username,
        phone=request.phone,
        organization_id=request.organization_id,
        status="active",
    )
    db.add(user)
    db.flush()
    sync_user_roles(db, user.id, request.role_ids)
    db.commit()
    db.refresh(user)
    return build_user_response(user, db)


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    request: UserUpdate,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    user = db.query(PlatformUser).filter(PlatformUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    for key, value in request.model_dump(exclude_unset=True, exclude={"role_ids"}).items():
        setattr(user, key, value)
    if request.role_ids is not None:
        sync_user_roles(db, user.id, request.role_ids)
    db.commit()
    db.refresh(user)
    return build_user_response(user, db)


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="不能删除当前登录用户")
    user = db.query(PlatformUser).filter(PlatformUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.delete(user)
    db.commit()
    return {"message": "删除成功"}


@router.get("/roles", response_model=list[RoleResponse])
def list_roles(
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    roles = db.query(PlatformRole).order_by(PlatformRole.id.asc()).all()
    return [build_role_response(role) for role in roles]


@router.post("/roles", response_model=RoleResponse)
def create_role(
    request: RoleCreate,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    existing = db.query(PlatformRole).filter(
        or_(PlatformRole.name == request.name, PlatformRole.code == request.code)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="角色名称或编码已存在")
    role = PlatformRole(name=request.name, code=request.code, description=request.description)
    db.add(role)
    db.flush()
    sync_role_permissions(db, role.id, request.permissions)
    db.commit()
    db.refresh(role)
    return build_role_response(role)


@router.put("/roles/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: int,
    request: RoleUpdate,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    role = db.query(PlatformRole).filter(PlatformRole.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    if role.is_system and request.status == "disabled":
        raise HTTPException(status_code=400, detail="系统角色不能禁用")

    for key, value in request.model_dump(exclude_unset=True, exclude={"permissions"}).items():
        setattr(role, key, value)
    if request.permissions is not None and not role.is_system:
        sync_role_permissions(db, role.id, request.permissions)
    db.commit()
    db.refresh(role)
    return build_role_response(role)


@router.delete("/roles/{role_id}")
def delete_role(
    role_id: int,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    role = db.query(PlatformRole).filter(PlatformRole.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    if role.is_system:
        raise HTTPException(status_code=400, detail="系统角色不能删除")
    db.delete(role)
    db.commit()
    return {"message": "删除成功"}


@router.get("/organizations", response_model=list[OrganizationResponse])
def list_organizations(
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    organizations = db.query(Organization).order_by(Organization.sort_order.asc(), Organization.id.asc()).all()
    return [build_organization_response(item, db) for item in organizations]


@router.post("/organizations", response_model=OrganizationResponse)
def create_organization(
    request: OrganizationCreate,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    existing = db.query(Organization).filter(Organization.code == request.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="组织编码已存在")
    org = Organization(**request.model_dump())
    db.add(org)
    db.commit()
    db.refresh(org)
    return build_organization_response(org, db)


@router.put("/organizations/{organization_id}", response_model=OrganizationResponse)
def update_organization(
    organization_id: int,
    request: OrganizationUpdate,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="组织不存在")
    for key, value in request.model_dump(exclude_unset=True).items():
        setattr(org, key, value)
    db.commit()
    db.refresh(org)
    return build_organization_response(org, db)


@router.delete("/organizations/{organization_id}")
def delete_organization(
    organization_id: int,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="组织不存在")
    if db.query(PlatformUser).filter(PlatformUser.organization_id == organization_id).first():
        raise HTTPException(status_code=400, detail="组织下存在用户，不能删除")
    db.delete(org)
    db.commit()
    return {"message": "删除成功"}


@router.get("/menus", response_model=list[MenuResponse])
def list_menus(
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    menus = db.query(PlatformMenu).order_by(PlatformMenu.sort_order.asc(), PlatformMenu.id.asc()).all()
    return [MenuResponse(**menu.__dict__) for menu in menus]


@router.post("/menus", response_model=MenuResponse)
def create_menu(
    request: MenuCreate,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    existing = db.query(PlatformMenu).filter(PlatformMenu.code == request.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="菜单编码已存在")
    menu = PlatformMenu(**request.model_dump())
    db.add(menu)
    db.commit()
    db.refresh(menu)
    return MenuResponse(**menu.__dict__)


@router.put("/menus/{menu_id}", response_model=MenuResponse)
def update_menu(
    menu_id: int,
    request: MenuUpdate,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    menu = db.query(PlatformMenu).filter(PlatformMenu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="菜单不存在")
    for key, value in request.model_dump(exclude_unset=True).items():
        setattr(menu, key, value)
    db.commit()
    db.refresh(menu)
    return MenuResponse(**menu.__dict__)


@router.delete("/menus/{menu_id}")
def delete_menu(
    menu_id: int,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    menu = db.query(PlatformMenu).filter(PlatformMenu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="菜单不存在")
    db.delete(menu)
    db.commit()
    return {"message": "删除成功"}


def sync_user_roles(db: Session, user_id: int, role_ids: list[int]) -> None:
    db.query(PlatformUserRole).filter(PlatformUserRole.user_id == user_id).delete()
    for role_id in role_ids:
        db.add(PlatformUserRole(user_id=user_id, role_id=role_id))


def sync_role_permissions(db: Session, role_id: int, permissions: list[str]) -> None:
    db.query(PlatformPermission).filter(PlatformPermission.role_id == role_id).delete()
    for code in permissions:
        resource, _, action = code.partition(":")
        if resource and action:
            db.add(PlatformPermission(role_id=role_id, resource=resource, action=action))


def build_role_response(role: PlatformRole) -> RoleResponse:
    permissions = [f"{item.resource}:{item.action}" for item in role.permissions]
    return RoleResponse(
        id=role.id,
        name=role.name,
        code=role.code,
        description=role.description or "",
        is_system=role.is_system,
        status=role.status,
        permissions=sorted(permissions),
        created_at=role.created_at,
    )


def build_organization_response(org: Organization, db: Session) -> OrganizationResponse:
    user_count = db.query(PlatformUser).filter(PlatformUser.organization_id == org.id).count()
    return OrganizationResponse(
        id=org.id,
        parent_id=org.parent_id,
        name=org.name,
        code=org.code,
        description=org.description or "",
        status=org.status,
        sort_order=org.sort_order,
        user_count=user_count,
        created_at=org.created_at,
    )

