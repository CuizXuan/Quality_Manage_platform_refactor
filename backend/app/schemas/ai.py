"""AI Central Schemas — Pydantic v2"""
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


# ── AI Config ──────────────────────────────────────────────────────────────────

class AIConfigCreate(BaseModel):
    """创建 AI 配置"""
    name: str = Field(default="MiniMax", max_length=100)
    api_key: str = Field(..., max_length=500)
    base_url: str = Field(default="https://api.minimaxi.com/v1", max_length=300)
    model: str = Field(default="MiniMax-M2.7", max_length=100)
    enabled: bool = Field(default=False)


class AIConfigUpdate(BaseModel):
    """更新 AI 配置"""
    name: Optional[str] = Field(None, max_length=100)
    api_key: Optional[str] = Field(None, max_length=500)
    base_url: Optional[str] = Field(None, max_length=300)
    model: Optional[str] = Field(None, max_length=100)
    enabled: Optional[bool] = None


class AIConfigResponse(BaseModel):
    """AI 配置响应"""
    id: int
    name: str
    api_key: str
    base_url: str
    model: str
    enabled: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Prompt Templates ─────────────────────────────────────────────────────────────

class AIPromptTemplateCreate(BaseModel):
    """创建 Prompt 模板"""
    name: str = Field(..., max_length=200)
    description: Optional[str] = Field("", max_length=1000)
    template_type: Literal[
        "variant_generation", "assertion_generation", "failure_analysis", "report_summary", "requirement_analysis", "test_design"
    ]
    system_prompt: str = Field("")
    user_prompt_template: str = Field("")
    variables: List[str] = Field(default_factory=list)
    enabled: bool = Field(default=True)


class AIPromptTemplateUpdate(BaseModel):
    """更新 Prompt 模板"""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    template_type: Optional[
        Literal["variant_generation", "assertion_generation", "failure_analysis", "report_summary", "requirement_analysis", "test_design"]
    ] = None
    system_prompt: Optional[str] = None
    user_prompt_template: Optional[str] = None
    variables: Optional[List[str]] = None
    enabled: Optional[bool] = None


class AIPromptTemplateResponse(BaseModel):
    """Prompt 模板响应"""
    id: int
    name: str
    description: str = ""
    template_type: str
    system_prompt: str = ""
    user_prompt_template: str = ""
    variables: List[str] = []
    enabled: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── AI Analysis ─────────────────────────────────────────────────────────────────

class AIAnalysisCreate(BaseModel):
    """创建分析记录（内部使用）"""
    target_type: Literal["case", "variant", "scenario", "execution", "report"]
    target_id: int
    analysis_type: Literal[
        "variant_generation", "assertion_generation", "failure_analysis", "report_summary", "requirement_analysis", "test_design"
    ]
    model_used: str
    raw_response: str = ""
    summary: str = ""
    created_by: Optional[int] = None


class AIAnalysisResponse(BaseModel):
    """AI 分析记录响应"""
    id: int
    target_type: str
    target_id: int
    analysis_type: str
    model_used: str
    raw_response: str = ""
    summary: str = ""
    created_by: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── AI Suggestions ──────────────────────────────────────────────────────────────

class AISuggestionCreate(BaseModel):
    """创建 AI 建议（内部使用）"""
    analysis_id: int
    suggestion_type: str
    content: str  # JSON string
    accepted: bool = Field(default=False)
    accepted_at: Optional[datetime] = None
    accepted_by: Optional[int] = None
    accepted_comment: Optional[str] = Field("", max_length=1000)


class AISuggestionUpdate(BaseModel):
    """更新 AI 建议"""
    suggestion_type: Optional[str] = None
    content: Optional[str] = None
    accepted: Optional[bool] = None
    accepted_at: Optional[datetime] = None
    accepted_by: Optional[int] = None
    accepted_comment: Optional[str] = Field(None, max_length=1000)


class AISuggestionResponse(BaseModel):
    """AI 建议响应"""
    id: int
    analysis_id: int
    suggestion_type: str
    content: str  # JSON string
    accepted: bool = False
    accepted_at: Optional[datetime] = None
    accepted_by: Optional[int] = None
    accepted_comment: str = ""
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Generation Requests ─────────────────────────────────────────────────────────

class GenerateVariantsRequest(BaseModel):
    """生成用例变体请求"""
    case_id: Optional[int] = None
    case_data: Optional[Dict[str, Any]] = None  # {name, method, url, headers, body}


class GenerateAssertionsRequest(BaseModel):
    """生成断言请求"""
    case_id: Optional[int] = None
    response_body: Optional[Dict[str, Any]] = None
    execution_step_id: Optional[int] = None
    case_data: Optional[Dict[str, Any]] = None  # 支持从用例数据生成断言


