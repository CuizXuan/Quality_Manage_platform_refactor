# =============================================================================
# Report Schemas - 报告/缺陷/质量门禁 Pydantic 模型
# =============================================================================

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ── Report Schemas ────────────────────────────────────────────────────────────

class ReportCreate(BaseModel):
    """创建报告"""
    name: str = Field(..., max_length=200, description="报告名称")
    report_type: Literal["execution", "scenario", "suite"] = Field(..., description="报告类型")
    target_id: Optional[int] = Field(None, description="关联目标ID")
    target_name: Optional[str] = Field(None, description="关联目标名称")
    environment: Optional[str] = Field(None, description="执行环境")
    summary: Dict[str, Any] = Field(default_factory=dict, description="汇总数据")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="详细指标")
    duration_ms: Optional[int] = Field(None, description="执行耗时（毫秒）")
    triggered_by: Optional[int] = Field(None, description="触发人")
    project_id: Optional[int] = None
    version_id: Optional[int] = None
    iteration_id: Optional[int] = None


class ReportUpdate(BaseModel):
    """更新报告"""
    name: Optional[str] = Field(None, max_length=200)
    environment: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
    duration_ms: Optional[int] = None
    project_id: Optional[int] = None
    version_id: Optional[int] = None
    iteration_id: Optional[int] = None


class ReportResponse(BaseModel):
    """报告响应"""
    id: int
    name: str
    report_type: str
    target_id: Optional[int] = None
    target_name: Optional[str] = None
    environment: Optional[str] = None
    summary: Dict[str, Any] = {}
    metrics: Dict[str, Any] = {}
    executed_at: datetime
    duration_ms: Optional[int] = None
    triggered_by: Optional[int] = None
    created_at: datetime
    project_id: Optional[int] = None
    version_id: Optional[int] = None
    iteration_id: Optional[int] = None

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    """报告列表响应（分页）"""
    items: List[ReportResponse]
    total: int
    page: int
    page_size: int


# ── Defect Schemas ───────────────────────────────────────────────────────────

class DefectCreate(BaseModel):
    """创建缺陷"""
    title: str = Field(..., max_length=300, description="缺陷标题")
    description: Optional[str] = Field(None, description="缺陷描述")
    severity: Literal["critical", "high", "medium", "low"] = Field(default="medium", description="严重程度")
    priority: Literal["P0", "P1", "P2", "P3"] = Field(default="P2", description="优先级")
    defect_type: Literal["functional", "api", "performance", "security"] = Field(
        default="functional", description="缺陷类型"
    )
    project_id: Optional[int] = Field(None, description="项目ID")
    case_id: Optional[int] = Field(None, description="关联用例ID")
    execution_id: Optional[int] = Field(None, description="关联执行记录ID")
    assigned_to: Optional[int] = Field(None, description="指派给")
    tags: List[str] = Field(default_factory=list, description="标签")
    version_id: Optional[int] = None
    iteration_id: Optional[int] = None
    requirement_id: Optional[int] = None


class DefectUpdate(BaseModel):
    """更新缺陷"""
    title: Optional[str] = Field(None, max_length=300)
    description: Optional[str] = None
    severity: Optional[Literal["critical", "high", "medium", "low"]] = None
    priority: Optional[Literal["P0", "P1", "P2", "P3"]] = None
    status: Optional[Literal["open", "confirmed", "fixed", "verified", "closed"]] = None
    defect_type: Optional[Literal["functional", "api", "performance", "security"]] = None
    project_id: Optional[int] = None
    case_id: Optional[int] = None
    execution_id: Optional[int] = None
    assigned_to: Optional[int] = None
    tags: Optional[List[str]] = None
    version_id: Optional[int] = None
    iteration_id: Optional[int] = None
    requirement_id: Optional[int] = None


