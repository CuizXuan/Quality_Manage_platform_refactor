from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ScheduleBase(BaseModel):
    name: str
    description: str = ""
    target_type: str  # case / scenario
    target_id: int
    cron_expression: str
    environment_id: Optional[int] = None
    enabled: bool = True
    notify_on: str = "never"  # never / always / failure
    notify_channels: List[str] = []


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    cron_expression: Optional[str] = None
    environment_id: Optional[int] = None
    enabled: Optional[bool] = None
    notify_on: Optional[str] = None
    notify_channels: Optional[List[str]] = None


class ScheduleResponse(ScheduleBase):
    id: int
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    run_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScheduleRunRequest(BaseModel):
    environment_id: Optional[int] = None
    variables: dict = {}
