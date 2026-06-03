from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ImportRequest(BaseModel):
    source_type: str = Field(..., pattern="^(openapi|postman|apifox)$")
    source_name: str = Field(default="", max_length=200)
    source_url: Optional[str] = None
    raw_content: Optional[str] = None
    project_id: Optional[int] = None


class ImportIssueResponse(BaseModel):
    id: int
    issue_type: str
    severity: str
    endpoint_path: str = ""
    method: str = ""
    message: str = ""
    details: Dict = {}


class ImportJobResponse(BaseModel):
    id: int
    project_id: Optional[int] = None
    source_type: str
    source_name: str
    source_ref: Optional[str] = None
    status: str
    total_count: int = 0
    imported_count: int = 0
    issue_count: int = 0
    summary: Dict = {}
    issues: List[ImportIssueResponse] = []
