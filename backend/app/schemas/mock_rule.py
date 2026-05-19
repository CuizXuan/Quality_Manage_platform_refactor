from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class MockMatchCondition(BaseModel):
    type: str  # header / query / body / cookie
    key: str
    operator: str  # equals / contains / regex / exists
    value: Optional[str] = None


class MockRuleBase(BaseModel):
    name: str
    description: str = ""
    path: str
    method: str = "GET"
    response_status: int = 200
    response_headers: Dict[str, str] = {}
    response_body: str = ""
    response_template_type: str = "none"  # none / jinja2
    delay_ms: int = 0
    match_conditions: List[MockMatchCondition] = []
    enabled: bool = True


class MockRuleCreate(MockRuleBase):
    pass


class MockRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    path: Optional[str] = None
    method: Optional[str] = None
    response_status: Optional[int] = None
    response_headers: Optional[Dict[str, str]] = None
    response_body: Optional[str] = None
    response_template_type: Optional[str] = None
    delay_ms: Optional[int] = None
    match_conditions: Optional[List[MockMatchCondition]] = None
    enabled: Optional[bool] = None


class MockRuleResponse(MockRuleBase):
    id: int
    hit_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