class AnalyzeFailureRequest(BaseModel):
    """失败归因分析请求"""
    execution_step_id: Optional[int] = None
    case_data: Optional[Dict[str, Any]] = None


class SummarizeReportRequest(BaseModel):
    """报告总结请求"""
    report_id: int


class AcceptSuggestionRequest(BaseModel):
    """采纳建议请求"""
    accepted_comment: Optional[str] = Field(None, max_length=1000)


RequirementSourceType = Literal[
    "prd", "srs", "user_story", "axure", "figma", "ocr", "flowchart", "api_doc", "mixed", "other"
]


class RequirementSourceItem(BaseModel):
    """需求来源补充材料"""
    source_name: str = Field(..., min_length=1, max_length=200)
    source_type: RequirementSourceType = "other"
    content: str = Field(..., min_length=1, max_length=60000)

    @field_validator("source_name", "content")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("内容不能为空")
        return cleaned


class AnalyzeRequirementRequest(BaseModel):
    """需求分析 Agent 请求"""
    target_id: Optional[int] = None
    source_name: str = Field(..., min_length=1, max_length=200)
    source_type: RequirementSourceType
    content: str = Field(..., min_length=1, max_length=60000)
    extra_sources: List[RequirementSourceItem] = Field(default_factory=list)
    project_id: Optional[int] = None
    version_id: Optional[int] = None
    iteration_id: Optional[int] = None
    analysis_focus: List[str] = Field(default_factory=list)

    @field_validator("source_name", "content")
    @classmethod
    def strip_request_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("内容不能为空")
        return cleaned


class RequirementAnalysisItem(BaseModel):
    """结构化需求条目"""
    title: str = ""
    description: str = ""
    source_type: str = "other"
    source_key: Optional[str] = None
    priority: str = "P2"
    status: str = "open"


class AcceptanceCriteriaItem(BaseModel):
    """验收标准条目"""
    requirement_key: Optional[str] = None
    criteria: str = ""
    priority: str = "P2"


class BusinessRuleItem(BaseModel):
    """业务规则条目"""
    name: str = ""
    description: str = ""
    source_key: Optional[str] = None


class RequirementRiskItem(BaseModel):
    """需求风险条目"""
    risk: str = ""
    impact: str = ""
    suggestion: str = ""


class RequirementAnalysisPayload(BaseModel):
    """需求分析结构化载荷"""
    summary: str = ""
    requirements: List[RequirementAnalysisItem] = Field(default_factory=list)
    acceptance_criteria: List[AcceptanceCriteriaItem] = Field(default_factory=list)
    business_rules: List[BusinessRuleItem] = Field(default_factory=list)
    process_flows: List[Any] = Field(default_factory=list)
    api_clues: List[Any] = Field(default_factory=list)
    ambiguities: List[Any] = Field(default_factory=list)
    risks: List[Any] = Field(default_factory=list)
    test_suggestions: List[Any] = Field(default_factory=list)
    coverage_notes: List[Any] = Field(default_factory=list)


class RequirementAnalysisResponse(BaseModel):
    """需求分析 Agent 响应"""
    suggestion_id: int
    agent_type: str
    status: str
    payload: RequirementAnalysisPayload
    trace_meta: Dict[str, Any] = Field(default_factory=dict)


# ── Multi-Agent Workflow ─────────────────────────────────────────────────────

# ── 七期 A：origin 追踪允许值 ─────────────────────────────────────────────
ALLOWED_ORIGIN_MODULES = {
    "requirement",
    "case",
    "scenario",
    "execution",
    "report",
    "ai_workbench",
}
ALLOWED_ORIGIN_TYPES = {
    "requirement_item",
    "test_case",
    "scenario",
    "execution_run",
    "report",
    "manual_input",
}


