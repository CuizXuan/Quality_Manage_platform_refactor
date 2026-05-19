from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Union, Literal
from datetime import datetime


class AssertionRule(BaseModel):
    id: str
    type: str
    operator: str
    expected: Optional[Union[str, int, float]] = None
    path: Optional[str] = None
    header_name: Optional[str] = None
    enabled: bool = True


class TestCaseBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = ""
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"] = "GET"
    url: str = Field(default="", max_length=2000)
    headers: Optional[dict] = {}
    params: Optional[dict] = {}
    body: Optional[str] = ""
    body_type: Literal["json", "xml", "form", "raw", "binary"] = "json"
    request_body: Optional[str] = ""
    response_body: Optional[str] = ""
    auth_type: Literal["none", "basic", "bearer", "api_key", "oauth2", "aws"] = "none"
    auth_config: Optional[dict] = {}
    folder_path: str = "/"
    sort_order: int = 0
    assertions: Optional[List[AssertionRule]] = []
    pre_script: Optional[str] = ""
    post_script: Optional[str] = ""
    timeout: int = Field(default=30, ge=1, le=300)
    follow_redirects: bool = True
    verify_ssl: bool = True

    @field_validator("name", mode="before")
    @classmethod
    def name_not_empty(cls, v):
        if isinstance(v, str) and not v.strip():
            raise ValueError("name cannot be empty or whitespace")
        return v.strip() if isinstance(v, str) else v


class TestCaseCreate(TestCaseBase):
    pass


class TestCaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    method: Optional[str] = None
    url: Optional[str] = None
    headers: Optional[dict] = None
    params: Optional[dict] = None
    body: Optional[str] = None
    body_type: Optional[str] = None
    request_body: Optional[str] = None
    response_body: Optional[str] = None
    auth_type: Optional[str] = None
    auth_config: Optional[dict] = None
    folder_path: Optional[str] = None
    sort_order: Optional[int] = None
    assertions: Optional[List[AssertionRule]] = None
    pre_script: Optional[str] = None
    post_script: Optional[str] = None
    timeout: Optional[int] = None
    follow_redirects: Optional[bool] = None
    verify_ssl: Optional[bool] = None


class TestCaseResponse(BaseModel):
    id: int
    name: Optional[str] = None
    description: Optional[str] = None
    method: Optional[str] = None
    url: Optional[str] = None
    headers: Optional[dict] = {}
    params: Optional[dict] = {}
    body: Optional[str] = None
    body_type: Optional[str] = None
    request_body: Optional[str] = None
    response_body: Optional[str] = None
    auth_type: Optional[str] = None
    auth_config: Optional[dict] = {}
    folder_path: Optional[str] = None
    sort_order: Optional[int] = None
    assertions: Optional[list] = []
    pre_script: Optional[str] = None
    post_script: Optional[str] = None
    timeout: Optional[int] = None
    follow_redirects: Optional[bool] = True
    verify_ssl: Optional[bool] = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RunCaseRequest(BaseModel):
    environment_id: Optional[int] = None
    variables: Optional[dict] = {}


class BatchDeleteRequest(BaseModel):
    ids: List[int]
