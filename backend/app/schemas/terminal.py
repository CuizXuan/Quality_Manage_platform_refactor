from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DebugRequestCreate(BaseModel):
    method: str = Field(default="GET", max_length=10)
    url: str = Field(..., max_length=2000)
    query_params: Dict[str, Any] = Field(default_factory=dict)
    headers: Dict[str, Any] = Field(default_factory=dict)
    cookies: Dict[str, Any] = Field(default_factory=dict)
    auth_config: Dict[str, Any] = Field(default_factory=dict)
    body_type: str = Field(default="none", max_length=20)
    body: str = Field(default="")
    environment_id: Optional[int] = None


class DebugResponse(BaseModel):
    id: int
    status_code: int
    response_headers: Dict[str, Any]
    response_body: str
    duration_ms: int
    error_message: str
    created_at: str


class DebugRequestResponse(BaseModel):
    id: int
    method: str
    url: str
    query_params: Dict[str, Any]
    headers: Dict[str, Any]
    cookies: Dict[str, Any]
    auth_config: Dict[str, Any]
    body_type: str
    body: str
    status: str
    source_type: str
    created_at: str
    latest_result: Optional[DebugResponse] = None


class DebugHistoryItem(BaseModel):
    id: int
    method: str
    url: str
    status_code: Optional[int] = None
    duration_ms: Optional[int] = None
    created_at: str


class DebugHistoryResponse(BaseModel):
    items: List[DebugHistoryItem]
    total: int
    page: int
    page_size: int


class SaveAsCaseRequest(BaseModel):
    debug_request_id: int
    case_name: str
    case_description: str = ""
    folder_id: Optional[int] = None


class SaveAsCaseResponse(BaseModel):
    case_id: int
    message: str


class ImportDocumentRequest(BaseModel):
    source_url: Optional[str] = None
    raw_content: str = ""
    content_type: str = Field(default="openapi", max_length=20)


class ImportDocumentItem(BaseModel):
    method: str
    url: str
    summary: str = ""


class ImportDocumentResponse(BaseModel):
    items: List[ImportDocumentItem]
    total: int
