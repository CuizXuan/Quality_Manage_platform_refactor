from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union
from datetime import datetime


class AssertionResult(BaseModel):
    id: str
    type: str
    path: Optional[str] = None
    passed: bool
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    message: str = ""


class ExecutionData(BaseModel):
    status_code: int
    headers: Optional[dict] = {}
    body: Optional[Any] = None
    size: int = 0
    time_ms: int = 0


class ExecutionResponse(BaseModel):
    execution_id: str
    case_id: int
    status: str
    response: Optional[ExecutionData] = None
    assertion_results: Optional[List[AssertionResult]] = []
    extracted_variables: Optional[dict] = {}


class StepExecutionResult(BaseModel):
    step_order: int
    case_id: int
    case_name: str = ""
    status: str
    response_time_ms: int = 0
    extracted: Optional[dict] = {}


class ScenarioSummary(BaseModel):
    total_steps: int
    passed_steps: int
    failed_steps: int
    skipped_steps: int
    total_time_ms: int


class ScenarioExecutionResponse(BaseModel):
    execution_id: str
    scenario_id: int
    status: str
    summary: ScenarioSummary
    steps: Optional[List[StepExecutionResult]] = []
    final_variables: Optional[dict] = {}
