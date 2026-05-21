"""
Report Router — 报告 / 缺陷 / 质量门禁 所有 API 端点
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.report import (
    ReportCreate,
    ReportUpdate,
    ReportResponse,
    ReportListResponse,
    DefectCreate,
    DefectUpdate,
    DefectStatusTransition,
    DefectResponse,
    DefectListResponse,
    QualityGateCreate,
    QualityGateUpdate,
    QualityGateResponse,
    QualityGateListResponse,
    QualityGateEvaluateRequest,
    QualityGateEvaluateResponse,
)
from app.services.report_service import ReportService
from app.services.defect_service import DefectService
from app.services.quality_gate_service import QualityGateService

router = APIRouter(prefix="/api/reports", tags=["reports"])


# ── Dependency helpers ────────────────────────────────────────────────────────

def _report_svc(db: Session = Depends(get_db)) -> ReportService:
    return ReportService(db)


def _defect_svc(db: Session = Depends(get_db)) -> DefectService:
    return DefectService(db)


def _gate_svc(db: Session = Depends(get_db)) -> QualityGateService:
    return QualityGateService(db)


# =============================================================================
# Report Endpoints
# =============================================================================

@router.get("", response_model=dict)
def list_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    report_type: Optional[str] = None,
    environment: Optional[str] = None,
    svc: ReportService = Depends(_report_svc),
):
    """List test reports with pagination and filtering."""
    items, total = svc.list_reports(
        page=page,
        page_size=page_size,
        keyword=keyword,
        report_type=report_type,
        environment=environment,
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("", response_model=dict)
def create_report(data: ReportCreate, svc: ReportService = Depends(_report_svc)):
    """Create a new test report."""
    report = svc.create_report(data.model_dump())
    return report


@router.get("/{report_id}", response_model=dict)
def get_report(report_id: int, svc: ReportService = Depends(_report_svc)):
    """Get a report by ID."""
    report = svc.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.put("/{report_id}", response_model=dict)
def update_report(
    report_id: int,
    data: ReportUpdate,
    svc: ReportService = Depends(_report_svc),
):
    """Update a report."""
    report = svc.update_report(report_id, data.model_dump(exclude_unset=True))
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.delete("/{report_id}")
def delete_report(report_id: int, svc: ReportService = Depends(_report_svc)):
    """Delete a report."""
    ok = svc.delete_report(report_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"ok": True}


# =============================================================================
# Defect Endpoints
# =============================================================================

@router.get("/defects", response_model=dict)
def list_defects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    priority: Optional[str] = None,
    defect_type: Optional[str] = None,
    assigned_to: Optional[int] = None,
    project_id: Optional[int] = None,
    svc: DefectService = Depends(_defect_svc),
):
    """List defects with pagination and filtering."""
    items, total = svc.list_defects(
        page=page,
        page_size=page_size,
        keyword=keyword,
        status=status,
        severity=severity,
        priority=priority,
        defect_type=defect_type,
        assigned_to=assigned_to,
        project_id=project_id,
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("/defects", response_model=dict)
def create_defect(data: DefectCreate, svc: DefectService = Depends(_defect_svc)):
    """Create a new defect."""
    defect = svc.create_defect(data.model_dump())
    return defect


@router.get("/defects/{defect_id}", response_model=dict)
def get_defect(defect_id: int, svc: DefectService = Depends(_defect_svc)):
    """Get a defect by ID."""
    defect = svc.get_defect(defect_id)
    if not defect:
        raise HTTPException(status_code=404, detail="Defect not found")
    return defect


@router.put("/defects/{defect_id}", response_model=dict)
def update_defect(
    defect_id: int,
    data: DefectUpdate,
    svc: DefectService = Depends(_defect_svc),
):
    """Update a defect (excluding status — use transition endpoint)."""
    defect = svc.update_defect(defect_id, data.model_dump(exclude_unset=True))
    if not defect:
        raise HTTPException(status_code=404, detail="Defect not found")
    return defect


@router.post("/defects/{defect_id}/transition", response_model=dict)
def transition_defect(
    defect_id: int,
    data: DefectStatusTransition,
    svc: DefectService = Depends(_defect_svc),
):
    """
    Transition defect status through the valid lifecycle:
    open → confirmed → fixed → verified → closed

    Valid transitions:
      open → confirmed, closed
      confirmed → fixed, open
      fixed → verified, confirmed
      verified → closed
      closed → open
    """
    try:
        defect = svc.transition_status(defect_id, data.status)
        return defect
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/defects/{defect_id}")
def delete_defect(defect_id: int, svc: DefectService = Depends(_defect_svc)):
    """Delete a defect."""
    ok = svc.delete_defect(defect_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Defect not found")
    return {"ok": True}


@router.get("/defects/stats/summary", response_model=dict)
def get_defect_statistics(
    project_id: Optional[int] = None,
    svc: DefectService = Depends(_defect_svc),
):
    """Get defect statistics by status and severity."""
    return svc.get_statistics(project_id=project_id)


# =============================================================================
# QualityGate Endpoints
# =============================================================================

@router.get("/quality-gates", response_model=dict)
def list_quality_gates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    gate_type: Optional[str] = None,
    enabled: Optional[bool] = None,
    svc: QualityGateService = Depends(_gate_svc),
):
    """List quality gates with pagination and filtering."""
    items, total = svc.list_gates(
        page=page,
        page_size=page_size,
        keyword=keyword,
        gate_type=gate_type,
        enabled=enabled,
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("/quality-gates", response_model=dict)
def create_quality_gate(
    data: QualityGateCreate,
    svc: QualityGateService = Depends(_gate_svc),
):
    """Create a new quality gate."""
    gate = svc.create_gate(data.model_dump())
    return gate


@router.get("/quality-gates/{gate_id}", response_model=dict)
def get_quality_gate(gate_id: int, svc: QualityGateService = Depends(_gate_svc)):
    """Get a quality gate by ID."""
    gate = svc.get_gate(gate_id)
    if not gate:
        raise HTTPException(status_code=404, detail="Quality gate not found")
    return gate


@router.put("/quality-gates/{gate_id}", response_model=dict)
def update_quality_gate(
    gate_id: int,
    data: QualityGateUpdate,
    svc: QualityGateService = Depends(_gate_svc),
):
    """Update a quality gate."""
    gate = svc.update_gate(gate_id, data.model_dump(exclude_unset=True))
    if not gate:
        raise HTTPException(status_code=404, detail="Quality gate not found")
    return gate


@router.delete("/quality-gates/{gate_id}")
def delete_quality_gate(gate_id: int, svc: QualityGateService = Depends(_gate_svc)):
    """Delete a quality gate."""
    ok = svc.delete_gate(gate_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Quality gate not found")
    return {"ok": True}


@router.post("/quality-gates/{gate_id}/evaluate", response_model=dict)
def evaluate_quality_gate(
    gate_id: int,
    request: QualityGateEvaluateRequest,
    svc: QualityGateService = Depends(_gate_svc),
):
    """
    Evaluate a quality gate against given execution metrics.

    The request body should include execution metrics such as:
    {
        "execution_id": 123,
        "execution_metrics": {
            "pass_rate": 95.5,
            "test_pass_rate": 90.0,
            "defect_count": 3,
            "critical_defects": 0,
            "avg_duration": 1200
        }
    }
    """
    # Build metrics from request
    metrics = {
        "pass_rate": request.scope_filter.get("pass_rate"),
        "test_pass_rate": request.scope_filter.get("test_pass_rate"),
        "defect_count": request.scope_filter.get("defect_count"),
        "critical_defects": request.scope_filter.get("critical_defects"),
        "avg_duration": request.scope_filter.get("avg_duration"),
    }
    # Remove None values
    metrics = {k: v for k, v in metrics.items() if v is not None}

    try:
        result = svc.evaluate_gate(gate_id, metrics)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/quality-gates/evaluate-all", response_model=dict)
def evaluate_all_quality_gates(
    request: QualityGateEvaluateRequest,
    gate_type: Optional[str] = "execution",
    svc: QualityGateService = Depends(_gate_svc),
):
    """
    Evaluate all enabled quality gates of a given type against execution metrics.

    Returns a list of evaluation results.
    """
    metrics = {
        k: v for k, v in request.scope_filter.items()
        if v is not None
    }
    results = svc.evaluate_all_gates_for_execution(metrics, gate_type=gate_type)
    return {"evaluations": results}
