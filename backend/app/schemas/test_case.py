from typing import Any, Dict, List, Optional, Literal

from pydantic import BaseModel, Field


class TestCaseCreate(BaseModel):
    name: str = Field(..., max_length=200)
    description: str = ""
    folder_id: Optional[int] = None
    priority: Literal["P0", "P1", "P2", "P3"] = Field(default="P2")
    tags: List[str] = Field(default_factory=list)
    pre_condition: str = ""
    case_type: Literal["api", "functional"] = Field(default="api")
    api_case: Optional[Dict[str, Any]] = Field(default=None)
    functional_case: Optional[Dict[str, Any]] = Field(default=None)


class TestCaseUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    folder_id: Optional[int] = None
    priority: Optional[Literal["P0", "P1", "P2", "P3"]] = None
    tags: Optional[List[str]] = None
    pre_condition: Optional[str] = None
    api_case: Optional[Dict[str, Any]] = Field(default=None)
    functional_case: Optional[Dict[str, Any]] = Field(default=None)


class TestCaseResponse(BaseModel):
    id: int
    name: str
    description: str = ""
    folder_id: Optional[int] = None
    priority: str = "P2"
    tags: List[str] = []
    pre_condition: str = ""
    case_type: Literal["api", "functional"]
    source_debug_id: Optional[int] = None
    created_by: Optional[int] = None
    created_at: str
    updated_at: Optional[str] = None
    api_case: Optional[Dict[str, Any]] = None
    functional_case: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class TestCaseListResponse(BaseModel):
    items: List[TestCaseResponse]
    total: int
    page: int
    page_size: int


class DeleteResponse(BaseModel):
    id: int