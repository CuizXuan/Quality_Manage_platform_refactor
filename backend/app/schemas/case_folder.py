from typing import List, Optional

from pydantic import BaseModel, Field


class CaseFolderCreate(BaseModel):
    case_type: str = Field(default="api", max_length=20)
    parent_id: Optional[int] = None
    name: str = Field(..., max_length=200)
    sort_order: int = Field(default=0)


class CaseFolderUpdate(BaseModel):
    parent_id: Optional[int] = None
    name: Optional[str] = Field(None, max_length=200)
    sort_order: Optional[int] = None


class CaseFolderResponse(BaseModel):
    id: int
    case_type: str
    parent_id: Optional[int] = None
    name: str
    sort_order: int
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class CaseFolderTreeResponse(BaseModel):
    items: List[CaseFolderResponse]
    total: int