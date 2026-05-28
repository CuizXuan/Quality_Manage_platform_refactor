from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.background import BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.platform import PlatformUser
from app.routers.platform_auth import get_current_platform_user
from app.services import test_plan_service as service
from app.services.test_plan_service import _run_test_plan_background
from app.schemas.test_plan import (
    TestPlanCreate,
    TestPlanUpdate,
    TestPlanResponse,
    TestPlanListResponse,
    TestSuiteCreate,
    TestSuiteUpdate,
    TestSuiteResponse,
    TestSuiteListResponse,
    TestSuiteItemCreate,
    TestSuiteItemResponse,
    TestSuiteItemListResponse,
    TestPlanRunResponse,
    TestPlanRunListResponse,
)

router = APIRouter(prefix="/api/test-plans", tags=["测试计划"])


# ── TestPlan ──────────────────────────────────────────────────────────────────

@router.get("", response_model=TestPlanListResponse)
def list_plans(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    items, total = service.TestPlanService(db).list_plans(
        project_id=project_id, status=status, keyword=keyword, page=page, page_size=page_size
    )
    return TestPlanListResponse(items=items, total=total, page=page, page_size=page_size)


# ── TestPlanRun (static paths before /{plan_id}) ───────────────────────────────

@router.get("/runs", response_model=TestPlanRunListResponse)
def list_runs(
    plan_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    items, total = service.TestPlanService(db).list_runs(
        plan_id=plan_id, status=status, page=page, page_size=page_size
    )
    return TestPlanRunListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/runs/{run_id}", response_model=TestPlanRunResponse)
def get_run(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    result = service.TestPlanService(db).get_run(run_id)
    if not result:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    return result


# ── TestSuite (static paths before /{plan_id}) ──────────────────────────────────

@router.put("/suites/{suite_id}", response_model=TestSuiteResponse)
def update_suite(
    suite_id: int,
    data: TestSuiteUpdate,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    result = service.TestPlanService(db).update_suite(suite_id, data.model_dump(exclude_unset=True))
    if not result:
        raise HTTPException(status_code=404, detail="测试套件不存在")
    return result


@router.delete("/suites/{suite_id}")
def delete_suite(
    suite_id: int,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    if not service.TestPlanService(db).delete_suite(suite_id):
        raise HTTPException(status_code=404, detail="测试套件不存在")
    return {"success": True}


# ── TestSuiteItem (static paths before /{plan_id}) ────────────────────────────

@router.post("/suites/items", response_model=TestSuiteItemResponse, status_code=201)
def add_suite_item(
    data: TestSuiteItemCreate,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    try:
        result = service.TestPlanService(db).add_suite_item(data.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return result


@router.delete("/suites/items/{item_id}")
def remove_suite_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    if not service.TestPlanService(db).remove_suite_item(item_id):
        raise HTTPException(status_code=404, detail="套件项不存在")
    return {"success": True}


# ── TestPlan CRUD (/{plan_id} after static paths) ─────────────────────────────

@router.get("/{plan_id}", response_model=TestPlanResponse)
def get_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    result = service.TestPlanService(db).get_plan(plan_id)
    if not result:
        raise HTTPException(status_code=404, detail="测试计划不存在")
    return result


@router.post("", response_model=TestPlanResponse, status_code=201)
def create_plan(
    data: TestPlanCreate,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    try:
        result = service.TestPlanService(db).create_plan(data.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result


@router.put("/{plan_id}", response_model=TestPlanResponse)
def update_plan(
    plan_id: int,
    data: TestPlanUpdate,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    try:
        result = service.TestPlanService(db).update_plan(plan_id, data.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not result:
        raise HTTPException(status_code=404, detail="测试计划不存在")
    return result


@router.delete("/{plan_id}")
def delete_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    if not service.TestPlanService(db).delete_plan(plan_id):
        raise HTTPException(status_code=404, detail="测试计划不存在")
    return {"success": True}


# ── TestSuite (/{plan_id} sub-routes) ───────────────────────────────────────

@router.get("/{plan_id}/suites", response_model=TestSuiteListResponse)
def list_suites(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    items = service.TestPlanService(db).list_suites(plan_id)
    return TestSuiteListResponse(items=items, total=len(items), page=1, page_size=len(items))


@router.post("/{plan_id}/suites", response_model=TestSuiteResponse, status_code=201)
def create_suite(
    plan_id: int,
    data: TestSuiteCreate,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    # Override plan_id from path
    data_dict = data.model_dump()
    data_dict["plan_id"] = plan_id
    try:
        result = service.TestPlanService(db).create_suite(data_dict)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return result


# ── TestPlanRun ───────────────────────────────────────────────────────────────

@router.post("/{plan_id}/run")
def run_plan(
    plan_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: PlatformUser = Depends(get_current_platform_user),
):
    """Execute a test plan in background."""
    svc = service.TestPlanService(db)
    plan = svc.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="测试计划不存在")

    # Create run record
    from datetime import datetime
    from app.models.test_plan import TestPlanRun
    run = TestPlanRun(
        plan_id=plan_id,
        status="running",
        started_at=datetime.utcnow(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # Start background execution
    background_tasks.add_task(_run_test_plan_background, run.id, plan_id)

    return {"id": run.id, "status": "running"}