class DefectStatusTransition(BaseModel):
    """缺陷状态流转"""
    status: Literal["open", "confirmed", "fixed", "verified", "closed"] = Field(
        ..., description="目标状态"
    )
    comment: Optional[str] = Field(None, description="状态变更说明")


class DefectResponse(BaseModel):
    """缺陷响应"""
    id: int
    title: str
    description: str = ""
    severity: str = "medium"
    priority: str = "P2"
    status: str = "open"
    defect_type: str = "functional"
    project_id: Optional[int] = None
    case_id: Optional[int] = None
    execution_id: Optional[int] = None
    assigned_to: Optional[int] = None
    reported_by: Optional[int] = None
    opened_at: datetime
    confirmed_at: Optional[datetime] = None
    fixed_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    tags: List[str] = []
    attachments: List[Dict[str, Any]] = []
    version_id: Optional[int] = None
    iteration_id: Optional[int] = None
    requirement_id: Optional[int] = None

    class Config:
        from_attributes = True


class DefectListResponse(BaseModel):
    """缺陷列表响应（分页）"""
    items: List[DefectResponse]
    total: int
    page: int
    page_size: int


# ── QualityGate Schemas ───────────────────────────────────────────────────────

class QualityGateCondition(BaseModel):
    """门禁条件"""
    metric: Literal["pass_rate", "test_pass_rate", "defect_count", "critical_defects", "avg_duration"] = Field(
        ..., description="指标名称"
    )
    operator: Literal[">=", "<=", ">", "<", "==", "!="] = Field(..., description="比较操作符")
    threshold: float = Field(..., description="阈值")


class QualityGateCreate(BaseModel):
    """创建质量门禁规则"""
    name: str = Field(..., max_length=200, description="门禁名称")
    description: Optional[str] = Field(None, description="门禁描述")
    gate_type: Literal["execution", "scheduled", "pre_deploy"] = Field(
        default="execution", description="门禁类型"
    )
    enabled: bool = Field(default=True, description="是否启用")
    conditions: List[QualityGateCondition] = Field(
        default_factory=list, description="门禁条件"
    )
    gate_level: Literal["blocking", "warning", "info"] = Field(
        default="warning", description="门禁等级"
    )
    scope_filter: Dict[str, Any] = Field(default_factory=dict, description="作用范围筛选")


class QualityGateUpdate(BaseModel):
    """更新质量门禁规则"""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    gate_type: Optional[Literal["execution", "scheduled", "pre_deploy"]] = None
    enabled: Optional[bool] = None
    conditions: Optional[List[QualityGateCondition]] = None
    gate_level: Optional[Literal["blocking", "warning", "info"]] = None
    scope_filter: Optional[Dict[str, Any]] = None


class QualityGateResponse(BaseModel):
    """质量门禁响应"""
    id: int
    name: str
    description: str = ""
    gate_type: str = "execution"
    enabled: bool = True
    conditions: List[Dict[str, Any]] = []
    gate_level: str = "warning"
    scope_filter: Dict[str, Any] = {}
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    last_evaluated_at: Optional[datetime] = None
    last_result: Optional[str] = None

    class Config:
        from_attributes = True


class QualityGateListResponse(BaseModel):
    """质量门禁列表响应（分页）"""
    items: List[QualityGateResponse]
    total: int
    page: int
    page_size: int


class QualityGateEvaluateRequest(BaseModel):
    """门禁评估请求"""
    execution_id: Optional[int] = Field(None, description="执行记录ID")
    scenario_id: Optional[int] = Field(None, description="场景ID")
    scope_filter: Dict[str, Any] = Field(default_factory=dict, description="临时覆盖的范围筛选")


class QualityGateEvaluateResponse(BaseModel):
    """门禁评估结果"""
    gate_id: int
    gate_name: str
    gate_level: str
    overall_result: Literal["pass", "fail", "warning", "skipped"]
    details: List[Dict[str, Any]]  # 每条条件的评估结果
    evaluated_at: datetime
