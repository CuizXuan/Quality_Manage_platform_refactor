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
    is_automated: bool = False
    auto_script_path: str = Field(default="", max_length=1000)
    auto_script_config: Dict[str, Any] = Field(default_factory=dict)
    auto_case_id: str = Field(default="", max_length=100)
    api_case: Optional[Dict[str, Any]] = Field(default=None)
    functional_case: Optional[Dict[str, Any]] = Field(default=None)
    project_id: Optional[int] = None
    version_id: Optional[int] = None
    iteration_id: Optional[int] = None
    requirement_id: Optional[int] = None


class TestCaseUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    folder_id: Optional[int] = None
    priority: Optional[Literal["P0", "P1", "P2", "P3"]] = None
    tags: Optional[List[str]] = None
    pre_condition: Optional[str] = None
    is_automated: Optional[bool] = None
    auto_script_path: Optional[str] = Field(default=None, max_length=1000)
    auto_script_config: Optional[Dict[str, Any]] = None
    auto_case_id: Optional[str] = Field(default=None, max_length=100)
    api_case: Optional[Dict[str, Any]] = Field(default=None)
    functional_case: Optional[Dict[str, Any]] = Field(default=None)
    project_id: Optional[int] = None
    version_id: Optional[int] = None
    iteration_id: Optional[int] = None
    requirement_id: Optional[int] = None


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
    creator_name: str = ""
    is_automated: bool = False
    auto_script_path: str = ""
    auto_script_config: Dict[str, Any] = {}
    auto_case_id: str = ""
    created_at: str
    updated_at: Optional[str] = None
    api_case: Optional[Dict[str, Any]] = None
    functional_case: Optional[Dict[str, Any]] = None
    project_id: Optional[int] = None
    version_id: Optional[int] = None
    iteration_id: Optional[int] = None
    requirement_id: Optional[int] = None

    class Config:
        from_attributes = True


class TestCaseListResponse(BaseModel):
    items: List[TestCaseResponse]
    total: int
    page: int
    page_size: int
    stats: Dict[str, Any] = Field(default_factory=dict)


class DeleteResponse(BaseModel):
    id: int


class BatchDeleteRequest(BaseModel):
    ids: List[int] = Field(..., min_length=1)


class BatchUpdateRequest(BaseModel):
    ids: List[int] = Field(..., min_length=1)
    priority: Optional[Literal["P0", "P1", "P2", "P3"]] = None
    is_automated: Optional[bool] = None


class BatchActionResponse(BaseModel):
    count: int
