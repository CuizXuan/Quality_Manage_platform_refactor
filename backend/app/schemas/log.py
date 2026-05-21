"""Operation Log Schemas — Pydantic v2"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class LogQuery(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    keyword: Optional[str] = None
    module: Optional[str] = None
    action: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class LogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    username: str
    action: str
    module: str
    detail: str
    ip: str
    created_at: datetime

    model_config = {"from_attributes": True}


class LogListResponse(BaseModel):
    items: list[LogResponse]
    total: int
    page: int
    page_size: int
