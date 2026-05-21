"""AI Central Schemas — Pydantic v2"""
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ── AI Config ──────────────────────────────────────────────────────────────────

class AIConfigCreate(BaseModel):
    """创建 AI 配置"""
    name: str = Field(default="MiniMax", max_length=100)
    api_key: str = Field(..., max_length=500)
    base_url: str = Field(default="https://api.minimaxi.com", max_length=300)
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
        "variant_generation", "assertion_generation", "failure_analysis", "report_summary"
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
        Literal["variant_generation", "assertion_generation", "failure_analysis", "report_summary"]
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
        "variant_generation", "assertion_generation", "failure_analysis", "report_summary"
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


class AnalyzeFailureRequest(BaseModel):
    """失败归因分析请求"""
    execution_step_id: int


class SummarizeReportRequest(BaseModel):
    """报告总结请求"""
    report_id: int


class AcceptSuggestionRequest(BaseModel):
    """采纳建议请求"""
    accepted_comment: Optional[str] = Field(None, max_length=1000)


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
