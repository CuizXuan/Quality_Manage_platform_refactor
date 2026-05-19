# -*- coding: utf-8 -*-
"""
Phase 5 - 插件市场 API
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.plugin_service import PluginMarketplaceService

router = APIRouter(prefix="/api/marketplace", tags=["插件市场 (Phase 5)"])


def get_plugin_service(db: Session = Depends(get_db)) -> PluginMarketplaceService:
    return PluginMarketplaceService(db)


# ==================== Plugin APIs ====================

class PluginPublishRequest(BaseModel):
    name: str
    slug: str
    version: str
    category: str
    description: Optional[str] = None
    author: Optional[str] = None
    author_url: Optional[str] = None
    homepage: Optional[str] = None
    license: Optional[str] = "MIT"
    tags: Optional[List[str]] = []
    requirements: Optional[dict] = {}
    config_schema: Optional[dict] = None
    manifest: Optional[dict] = None
    readme: Optional[str] = None


class PluginInstallRequest(BaseModel):
    project_id: Optional[int] = None
    version: Optional[str] = None
    config: Optional[dict] = None


class PluginReviewRequest(BaseModel):
    rating: int
    title: Optional[str] = None
    content: Optional[str] = None
    pros: Optional[str] = None
    cons: Optional[str] = None


@router.get("/plugins")
async def list_plugins(
    category: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = "download_count",
    page: int = 1,
    page_size: int = 20,
    service: PluginMarketplaceService = Depends(get_plugin_service),
):
    """获取插件列表"""
    return service.list_plugins(
        category=category,
        search=search,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )


@router.post("/plugins")
async def publish_plugin(
    request: PluginPublishRequest,
    req: Request,
    service: PluginMarketplaceService = Depends(get_plugin_service),
):
    """发布插件"""
    user_id = getattr(req.state, "user_id", None) or 1
    return service.publish_plugin(request.model_dump(), user_id)


@router.get("/plugins/{plugin_id}")
async def get_plugin(
    plugin_id: int,
    service: PluginMarketplaceService = Depends(get_plugin_service),
):
    """获取插件详情"""
    plugin = service.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return plugin


@router.put("/plugins/{plugin_id}")
async def update_plugin(
    plugin_id: int,
    request: PluginPublishRequest,
    req: Request,
    service: PluginMarketplaceService = Depends(get_plugin_service),
):
    """更新插件"""
    user_id = getattr(req.state, "user_id", None) or 1
    result = service.update_plugin(plugin_id, request.model_dump(), user_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.delete("/plugins/{plugin_id}")
async def delete_plugin(
    plugin_id: int,
    req: Request,
    service: PluginMarketplaceService = Depends(get_plugin_service),
):
    """删除插件"""
    user_id = getattr(req.state, "user_id", None) or 1
    result = service.delete_plugin(plugin_id, user_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/plugins/{plugin_id}/install")
async def install_plugin(
    plugin_id: int,
    request: PluginInstallRequest,
    req: Request,
    service: PluginMarketplaceService = Depends(get_plugin_service),
):
    """安装插件"""
    user_id = getattr(req.state, "user_id", None) or 1
    return service.install_plugin(
        plugin_id=plugin_id,
        user_id=user_id,
        project_id=request.project_id,
        version=request.version,
        config=request.config,
    )


@router.post("/plugins/{plugin_id}/uninstall")
async def uninstall_plugin(
    plugin_id: int,
    req: Request,
    service: PluginMarketplaceService = Depends(get_plugin_service),
):
    """卸载插件"""
    user_id = getattr(req.state, "user_id", None) or 1
    result = service.uninstall_plugin(plugin_id, user_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.get("/my-plugins")
async def get_my_plugins(
    req: Request,
    service: PluginMarketplaceService = Depends(get_plugin_service),
):
    """获取我的插件（已安装）"""
    user_id = getattr(req.state, "user_id", None) or 1
    return service.get_my_plugins(user_id)


@router.get("/my-published")
async def get_my_published(
    req: Request,
    service: PluginMarketplaceService = Depends(get_plugin_service),
):
    """获取我发布的插件"""
    user_id = getattr(req.state, "user_id", None) or 1
    return service.get_my_published(user_id)


# ==================== Plugin Reviews ====================

@router.get("/plugins/{plugin_id}/reviews")
async def get_plugin_reviews(
    plugin_id: int,
    page: int = 1,
    page_size: int = 20,
    service: PluginMarketplaceService = Depends(get_plugin_service),
):
    """获取插件评论"""
    return service.get_reviews(plugin_id, page, page_size)


@router.post("/plugins/{plugin_id}/reviews")
async def create_review(
    plugin_id: int,
    request: PluginReviewRequest,
    req: Request,
    service: PluginMarketplaceService = Depends(get_plugin_service),
):
    """评论插件"""
    user_id = getattr(req.state, "user_id", None) or 1
    return service.create_review(
        plugin_id=plugin_id,
        user_id=user_id,
        rating=request.rating,
        title=request.title,
        content=request.content,
        pros=request.pros,
        cons=request.cons,
    )


# ==================== CLI Auth APIs ====================

class CLIKeyCreateRequest(BaseModel):
    name: str
    permissions: Optional[List[str]] = ["read"]
    expires_in_days: Optional[int] = None


@router.post("/cli/auth/token")
async def create_cli_token(
    api_key: str,
    service: PluginMarketplaceService = Depends(get_plugin_service),
):
    """验证 API Key 并返回访问令牌（模拟）"""
    result = service.validate_cli_key(api_key)
    if not result.get("success"):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return result


@router.post("/cli/keys")
async def create_cli_key(
    request: CLIKeyCreateRequest,
    req: Request,
    service: PluginMarketplaceService = Depends(get_plugin_service),
):
    """创建 CLI Key"""
    user_id = getattr(req.state, "user_id", None) or 1
    return service.create_cli_key(
        user_id=user_id,
        name=request.name,
        permissions=request.permissions,
        expires_in_days=request.expires_in_days,
    )


@router.get("/cli/keys")
async def list_cli_keys(
    req: Request,
    service: PluginMarketplaceService = Depends(get_plugin_service),
):
    """列出我的 CLI Keys"""
    user_id = getattr(req.state, "user_id", None) or 1
    return service.list_cli_keys(user_id)


@router.delete("/cli/keys/{key_id}")
async def delete_cli_key(
    key_id: int,
    req: Request,
    service: PluginMarketplaceService = Depends(get_plugin_service),
):
    """删除 CLI Key"""
    user_id = getattr(req.state, "user_id", None) or 1
    result = service.delete_cli_key(key_id, user_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


# ==================== Categories ====================

@router.get("/categories")
async def get_categories(
    service: PluginMarketplaceService = Depends(get_plugin_service),
):
    """获取插件分类统计"""
    return service.get_categories()