class StartRequirementWorkflowRequest(BaseModel):
    """启动需求到测试设计工作流请求。

    七期 A：新增 ``origin_*`` 字段用于在 ``input_payload`` /
    ``result_payload.trace_meta`` 中保留业务来源上下文，不影响 workflow 执行语义。
    """
    target_id: Optional[int] = None
    source_name: str = Field(..., min_length=1, max_length=200)
    source_type: RequirementSourceType = "other"
    content: str = Field(..., min_length=1, max_length=60000)
    extra_sources: List[RequirementSourceItem] = Field(default_factory=list)
    project_id: Optional[int] = None
    version_id: Optional[int] = None
    iteration_id: Optional[int] = None
    analysis_focus: List[str] = Field(default_factory=list)
    auto_continue: bool = True

    # ── 七期 A：origin 追踪（可选） ─────────────────────────────────
    origin_module: Optional[str] = None
    origin_type: Optional[str] = None
    origin_ids: List[int] = Field(default_factory=list)
    origin_meta: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("source_name", "content")
    @classmethod
    def strip_workflow_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("内容不能为空")
        return cleaned

    @field_validator("origin_module")
    @classmethod
    def normalize_origin_module(cls, value: Optional[str]) -> Optional[str]:
        if value is None or value == "":
            return None
        cleaned = str(value).strip()
        if not cleaned:
            return None
        if cleaned not in ALLOWED_ORIGIN_MODULES:
            # 不在白名单 → 静默置空，避免 LLM/前端脏数据破坏写入
            return None
        return cleaned

    @field_validator("origin_type")
    @classmethod
    def normalize_origin_type(cls, value: Optional[str]) -> Optional[str]:
        if value is None or value == "":
            return None
        cleaned = str(value).strip()
        if not cleaned:
            return None
        if cleaned not in ALLOWED_ORIGIN_TYPES:
            return None
        return cleaned


class AIWorkflowStepResponse(BaseModel):
    """工作流步骤响应。"""
    id: int
    run_id: int
    step_order: int
    agent_type: str
    status: str
    input_payload: Dict[str, Any] = Field(default_factory=dict)
    output_payload: Dict[str, Any] = Field(default_factory=dict)
    suggestion_id: Optional[int] = None
    error_message: str = ""
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AIWorkflowRunResponse(BaseModel):
    """工作流运行响应。"""
    id: int
    workflow_type: str
    status: str
    source_name: str = ""
    source_type: str = "other"
    input_payload: Dict[str, Any] = Field(default_factory=dict)
    result_payload: Dict[str, Any] = Field(default_factory=dict)
    current_step: str = ""
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    steps: List[AIWorkflowStepResponse] = Field(default_factory=list)
    error: Optional[str] = None

    model_config = {"from_attributes": True}


class WorkflowAdoptRequest(BaseModel):
    """采纳 workflow 结果写入业务表的请求。"""
    project_id: int = Field(..., gt=0)
    version_id: Optional[int] = None
    iteration_id: Optional[int] = None
    adopt_requirements: bool = True
    adopt_functional_cases: bool = True
    adopt_api_cases: bool = True
    # None = 全量；空列表 = 全部跳过
    selected_requirement_indexes: Optional[List[int]] = None
    selected_functional_case_indexes: Optional[List[int]] = None
    selected_api_case_indexes: Optional[List[int]] = None
    link_cases_to_requirements: bool = True
    # force=True 允许重复采纳；默认 False 阻止重复
    force: bool = False

    # 四期加固：场景草稿采纳
    adopt_scenario_drafts: bool = False
    selected_scenario_draft_indexes: Optional[List[int]] = None
    link_scenario_steps_to_cases: bool = True


class WorkflowAdoptRequirementResult(BaseModel):
    """单条需求采纳结果。"""
    index: int
    title: str
    requirement_id: Optional[int] = None
    status: str  # created | skipped | error
    error: Optional[str] = None


class WorkflowAdoptCaseResult(BaseModel):
    """单条用例采纳结果。"""
    index: int
    name: str
    case_id: Optional[int] = None
    case_type: str  # functional | api
    requirement_id: Optional[int] = None
    status: str  # created | skipped | error
    error: Optional[str] = None


class WorkflowAdoptScenarioResult(BaseModel):
    """单条场景草稿采纳结果。"""
    index: int
    name: str
    scenario_id: Optional[int] = None
    step_count: int = 0
    status: str  # created | skipped | error
    error: Optional[str] = None


class WorkflowAdoptResponse(BaseModel):
    """采纳 workflow 结果的响应摘要。"""
    run_id: int
    project_id: int
    version_id: Optional[int] = None
    iteration_id: Optional[int] = None
    created_requirements: List[WorkflowAdoptRequirementResult] = Field(default_factory=list)
    created_cases: List[WorkflowAdoptCaseResult] = Field(default_factory=list)
    created_scenarios: List[WorkflowAdoptScenarioResult] = Field(default_factory=list)
    skipped: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)

    # 三期加固：累计语义，前端可显式拿到
    force_adoption_count: int = 0
    cumulative_requirement_ids: List[int] = Field(default_factory=list)
    cumulative_case_ids: List[int] = Field(default_factory=list)
    # 四期加固：累计场景 ID
    cumulative_scenario_ids: List[int] = Field(default_factory=list)


# ── Phase 5: Execution Planner ────────────────────────────────────────


