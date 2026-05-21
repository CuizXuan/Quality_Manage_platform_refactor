# -*- coding: utf-8 -*-
"""字典管理路由 + 公开查询路由"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.platform import PlatformUser
from app.routers.platform_auth import get_current_platform_user
from app.schemas.dictionary import (
    DictTypeCreate,
    DictTypeUpdate,
    DictTypeResponse,
    DictTypeListResponse,
    DictItemCreate,
    DictItemUpdate,
    DictItemResponse,
    DictItemListResponse,
    DictItemReorderRequest,
    PublicDictResponse,
    PublicAllDictResponse,
)
from app.services.dict_service import DictService
from app.services.log_service import LogService

# ========== 管理 API（需鉴权）==========
router = APIRouter(prefix="/api/system", tags=["字典管理"])


@router.get("/dict-types", response_model=DictTypeListResponse)
def list_dict_types(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None, description="搜索类型编码或名称"),
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    """字典类型列表（分页）"""
    service = DictService(db)
    items, total = service.list_types(page=page, page_size=page_size, keyword=keyword)
    return DictTypeListResponse(
        items=[DictTypeResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/dict-types", response_model=DictTypeResponse)
def create_dict_type(
    data: DictTypeCreate,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    """创建字典类型"""
    service = DictService(db)
    try:
        item = service.create_type(data)
        LogService(db, current_user.id, current_user.username).log_crud(
            "创建", "字典管理", f"类型:{data.name}", item.id
        )
        return DictTypeResponse.model_validate(item)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/dict-types/{type_id}", response_model=DictTypeResponse)
def update_dict_type(
    type_id: int,
    data: DictTypeUpdate,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    """更新字典类型"""
    service = DictService(db)
    item = service.update_type(type_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="字典类型不存在")
    LogService(db, current_user.id, current_user.username).log_crud(
        "更新", "字典管理", f"类型:{item.name}", type_id
    )
    return DictTypeResponse.model_validate(item)


@router.delete("/dict-types/{type_id}")
def delete_dict_type(
    type_id: int,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    """删除字典类型（级联删除所有字典项）"""
    service = DictService(db)
    item = service.get_type(type_id)
    if not item:
        raise HTTPException(status_code=404, detail="字典类型不存在")
    typename = item.name
    success = service.delete_type(type_id)
    if not success:
        raise HTTPException(status_code=404, detail="字典类型不存在")
    LogService(db, current_user.id, current_user.username).log_crud(
        "删除", "字典管理", f"类型:{typename}", type_id
    )
    return {"message": "删除成功"}


@router.get("/dict-types/{type_id}/items", response_model=DictItemListResponse)
def list_type_items(
    type_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    """获取某类型下的字典项（分页）"""
    service = DictService(db)
    dict_type = service.get_type(type_id)
    if not dict_type:
        raise HTTPException(status_code=404, detail="字典类型不存在")
    items, total = service.get_items_by_type_id(type_id, page=page, page_size=page_size)
    return DictItemListResponse(
        items=[DictItemResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/dict-items", response_model=DictItemListResponse)
def list_dict_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type_id: Optional[int] = Query(None, description="字典类型ID"),
    keyword: Optional[str] = Query(None, description="搜索字典编码或名称"),
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    """字典项列表（分页）"""
    service = DictService(db)
    items, total = service.list_items(page=page, page_size=page_size, type_id=type_id, keyword=keyword)
    return DictItemListResponse(
        items=[DictItemResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/dict-items", response_model=DictItemResponse)
def create_dict_item(
    data: DictItemCreate,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    """创建字典项"""
    service = DictService(db)
    # 验证类型存在
    dict_type = service.get_type(data.type_id)
    if not dict_type:
        raise HTTPException(status_code=400, detail="字典类型不存在")
    try:
        item = service.create_item(data)
        LogService(db, current_user.id, current_user.username).log_crud(
            "创建", "字典管理", f"字典项:{data.name}", item.id
        )
        return DictItemResponse.model_validate(item)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/dict-items/{item_id}", response_model=DictItemResponse)
def update_dict_item(
    item_id: int,
    data: DictItemUpdate,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    """更新字典项"""
    service = DictService(db)
    item = service.update_item(item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="字典项不存在")
    LogService(db, current_user.id, current_user.username).log_crud(
        "更新", "字典管理", f"字典项:{item.name}", item_id
    )
    return DictItemResponse.model_validate(item)


@router.delete("/dict-items/{item_id}")
def delete_dict_item(
    item_id: int,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    """删除字典项"""
    service = DictService(db)
    item = service.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="字典项不存在")
    itemname = item.name
    success = service.delete_item(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="字典项不存在")
    LogService(db, current_user.id, current_user.username).log_crud(
        "删除", "字典管理", f"字典项:{itemname}", item_id
    )
    return {"message": "删除成功"}


@router.put("/dict-items/{item_id}/toggle-status", response_model=DictItemResponse)
def toggle_item_status(
    item_id: int,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    """启用/禁用切换"""
    service = DictService(db)
    item = service.toggle_item_status(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="字典项不存在")
    LogService(db, current_user.id, current_user.username).log_crud(
        "切换状态", "字典管理", f"字典项:{item.name}", item_id
    )
    return DictItemResponse.model_validate(item)


@router.put("/dict-items/reorder")
def reorder_dict_items(
    data: DictItemReorderRequest,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    """批量更新字典项排序"""
    service = DictService(db)
    service.reorder_items(data.items)
    LogService(db, current_user.id, current_user.username).log(
        "批量排序", "字典管理", f"更新了 {len(data.items)} 项排序"
    )
    return {"message": "排序更新成功"}


# ========== 公开查询 API（无需鉴权）==========
public_router = APIRouter(prefix="/api/dicts", tags=["字典查询"])


@public_router.get("/{type_code}", response_model=PublicDictResponse)
def get_public_dict(type_code: str, db: Session = Depends(get_db)):
    """获取某类型所有启用的字典项（高性能，带缓存）"""
    service = DictService(db)
    return service.get_public_dict(type_code)


@public_router.get("", response_model=PublicAllDictResponse)
def get_all_public_dicts(db: Session = Depends(get_db)):
    """获取所有启用字典（按类型分组，带缓存）"""
    service = DictService(db)
    return service.get_all_public_dicts()
