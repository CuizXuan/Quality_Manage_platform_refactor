# -*- coding: utf-8 -*-
"""
Phase 4 - 租户中间件
请求级租户隔离
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from typing import Callable, Optional
import jwt
from app.config import SECRET_KEY, ALGORITHM


class TenantMiddleware(BaseHTTPMiddleware):
    """
    租户隔离中间件
    
    功能：
    1. 从 JWT Token 中解析 tenant_id
    2. 将 tenant_id 注入到 request state 中
    3. 提供当前租户的上下文信息
    """
    
    # 不需要租户验证的路径
    EXEMPT_PATHS = [
        "/api/auth/login",
        "/api/auth/register",
        "/api/auth/refresh",
        "/api/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/",
        "/api/openapi/endpoints",
        "/api/openapi/docs",
        "/api/openapi/auth/token",
        "/api/openapi/public",
        "/proxy", "/proxy/",  # API 代理端点
        # AI 模型配置 - 公开接口
        "/api/ai/models/providers",
    ]
    
    # 需要租户验证的路径前缀
    TENANT_PATH_PREFIXES = [
        "/api/tenant",
        "/api/cases",
        "/api/scenarios",
        "/api/environments",
        "/api/schedules",
        "/api/datasets",
        "/api/mocks",
        "/api/reports",
        "/api/loadtest",
        "/api/repositories",
        "/api/coverage",
        "/api/defects",
        "/api/quality-gates",
        "/api/integrations",
        "/api/case-folders",
    ]
    
    def __init__(self, app):
        super().__init__(app)
        self.secret_key = SECRET_KEY
        self.algorithm = ALGORITHM
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        
        # 检查是否豁免
        if self._is_exempt(path):
            request.state.tenant_id = None
            request.state.user_id = None
            request.state.is_authenticated = False
            return await call_next(request)

        # OPTIONS preflight（cors）直接放行
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # 从请求头获取 token
        auth_header = request.headers.get("Authorization", "")
        token = None
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
        
        if not token:
            # 需要认证但没有 token
            return JSONResponse(
                status_code=401,
                content={"detail": "未提供认证令牌"}
            )
        
        # 解析 token
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = int(payload.get("sub"))
            tenant_id = payload.get("tenant_id")
            
            # 注入到 request state
            request.state.user_id = user_id
            request.state.tenant_id = tenant_id
            request.state.is_authenticated = True
            request.state.token_payload = payload
            
        except jwt.ExpiredSignatureError:
            return JSONResponse(
                status_code=401,
                content={"detail": "令牌已过期"}
            )
        except jwt.InvalidTokenError:
            return JSONResponse(
                status_code=401,
                content={"detail": "令牌无效"}
            )
        except Exception:
            return JSONResponse(
                status_code=401,
                content={"detail": "认证失败"}
            )
        
        # 对于需要租户验证的路径，检查租户
        if self._requires_tenant(request):
            if tenant_id is None:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "需要租户权限"}
                )
        
        return await call_next(request)
    
    def _is_exempt(self, path: str) -> bool:
        """检查路径是否豁免"""
        # 精确匹配
        if path in self.EXEMPT_PATHS:
            return True
        # 前缀匹配
        for prefix in ["/docs", "/redoc", "/openapi"]:
            if path.startswith(prefix):
                return True
        return False
    
    def _requires_tenant(self, request: Request) -> bool:
        """检查路径是否需要租户验证"""
        path = request.url.path
        for prefix in self.TENANT_PATH_PREFIXES:
            if path.startswith(prefix):
                return True
        return False


def get_current_tenant_id(request: Request) -> Optional[int]:
    """从请求中获取当前租户 ID"""
    return getattr(request.state, "tenant_id", None)


def get_current_user_id(request: Request) -> Optional[int]:
    """从请求中获取当前用户 ID"""
    return getattr(request.state, "user_id", None)


def is_authenticated(request: Request) -> bool:
    """检查是否已认证"""
    return getattr(request.state, "is_authenticated", False)
