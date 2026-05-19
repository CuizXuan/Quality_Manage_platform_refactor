# -*- coding: utf-8 -*-
"""
Phase 4 - 开放API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db, SessionLocal
from app.services.auth_service import AuthService
from app.services.dashboard_service import OpenAPIService

router = APIRouter(prefix="/api/openapi", tags=["开放API"])
security = HTTPBearer(auto_error=False)


# ==================== API文档 ====================

@router.get("/endpoints", summary="获取API端点列表")
def get_api_endpoints():
    """获取所有可用的API端点"""
    service = OpenAPIService(db := SessionLocal())
    try:
        return {"items": service.get_api_endpoints()}
    finally:
        db.close()


@router.get("/docs", summary="API文档")
def get_api_docs():
    """返回API文档信息"""
    return {
        "title": "Quality Manage Platform API",
        "version": "1.4.0",
        "description": "质量保障平台开放API文档",
        "authentication": "在请求头中添加 Authorization: Bearer <token>",
        "rate_limit": "1000 requests/minute"
    }


# ==================== API Key管理 ====================

class APIKeyResponse(BaseModel):
    key_id: str
    key_prefix: str
    created_at: str
    permissions: List[str]
    rate_limit: int


@router.get("/keys", summary="获取API Key列表")
def get_api_keys(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """获取当前用户的API Key列表"""
    # 简化版：返回模拟数据
    return {
        "items": [
            {
                "key_id": "key_001",
                "key_prefix": "sk-test-****",
                "name": "测试Key",
                "created_at": "2026-04-11T00:00:00",
                "permissions": ["read", "write"],
                "rate_limit": 1000,
                "last_used": None
            }
        ]
    }


class APIKeyCreate(BaseModel):
    name: str
    permissions: List[str] = ["read"]
    rate_limit: int = 1000


@router.post("/keys", summary="创建API Key")
def create_api_key(
    request: APIKeyCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """创建新的API Key"""
    # 简化版：生成模拟key
    import secrets
    new_key = f"sk-{secrets.token_hex(16)}"
    return {
        "key_id": f"key_{secrets.token_hex(4)}",
        "key": new_key,
        "key_prefix": new_key[:12] + "****",
        "name": request.name,
        "created_at": "2026-04-11T12:00:00",
        "permissions": request.permissions,
        "rate_limit": request.rate_limit
    }


@router.delete("/keys/{key_id}", summary="删除API Key")
def delete_api_key(
    key_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """删除API Key"""
    return {"message": "删除成功"}


# ==================== 认证 API（公开） ====================

from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/auth/token", summary="获取访问令牌")
def get_access_token(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    使用用户名密码获取访问令牌
    可用于第三方系统集成
    """
    auth_service = AuthService(db)
    user = auth_service.authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    access_token = auth_service.create_access_token(user.id, user.tenant_id)
    refresh_token = auth_service.create_refresh_token(user.id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 1800
    }


# ==================== 公共数据 API（需要API Key） ====================

def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """验证API Key"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="未提供API Key")
    
    service = OpenAPIService(SessionLocal())
    try:
        valid, info = service.validate_api_key(x_api_key)
        if not valid:
            raise HTTPException(status_code=401, detail="无效的API Key")
        return info
    finally:
        SessionLocal().close()


@router.get("/public/health", summary="公共健康检查")
def public_health():
    """公共健康检查接口，不需要认证"""
    return {"status": "ok", "timestamp": "2026-04-11T12:00:00"}


@router.get("/public/projects", summary="获取公开项目")
def public_projects(
    x_api_key: Optional[str] = Header(None)
):
    """获取公开项目列表"""
    if x_api_key:
        verify_api_key(x_api_key)
    # 返回模拟数据
    return {
        "items": [
            {"id": 1, "name": "示例项目", "key": "DEMO"}
        ]
    }



