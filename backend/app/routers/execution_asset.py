from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.execution_asset import UnifiedRunCreate, UnifiedRunListResponse, UnifiedRunResponse
from app.services.execution_service import ExecutionService

router = APIRouter(prefix="/api/executions", tags=["execution"])


@router.get("/runs", response_model=UnifiedRunListResponse)
def list_runs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    target_type: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    items, total = ExecutionService(db).list_runs(page=page, page_size=page_size, target_type=target_type, status=status)
    return UnifiedRunListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/runs", response_model=UnifiedRunResponse)
def create_run(data: UnifiedRunCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    try:
        return ExecutionService(db).create_run(data.model_dump(), background_tasks)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/runs/{run_id}", response_model=UnifiedRunResponse)
def get_run(run_id: int, db: Session = Depends(get_db)):
    result = ExecutionService(db).get_run(run_id)
    if not result:
        raise HTTPException(status_code=404, detail="Run not found")
    return result


@router.post("/runs/{run_id}/cancel", response_model=UnifiedRunResponse)
def cancel_run(run_id: int, db: Session = Depends(get_db)):
    result = ExecutionService(db).cancel_run(run_id)
    if not result:
        raise HTTPException(status_code=404, detail="Run not found")
    return result


@router.post("/runs/{run_id}/rerun-failed", response_model=UnifiedRunResponse)
def rerun_failed(run_id: int, db: Session = Depends(get_db)):
    result = ExecutionService(db).rerun_failed(run_id)
    if not result:
        raise HTTPException(status_code=404, detail="Run not found")
    return result


@router.get("/runs/{run_id}/stream")
def stream_run(run_id: int, db: Session = Depends(get_db)):
    result = ExecutionService(db).get_run(run_id)
    if not result:
        raise HTTPException(status_code=404, detail="Run not found")
    return {
        "run_id": run_id,
        "status": result["status"],
        "queue_status": result["queue_status"],
        "summary": result["summary"],
    }


@router.get("/runs/{run_id}/artifacts")
def list_artifacts(run_id: int, db: Session = Depends(get_db)):
    return ExecutionService(db).list_artifacts(run_id)
