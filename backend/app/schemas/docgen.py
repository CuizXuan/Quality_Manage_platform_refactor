# =============================================================================
# Docgen Schemas - 文档生成 Pydantic 模型
# =============================================================================

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ── DocGen Task Schemas ────────────────────────────────────────────────────────

class DocGenTaskCreate(BaseModel):
    """创建文档生成任务"""
    name: str = Field(..., max_length=200, description="任务名称")
    task_type: Literal["requirement_design", "database_design", "api_design"] = Field(
        ..., description="任务类型"
    )
    source_filename: Optional[str] = Field(None, description="源文件名")


class DocGenTaskUpdate(BaseModel):
    """更新任务"""
    status: Optional[str] = None
    output_filename: Optional[str] = None
    output_path: Optional[str] = None
    message: Optional[str] = None
    finished_at: Optional[datetime] = None


class DocGenTaskResponse(BaseModel):
    """任务响应"""
    id: int
    name: str
    task_type: str
    status: str
    source_filename: Optional[str] = None
    output_filename: Optional[str] = None
    output_path: Optional[str] = None
    message: str = ""
    created_by: Optional[int] = None
    created_at: datetime
    finished_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocGenTaskListResponse(BaseModel):
    """任务列表响应（分页）"""
    items: List[DocGenTaskResponse]
    total: int
    page: int
    page_size: int


# ── DocGen Rule Schemas ────────────────────────────────────────────────────────

class DocGenRuleCreate(BaseModel):
    """创建规则"""
    name: str = Field(..., max_length=200, description="规则名称")
    doc_type: Literal["requirement_outline", "requirement_detail", "database_design", "api_design"] = Field(
        ..., description="文档类型"
    )
    filename: Optional[str] = Field(None, description="规则文件名")
    content: str = Field(..., description="规则内容（JSON）")
    enabled: bool = Field(default=True, description="是否启用")


class DocGenRuleUpdate(BaseModel):
    """更新规则"""
    name: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = None
    enabled: Optional[bool] = None


class DocGenRuleResponse(BaseModel):
    """规则响应"""
    id: int
    name: str
    doc_type: str
    filename: Optional[str] = None
    content: str = ""
    enabled: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocGenRuleListResponse(BaseModel):
    """规则列表响应（分页）"""
    items: List[DocGenRuleResponse]
    total: int
    page: int
    page_size: int


# ── DocGen Template Schemas ──────────────────────────────────────────────────

class DocGenTemplateResponse(BaseModel):
    """模板响应"""
    id: int
    name: str
    doc_type: Optional[str] = None
    filename: Optional[str] = None
    file_path: str
    file_size: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DocGenTemplateListResponse(BaseModel):
    """模板列表响应（分页）"""
    items: List[DocGenTemplateResponse]
    total: int
    page: int
    page_size: int


# ── DocGen Generation Request Schemas ─────────────────────────────────────────

class DocGenRequirementGenerateRequest(BaseModel):
    """需求文档生成请求"""
    source_file_path: str = Field(..., description="需求文档路径（上传后）")
    template_id: Optional[int] = Field(None, description="模板ID")
    rule_ids: List[int] = Field(default_factory=list, description="规则ID列表")
    output_filename: Optional[str] = Field(None, description="输出文件名")


class DocGenDatabaseGenerateRequest(BaseModel):
    """数据库设计文档生成请求"""
    db_type: Literal["sqlite", "mysql", "postgres"] = Field(..., description="数据库类型")
    host: Optional[str] = Field(None, description="主机")
    port: Optional[int] = Field(None, description="端口")
    database: Optional[str] = Field(None, description="数据库名")
    username: Optional[str] = Field(None, description="用户名")
    password: Optional[str] = Field(None, description="密码（不持久化）")
    file_path: Optional[str] = Field(None, description="SQLite文件路径（上传后）")
    selected_tables: List[str] = Field(default_factory=list, description="选择的表名")
    output_filename: Optional[str] = Field(None, description="输出文件名")


class DocGenApiGenerateRequest(BaseModel):
    """API文档生成请求"""
    source_type: Literal["system", "url", "file"] = Field(..., description="来源类型")
    openapi_url: Optional[str] = Field(None, description="OpenAPI URL")
    openapi_file_path: Optional[str] = Field(None, description="OpenAPI文件路径（上传后）")
    selected_tags: List[str] = Field(default_factory=list, description="选择的标签")
    output_format: Literal["markdown", "docx"] = Field(default="markdown", description="输出格式")
    output_filename: Optional[str] = Field(None, description="输出文件名")


# ── DocGen Preview Schemas ────────────────────────────────────────────────────

class DocGenRequirementPreview(BaseModel):
    """需求文档预览结果"""
    total_leaves: int = Field(..., description="功能点总数")
    platforms: List[str] = Field(..., description="平台列表")
    sections: Dict[str, List[str]] = Field(..., description="模块-子功能组结构")


class DocGenApiPreview(BaseModel):
    """API预览结果"""
    total_endpoints: int
    tags: List[str]
    endpoints: List[Dict[str, Any]]


class DocGenDatabasePreview(BaseModel):
    """数据库预览结果"""
    total_tables: int
    tables: List[Dict[str, Any]]