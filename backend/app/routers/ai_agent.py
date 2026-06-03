from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.ai_repository import AIRepository
from app.services.ai_agent_service import AIAgentService
from app.schemas.ai import (
    AnalyzeRequirementRequest,
    AIWorkflowRunResponse,
    AIWorkflowTraceResponse,
    RequirementAnalysisResponse,
    StartRequirementWorkflowRequest,
    StartWorkflowFromRequirementsRequest,
    WorkflowAdoptRequest,
    WorkflowAdoptResponse,
    WorkflowExecutionAnalysisRequest,
    WorkflowExecutionAnalysisResponse,
    WorkflowExecutionPlanRequest,
    WorkflowExecutionPlanResponse,
    WorkflowExecutionConfirmRequest,
    WorkflowExecutionConfirmResponse,
)
from app.services.ai_service import AIService
from app.services.ai_workflow_service import AIWorkflowService

router = APIRouter(prefix="/api/ai", tags=["ai-agent"])


def _agent_service(db: Session) -> AIAgentService:
    config = AIRepository.get_config(db)
    ai_service = AIService(config) if config else None
    return AIAgentService(db, ai_service)


def _workflow_service(db: Session) -> AIWorkflowService:
    config = AIRepository.get_config(db)
    ai_service = AIService(config) if config else None
    return AIWorkflowService(db, ai_service)


@router.post("/agents/asset-understand")
def asset_understand(payload: dict, db: Session = Depends(get_db)):
    return _agent_service(db).run_asset_understand(payload)


@router.post("/agents/design-tests")
def design_tests(payload: dict, db: Session = Depends(get_db)):
    return _agent_service(db).run_design_tests(payload)


@router.post("/agents/analyze-requirements", response_model=RequirementAnalysisResponse)
def analyze_requirements(data: AnalyzeRequirementRequest, db: Session = Depends(get_db)):
    if not data.content.strip():
        raise HTTPException(status_code=400, detail="需求内容不能为空")
    return _agent_service(db).run_analyze_requirements(data.model_dump())


@router.post("/agents/analyze-failure")
def analyze_failure(payload: dict, db: Session = Depends(get_db)):
    return _agent_service(db).run_analyze_failure(payload)


@router.post("/agents/release-advice")
def release_advice(payload: dict, db: Session = Depends(get_db)):
    return _agent_service(db).run_release_advice(payload)


@router.post("/suggestions/{suggestion_id}/reject")
def reject_suggestion(suggestion_id: int, payload: dict | None = None, db: Session = Depends(get_db)):
    result = _agent_service(db).reject_suggestion(suggestion_id, comment=(payload or {}).get("comment", ""))
    if not result:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    return result


# ── Multi-Agent Workflow ────────────────────────────────────────────────────


@router.post(
    "/workflows/requirement-to-test-design",
    response_model=AIWorkflowRunResponse,
)
def start_requirement_workflow(
    data: StartRequirementWorkflowRequest,
    db: Session = Depends(get_db),
):
    """启动需求到测试设计多 Agent 工作流。"""
    if not data.content.strip():
        raise HTTPException(status_code=400, detail="需求内容不能为空")
    return _workflow_service(db).start_requirement_to_test_design(
        data.model_dump(), created_by=None
    )


# ── 七期 A：按业务来源查询 / 从需求启动 workflow ─────────────────────────
# 注意：以下静态路径必须注册在 /workflows/{run_id} 之前，
# 否则 FastAPI 会把 "by-source" / "from-requirements" 当作 run_id 解析失败。


