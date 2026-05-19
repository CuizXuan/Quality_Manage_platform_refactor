from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ReportTemplateBase(BaseModel):
    name: str
    description: str = ""
    type: str = "html"  # html / pdf / markdown
    content: str = ""
    is_default: bool = False


class ReportTemplateCreate(ReportTemplateBase):
    pass


class ReportTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    content: Optional[str] = None
    is_default: Optional[bool] = None


class ReportTemplateResponse(ReportTemplateBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReportGenerateRequest(BaseModel):
    template_id: Optional[int] = None
    execution_ids: list[int] = []
    scenario_ids: Optional[list[int]] = None
    name: str = "API Test Report"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
