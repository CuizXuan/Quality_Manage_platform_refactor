# =============================================================================
# Quality Analytics Schemas - 质量分析 Pydantic 模型
# =============================================================================

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class QualityAnalyticsFilter(BaseModel):
    """质量分析通用筛选条件"""
    project_id: Optional[int] = Field(None, description="项目ID")
    version_id: Optional[int] = Field(None, description="版本ID")
    iteration_id: Optional[int] = Field(None, description="迭代ID")
    start_date: Optional[datetime] = Field(None, description="开始时间")
    end_date: Optional[datetime] = Field(None, description="结束时间")


class OverviewMetrics(BaseModel):
    """概览指标"""
    report_count: int = Field(0, description="报告总数")
    execution_count: int = Field(0, description="执行次数")
    total_cases: int = Field(0, description="用例总数")
    passed_cases: int = Field(0, description="通过用例数")
    failed_cases: int = Field(0, description="失败用例数")
    average_pass_rate: float = Field(0.0, description="平均通过率")
    defect_total: int = Field(0, description="缺陷总数")
    defect_p0p1: int = Field(0, description="P0/P1 缺陷数")
    defect_open: int = Field(0, description="未关闭缺陷数")
    requirement_total: int = Field(0, description="需求总数")
    requirement_covered: int = Field(0, description="已覆盖需求数")
    quality_score: float = Field(0.0, description="质量评分 0-100")


class TrendPoint(BaseModel):
    """趋势数据点"""
    date: str = Field(..., description="日期 YYYY-MM-DD")
    pass_rate: float = Field(0.0, description="通过率")
    defect_count: int = Field(0, description="新增缺陷数")
    execution_count: int = Field(0, description="执行次数")


class DefectDistributionItem(BaseModel):
    """缺陷分布条目"""
    severity: str = Field(..., description="严重程度")
    count: int = Field(0, description="数量")
    open_count: int = Field(0, description="未关闭数")


class RequirementCoverageItem(BaseModel):
    """需求覆盖条目"""
    requirement_id: int
    title: str = ""
    status: str = ""
    covered: bool = False
    defect_count: int = 0


class ReleaseGateResult(BaseModel):
    """发布门禁结论"""
    overall_pass: bool = Field(False, description="总体通过状态")
    gate_name: str = Field("", description="门禁名称")
    gate_level: str = Field("warning", description="门禁级别")
    conditions_passed: int = Field(0, description="通过条件数")
    conditions_failed: int = Field(0, description="失败条件数")
    blockers: List[str] = Field(default_factory=list, description="阻塞项列表")


class OverviewResponse(BaseModel):
    """概览响应"""
    metrics: OverviewMetrics
    scope_note: Optional[str] = Field(None, description="统计范围说明")


class TrendsResponse(BaseModel):
    """趋势响应"""
    points: List[TrendPoint]
    scope_note: Optional[str] = None


class DefectDistributionResponse(BaseModel):
    """缺陷分布响应"""
    items: List[DefectDistributionItem]
    scope_note: Optional[str] = None


class RequirementCoverageResponse(BaseModel):
    """需求覆盖响应"""
    items: List[RequirementCoverageItem]
    coverage_rate: float = Field(0.0, description="覆盖率 0-100")
    scope_note: Optional[str] = None


class ReleaseGateResponse(BaseModel):
    """发布门禁响应"""
    result: ReleaseGateResult
    gates_checked: int = Field(0, description="检查的门禁数")
    scope_note: Optional[str] = None