class WorkflowExecutionPlanRequest(BaseModel):
    """生成执行计划请求（不启动执行）。"""
    scenario_ids: Optional[List[int]] = None
    environment_id: Optional[int] = None
    include_draft_scenarios: bool = True


class WorkflowExecutionBatchInfo(BaseModel):
    """执行批次信息。"""
    name: str
    scenario_ids: List[int] = Field(default_factory=list)
    priority: str = "P2"
    run_mode: str = "sequential"
    environment_id: Optional[int] = None
    rationale: str = ""


class WorkflowExecutionPreCheck(BaseModel):
    """前置检查。"""
    name: str
    status: str = "pending"
    description: str = ""


class WorkflowExecutionPlanResponse(BaseModel):
    """执行计划响应（不创建 execution_runs）。"""
    run_id: int
    suggestion_id: Optional[int] = None
    agent_type: str = "execution-planner"
    status: str = "pending_confirm"
    payload: Dict[str, Any] = Field(default_factory=dict)


class WorkflowExecutionConfirmRequest(BaseModel):
    """人工确认执行计划并启动执行。"""
    batch_indexes: Optional[List[int]] = None
    scenario_ids: Optional[List[int]] = None
    environment_id: Optional[int] = None


class WorkflowExecutionConfirmResponse(BaseModel):
    """确认执行响应：返回本次启动的 execution_run_ids。"""
    run_id: int
    status: str
    execution_run_ids: List[int] = Field(default_factory=list)
    scenario_ids: List[int] = Field(default_factory=list)
    environment_id: Optional[int] = None


# ── Phase 6: Execution Result Analyst ───────────────────────────────────


class WorkflowExecutionAnalysisRequest(BaseModel):
    """执行结果分析请求：基于本 workflow 已启动的 execution_runs 做质量闭环分析。

    - 不传 execution_run_ids 时，分析 confirmation 中全部 execution_run_ids。
    - 显式传入 execution_run_ids 时，会与 confirmation 中的白名单取交集；
      交集为空则返回 `WORKFLOW_EXECUTION_ANALYSIS_TARGET_EMPTY`，避免分析
      任何非本 workflow 启动的执行。
    """

    execution_run_ids: Optional[List[int]] = None
    include_running: bool = True


class WorkflowExecutionAnalysisResponse(BaseModel):
    """执行结果分析响应：写回 run.result_payload.execution_analysis 的内容。"""

    run_id: int
    suggestion_id: Optional[int] = None
    agent_type: str = "execution-result-analyst"
    status: str = "completed"
    payload: Dict[str, Any] = Field(default_factory=dict)


# ── Generation Responses ────────────────────────────────────────────────────────

class VariantItem(BaseModel):
    """变体项"""
    variant_type: str  # edge_case | negative | boundary | high_load | ...
    description: str
    override_config: Dict[str, Any] = {}


class AssertionItem(BaseModel):
    """断言项"""
    assertion_type: str  # status_code | json_equals | json_contains | json_exists | ...
    field: str  # JSONPath
    expected_value: str
    description: str = ""


class GenerateVariantsResponse(BaseModel):
    """生成变体响应"""
    analysis_id: int
    variants: List[VariantItem]


class GenerateAssertionsResponse(BaseModel):
    """生成断言响应"""
    analysis_id: int
    assertions: List[AssertionItem]


class AnalyzeFailureResponse(BaseModel):
    """失败归因响应"""
    analysis_id: int
    root_cause: str
    severity: Optional[str] = None  # critical | high | medium | low
    suggestions: List[Dict[str, Any]]  # [{type, description, effort}]


class SummarizeReportResponse(BaseModel):
    """报告总结响应"""
    analysis_id: int
    summary_md: str
    risk_score: int = Field(..., ge=0, le=100)
    risk_factors: List[str] = []


# ── Paginated Responses ────────────────────────────────────────────────────────

class PaginatedTemplateResponse(BaseModel):
    """分页模板响应"""
    items: List[AIPromptTemplateResponse]
    total: int
    page: int
    page_size: int


class PaginatedAnalysisResponse(BaseModel):
    """分页分析响应"""
    items: List[AIAnalysisResponse]
    total: int
    page: int
    page_size: int


# ── 七期 A：按来源查询 workflow ────────────────────────────────────────


class AIWorkflowTraceResponse(BaseModel):
    """按业务来源查询到的 workflow run 列表响应。"""

    items: List[AIWorkflowRunResponse] = Field(default_factory=list)
    total: int = 0


class StartWorkflowFromRequirementsRequest(BaseModel):
    """从 requirement_items 启动 requirement_to_test_design workflow。"""

    requirement_ids: List[int] = Field(..., min_length=1, max_length=20)
    analysis_focus: List[str] = Field(default_factory=list)
