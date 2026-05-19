# -*- coding: utf-8 -*-
"""
Phase 5 - AI 模型配置 API
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.ai.ai_model_service import AIModelService

router = APIRouter(prefix="/api/ai/models", tags=["AI模型配置 (Phase 5)"])


def get_model_service(db: Session = Depends(get_db)) -> AIModelService:
    return AIModelService(db)


class ModelConfigCreate(BaseModel):
    name: str
    provider: str
    api_key: str
    model: str
    base_url: Optional[str] = None
    group_id: Optional[str] = None
    temperature: Optional[int] = 7
    max_tokens: Optional[int] = 4096
    is_default: Optional[bool] = False


class ModelConfigUpdate(BaseModel):
    name: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None
    group_id: Optional[str] = None
    temperature: Optional[int] = None
    max_tokens: Optional[int] = None
    enabled: Optional[bool] = None
    is_default: Optional[bool] = None


@router.get("/providers")
async def get_providers(service: AIModelService = Depends(get_model_service)):
    """获取支持的 AI 模型供应商列表"""
    return service.get_providers()


@router.get("/configs")
async def list_configs(
    include_disabled: bool = False,
    service: AIModelService = Depends(get_model_service),
):
    """获取所有模型配置"""
    return service.get_configs(include_disabled=include_disabled)


@router.get("/configs/{config_id}")
async def get_config(
    config_id: int,
    service: AIModelService = Depends(get_model_service),
):
    """获取单个配置"""
    config = service.get_config(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    return config


@router.post("/configs")
async def create_config(
    request: ModelConfigCreate,
    service: AIModelService = Depends(get_model_service),
):
    """创建模型配置"""
    result = service.create_config(
        name=request.name,
        provider=request.provider,
        api_key=request.api_key,
        model=request.model,
        base_url=request.base_url,
        group_id=request.group_id,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        is_default=request.is_default,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.put("/configs/{config_id}")
async def update_config(
    config_id: int,
    request: ModelConfigUpdate,
    service: AIModelService = Depends(get_model_service),
):
    """更新模型配置"""
    result = service.update_config(
        config_id=config_id,
        name=request.name,
        api_key=request.api_key,
        model=request.model,
        base_url=request.base_url,
        group_id=request.group_id,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        enabled=request.enabled,
        is_default=request.is_default,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.delete("/configs/{config_id}")
async def delete_config(
    config_id: int,
    service: AIModelService = Depends(get_model_service),
):
    """删除模型配置"""
    result = service.delete_config(config_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/configs/{config_id}/set-default")
async def set_default(
    config_id: int,
    service: AIModelService = Depends(get_model_service),
):
    """设为默认模型"""
    result = service.set_default(config_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/configs/{config_id}/test")
async def test_connection(
    config_id: int,
    service: AIModelService = Depends(get_model_service),
):
    """测试模型连接"""
    result = service.test_connection(config_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.get("/default")
async def get_default(service: AIModelService = Depends(get_model_service)):
    """获取当前默认模型"""
    config = service.get_default_config()
    if not config:
        return {"error": "No default model configured"}
    return config


class ChatRequest(BaseModel):
    messages: List[dict]  # [{"role": "user", "content": "..."}]
    config_id: Optional[int] = None
    model: Optional[str] = None
    temperature: Optional[int] = None
    max_tokens: Optional[int] = None


@router.post("/chat")
async def chat(
    request: ChatRequest,
    service: AIModelService = Depends(get_model_service),
):
    """通用 LLM 对话接口"""
    result = service.chat(
        messages=request.messages,
        config_id=request.config_id,
        model=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )
    if not result.get("success"):
        raise HTTPException(status_code=502, detail=result.get("error"))
    return result
