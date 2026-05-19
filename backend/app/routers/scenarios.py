from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
import json
from app.database import get_db
from app.models.scenario import Scenario, ScenarioStep
from app.models.case import TestCase
from app.models.environment import Environment
from app.models.execution_log import ExecutionLog
from app.schemas.scenario import (
    ScenarioCreate, ScenarioUpdate, ScenarioResponse,
    ScenarioStepCreate, ScenarioStepUpdate, ScenarioStepResponse,
)
from app.schemas.case import RunCaseRequest
from app.services.scenario_executor import ScenarioExecutor
from app.middleware.tenant_middleware import get_current_tenant_id

router = APIRouter(prefix="/api/scenarios", tags=["Scenarios"])


def get_tenant_id(request: Request) -> int:
    tenant_id = get_current_tenant_id(request)
    if tenant_id is None:
        raise HTTPException(status_code=403, detail="需要租户权限")
    return tenant_id


@router.get("", response_model=List[ScenarioResponse])
def list_scenarios(db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    scenarios = db.query(Scenario).filter(Scenario.tenant_id == tenant_id).order_by(Scenario.folder_path, Scenario.id).all()
    return [_parse_scenario(s, db, tenant_id) for s in scenarios]


@router.post("", response_model=ScenarioResponse)
def create_scenario(data: ScenarioCreate, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    scenario = Scenario(
        tenant_id=tenant_id,
        name=data.name,
        description=data.description,
        folder_path=data.folder_path,
        variables=json.dumps(data.variables or {}),
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return _parse_scenario(scenario, db, tenant_id)


@router.get("/{scenario_id}", response_model=ScenarioResponse)
def get_scenario(scenario_id: int, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id, Scenario.tenant_id == tenant_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return _parse_scenario(scenario, db, tenant_id)


@router.put("/{scenario_id}", response_model=ScenarioResponse)
def update_scenario(scenario_id: int, data: ScenarioUpdate, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id, Scenario.tenant_id == tenant_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    for key, value in data.model_dump().items():
        if key == "variables":
            setattr(scenario, key, json.dumps(value) if value else "{}")
        else:
            setattr(scenario, key, value)
    db.commit()
    db.refresh(scenario)
    return _parse_scenario(scenario, db, tenant_id)


@router.delete("/{scenario_id}")
def delete_scenario(scenario_id: int, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id, Scenario.tenant_id == tenant_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    db.delete(scenario)
    db.commit()
    return {"code": 0, "message": "deleted"}


@router.post("/{scenario_id}/steps", response_model=ScenarioStepResponse)
def add_step(scenario_id: int, data: ScenarioStepCreate, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id, Scenario.tenant_id == tenant_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    step = ScenarioStep(
        scenario_id=scenario_id,
        case_id=data.case_id,
        step_order=data.step_order,
        extract_rules=json.dumps([e.model_dump() for e in (data.extract_rules or [])]),
        skip_on_failure=data.skip_on_failure,
        retry_times=data.retry_times,
        retry_interval=data.retry_interval,
        enabled=data.enabled,
    )
    db.add(step)
    db.commit()
    db.refresh(step)
    return _parse_step(step)


@router.put("/{scenario_id}/steps/{step_id}", response_model=ScenarioStepResponse)
def update_step(scenario_id: int, step_id: int, data: ScenarioStepUpdate, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    step = db.query(ScenarioStep).filter(ScenarioStep.id == step_id, ScenarioStep.scenario_id == scenario_id).first()
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
    for key, value in data.model_dump().items():
        if key == "extract_rules":
            setattr(step, key, json.dumps(value) if value else "[]")
        else:
            setattr(step, key, value)
    db.commit()
    db.refresh(step)
    return _parse_step(step)


@router.delete("/{scenario_id}/steps/{step_id}")
def delete_step(scenario_id: int, step_id: int, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    step = db.query(ScenarioStep).filter(ScenarioStep.id == step_id, ScenarioStep.scenario_id == scenario_id).first()
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
    db.delete(step)
    db.commit()
    return {"code": 0, "message": "deleted"}


@router.put("/{scenario_id}/steps/reorder")
def reorder_steps(scenario_id: int, step_ids: List[int], db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    # 验证场景属于当前租户
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id, Scenario.tenant_id == tenant_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    for order, step_id in enumerate(step_ids):
        step = db.query(ScenarioStep).filter(ScenarioStep.id == step_id, ScenarioStep.scenario_id == scenario_id).first()
        if step:
            step.step_order = order
    db.commit()
    return {"code": 0, "message": "reordered"}


@router.post("/{scenario_id}/run")
async def run_scenario(scenario_id: int, body: RunCaseRequest, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id, Scenario.tenant_id == tenant_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    # 获取环境变量（需要 tenant 过滤）
    env_vars = {}
    env_id = body.environment_id
    if env_id:
        env = db.query(Environment).filter(Environment.id == env_id, Environment.tenant_id == tenant_id).first()
        if env:
            env_vars = json.loads(env.variables or "{}")
    else:
        env = db.query(Environment).filter(Environment.is_default == True, Environment.tenant_id == tenant_id).first()
        if env:
            env_id = env.id
            env_vars = json.loads(env.variables or "{}")

    # 构建场景数据（含步骤和用例详情）
    scenario_data = _parse_scenario(scenario, db, tenant_id)

    # 填充每个步骤的用例数据
    for step in scenario_data["steps"]:
        case = db.query(TestCase).filter(TestCase.id == step["case_id"], TestCase.tenant_id == tenant_id).first()
        if case:
            from app.routers.cases import _parse_case
            step["case_data"] = _parse_case(case)

    # 执行场景
    executor = ScenarioExecutor()
    result = await executor.execute_scenario(scenario_data, env_vars, body.variables)

    # 保存每个步骤的执行记录
    for step_result in result.get("steps", []):
        case_id = step_result.get("case_id")
        step_order = step_result.get("step_order")
        step_record = db.query(ScenarioStep).filter(
            ScenarioStep.scenario_id == scenario_id,
            ScenarioStep.step_order == step_order
        ).first()

        log = ExecutionLog(
            tenant_id=tenant_id,
            case_id=case_id,
            scenario_id=scenario_id,
            scenario_step_id=step_record.id if step_record else None,
            execution_type="scenario",
            execution_id=result["execution_id"],
            request_url="",
            request_method="",
            request_headers="{}",
            request_body="",
            response_status=200 if step_result["status"] == "success" else 0,
            response_headers="{}",
            response_body=json.dumps(step_result.get("assertion_results", [])),
            response_size=0,
            response_time_ms=step_result.get("response_time_ms", 0),
            status=step_result["status"],
            assertion_results=json.dumps(step_result.get("assertion_results", [])),
            environment_id=env_id,
            triggered_by="user",
        )
        db.add(log)

    db.commit()
    return {"code": 0, "message": "success", "data": result}


def _parse_scenario(scenario: Scenario, db: Session, tenant_id: int) -> dict:
    steps = db.query(ScenarioStep).filter(ScenarioStep.scenario_id == scenario.id).order_by(ScenarioStep.step_order).all()
    return {
        "id": scenario.id,
        "name": scenario.name,
        "description": scenario.description,
        "folder_path": scenario.folder_path,
        "variables": json.loads(scenario.variables or "{}"),
        "created_at": scenario.created_at,
        "updated_at": scenario.updated_at,
        "steps": [_parse_step(s) for s in steps],
    }


def _parse_step(step: ScenarioStep) -> dict:
    return {
        "id": step.id,
        "scenario_id": step.scenario_id,
        "case_id": step.case_id,
        "step_order": step.step_order,
        "extract_rules": json.loads(step.extract_rules or "[]"),
        "skip_on_failure": step.skip_on_failure,
        "retry_times": step.retry_times,
        "retry_interval": step.retry_interval,
        "enabled": step.enabled,
    }
