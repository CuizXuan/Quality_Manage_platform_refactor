# -*- coding: utf-8 -*-
"""
Phase 4 - 认证路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.services.auth_service import AuthService, get_auth_service
from app.models.tenant import User

router = APIRouter(prefix="/api/auth", tags=["认证"])
security = HTTPBearer(auto_error=False)


# 请求/响应模型
class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30分钟


class UserInfo(BaseModel):
    id: int
    username: str
    email: str
    tenant_id: Optional[int]
    roles: list
    permissions: list
    
    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    message: str


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, req: Request, db: Session = Depends(get_db)):
    """用户登录"""
    auth_service = AuthService(db)
    user = auth_service.authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    # 更新登录信息
    client_ip = req.client.host if req.client else None
    auth_service.update_last_login(user, client_ip)
    
    # 生成令牌
    access_token = auth_service.create_access_token(user.id, user.tenant_id)
    refresh_token = auth_service.create_refresh_token(user.id)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=1800
    )


@router.post("/register", response_model=TokenResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """用户注册"""
    auth_service = AuthService(db)
    
    # 验证密码强度
    if len(request.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码长度至少6位"
        )
    
    try:
        user, access_token = auth_service.register_user(
            username=request.username,
            email=request.email,
            password=request.password
        )
        refresh_token = auth_service.create_refresh_token(user.id)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=1800
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: RefreshRequest, db: Session = Depends(get_db)):
    """刷新令牌"""
    auth_service = AuthService(db)
    access_token = auth_service.refresh_access_token(request.refresh_token)
    
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌"
        )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=request.refresh_token,
        expires_in=1800
    )


@router.get("/me", response_model=UserInfo)
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """获取当前用户信息"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌"
        )
    
    auth_service = AuthService(db)
    payload = auth_service.decode_token(credentials.credentials)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌无效或已过期"
        )
    
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )
    
    roles = auth_service.get_user_roles(user_id)
    permissions = auth_service.get_user_permissions(user_id)
    
    return UserInfo(
        id=user.id,
        username=user.username,
        email=user.email,
        tenant_id=user.tenant_id,
        roles=roles,
        permissions=permissions
    )


@router.post("/logout", response_model=MessageResponse)
def logout():
    """用户登出（前端清除令牌即可）"""
    return MessageResponse(message="登出成功")
