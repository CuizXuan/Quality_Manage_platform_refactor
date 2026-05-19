from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class Organization(Base):
    __tablename__ = "platform_organizations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    parent_id = Column(Integer, ForeignKey("platform_organizations.id"), nullable=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text, default="")
    status = Column(String(20), default="active")
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    parent = relationship("Organization", remote_side=[id])
    users = relationship("PlatformUser", back_populates="organization")


class PlatformUser(Base):
    __tablename__ = "platform_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("platform_organizations.id"), nullable=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    display_name = Column(String(100), default="")
    phone = Column(String(30), default="")
    status = Column(String(20), default="active")
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship("Organization", back_populates="users")
    role_links = relationship("PlatformUserRole", back_populates="user", cascade="all, delete-orphan")


class PlatformRole(Base):
    __tablename__ = "platform_roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(80), unique=True, nullable=False)
    code = Column(String(80), unique=True, nullable=False)
    description = Column(Text, default="")
    is_system = Column(Boolean, default=False)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user_links = relationship("PlatformUserRole", back_populates="role", cascade="all, delete-orphan")
    permissions = relationship("PlatformPermission", back_populates="role", cascade="all, delete-orphan")


class PlatformUserRole(Base):
    __tablename__ = "platform_user_roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("platform_users.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("platform_roles.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("PlatformUser", back_populates="role_links")
    role = relationship("PlatformRole", back_populates="user_links")


class PlatformPermission(Base):
    __tablename__ = "platform_permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey("platform_roles.id"), nullable=False)
    resource = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    role = relationship("PlatformRole", back_populates="permissions")


class PlatformMenu(Base):
    __tablename__ = "platform_menus"

    id = Column(Integer, primary_key=True, autoincrement=True)
    parent_id = Column(Integer, ForeignKey("platform_menus.id"), nullable=True)
    name = Column(String(100), nullable=False)
    code = Column(String(100), unique=True, nullable=False)
    path = Column(String(200), default="")
    icon = Column(String(80), default="")
    component = Column(String(200), default="")
    permission_code = Column(String(120), default="")
    visible = Column(Boolean, default=True)
    status = Column(String(20), default="active")
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    parent = relationship("PlatformMenu", remote_side=[id])

