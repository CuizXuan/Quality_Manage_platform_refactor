import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from app.database import get_db
from app.models.schedule import Schedule
from app.models.case import TestCase
from app.models.scenario import Scenario
from app.models.environment import Environment
from app.models.execution_log import ExecutionLog
from app.schemas.schedule import (
    ScheduleCreate, ScheduleUpdate, ScheduleResponse, ScheduleRunRequest,
)
from app.services.request_executor import RequestExecutor
from app.services.scenario_executor import ScenarioExecutor
from app.middleware.tenant_middleware import get_current_tenant_id

router = APIRouter(prefix="/api/schedules", tags=["Schedules"])


def get_tenant_id(request: Request) -> int:
    """从请求状态获取当前租户 ID"""
    tenant_id = get_current_tenant_id(request)
    if tenant_id is None:
        raise HTTPException(status_code=403, detail="需要租户权限")
    return tenant_id


def _parse_schedule(s: Schedule) -> dict:
    return {
        "id": s.id,
        "name": s.name,
        "description": s.description,
        "target_type": s.target_type,
        "target_id": s.target_id,
        "cron_expression": s.cron_expression,
        "environment_id": s.environment_id,
        "enabled": s.enabled,
        "notify_on": s.notify_on,
        "notify_channels": json.loads(s.notify_channels or "[]"),
        "last_run_at": s.last_run_at,
        "next_run_at": s.next_run_at,
        "run_count": s.run_count,
        "success_count": s.success_count,
        "failure_count": s.failure_count,
        "created_at": s.created_at,
        "updated_at": s.updated_at,
    }


