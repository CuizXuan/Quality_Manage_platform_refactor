from sqlalchemy.orm import Session

from app.models.platform import (
    Organization,
    PlatformMenu,
    PlatformPermission,
    PlatformRole,
    PlatformUser,
    PlatformUserRole,
)
from app.services.platform_auth import PlatformAuthService


DEFAULT_PERMISSIONS = [
    ("system", "view"),
    ("system", "manage"),
    ("user", "manage"),
    ("role", "manage"),
    ("menu", "manage"),
    ("organization", "manage"),
]

DEFAULT_MENUS = [
    {
        "name": "工作台",
        "code": "dashboard",
        "path": "/",
        "icon": "Monitor",
        "component": "Dashboard",
        "permission_code": "system:view",
        "sort_order": 10,
    },
    {
        "name": "用户管理",
        "code": "system_users",
        "path": "/system/users",
        "icon": "UserRound",
        "component": "UserManagement",
        "permission_code": "user:manage",
        "sort_order": 20,
    },
    {
        "name": "角色管理",
        "code": "system_roles",
        "path": "/system/roles",
        "icon": "ShieldCheck",
        "component": "RoleManagement",
        "permission_code": "role:manage",
        "sort_order": 30,
    },
    {
        "name": "组织管理",
        "code": "system_organizations",
        "path": "/system/organizations",
        "icon": "Network",
        "component": "OrganizationManagement",
        "permission_code": "organization:manage",
        "sort_order": 40,
    },
    {
        "name": "菜单管理",
        "code": "system_menus",
        "path": "/system/menus",
        "icon": "PanelLeft",
        "component": "MenuManagement",
        "permission_code": "menu:manage",
        "sort_order": 50,
    },
]


def seed_platform(db: Session) -> None:
    admin_role = _ensure_admin_role(db)
    root_org = _ensure_root_organization(db)
    _ensure_default_admin(db, root_org.id, admin_role.id)
    _ensure_default_menus(db)
    db.commit()


def _ensure_admin_role(db: Session) -> PlatformRole:
    role = db.query(PlatformRole).filter(PlatformRole.code == "super_admin").first()
    if not role:
        role = PlatformRole(
            name="超级管理员",
            code="super_admin",
            description="拥有平台全部管理权限",
            is_system=True,
        )
        db.add(role)
        db.flush()

    existing = {
        f"{item.resource}:{item.action}"
        for item in db.query(PlatformPermission).filter(PlatformPermission.role_id == role.id).all()
    }
    for resource, action in DEFAULT_PERMISSIONS:
        code = f"{resource}:{action}"
        if code not in existing:
            db.add(PlatformPermission(role_id=role.id, resource=resource, action=action))
    return role


def _ensure_root_organization(db: Session) -> Organization:
    org = db.query(Organization).filter(Organization.code == "root").first()
    if org:
        return org
    org = Organization(name="默认组织", code="root", description="平台默认组织")
    db.add(org)
    db.flush()
    return org


def _ensure_default_admin(db: Session, organization_id: int, role_id: int) -> None:
    user = db.query(PlatformUser).filter(PlatformUser.username == "admin").first()
    if not user:
        user = PlatformUser(
            organization_id=organization_id,
            username="admin",
            email="admin@example.com",
            password_hash=PlatformAuthService.hash_password("admin123"),
            display_name="系统管理员",
            status="active",
        )
        db.add(user)
        db.flush()

    link = db.query(PlatformUserRole).filter(
        PlatformUserRole.user_id == user.id,
        PlatformUserRole.role_id == role_id,
    ).first()
    if not link:
        db.add(PlatformUserRole(user_id=user.id, role_id=role_id))


def _ensure_default_menus(db: Session) -> None:
    existing_codes = {item.code for item in db.query(PlatformMenu).all()}
    for item in DEFAULT_MENUS:
        if item["code"] not in existing_codes:
            db.add(PlatformMenu(**item))

