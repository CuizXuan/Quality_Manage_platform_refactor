from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


# ── TestPlan ──────────────────────────────────────────────────────────────────

class TestPlanCreate(BaseModel):
    project_id: Optional[int] = None
    version_id: Optional[int] = None
    iteration_id: Optional[int] = None
    name: str = Field(..., max_length=200)
    description: Optional[str] = ""
    status: Optional[str] = "draft"
    owner_id: Optional[int] = None


class TestPlanUpdate(BaseModel):
    project_id: Optional[int] = None
    version_id: Optional[int] = None
    iteration_id: Optional[int] = None
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    status: Optional[str] = None
    owner_id: Optional[int] = None


class TestSuiteItemDetailResponse(BaseModel):
    id: int
    suite_id: int
    item_type: str
    item_id: int
    item_name: Optional[str] = None
    sort_order: int = 0

    class Config:
        from_attributes = True


class TestSuiteDetailResponse(BaseModel):
    id: int
    plan_id: int
    name: str
    description: Optional[str] = ""
    sort_order: int = 0
    items: List[TestSuiteItemDetailResponse] = []

    class Config:
        from_attributes = True


class TestPlanResponse(BaseModel):
    id: int
    project_id: Optional[int] = None
    version_id: Optional[int] = None
    iteration_id: Optional[int] = None
    name: str
    description: Optional[str] = ""
    status: str = "draft"
    owner_id: Optional[int] = None
    created_at: str = ""
    updated_at: str = ""
    suites: List[TestSuiteDetailResponse] = []

    class Config:
        from_attributes = True


# ── TestSuite ─────────────────────────────────────────────────────────────────

class TestSuiteCreate(BaseModel):
    plan_id: Optional[int] = None  # from path, body doesn't require it
    name: str = Field(..., max_length=200)
    description: Optional[str] = ""
    sort_order: Optional[int] = 0


class TestSuiteUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    sort_order: Optional[int] = None


class TestSuiteResponse(BaseModel):
    id: int
    plan_id: int
    name: str
    description: Optional[str] = ""
    sort_order: int = 0
    items: List["TestSuiteItemDetailResponse"] = []  # optional for list vs detail

    class Config:
        from_attributes = True


# ── TestSuiteItem ─────────────────────────────────────────────────────────────

class TestSuiteItemCreate(BaseModel):
    suite_id: int
    item_type: Literal["case", "scenario"]
    item_id: int
    sort_order: Optional[int] = 0


class TestSuiteItemResponse(BaseModel):
    id: int
    suite_id: int
    item_type: str
    item_id: int
    item_name: Optional[str] = None
    sort_order: int = 0

    class Config:
        from_attributes = True


# ── TestPlanRun ───────────────────────────────────────────────────────────────

class TestPlanRunResponse(BaseModel):
    id: int
    plan_id: int
    status: str = "pending"
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    duration_ms: Optional[int] = None
    summary: Dict[str, Any] = {}

    class Config:
        from_attributes = True


# ── List responses ────────────────────────────────────────────────────────────

class TestPlanListResponse(BaseModel):
    items: List[TestPlanResponse]
    total: int
    page: int
    page_size: int


class TestSuiteListResponse(BaseModel):
    items: List[TestSuiteResponse]
    total: int
    page: int
    page_size: int


class TestSuiteItemListResponse(BaseModel):
    items: List[TestSuiteItemResponse]
    total: int
    page: int
    page_size: int


class TestPlanRunListResponse(BaseModel):
    items: List[TestPlanRunResponse]
    total: int
    page: int
    page_size: int