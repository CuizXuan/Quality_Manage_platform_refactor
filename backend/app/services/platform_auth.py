from datetime import datetime, timedelta
from typing import Optional

import bcrypt
import jwt
from sqlalchemy.orm import Session

from app.config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, REFRESH_TOKEN_EXPIRE_DAYS, SECRET_KEY
from app.models.platform import PlatformPermission, PlatformRole, PlatformUser, PlatformUserRole


class PlatformAuthService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode(), password_hash.encode())
        except ValueError:
            return False

    @staticmethod
    def create_access_token(user_id: int) -> str:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {"sub": str(user_id), "type": "access", "exp": expire}
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def create_refresh_token(user_id: int) -> str:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        payload = {"sub": str(user_id), "type": "refresh", "exp": expire}
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        try:
            return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except jwt.PyJWTError:
            return None

    def authenticate_user(self, username: str, password: str) -> Optional[PlatformUser]:
        user = self.db.query(PlatformUser).filter(PlatformUser.username == username).first()
        if not user or user.status != "active":
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        return user

    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        payload = self.decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None
        user = self.db.query(PlatformUser).filter(PlatformUser.id == int(payload["sub"])).first()
        if not user or user.status != "active":
            return None
        return self.create_access_token(user.id)

    def get_user_permissions(self, user_id: int) -> list[str]:
        roles = self.get_user_roles(user_id)
        role_ids = [role.id for role in roles]
        if not role_ids:
            return []
        permissions = self.db.query(PlatformPermission).filter(
            PlatformPermission.role_id.in_(role_ids)
        ).all()
        return sorted({f"{item.resource}:{item.action}" for item in permissions})

    def get_user_roles(self, user_id: int) -> list[PlatformRole]:
        links = self.db.query(PlatformUserRole).filter(PlatformUserRole.user_id == user_id).all()
        role_ids = [link.role_id for link in links]
        if not role_ids:
            return []
        return self.db.query(PlatformRole).filter(PlatformRole.id.in_(role_ids)).all()

