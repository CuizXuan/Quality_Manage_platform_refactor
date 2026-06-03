from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class UnifiedRunCreate(BaseModel):
    run_type: Literal["manual", "scheduled", "rerun"] = "manual"
    target_type: Literal["case", "scenario", "plan"]
    target_id: int
    project_id: Optional[int] = None
    environment_id: Optional[int] = None


class UnifiedRunResponse(BaseModel):
    id: int
    run_type: str
    target_type: str
    target_id: int
    project_id: Optional[int] = None
    environment_id: Optional[int] = None
    source_run_id: Optional[int] = None
    status: str
    queue_status: str
    summary: Dict = {}
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    duration_ms: Optional[int] = None
    items: List[Dict] = []


class UnifiedRunListResponse(BaseModel):
    items: List[UnifiedRunResponse]
    total: int
    page: int
    page_size: int
