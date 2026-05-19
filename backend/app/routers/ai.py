# -*- coding: utf-8 -*-
"""
Phase 4 - AI分析路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List, Any
from app.database import get_db
from app.models.tenant import User
from app.services.auth_service import AuthService
from app.services.ai_service import AIFailureService, AIChangeImpactService, AIAlertService, AIPerformanceService

router = APIRouter(prefix="/api/ai", tags=["智能分析"])
security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    if not credentials:
        raise HTTPException(status_code=401, detail="未提供认证令牌")
    auth_service = AuthService(db)
    payload = auth_service.decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="令牌无效或已过期")
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


# ==================== 失败聚类 API ====================

@router.get("/clusters", summary="获取失败聚类列表")
def get_clusters(
    project_id: int = Query(..., description="项目ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    resolved: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取项目的失败聚类列表"""
    service = AIFailureService(db)
    clusters, total = service.get_clusters(project_id, page, page_size, resolved)
    return {
        "items": clusters,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/clusters/{cluster_id}", summary="获取聚类详情")
def get_cluster(
    cluster_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取聚类详情"""
    service = AIFailureService(db)
    cluster = service.get_cluster_by_id(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="聚类不存在")
    return cluster


@router.post("/clusters/{cluster_id}/analyze", summary="触发AI分析")
def analyze_cluster(
    cluster_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """对聚类进行根因分析"""
    service = AIFailureService(db)
    result = service.analyze_root_cause(cluster_id)
    if not result:
        raise HTTPException(status_code=404, detail="聚类不存在")
    return result


@router.put("/clusters/{cluster_id}/resolve", summary="标记为已解决")
def resolve_cluster(
    cluster_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """标记聚类为已解决"""
    service = AIFailureService(db)
    success, error = service.resolve_cluster(cluster_id)
    if not success:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "操作成功"}


@router.delete("/clusters/{cluster_id}/ignore", summary="忽略聚类")
def ignore_cluster(
    cluster_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """忽略聚类"""
    service = AIFailureService(db)
    success, error = service.ignore_cluster(cluster_id)
    if not success:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "操作成功"}


# ==================== 变更影响 API ====================

@router.post("/impact/predict", summary="预测变更影响")
def predict_impact(
    project_id: int,
    commit_hash: str,
    changed_files: List[str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """预测变更影响"""
    service = AIChangeImpactService(db)
    result = service.predict_impact(project_id, commit_hash, changed_files)
    return result


@router.get("/impact/history", summary="获取预测历史")
def get_impact_history(
    project_id: int = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取变更影响预测历史"""
    service = AIChangeImpactService(db)
    impacts, total = service.get_impact_history(project_id, page, page_size)
    return {
        "items": impacts,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/impact/{impact_id}", summary="获取预测详情")
def get_impact(
    impact_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取预测详情"""
    service = AIChangeImpactService(db)
    impact = service.get_impact_by_id(impact_id)
    if not impact:
        raise HTTPException(status_code=404, detail="预测记录不存在")
    return impact


# ==================== 告警规则 API ====================

@router.get("/alerts/rules", summary="获取告警规则列表")
def get_alert_rules(
    project_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取告警规则列表"""
    service = AIAlertService(db)
    rules = service.get_alert_rules(project_id)
    return {"items": rules}


class AlertRuleCreate(BaseModel):
    name: str
    type: str
    threshold: float
    severity: str = "medium"
    notify_channels: Optional[List[str]] = None
    scope: Optional[dict] = None


@router.post("/alerts/rules", summary="创建告警规则")
def create_alert_rule(
    project_id: int,
    request: AlertRuleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建告警规则"""
    service = AIAlertService(db)
    rule, success, error = service.create_alert_rule(
        project_id=project_id,
        user_id=current_user.id,
        name=request.name,
        rule_type=request.type,
        threshold=request.threshold,
        severity=request.severity,
        notify_channels=request.notify_channels,
        scope=request.scope
    )
    if not success:
        raise HTTPException(status_code=400, detail=error)
    return service.get_alert_rules(project_id)


@router.put("/alerts/rules/{rule_id}", summary="更新告警规则")
def update_alert_rule(
    rule_id: int,
    threshold: Optional[float] = None,
    severity: Optional[str] = None,
    enabled: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新告警规则"""
    service = AIAlertService(db)
    kwargs = {}
    if threshold is not None:
        kwargs["threshold"] = threshold
    if severity is not None:
        kwargs["severity"] = severity
    if enabled is not None:
        kwargs["enabled"] = enabled
    
    rule, success, error = service.update_alert_rule(rule_id, **kwargs)
    if not success:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "更新成功"}


@router.delete("/alerts/rules/{rule_id}", summary="删除告警规则")
def delete_alert_rule(
    rule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除告警规则"""
    service = AIAlertService(db)
    success, error = service.delete_alert_rule(rule_id)
    if not success:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "删除成功"}


@router.put("/alerts/rules/{rule_id}/toggle", summary="启用/禁用规则")
def toggle_alert_rule(
    rule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """切换告警规则启用状态"""
    service = AIAlertService(db)
    success, error = service.toggle_alert_rule(rule_id)
    if not success:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "操作成功"}


@router.post("/alerts/check", summary="检查告警")
def check_alerts(
    project_id: int,
    metrics: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """检查告警条件"""
    service = AIAlertService(db)
    triggered = service.check_alerts(project_id, metrics)
    return {"triggered": triggered, "count": len(triggered)}


# ==================== 性能基线 API ====================

@router.get("/baselines", summary="获取性能基线列表")
def get_baselines(
    project_id: int = Query(...),
    case_id: Optional[int] = Query(None),
    scenario_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取性能基线"""
    service = AIPerformanceService(db)
    baselines = service.get_baselines(project_id, case_id, scenario_id)
    return {"items": baselines}


class BaselineCreate(BaseModel):
    metric_name: str
    baseline_value: float
    upper_bound: Optional[float] = None
    lower_bound: Optional[float] = None
    case_id: Optional[int] = None
    scenario_id: Optional[int] = None
    environment_id: Optional[int] = None


@router.post("/baselines", summary="创建性能基线")
def create_baseline(
    project_id: int,
    request: BaselineCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建性能基线"""
    service = AIPerformanceService(db)
    baseline, success, error = service.create_baseline(
        project_id=project_id,
        metric_name=request.metric_name,
        baseline_value=request.baseline_value,
        upper_bound=request.upper_bound,
        lower_bound=request.lower_bound,
        case_id=request.case_id,
        scenario_id=request.scenario_id,
        environment_id=request.environment_id
    )
    if not success:
        raise HTTPException(status_code=400, detail=error)
    return service.get_baselines(project_id)


@router.post("/baselines/{baseline_id}/collect", summary="采集基线数据")
def collect_baseline(
    baseline_id: int,
    value: float,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """采集新数据更新基线"""
    service = AIPerformanceService(db)
    result = service.collect_baseline_data(baseline_id, value)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.delete("/baselines/{baseline_id}", summary="删除性能基线")
def delete_baseline(
    baseline_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除性能基线"""
    service = AIPerformanceService(db)
    success, error = service.delete_baseline(baseline_id)
    if not success:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "删除成功"}
