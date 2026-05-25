from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── ApiGroup ──────────────────────────────────────────────────────────────────

class ApiGroupCreate(BaseModel):
    project_id: Optional[int] = None
    name: str = Field(..., max_length=200)
    parent_id: Optional[int] = None
    sort_order: Optional[int] = 0


class ApiGroupUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None


class ApiGroupResponse(BaseModel):
    id: int
    project_id: Optional[int] = None
    name: str
    parent_id: Optional[int] = None
    sort_order: Optional[int] = 0
    created_at: str = ""
    updated_at: str = ""

    class Config:
        from_attributes = True


# ── ApiDefinition ──────────────────────────────────────────────────────────────

class ApiDefinitionCreate(BaseModel):
    project_id: Optional[int] = None
    group_id: Optional[int] = None
    name: str = Field(..., max_length=200)
    method: str = Field(..., max_length=10)
    path: str = Field(..., max_length=500)
    base_url: Optional[str] = Field(None, max_length=500)
    summary: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    parameters: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    request_body: Optional[Dict[str, Any]] = Field(default_factory=dict)
    responses: Optional[Dict[str, Any]] = Field(default_factory=dict)
    version: Optional[str] = Field("1.0.0", max_length=20)
    status: Optional[str] = "active"


class ApiDefinitionUpdate(BaseModel):
    project_id: Optional[int] = None
    group_id: Optional[int] = None
    name: Optional[str] = Field(None, max_length=200)
    method: Optional[str] = Field(None, max_length=10)
    path: Optional[str] = Field(None, max_length=500)
    base_url: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    parameters: Optional[List[Dict[str, Any]]] = None
    request_body: Optional[Dict[str, Any]] = None
    responses: Optional[Dict[str, Any]] = None
    version: Optional[str] = None
    status: Optional[str] = None


class ApiDefinitionResponse(BaseModel):
    id: int
    project_id: Optional[int] = None
    group_id: Optional[int] = None
    name: str
    method: str
    path: str
    base_url: Optional[str] = None
    summary: Optional[str] = ""
    description: Optional[str] = ""
    tags: List[str] = []
    parameters: List[Dict[str, Any]] = []
    request_body: Dict[str, Any] = {}
    responses: Dict[str, Any] = {}
    version: str = "1.0.0"
    status: str = "active"
    created_at: str = ""
    updated_at: str = ""

    class Config:
        from_attributes = True


class DebugPayloadResponse(BaseModel):
    method: str
    url: str
    headers: Dict[str, str] = {}
    body_type: str = "none"
    body: str = ""
    query_params: Dict[str, Any] = {}


# ── ApiImportRecord ────────────────────────────────────────────────────────────

class ApiImportRequest(BaseModel):
    source_type: str = Field(..., description="url or json")
    source_url: Optional[str] = None
    raw_content: Optional[str] = None
    project_id: Optional[int] = None


class ApiImportRecordResponse(BaseModel):
    id: int
    project_id: Optional[int] = None
    source_type: str
    source_url: Optional[str] = None
    status: str
    imported_count: int = 0
    message: str = ""
    created_at: str = ""

    class Config:
        from_attributes = True


class OpenApiImportResult(BaseModel):
    total: int
    imported: int
    skipped: int
    groups_created: int
    message: str = ""


# ── List response ─────────────────────────────────────────────────────────────

class ApiGroupListResponse(BaseModel):
    items: List[ApiGroupResponse]
    total: int
    page: int
    page_size: int


class ApiDefinitionListResponse(BaseModel):
    items: List[ApiDefinitionResponse]
    total: int
    page: int
    page_size: int