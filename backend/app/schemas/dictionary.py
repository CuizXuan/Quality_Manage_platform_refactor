from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DictionaryCreate(BaseModel):
    category: str = Field(..., max_length=50)
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    sort_order: int = 0


class DictionaryUpdate(BaseModel):
    category: Optional[str] = Field(None, max_length=50)
    code: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=100)
    sort_order: Optional[int] = None
    status: Optional[str] = None


class DictionaryResponse(BaseModel):
    id: int
    category: str
    code: str
    name: str
    sort_order: int = 0
    status: str = "active"
    created_at: datetime

    class Config:
        from_attributes = True