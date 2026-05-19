# -*- coding: utf-8 -*-
"""
Phase 4 - 项目服务
"""
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from datetime import datetime
from app.models.tenant import Project, ProjectMember, User, Version
from app.services.rbac_service import RBACService


class ProjectService:
    """项目管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.rbac_service = RBACService(db)
    
    # ==================== 项目 CRUD ====================
    
    def get_projects(self, tenant_id: int, page: int = 1, page_size: int = 20, 
                     keyword: str = None, status: str = None) -> Tuple[List[Project], int]:
        """获取项目列表"""
        query = self.db.query(Project).filter(Project.tenant_id == tenant_id)
        
        if keyword:
            query = query.filter(
                or_(
                    Project.name.ilike(f"%{keyword}%"),
                    Project.key.ilike(f"%{keyword}%"),
                    Project.description.ilike(f"%{keyword}%")
                )
            )
        
        if status:
            query = query.filter(Project.status == status)
        
        total = query.count()
        projects = query.order_by(Project.created_at.desc())\
                       .offset((page - 1) * page_size)\
                       .limit(page_size)\
                       .all()
        
        return projects, total
    
    def get_project_by_id(self, project_id: int) -> Optional[Project]:
        """获取项目详情"""
        return self.db.query(Project).filter(Project.id == project_id).first()
    
    def get_project_by_key(self, key: str) -> Optional[Project]:
        """根据 key 获取项目"""
        return self.db.query(Project).filter(Project.key == key).first()
    
    def create_project(self, tenant_id: int, user_id: int, 
                       name: str, key: str, description: str = "",
                       repository_id: int = None) -> Tuple[Project, bool, str]:
        """
        创建项目
        返回: (项目, 是否成功, 错误信息)
        """
        # 检查 key 唯一性
        existing = self.get_project_by_key(key)
        if existing:
            return None, False, f"项目Key '{key}' 已存在"
        
        # 检查 key 格式
        if not key.isalnum() or len(key) < 3 or len(key) > 20:
            return None, False, "项目Key只能包含字母和数字，长度3-20字符"
        
        # 检查配额
        tenant_projects = self.db.query(Project).filter(
            Project.tenant_id == tenant_id,
            Project.status == "active"
        ).count()
        
        # TODO: 从租户配置中读取配额
        max_projects = 10
        if tenant_projects >= max_projects:
            return None, False, f"项目数量已达上限({max_projects})，请联系管理员"
        
        try:
            project = Project(
                tenant_id=tenant_id,
                name=name,
                key=key.upper(),
                description=description,
                repository_id=repository_id,
                created_by=user_id,
                status="active"
            )
            self.db.add(project)
            self.db.flush()
            
            # 自动添加创建者为项目管理员
            member = ProjectMember(
                project_id=project.id,
                user_id=user_id,
                role="admin"
            )
            self.db.add(member)
            
            self.db.commit()
            self.db.refresh(project)
            return project, True, ""
        except Exception as e:
            self.db.rollback()
            return None, False, str(e)
    
    def update_project(self, project_id: int, user_id: int,
                      name: str = None, description: str = None,
                      avatar: str = None, status: str = None,
                      repository_id: int = None) -> Tuple[Project, bool, str]:
        """
        更新项目
        """
        project = self.get_project_by_id(project_id)
        if not project:
            return None, False, "项目不存在"
        
        # 检查权限
        if not self.check_project_permission(user_id, project_id, "project", "update"):
            return None, False, "没有更新项目的权限"
        
        try:
            if name is not None:
                project.name = name
            if description is not None:
                project.description = description
            if avatar is not None:
                project.avatar = avatar
            if status is not None:
                project.status = status
            if repository_id is not None:
                project.repository_id = repository_id
            
            project.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(project)
            return project, True, ""
        except Exception as e:
            self.db.rollback()
            return None, False, str(e)
    
    def delete_project(self, project_id: int, user_id: int) -> Tuple[bool, str]:
        """删除项目（软删除）"""
        project = self.get_project_by_id(project_id)
        if not project:
            return False, "项目不存在"
        
        # 检查权限
        if not self.check_project_permission(user_id, project_id, "project", "delete"):
            return False, "没有删除项目的权限"
        
        # 软删除
        project.status = "deleted"
        project.updated_at = datetime.utcnow()
        self.db.commit()
        return True, ""
    
    def archive_project(self, project_id: int, user_id: int) -> Tuple[bool, str]:
        """归档项目"""
        return self.update_project(project_id, user_id, status="archived")
    
    # ==================== 成员管理 ====================
    
    def get_members(self, project_id: int) -> List[dict]:
        """获取项目成员列表"""
        members = self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id
        ).all()
        
        result = []
        for m in members:
            user = self.db.query(User).filter(User.id == m.user_id).first()
            if user:
                result.append({
                    "id": m.id,
                    "user_id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "avatar": user.avatar,
                    "role": m.role,
                    "created_at": m.created_at
                })
        return result
    
    def add_member(self, project_id: int, user_id: int, 
                    target_user_id: int, role: str) -> Tuple[ProjectMember, bool, str]:
        """添加项目成员"""
        # 检查权限
        if not self.check_project_permission(user_id, project_id, "project", "manage_members"):
            return None, False, "没有管理项目成员的权限"
        
        # 检查目标用户存在
        target_user = self.db.query(User).filter(User.id == target_user_id).first()
        if not target_user:
            return None, False, "用户不存在"
        
        # 检查是否已是成员
        existing = self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == target_user_id
        ).first()
        if existing:
            return None, False, "用户已是项目成员"
        
        # 验证角色
        valid_roles = ["admin", "developer", "tester", "viewer"]
        if role not in valid_roles:
            return None, False, f"无效的角色，有效值: {', '.join(valid_roles)}"
        
        try:
            member = ProjectMember(
                project_id=project_id,
                user_id=target_user_id,
                role=role
            )
            self.db.add(member)
            self.db.commit()
            self.db.refresh(member)
            return member, True, ""
        except Exception as e:
            self.db.rollback()
            return None, False, str(e)
    
    def update_member_role(self, project_id: int, user_id: int,
                          target_user_id: int, new_role: str) -> Tuple[bool, str]:
        """更新成员角色"""
        # 检查权限
        if not self.check_project_permission(user_id, project_id, "project", "manage_members"):
            return False, "没有管理项目成员的权限"
        
        member = self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == target_user_id
        ).first()
        if not member:
            return False, "成员不存在"
        
        valid_roles = ["admin", "developer", "tester", "viewer"]
        if new_role not in valid_roles:
            return False, f"无效的角色"
        
        member.role = new_role
        self.db.commit()
        return True, ""
    
    def remove_member(self, project_id: int, user_id: int,
                      target_user_id: int) -> Tuple[bool, str]:
        """移除项目成员"""
        # 检查权限
        if not self.check_project_permission(user_id, project_id, "project", "manage_members"):
            return False, "没有管理项目成员的权限"
        
        # 不能移除自己
        if user_id == target_user_id:
            return False, "不能移除自己"
        
        member = self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == target_user_id
        ).first()
        if not member:
            return False, "成员不存在"
        
        self.db.delete(member)
        self.db.commit()
        return True, ""
    
    # ==================== 权限检查 ====================
    
    def check_project_permission(self, user_id: int, project_id: int,
                                 resource: str, action: str) -> bool:
        """检查用户对项目的权限"""
        project = self.get_project_by_id(project_id)
        if not project:
            return False
        
        # 检查是否是项目成员
        member = self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        ).first()
        
        if not member:
            return False
        
        # 项目管理员拥有所有项目权限
        if member.role == "admin":
            return True
        
        # 根据项目内角色判断权限
        role_permissions = {
            "developer": ["project:read", "case:*", "scenario:*", "environment:read", 
                        "schedule:read", "defect:create", "defect:read"],
            "tester": ["project:read", "case:*", "scenario:*", "environment:*",
                       "schedule:*", "defect:*", "report:*"],
            "viewer": ["project:read", "case:read", "scenario:read", 
                      "environment:read", "schedule:read", "defect:read", "report:read"]
        }
        
        perms = role_permissions.get(member.role, [])
        required = f"{resource}:{action}"
        
        # 检查精确匹配或通配符
        if required in perms or f"{resource}:*" in perms:
            return True
        
        return self.rbac_service.has_permission(user_id, resource, action)
    
    def get_user_projects(self, user_id: int, tenant_id: int = None) -> List[Project]:
        """获取用户参与的项目列表"""
        # 如果是超级管理员，返回所有租户项目
        if tenant_id:
            user_roles = self.rbac_service.get_user_roles(user_id)
            if "SuperAdmin" in user_roles or "TenantAdmin" in user_roles:
                query = self.db.query(Project).filter(Project.tenant_id == tenant_id)
                return query.filter(Project.status != "deleted").all()
        
        # 普通用户只返回其参与的项目
        member_project_ids = self.db.query(ProjectMember.project_id).filter(
            ProjectMember.user_id == user_id
        ).all()
        project_ids = [p[0] for p in member_project_ids]
        
        if not project_ids:
            return []
        
        query = self.db.query(Project).filter(Project.id.in_(project_ids))
        if tenant_id:
            query = query.filter(Project.tenant_id == tenant_id)
        return query.filter(Project.status != "deleted").all()
    
    def get_project_stats(self, project_id: int) -> dict:
        """获取项目统计信息"""
        project = self.get_project_by_id(project_id)
        if not project:
            return None
        
        member_count = self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id
        ).count()
        
        version_count = self.db.query(Version).filter(
            Version.project_id == project_id
        ).count()
        
        return {
            "member_count": member_count,
            "version_count": version_count,
            "created_at": project.created_at,
            "updated_at": project.updated_at
        }
