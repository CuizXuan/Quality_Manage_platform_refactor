"""
Scenario Router — 场景编排所有 API 端点
"""
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.scenario import (
    ScenarioCreate,
    ScenarioUpdate,
    ScenarioResponse,
    ScenarioStepCreate,
    ScenarioStepUpdate,
    ScenarioStepResponse,
    ExecutionRunResponse,
)
from app.services.scenario_service import ScenarioService, _run_scenario_background

router = APIRouter(prefix="/api/scenario", tags=["scenario"])


def _service(db: Session = Depends(get_db)) -> ScenarioService:
    return ScenarioService(db)


# ── Execution routes (MUST be before /{scenario_id} to avoid "runs" being captured as scenario_id) ──

@router.get("/runs", response_model=dict)
def list_executions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    run_type: Optional[str] = None,
    target_id: Optional[int] = None,
    status: Optional[str] = None,
    svc: ScenarioService = Depends(_service),
):
    """List execution runs."""
    runs, total = svc.list_executions(
        page=page, page_size=page_size,
        run_type=run_type, target_id=target_id, status=status
    )
    return {"items": runs, "total": total, "page": page, "page_size": page_size}


@router.get("/runs/{run_id}", response_model=dict)
def get_execution(run_id: int, svc: ScenarioService = Depends(_service)):
    """Get an execution run by ID."""
    run = svc.get_execution(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Execution run not found")
    return run


@router.post("/{scenario_id}/run", response_model=dict)
def start_execution(
    scenario_id: int,
    background_tasks: BackgroundTasks,
    environment_id: Optional[int] = None,
    svc: ScenarioService = Depends(_service),
):
    """Start a scenario execution. Returns run ID immediately; steps run asynchronously."""
    run = svc.start_execution(scenario_id, environment_id=environment_id)
    if not run:
        raise HTTPException(status_code=404, detail="Scenario not found")
    # Kick off async execution in background
    background_tasks.add_task(_run_scenario_background, run["id"], scenario_id)
    return run


# ── Scenario CRUD ──────────────────────────────────────────────────

@router.get("", response_model=dict)
def list_scenarios(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    project_id: Optional[int] = Query(None),
    version_id: Optional[int] = Query(None),
    iteration_id: Optional[int] = Query(None),
    svc: ScenarioService = Depends(_service),
):
    """List scenarios with pagination."""
    items, total = svc.list_scenarios(
        page=page,
        page_size=page_size,
        keyword=keyword,
        status=status,
        project_id=project_id,
        version_id=version_id,
        iteration_id=iteration_id,
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("", response_model=dict)
def create_scenario(data: ScenarioCreate, svc: ScenarioService = Depends(_service)):
    """Create a new scenario."""
    scenario = svc.create_scenario(data.model_dump())
    return scenario


@router.get("/{scenario_id}", response_model=dict)
def get_scenario(scenario_id: int, svc: ScenarioService = Depends(_service)):
    """Get a scenario by ID."""
    scenario = svc.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


@router.put("/{scenario_id}", response_model=dict)
def update_scenario(
    scenario_id: int,
    data: ScenarioUpdate,
    svc: ScenarioService = Depends(_service),
):
    """Update a scenario."""
    scenario = svc.update_scenario(scenario_id, data.model_dump(exclude_unset=True))
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


@router.delete("/{scenario_id}")
def delete_scenario(scenario_id: int, svc: ScenarioService = Depends(_service)):
    """Delete a scenario."""
    ok = svc.delete_scenario(scenario_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return {"ok": True}


# ── Scenario Steps ─────────────────────────────────────────────────

@router.post("/{scenario_id}/steps", response_model=dict)
def add_step(
    scenario_id: int,
    data: ScenarioStepCreate,
    svc: ScenarioService = Depends(_service),
):
    """Add a step to a scenario."""
    step = svc.add_step(scenario_id, data.model_dump())
    if not step:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return step


@router.put("/steps/{step_id}", response_model=dict)
def update_step(
    step_id: int,
    data: ScenarioStepUpdate,
    svc: ScenarioService = Depends(_service),
):
    """Update a scenario step."""
    step = svc.update_step(step_id, data.model_dump(exclude_unset=True))
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
    return step


@router.delete("/steps/{step_id}")
def delete_step(step_id: int, svc: ScenarioService = Depends(_service)):
    """Delete a scenario step."""
    ok = svc.delete_step(step_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Step not found")
    return {"ok": True}


@router.post("/{scenario_id}/steps/reorder")
def reorder_steps(
    scenario_id: int,
    step_ids: list[int],
    svc: ScenarioService = Depends(_service),
):
    """Reorder steps of a scenario."""
    ok = svc.reorder_steps(scenario_id, step_ids)
    if not ok:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return {"ok": True}
