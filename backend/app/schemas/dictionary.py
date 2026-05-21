# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ============== DictType Schemas ==============

class DictTypeCreate(BaseModel):
    code: str = Field(..., max_length=50, description="唯一编码")
    name: str = Field(..., max_length=100, description="类型名称")
    description: Optional[str] = Field("", max_length=255, description="描述")
    sort_order: int = Field(0, ge=0, description="排序")
    status: str = Field("active", description="状态: active/disabled")


class DictTypeUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    sort_order: Optional[int] = Field(None, ge=0)
    status: Optional[str] = Field(None, description="状态: active/disabled")


class DictTypeResponse(BaseModel):
    id: int
    code: str
    name: str
    description: str = ""
    sort_order: int = 0
    status: str = "active"
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DictTypeListResponse(BaseModel):
    items: list[DictTypeResponse]
    total: int
    page: int
    page_size: int


# ============== DictItem Schemas ==============

class DictItemCreate(BaseModel):
    type_id: int = Field(..., description="字典类型ID")
    code: str = Field(..., max_length=50, description="字典编码")
    name: str = Field(..., max_length=100, description="显示名称")
    value: Optional[str] = Field("", max_length=100, description="存储值")
    sort_order: int = Field(0, ge=0, description="排序")
    status: str = Field("active", description="状态: active/disabled")
    color: Optional[str] = Field("", max_length=20, description="展示颜色")
    is_default: bool = Field(False, description="是否默认")


class DictItemUpdate(BaseModel):
    type_id: Optional[int] = None
    code: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=100)
    value: Optional[str] = Field(None, max_length=100)
    sort_order: Optional[int] = Field(None, ge=0)
    status: Optional[str] = Field(None, description="状态: active/disabled")
    color: Optional[str] = Field(None, max_length=20)
    is_default: Optional[bool] = None


class DictItemResponse(BaseModel):
    id: int
    type_id: int
    code: str
    name: str
    value: str = ""
    sort_order: int = 0
    status: str = "active"
    color: str = ""
    is_default: bool = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DictItemListResponse(BaseModel):
    items: list[DictItemResponse]
    total: int
    page: int
    page_size: int


# ============== 公开查询 Schema ==============

class PublicDictItem(BaseModel):
    """公开API返回的字典项格式"""
    label: str
    value: str
    code: str = ""
    color: str = ""
    isDefault: bool = False


class PublicDictType(BaseModel):
    """公开API返回的字典类型格式（带所有启用项）"""
    code: str
    name: str
    items: list[PublicDictItem]


class PublicDictResponse(BaseModel):
    """GET /api/dicts/{type_code} 返回格式"""
    items: list[PublicDictItem]


class PublicAllDictResponse(BaseModel):
    """GET /api/dicts 返回所有启用项（按类型分组）"""
    types: list[PublicDictType]


# ============== 排序更新 Schema ==============

class DictItemReorderItem(BaseModel):
    id: int
    sort_order: int


class DictItemReorderRequest(BaseModel):
    items: list[DictItemReorderItem]