@router.get(
    "/workflows/by-source",
    response_model=AIWorkflowTraceResponse,
)
def list_workflows_by_source(
    origin_module: str = Query(..., min_length=1, max_length=64),
    origin_type: str = Query(..., min_length=1, max_length=64),
    origin_id: int = Query(..., ge=0),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """按业务来源返回最近 N 个 workflow run，找不到记录返回空列表。"""
    return _workflow_service(db).list_workflows_by_source(
        origin_module=origin_module,
        origin_type=origin_type,
        origin_id=origin_id,
        limit=limit,
    )


@router.post(
    "/workflows/from-requirements",
    response_model=AIWorkflowRunResponse,
)
def start_workflow_from_requirements(
    data: StartWorkflowFromRequirementsRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """从 ``requirement_items`` 启动 ``requirement_to_test_design`` workflow。

    异步模式：先做业务校验并创建 run（状态 ``pending``），立即返回；
    真实 LLM 三步通过 ``BackgroundTasks`` 后台执行。
    不会自动采纳结果；后续在 AI 工作台查看并人工采纳。
    """
    result = _workflow_service(db).create_workflow_run_from_requirements(
        data.model_dump(), created_by=None
    )
    err = result.get("error")
    if err:
        code = err.get("code")
        if code in ("REQUIREMENT_NOT_FOUND", "REQUIREMENT_PROJECT_MISMATCH"):
            raise HTTPException(status_code=400, detail=err.get("message", ""))
        raise HTTPException(status_code=400, detail=err.get("message", "业务校验失败"))
    # 异步派发：run_id 由 result.id 给出；后台任务自己开新 SessionLocal，
    # 避开 router get_db generator 在 response 后被关闭的约束。
    run_id = result.get("id")
    if run_id:
        background_tasks.add_task(
            AIWorkflowService.execute_workflow_steps_async,
            run_id,
            data.model_dump(),
            None,
        )
    return result


@router.get(
    "/workflows/{run_id}",
    response_model=AIWorkflowRunResponse,
)
def get_workflow_run(run_id: int, db: Session = Depends(get_db)):
    """查询工作流运行详情。"""
    run = _workflow_service(db).get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Workflow run not found")
    return run


@router.post(
    "/workflows/{run_id}/adopt",
    response_model=WorkflowAdoptResponse,
)
def adopt_workflow_run(
    run_id: int,
    data: WorkflowAdoptRequest,
    db: Session = Depends(get_db),
):
    """人工采纳工作流结果，将需求/用例写入业务表。"""
    result = _workflow_service(db).adopt_requirement_to_test_design(
        run_id=run_id,
        request=data,
        created_by=None,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Workflow run not found")
    code = (result.get("summary") or {}).get("code")
    if code == "WORKFLOW_TYPE_MISMATCH":
        raise HTTPException(status_code=400, detail=result["summary"]["message"])
    if code == "WORKFLOW_NOT_COMPLETED":
        raise HTTPException(status_code=400, detail=result["summary"]["message"])
    if code == "WORKFLOW_ALREADY_ADOPTED":
        raise HTTPException(status_code=400, detail=result["summary"]["message"])
    return result


@router.post(
    "/workflows/{run_id}/execution-plan",
    response_model=WorkflowExecutionPlanResponse,
)
def plan_workflow_execution(
    run_id: int,
    data: WorkflowExecutionPlanRequest,
    db: Session = Depends(get_db),
):
    """生成执行计划；**不会**创建 execution_runs。"""
    result = _workflow_service(db).plan_execution_for_workflow(
        run_id=run_id,
        request=data,
        created_by=None,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Workflow run not found")
    err = result.get("error")
    if err:
        code = err.get("code")
        if code in ("WORKFLOW_TYPE_MISMATCH", "WORKFLOW_NOT_COMPLETED", "WORKFLOW_NO_SCENARIOS"):
            raise HTTPException(status_code=400, detail=err.get("message", ""))
    return result


@router.post(
    "/workflows/{run_id}/execution-plan/confirm",
    response_model=WorkflowExecutionConfirmResponse,
)
def confirm_workflow_execution(
    run_id: int,
    data: WorkflowExecutionConfirmRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """人工确认执行计划，启动 execution_runs。"""
    result = _workflow_service(db).confirm_execution_plan_for_workflow(
        run_id=run_id,
        request=data,
        background_tasks=background_tasks,
        confirmed_by=None,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Workflow run not found")
    err = result.get("error")
    if err:
        code = err.get("code")
        if code in (
            "WORKFLOW_EXECUTION_PLAN_MISSING",
            "WORKFLOW_EXECUTION_TARGET_EMPTY",
        ):
            raise HTTPException(status_code=400, detail=err.get("message", ""))
    return result


@router.post(
    "/workflows/{run_id}/execution-analysis",
    response_model=WorkflowExecutionAnalysisResponse,
)
def analyze_workflow_execution(
    run_id: int,
    data: WorkflowExecutionAnalysisRequest,
    db: Session = Depends(get_db),
):
    """基于本 workflow 启动的 execution_runs 生成质量闭环分析。

    - 不会创建 defects，不会修改业务状态。
    - 不传 `execution_run_ids` 时，分析 confirmation 中全部 execution_run_ids。
    - 显式传入时与 confirmation 取交集；交集为空返回 400。
    """
    result = _workflow_service(db).analyze_execution_results_for_workflow(
        run_id=run_id,
        request=data,
        created_by=None,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Workflow run not found")
    err = result.get("error")
    if err:
        code = err.get("code")
        if code in (
            "WORKFLOW_TYPE_MISMATCH",
            "WORKFLOW_EXECUTION_CONFIRMATION_MISSING",
            "WORKFLOW_EXECUTION_ANALYSIS_TARGET_EMPTY",
        ):
            raise HTTPException(status_code=400, detail=err.get("message", ""))
    return result
