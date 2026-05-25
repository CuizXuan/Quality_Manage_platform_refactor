# =============================================================================
# Quality Foundation Schemas - 质量基础 Pydantic 模型
# =============================================================================

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class QualityProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=50)
    description: str = ""
    status: str = "active"


class QualityProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[str] = None


class QualityProjectResponse(BaseModel):
    id: int
    name: str
    code: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QualityVersionCreate(BaseModel):
    project_id: int
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=50)
    status: str = "planning"
    planned_release_at: Optional[datetime] = None


class QualityVersionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    status: Optional[str] = None
    planned_release_at: Optional[datetime] = None


class QualityVersionResponse(BaseModel):
    id: int
    project_id: int
    name: str
    code: str
    status: str
    planned_release_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QualityIterationCreate(BaseModel):
    project_id: int
    version_id: int
    name: str = Field(..., min_length=1, max_length=200)
    status: str = "planning"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class QualityIterationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class QualityIterationResponse(BaseModel):
    id: int
    project_id: int
    version_id: int
    name: str
    status: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RequirementItemCreate(BaseModel):
    project_id: int
    version_id: Optional[int] = None
    iteration_id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=300)
    description: str = ""
    source_type: Optional[str] = None
    source_key: Optional[str] = None
    priority: str = "P2"
    status: str = "open"
    owner_id: Optional[int] = None


class RequirementItemUpdate(BaseModel):
    version_id: Optional[int] = None
    iteration_id: Optional[int] = None
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    description: Optional[str] = None
    source_type: Optional[str] = None
    source_key: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    owner_id: Optional[int] = None


class RequirementItemResponse(BaseModel):
    id: int
    project_id: int
    version_id: Optional[int]
    iteration_id: Optional[int]
    title: str
    description: str
    source_type: Optional[str]
    source_key: Optional[str]
    priority: str
    status: str
    owner_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RequirementCoverageResponse(BaseModel):
    total: int
    with_test_case: int
    with_scenario: int
    executed: int
    with_defect: int