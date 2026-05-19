# -*- coding: utf-8 -*-
"""
Phase 5 - 混沌工程 API
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.chaos import ChaosExperimentService, FaultInjectionService, ResilienceScoreService

router = APIRouter(prefix="/api/chaos", tags=["混沌工程 (Phase 5)"])


# ==================== Dependencies ====================

def get_chaos_service(db: Session = Depends(get_db)) -> ChaosExperimentService:
    return ChaosExperimentService(db)


def get_fault_service(db: Session = Depends(get_db)) -> FaultInjectionService:
    return FaultInjectionService(db)


def get_resilience_service(db: Session = Depends(get_db)) -> ResilienceScoreService:
    return ResilienceScoreService(db)


# ==================== Chaos Experiment APIs ====================

class ExperimentCreateRequest(BaseModel):
    name: str
    target_type: str  # service/pod/node/network
    project_id: int
    description: Optional[str] = None
    target_id: Optional[str] = None
    hypothesis: Optional[str] = None
    steady_state: Optional[dict] = None
    blast_radius: int = 0
    auto_rollback: bool = True
    rollback_condition: Optional[dict] = None


@router.post("/experiments")
async def create_experiment(
    request: ExperimentCreateRequest,
    req: Request,
    service: ChaosExperimentService = Depends(get_chaos_service),
):
    """创建混沌实验"""
    user_id = getattr(req.state, "user_id", None) or 1

    return service.create_experiment(
        name=request.name,
        target_type=request.target_type,
        project_id=request.project_id,
        user_id=user_id,
        description=request.description,
        target_id=request.target_id,
        hypothesis=request.hypothesis,
        steady_state=request.steady_state,
        blast_radius=request.blast_radius,
        auto_rollback=request.auto_rollback,
        rollback_condition=request.rollback_condition,
    )


@router.post("/experiments/{experiment_id}/start")
async def start_experiment(
    experiment_id: int,
    service: ChaosExperimentService = Depends(get_chaos_service),
):
    """启动实验"""
    result = service.start_experiment(experiment_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/experiments/{experiment_id}/pause")
async def pause_experiment(
    experiment_id: int,
    service: ChaosExperimentService = Depends(get_chaos_service),
):
    """暂停实验"""
    result = service.pause_experiment(experiment_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/experiments/{experiment_id}/stop")
async def stop_experiment(
    experiment_id: int,
    service: ChaosExperimentService = Depends(get_chaos_service),
):
    """停止实验"""
    result = service.stop_experiment(experiment_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.get("/experiments/{experiment_id}")
async def get_experiment(
    experiment_id: int,
    service: ChaosExperimentService = Depends(get_chaos_service),
):
    """获取实验详情"""
    experiment = service.get_experiment(experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return experiment


@router.get("/experiments/list/{project_id}")
async def list_experiments(
    project_id: int,
    page: int = 1,
    page_size: int = 20,
    service: ChaosExperimentService = Depends(get_chaos_service),
):
    """获取实验列表"""
    return service.list_experiments(project_id, page, page_size)


@router.delete("/experiments/{experiment_id}")
async def delete_experiment(
    experiment_id: int,
    service: ChaosExperimentService = Depends(get_chaos_service),
):
    """删除实验"""
    result = service.delete_experiment(experiment_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


# ==================== Fault Injection APIs ====================

class FaultInjectRequest(BaseModel):
    experiment_id: int
    fault_type: str
    target_service: str
    fault_config: dict
    blast_radius: int = 0


@router.post("/faults")
async def inject_fault(
    request: FaultInjectRequest,
    service: FaultInjectionService = Depends(get_fault_service),
):
    """注入故障"""
    result = service.inject_fault(
        experiment_id=request.experiment_id,
        fault_type=request.fault_type,
        target_service=request.target_service,
        fault_config=request.fault_config,
        blast_radius=request.blast_radius,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/faults/{fault_id}/rollback")
async def rollback_fault(
    fault_id: int,
    service: FaultInjectionService = Depends(get_fault_service),
):
    """回滚故障"""
    result = service.rollback_fault(fault_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.get("/fault-types")
async def get_fault_types(
    service: FaultInjectionService = Depends(get_fault_service),
):
    """获取故障类型列表"""
    return service.get_fault_types()


@router.get("/faults/{fault_id}/metrics")
async def get_fault_metrics(
    fault_id: int,
    service: FaultInjectionService = Depends(get_fault_service),
):
    """获取故障指标"""
    return service.get_fault_metrics(fault_id)


# ==================== Resilience Score APIs ====================

class EvaluateRequest(BaseModel):
    target_type: str  # service/pod/node
    target_id: str
    project_id: int


@router.post("/evaluate")
async def evaluate_resilience(
    request: EvaluateRequest,
    service: ResilienceScoreService = Depends(get_resilience_service),
):
    """评估韧性"""
    return service.evaluate(
        target_type=request.target_type,
        target_id=request.target_id,
        project_id=request.project_id,
    )


@router.get("/score/{target_type}/{target_id}")
async def get_latest_score(
    target_type: str,
    target_id: str,
    service: ResilienceScoreService = Depends(get_resilience_service),
):
    """获取最新评分"""
    score = service.get_latest_score(target_type, target_id)
    if not score:
        raise HTTPException(status_code=404, detail="No score found")
    return score


@router.get("/score-history/{target_type}/{target_id}")
async def get_score_history(
    target_type: str,
    target_id: str,
    limit: int = 10,
    service: ResilienceScoreService = Depends(get_resilience_service),
):
    """获取评分历史"""
    return service.get_score_history(target_type, target_id, limit)
