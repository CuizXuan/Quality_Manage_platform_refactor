# -*- coding: utf-8 -*-
"""
Phase 4 - 认证服务
支持 JWT 登录、注册、Token 刷新、多租户隔离
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
import bcrypt
import jwt
from sqlalchemy.orm import Session
from app.models.tenant import User, Tenant, UserRole, Role
from app.database import SessionLocal
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS


class AuthService:
    """认证服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    @staticmethod
    def hash_password(password: str) -> str:
        """密码哈希"""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """验证密码"""
        try:
            return bcrypt.checkpw(password.encode(), password_hash.encode())
        except Exception:
            return False
    
    @staticmethod
    def create_access_token(user_id: int, tenant_id: Optional[int] = None) -> str:
        """创建访问令牌"""
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": str(user_id),
            "tenant_id": tenant_id,
            "exp": expire,
            "type": "access"
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    @staticmethod
    def create_refresh_token(user_id: int) -> str:
        """创建刷新令牌"""
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "type": "refresh"
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        """解码令牌"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None  # 令牌过期
        except jwt.InvalidTokenError:
            return None  # 令牌无效
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """验证用户登录"""
        user = self.db.query(User).filter(User.username == username).first()
        if not user:
            return None
        if user.status != "active":
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        return user
    
    def register_user(self, username: str, email: str, password: str, 
                      tenant_id: Optional[int] = None) -> Tuple[User, str]:
        """
        注册新用户
        返回 (用户, 访问令牌)
        """
        # 检查用户名和邮箱唯一性
        existing = self.db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing:
            raise ValueError("用户名或邮箱已存在")
        
        # 创建用户
        user = User(
            username=username,
            email=email,
            password_hash=self.hash_password(password),
            tenant_id=tenant_id,
            status="active"
        )
        self.db.add(user)
        self.db.flush()
        
        # 如果没有指定租户，创建新租户
        if tenant_id is None:
            tenant = Tenant(
                name=f"{username}的团队",
                code=f"tenant_{username}_{int(datetime.utcnow().timestamp())}",
                description=f"{username}的私有租户"
            )
            self.db.add(tenant)
            self.db.flush()
            user.tenant_id = tenant.id
            
            # 创建默认项目（key 混入 user id 确保唯一）
            from app.models.tenant import Project, ProjectMember
            project = Project(
                tenant_id=tenant.id,
                name=f"{username}的项目",
                key=f"PROJ_{user.id}_{username.upper()[:4]}",
                description=f"{username}的默认项目",
                created_by=user.id
            )
            self.db.add(project)
            self.db.flush()
            
            pm = ProjectMember(
                project_id=project.id,
                user_id=user.id,
                role="admin"
            )
            self.db.add(pm)
        
        # 默认分配 Viewer 角色
        viewer_role = self.db.query(Role).filter(Role.name == "Viewer").first()
        if viewer_role:
            user_role = UserRole(user_id=user.id, role_id=viewer_role.id)
            self.db.add(user_role)
        
        self.db.commit()
        self.db.refresh(user)
        
        # 生成令牌
        access_token = self.create_access_token(user.id, user.tenant_id)
        return user, access_token
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """刷新访问令牌"""
        payload = self.decode_token(refresh_token)
        if not payload:
            return None
        if payload.get("type") != "refresh":
            return None
        
        user_id = int(payload.get("sub"))
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or user.status != "active":
            return None
        
        return self.create_access_token(user.id, user.tenant_id)
    
    def update_last_login(self, user: User, ip: str = None):
        """更新最后登录信息"""
        user.last_login_at = datetime.utcnow()
        user.last_login_ip = ip
        self.db.commit()
    
    def get_user_roles(self, user_id: int) -> list:
        """获取用户角色列表"""
        user_roles = self.db.query(UserRole).filter(UserRole.user_id == user_id).all()
        role_ids = [ur.role_id for ur in user_roles]
        roles = self.db.query(Role).filter(Role.id.in_(role_ids)).all()
        return [r.name for r in roles]
    
    def get_user_permissions(self, user_id: int) -> list:
        """获取用户权限列表"""
        user_roles = self.db.query(UserRole).filter(UserRole.user_id == user_id).all()
        role_ids = [ur.role_id for ur in user_roles]
        from app.models.tenant import Permission
        perms = self.db.query(Permission).filter(Permission.role_id.in_(role_ids)).all()
        return [(p.resource, p.action) for p in perms]


def get_auth_service() -> AuthService:
    """获取认证服务实例"""
    db = SessionLocal()
    return AuthService(db)
