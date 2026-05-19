from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ApiTestCaseCreate(BaseModel):
    method: str = Field(default="GET", max_length=10)
    url: str = Field(..., max_length=2000)
    headers: Dict[str, Any] = Field(default_factory=dict)
    params: Dict[str, Any] = Field(default_factory=dict)
    body_type: str = Field(default="none", max_length=20)
    body: str = ""
    auth_config: Dict[str, Any] = Field(default_factory=dict)
    expected_status: int = Field(default=200)
    assertions: List[Dict[str, Any]] = Field(default_factory=list)


class ApiTestCaseUpdate(BaseModel):
    method: Optional[str] = Field(None, max_length=10)
    url: Optional[str] = Field(None, max_length=2000)
    headers: Optional[Dict[str, Any]] = None
    params: Optional[Dict[str, Any]] = None
    body_type: Optional[str] = Field(None, max_length=20)
    body: Optional[str] = None
    auth_config: Optional[Dict[str, Any]] = None
    expected_status: Optional[int] = None
    assertions: Optional[List[Dict[str, Any]]] = None


class ApiTestCaseResponse(BaseModel):
    id: int
    testcase_id: int
    method: str
    url: str
    headers: Dict[str, Any]
    params: Dict[str, Any]
    body_type: str
    body: str
    auth_config: Dict[str, Any]
    expected_status: int
    assertions: List[Dict[str, Any]]
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True