@router.get("", response_model=List[ScheduleResponse])
def list_schedules(
    enabled: Optional[bool] = Query(None),
    target_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    query = db.query(Schedule).filter(Schedule.tenant_id == tenant_id)
    if enabled is not None:
        query = query.filter(Schedule.enabled == enabled)
    if target_type:
        query = query.filter(Schedule.target_type == target_type)
    schedules = query.order_by(desc(Schedule.created_at)).offset(skip).limit(limit).all()
    return [_parse_schedule(s) for s in schedules]


@router.post("", response_model=ScheduleResponse)
def create_schedule(data: ScheduleCreate, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    schedule = Schedule(
        tenant_id=tenant_id,
        name=data.name,
        description=data.description,
        target_type=data.target_type,
        target_id=data.target_id,
        cron_expression=data.cron_expression,
        environment_id=data.environment_id,
        enabled=data.enabled,
        notify_on=data.notify_on,
        notify_channels=json.dumps(data.notify_channels or []),
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return _parse_schedule(schedule)


@router.get("/{schedule_id}", response_model=ScheduleResponse)
def get_schedule(schedule_id: int, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    s = db.query(Schedule).filter(Schedule.id == schedule_id, Schedule.tenant_id == tenant_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return _parse_schedule(s)


@router.put("/{schedule_id}", response_model=ScheduleResponse)
def update_schedule(schedule_id: int, data: ScheduleUpdate, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    s = db.query(Schedule).filter(Schedule.id == schedule_id, Schedule.tenant_id == tenant_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Schedule not found")
    for key, value in data.model_dump().items():
        if value is not None:
            if key == "notify_channels":
                setattr(s, key, json.dumps(value))
            else:
                setattr(s, key, value)
    db.commit()
    db.refresh(s)
    return _parse_schedule(s)


@router.delete("/{schedule_id}")
def delete_schedule(schedule_id: int, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    s = db.query(Schedule).filter(Schedule.id == schedule_id, Schedule.tenant_id == tenant_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Schedule not found")
    db.delete(s)
    db.commit()
    return {"code": 0, "message": "deleted"}


@router.post("/{schedule_id}/toggle")
def toggle_schedule(schedule_id: int, body: dict, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    enabled = body.get("enabled", True)
    s = db.query(Schedule).filter(Schedule.id == schedule_id, Schedule.tenant_id == tenant_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Schedule not found")
    s.enabled = enabled
    db.commit()
    db.refresh(s)
    return {"code": 0, "data": _parse_schedule(s)}


@router.post("/{schedule_id}/run")
async def run_schedule_now(
    schedule_id: int,
    body: ScheduleRunRequest,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    """立即执行定时任务"""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id, Schedule.tenant_id == tenant_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    # 获取环境变量
    env_vars = {}
    env_id = body.environment_id or schedule.environment_id
    if env_id:
        env = db.query(Environment).filter(Environment.id == env_id, Environment.tenant_id == tenant_id).first()
        if env:
            env_vars = json.loads(env.variables or "{}")
    else:
        env = db.query(Environment).filter(Environment.is_default == True, Environment.tenant_id == tenant_id).first()
        if env:
            env_id = env.id
            env_vars = json.loads(env.variables or "{}")

    result = None
    status = "success"

    if schedule.target_type == "case":
        case = db.query(TestCase).filter(TestCase.id == schedule.target_id, TestCase.tenant_id == tenant_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Target case not found")

        from app.routers.cases import _parse_case
        case_data = _parse_case(case)
        executor = RequestExecutor()
        result = await executor.execute_case(case_data, env_vars, body.variables)
        status = result.get("status", "success")

        # 保存执行记录
        log = ExecutionLog(
            case_id=case.id,
            scenario_id=None,
            scenario_step_id=None,
            execution_type="schedule",
            execution_id=result["execution_id"],
            request_url=case.url,
            request_method=case.method,
            request_headers=case.headers,
            request_body=case.body,
            response_status=result["response"]["status_code"],
            response_headers=json.dumps(result["response"]["headers"]),
            response_body=json.dumps(result["response"]["body"]) if isinstance(result["response"]["body"], (dict, list)) else str(result["response"]["body"]),
            response_size=result["response"]["size"],
            response_time_ms=result["response"]["time_ms"],
            status=status,
            assertion_results=json.dumps(result["assertion_results"]),
            environment_id=env_id,
            triggered_by=f"schedule:{schedule.id}",
        )
        db.add(log)

    elif schedule.target_type == "scenario":
        scenario = db.query(Scenario).filter(Scenario.id == schedule.target_id, Scenario.tenant_id == tenant_id).first()
        if not scenario:
            raise HTTPException(status_code=404, detail="Target scenario not found")

        # 获取场景步骤和用例数据
        from app.models.scenario import ScenarioStep
        steps = db.query(ScenarioStep).filter(
            ScenarioStep.scenario_id == scenario.id,
            ScenarioStep.enabled == True,
        ).order_by(ScenarioStep.step_order).all()

        from app.routers.cases import _parse_case
        step_data = []
        for step in steps:
            case = db.query(TestCase).filter(TestCase.id == step.case_id, TestCase.tenant_id == tenant_id).first()
            if case:
                step_data.append({
                    "case_id": case.id,
                    "case_name": case.name,
                    "case_data": _parse_case(case),
                    "step_order": step.step_order,
                    "extract_rules": json.loads(step.extract_rules or "[]"),
                    "skip_on_failure": step.skip_on_failure,
                    "enabled": step.enabled,
                })

        scenario_data = {
            "id": scenario.id,
            "name": scenario.name,
            "variables": json.loads(scenario.variables or "{}"),
            "steps": step_data,
        }

        executor = ScenarioExecutor()
        result = await executor.execute_scenario(scenario_data, env_vars, body.variables)
        status = result.get("status", "success")

    # 更新统计
    schedule.run_count += 1
    schedule.last_run_at = datetime.now()
    if status == "success":
        schedule.success_count += 1
    else:
        schedule.failure_count += 1

    db.commit()

    return {"code": 0, "message": "executed", "data": result}


@router.post("/{schedule_id}/pause")
def pause_schedule(schedule_id: int, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id, Schedule.tenant_id == tenant_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    schedule.enabled = False
    db.commit()
    return {"code": 0, "message": "paused"}


@router.post("/{schedule_id}/resume")
def resume_schedule(schedule_id: int, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id, Schedule.tenant_id == tenant_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    schedule.enabled = True
    db.commit()
    return {"code": 0, "message": "resumed"}
