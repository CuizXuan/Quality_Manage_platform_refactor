# -*- coding: utf-8 -*-
"""
Phase 4 - RBAC 权限服务
"""
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from app.models.tenant import Role, Permission, UserRole, User


class RBACService:
    """RBAC 权限服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== 角色管理 ====================
    
    def get_roles(self, tenant_id: Optional[int] = None, include_system: bool = True) -> List[Role]:
        """获取角色列表"""
        query = self.db.query(Role)
        if tenant_id is not None:
            query = query.filter((Role.tenant_id == tenant_id) | (Role.is_system == False))
        if not include_system:
            query = query.filter(Role.is_system == False)
        return query.all()
    
    def get_role_by_id(self, role_id: int) -> Optional[Role]:
        """获取角色详情"""
        return self.db.query(Role).filter(Role.id == role_id).first()
    
    def get_role_by_name(self, name: str, tenant_id: Optional[int] = None) -> Optional[Role]:
        """根据名称获取角色"""
        query = self.db.query(Role).filter(Role.name == name)
        if tenant_id is not None:
            query = query.filter((Role.tenant_id == tenant_id) | (Role.is_system == True))
        return query.first()
    
    def create_role(self, name: str, description: str = "", 
                    tenant_id: Optional[int] = None) -> Role:
        """创建角色"""
        role = Role(
            name=name,
            description=description,
            tenant_id=tenant_id,
            is_system=False
        )
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role
    
    def update_role(self, role_id: int, name: str = None, 
                   description: str = None) -> Optional[Role]:
        """更新角色"""
        role = self.get_role_by_id(role_id)
        if not role or role.is_system:
            return None
        if name is not None:
            role.name = name
        if description is not None:
            role.description = description
        self.db.commit()
        self.db.refresh(role)
        return role
    
    def delete_role(self, role_id: int) -> bool:
        """删除角色（系统角色不可删除）"""
        role = self.get_role_by_id(role_id)
        if not role or role.is_system:
            return False
        # 移除所有用户关联
        self.db.query(UserRole).filter(UserRole.role_id == role_id).delete()
        # 移除所有权限
        self.db.query(Permission).filter(Permission.role_id == role_id).delete()
        # 删除角色
        self.db.delete(role)
        self.db.commit()
        return True
    
    # ==================== 权限管理 ====================
    
    def get_role_permissions(self, role_id: int) -> List[Permission]:
        """获取角色权限列表"""
        return self.db.query(Permission).filter(Permission.role_id == role_id).all()
    
    def add_permission(self, role_id: int, resource: str, action: str, 
                       scope: str = "all") -> Optional[Permission]:
        """为角色添加权限"""
        role = self.get_role_by_id(role_id)
        if not role:
            return None
        # 检查权限是否已存在
        existing = self.db.query(Permission).filter(
            Permission.role_id == role_id,
            Permission.resource == resource,
            Permission.action == action
        ).first()
        if existing:
            return existing
        perm = Permission(
            role_id=role_id,
            resource=resource,
            action=action,
            scope=scope
        )
        self.db.add(perm)
        self.db.commit()
        self.db.refresh(perm)
        return perm
    
    def remove_permission(self, role_id: int, resource: str, action: str) -> bool:
        """移除角色权限"""
        perm = self.db.query(Permission).filter(
            Permission.role_id == role_id,
            Permission.resource == resource,
            Permission.action == action
        ).first()
        if not perm:
            return False
        self.db.delete(perm)
        self.db.commit()
        return True
    
    def set_role_permissions(self, role_id: int, permissions: List[Tuple[str, str, str]]) -> bool:
        """批量设置角色权限（先删后加）"""
        role = self.get_role_by_id(role_id)
        if not role or role.is_system:
            return False
        # 删除现有非系统权限
        self.db.query(Permission).filter(Permission.role_id == role_id).delete()
        # 添加新权限
        for resource, action, scope in permissions:
            perm = Permission(
                role_id=role_id,
                resource=resource,
                action=action,
                scope=scope
            )
            self.db.add(perm)
        self.db.commit()
        return True
    
    # ==================== 用户角色关联 ====================
    
    def assign_role_to_user(self, user_id: int, role_id: int) -> bool:
        """为用户分配角色"""
        # 检查是否已分配
        existing = self.db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id
        ).first()
        if existing:
            return True
        user_role = UserRole(user_id=user_id, role_id=role_id)
        self.db.add(user_role)
        self.db.commit()
        return True
    
    def remove_role_from_user(self, user_id: int, role_id: int) -> bool:
        """移除用户角色"""
        user_role = self.db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id
        ).first()
        if not user_role:
            return False
        self.db.delete(user_role)
        self.db.commit()
        return True
    
    def get_user_roles(self, user_id: int) -> List[Role]:
        """获取用户的所有角色"""
        user_roles = self.db.query(UserRole).filter(UserRole.user_id == user_id).all()
        role_ids = [ur.role_id for ur in user_roles]
        return self.db.query(Role).filter(Role.id.in_(role_ids)).all()
    
    def get_user_permissions(self, user_id: int) -> List[Tuple[str, str]]:
        """获取用户的所有权限"""
        roles = self.get_user_roles(user_id)
        role_ids = [r.id for r in roles]
        perms = self.db.query(Permission).filter(Permission.role_id.in_(role_ids)).all()
        return [(p.resource, p.action) for p in perms]
    
    # ==================== 权限验证 ====================
    
    def has_permission(self, user_id: int, resource: str, action: str) -> bool:
        """检查用户是否有特定权限"""
        user_perms = self.get_user_permissions(user_id)
        # 检查 exact match
        if (resource, action) in user_perms:
            return True
        # 检查通配符权限 (resource:* 或 *:*)
        if (resource, "*") in user_perms or ("*", "*") in user_perms:
            return True
        return False
    
    def check_permission(self, user_id: int, resource: str, action: str) -> None:
        """权限检查，不通过则抛出异常"""
        if not self.has_permission(user_id, resource, action):
            raise PermissionError(f"用户没有 {resource}:{action} 权限")
