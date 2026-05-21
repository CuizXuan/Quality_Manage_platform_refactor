# =============================================================================
# Scenario Schemas - 场景编排 Pydantic 模型
# =============================================================================
# 包含：Scenario（场景）、ScenarioStep（场景步骤）、ExecutionRun（执行记录）
# =============================================================================

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class ScenarioStepCreate(BaseModel):
    """创建场景步骤"""
    case_id: int = Field(..., description="关联的用例ID")
    variant_id: Optional[int] = Field(None, description="可选的用例变体ID")
    name: str = Field(..., max_length=200, description="步骤名称")
    sort_order: int = Field(default=0, description="排序顺序")
    enabled: bool = Field(default=True, description="是否启用")
    retry_count: int = Field(default=0, description="重试次数")
    timeout_ms: int = Field(default=30000, description="超时时间（毫秒）")
    failure_strategy: Literal["stop", "continue", "retry", "skip"] = Field(
        default="stop", description="失败策略"
    )
    extract_rules: List[Dict[str, Any]] = Field(
        default_factory=list, description="数据提取规则"
    )
    inject_rules: List[Dict[str, Any]] = Field(
        default_factory=list, description="数据注入规则"
    )


class ScenarioStepUpdate(BaseModel):
    """更新场景步骤"""
    case_id: Optional[int] = None
    variant_id: Optional[int] = None
    name: Optional[str] = Field(None, max_length=200)
    sort_order: Optional[int] = None
    enabled: Optional[bool] = None
    retry_count: Optional[int] = None
    timeout_ms: Optional[int] = None
    failure_strategy: Optional[Literal["stop", "continue", "retry", "skip"]] = None
    extract_rules: Optional[List[Dict[str, Any]]] = None
    inject_rules: Optional[List[Dict[str, Any]]] = None


class ScenarioStepResponse(BaseModel):
    """场景步骤响应"""
    id: int
    scenario_id: int
    case_id: int
    variant_id: Optional[int] = None
    name: str
    sort_order: int
    enabled: bool = True
    retry_count: int = 0
    timeout_ms: int = 30000
    failure_strategy: str = "stop"
    extract_rules: List[Dict[str, Any]] = []
    inject_rules: List[Dict[str, Any]] = []

    class Config:
        from_attributes = True


class ScenarioCreate(BaseModel):
    """创建场景"""
    name: str = Field(..., max_length=200, description="场景名称")
    description: Optional[str] = Field(None, description="场景描述")
    scenario_type: str = Field(default="functional", description="场景类型")
    priority: str = Field(default="P2", description="优先级")
    version: int = Field(default=1, ge=1, description="版本号")
    status: str = Field(default="draft", description="状态")


class ScenarioUpdate(BaseModel):
    """更新场景"""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    scenario_type: Optional[str] = Field(None, description="场景类型")
    priority: Optional[str] = Field(None, description="优先级")
    version: Optional[int] = Field(None, ge=1, description="版本号")
    status: Optional[str] = None


class ScenarioResponse(BaseModel):
    """场景响应（含步骤列表）"""
    id: int
    name: str
    description: str = ""
    scenario_type: str = "functional"
    priority: str = "P2"
    status: str = "draft"
    version: int = 1
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[str] = None
    step_count: int = 0
    steps: List[ScenarioStepResponse] = []

    class Config:
        from_attributes = True


class ScenarioListResponse(BaseModel):
    """场景列表响应（分页）"""
    items: List[ScenarioResponse]
    total: int
    page: int
    page_size: int


class ExecutionRunResponse(BaseModel):
    """执行记录响应"""
    id: int
    run_type: str
    target_id: int
    environment_id: Optional[int] = None
    status: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    summary: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
