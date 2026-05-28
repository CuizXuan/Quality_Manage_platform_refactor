"""
Quality Analytics Router — 质量分析 API 路由
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.quality_analytics_service import QualityAnalyticsService
from app.schemas.quality_analytics import (
    OverviewResponse,
    TrendsResponse,
    DefectDistributionResponse,
    RequirementCoverageResponse,
    ReleaseGateResponse,
)


router = APIRouter(prefix="/api/quality-analytics", tags=["质量分析"])


def _svc(db: Session = Depends(get_db)) -> QualityAnalyticsService:
    return QualityAnalyticsService(db)


def _parse_date(val: Optional[str]) -> Optional[datetime]:
    if val:
        try:
            return datetime.fromisoformat(val.replace("Z", "+00:00"))
        except Exception:
            return None
    return None


@router.get("/overview", response_model=OverviewResponse)
def get_overview(
    project_id: Optional[int] = None,
    version_id: Optional[int] = None,
    iteration_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    svc: QualityAnalyticsService = Depends(_svc),
):
    """质量分析概览：报告数、执行次数、通过率、缺陷统计、需求覆盖率、质量评分"""
    start_dt = _parse_date(start_date)
    end_dt = _parse_date(end_date)
    result = svc.get_overview(
        project_id=project_id,
        version_id=version_id,
        iteration_id=iteration_id,
        start_date=start_dt,
        end_date=end_dt,
    )
    return result


@router.get("/trends", response_model=TrendsResponse)
def get_trends(
    project_id: Optional[int] = None,
    version_id: Optional[int] = None,
    iteration_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    days: int = Query(default=30, ge=7, le=365),
    svc: QualityAnalyticsService = Depends(_svc),
):
    """质量趋势：通过率趋势、缺陷趋势、执行次数趋势"""
    start_dt = _parse_date(start_date)
    end_dt = _parse_date(end_date)
    result = svc.get_trends(
        project_id=project_id,
        version_id=version_id,
        iteration_id=iteration_id,
        start_date=start_dt,
        end_date=end_dt,
        days=days,
    )
    return result


@router.get("/defect-distribution", response_model=DefectDistributionResponse)
def get_defect_distribution(
    project_id: Optional[int] = None,
    version_id: Optional[int] = None,
    iteration_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    svc: QualityAnalyticsService = Depends(_svc),
):
    """缺陷分布：按严重程度分组的缺陷数量和未关闭数"""
    start_dt = _parse_date(start_date)
    end_dt = _parse_date(end_date)
    result = svc.get_defect_distribution(
        project_id=project_id,
        version_id=version_id,
        iteration_id=iteration_id,
        start_date=start_dt,
        end_date=end_dt,
    )
    return result


@router.get("/requirement-coverage", response_model=RequirementCoverageResponse)
def get_requirement_coverage(
    project_id: Optional[int] = None,
    version_id: Optional[int] = None,
    iteration_id: Optional[int] = None,
    svc: QualityAnalyticsService = Depends(_svc),
):
    """需求覆盖率：需求列表和覆盖率"""
    result = svc.get_requirement_coverage(
        project_id=project_id,
        version_id=version_id,
        iteration_id=iteration_id,
    )
    return result


@router.get("/release-gate", response_model=ReleaseGateResponse)
def get_release_gate(
    project_id: Optional[int] = None,
    version_id: Optional[int] = None,
    iteration_id: Optional[int] = None,
    svc: QualityAnalyticsService = Depends(_svc),
):
    """发布门禁结论：门禁通过/失败状态和阻塞项"""
    result = svc.get_release_gate(
        project_id=project_id,
        version_id=version_id,
        iteration_id=iteration_id,
    )
    return result