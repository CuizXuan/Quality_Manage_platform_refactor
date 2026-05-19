from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class TestCaseCreate(BaseModel):
    case_type: Literal["functional", "api"] = Field(default="api")
    folder_id: Optional[int] = None
    name: str = Field(..., max_length=200)
    description: str = ""
    method: str = Field(default="GET", max_length=10)
    url: str = Field(..., max_length=2000)
    query_params: Dict[str, Any] = Field(default_factory=dict)
    headers: Dict[str, Any] = Field(default_factory=dict)
    cookies: Dict[str, Any] = Field(default_factory=dict)
    auth_config: Dict[str, Any] = Field(default_factory=dict)
    body_type: str = Field(default="none", max_length=20)
    body: str = ""
    expected_status: Optional[int] = None
    source_debug_id: Optional[int] = None


class TestCaseUpdate(BaseModel):
    case_type: Optional[Literal["functional", "api"]] = Field(None)
    folder_id: Optional[int] = None
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    method: Optional[str] = Field(None, max_length=10)
    url: Optional[str] = Field(None, max_length=2000)
    query_params: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, Any]] = None
    cookies: Optional[Dict[str, Any]] = None
    auth_config: Optional[Dict[str, Any]] = None
    body_type: Optional[str] = Field(None, max_length=20)
    body: Optional[str] = None
    expected_status: Optional[int] = None
    source_debug_id: Optional[int] = None


class TestCaseResponse(BaseModel):
    id: int
    case_type: Literal["functional", "api"]
    folder_id: Optional[int] = None
    name: str
    description: str = ""
    method: str
    url: str
    query_params: Dict[str, Any]
    headers: Dict[str, Any]
    cookies: Dict[str, Any]
    auth_config: Dict[str, Any]
    body_type: str
    body: str
    expected_status: Optional[int] = None
    source_debug_id: Optional[int] = None
    created_by: Optional[int] = None
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class TestCaseListResponse(BaseModel):
    items: List[TestCaseResponse]
    total: int
    page: int
    page_size: int


class DeleteResponse(BaseModel):
    id: int
