from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


class ExtractRule(BaseModel):
    id: str
    name: str
    source: str
    path: Optional[str] = None
    header_name: Optional[str] = None
    cookie_name: Optional[str] = None
    pattern: Optional[str] = None
    scope: str = "scenario"
    enabled: bool = True


class ScenarioStepBase(BaseModel):
    case_id: int
    step_order: Optional[int] = None
    extract_rules: Optional[List[ExtractRule]] = []
    skip_on_failure: bool = True
    retry_times: int = 0
    retry_interval: int = 1000
    enabled: bool = True


class ScenarioStepCreate(ScenarioStepBase):
    pass


class ScenarioStepUpdate(ScenarioStepBase):
    pass


class ScenarioStepResponse(ScenarioStepBase):
    id: int
    scenario_id: int

    class Config:
        from_attributes = True


class ScenarioBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = ""
    folder_path: str = "/"
    variables: Optional[dict] = {}

    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('场景名称不能为空')
        return v.strip()


class ScenarioCreate(ScenarioBase):
    pass


class ScenarioUpdate(ScenarioBase):
    pass


class ScenarioResponse(ScenarioBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    steps: Optional[List[ScenarioStepResponse]] = []

    class Config:
        from_attributes = True
