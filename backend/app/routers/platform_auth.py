from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.platform import PlatformUser, PlatformUserRole
from app.schemas.platform import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.platform_auth import PlatformAuthService

router = APIRouter(prefix="/api/auth", tags=["平台认证"])
security = HTTPBearer(auto_error=False)


def get_current_platform_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> PlatformUser:
    if not credentials:
        raise HTTPException(status_code=401, detail="未提供认证令牌")
    payload = PlatformAuthService.decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="令牌无效或已过期")
    user = db.query(PlatformUser).filter(PlatformUser.id == int(payload["sub"])).first()
    if not user or user.status != "active":
        raise HTTPException(status_code=401, detail="用户不可用")
    return user


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, http_request: Request, db: Session = Depends(get_db)):
    service = PlatformAuthService(db)
    user = service.authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    user.last_login_at = datetime.utcnow()
    db.commit()
    return TokenResponse(
        access_token=service.create_access_token(user.id),
        refresh_token=service.create_refresh_token(user.id),
    )


@router.post("/register", response_model=TokenResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(PlatformUser).filter(
        or_(PlatformUser.username == request.username, PlatformUser.email == request.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名或邮箱已存在")

    service = PlatformAuthService(db)
    user = PlatformUser(
        username=request.username,
        email=request.email,
        password_hash=service.hash_password(request.password),
        display_name=request.username,
        status="active",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return TokenResponse(
        access_token=service.create_access_token(user.id),
        refresh_token=service.create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: RefreshRequest, db: Session = Depends(get_db)):
    service = PlatformAuthService(db)
    access_token = service.refresh_access_token(request.refresh_token)
    if not access_token:
        raise HTTPException(status_code=401, detail="无效的刷新令牌")
    return TokenResponse(access_token=access_token, refresh_token=request.refresh_token)


@router.get("/me", response_model=UserResponse)
def me(current_user: PlatformUser = Depends(get_current_platform_user), db: Session = Depends(get_db)):
    return build_user_response(current_user, db)


@router.post("/logout")
def logout():
    return {"message": "登出成功"}


def build_user_response(user: PlatformUser, db: Session) -> UserResponse:
    links = db.query(PlatformUserRole).filter(PlatformUserRole.user_id == user.id).all()
    roles = [link.role for link in links if link.role]
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        display_name=user.display_name or "",
        phone=user.phone or "",
        status=user.status,
        organization_id=user.organization_id,
        organization_name=user.organization.name if user.organization else None,
        roles=[role.name for role in roles],
        role_ids=[role.id for role in roles],
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )

