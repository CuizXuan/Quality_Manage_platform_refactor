# -*- coding: utf-8 -*-
"""
Phase 5 - AI 测试生成 API
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.ai import AIGenService, RAGService, SelfHealService, SmartOrchService

router = APIRouter(prefix="/api/ai-gen", tags=["AI 生成 (Phase 5)"])


# ==================== Request/Response Models ====================

class GenerateRequest(BaseModel):
    source_type: str  # code/doc/curl/description
    source_content: str
    project_id: int
    options: Optional[dict] = None


class GenerateResponse(BaseModel):
    success: bool
    cases: List[dict]
    history_id: int
    model_used: str
    tokens_used: dict


class FeedbackRequest(BaseModel):
    accepted: bool
    feedback_score: Optional[int] = None
    feedback_comment: Optional[str] = None


class RetrieveContextRequest(BaseModel):
    query: str
    project_id: int
    top_k: Optional[int] = 5
    doc_types: Optional[List[str]] = None


class IndexDocumentRequest(BaseModel):
    doc_type: str  # test_case/api_doc/code/issue
    content: str
    project_id: int
    metadata: Optional[dict] = None


# ==================== Dependencies ====================

def get_ai_gen_service(db: Session = Depends(get_db)) -> AIGenService:
    return AIGenService(db)


def get_rag_service(db: Session = Depends(get_db)) -> RAGService:
    return RAGService(db)


# ==================== AI Generation APIs ====================

@router.post("/generate", response_model=GenerateResponse)
async def generate_test_cases(
    request: GenerateRequest,
    req: Request,
    service: AIGenService = Depends(get_ai_gen_service),
):
    """
    AI 生成测试用例

    支持多种输入源：
    - code: 代码片段 (Java/Python/Go 等)
    - doc: OpenAPI/Swagger 文档
    - curl: cURL 命令
    - description: 自然语言描述
    """
    # 获取用户 ID (从 request state)
    user_id = getattr(req.state, "user_id", None) or 1

    # 验证 source_type
    if request.source_type not in ["code", "doc", "curl", "description"]:
        raise HTTPException(status_code=400, detail="Invalid source_type")

    result = service.generate(
        source_type=request.source_type,
        source_content=request.source_content,
        project_id=request.project_id,
        user_id=user_id,
        options=request.options,
    )

    return result


@router.get("/history/{project_id}")
async def get_generation_history(
    project_id: int,
    page: int = 1,
    page_size: int = 20,
    service: AIGenService = Depends(get_ai_gen_service),
):
    """
    获取 AI 生成历史
    """
    return service.get_history(project_id=project_id, page=page, page_size=page_size)


@router.put("/history/{history_id}/feedback")
async def update_generation_feedback(
    history_id: int,
    request: FeedbackRequest,
    service: AIGenService = Depends(get_ai_gen_service),
):
    """
    更新生成用例的反馈
    """
    result = service.update_feedback(
        history_id=history_id,
        accepted=request.accepted,
        feedback_score=request.feedback_score,
        feedback_comment=request.feedback_comment,
    )

    if not result.get("success"):
        raise HTTPException(status_code=404, detail="History not found")

    return result


@router.get("/history/{history_id}/cases")
async def get_generation_cases(
    history_id: int,
    db: Session = Depends(get_db),
):
    """
    获取指定生成历史的用例详情
    """
    from app.models import AIGenHistory

    history = db.query(AIGenHistory).filter(AIGenHistory.id == history_id).first()
    if not history:
        raise HTTPException(status_code=404, detail="History not found")

    import json

    return {
        "cases": json.loads(history.generated_case) if history.generated_case else [],
        "source_type": history.source_type,
        "source_content": history.source_content,
        "accepted": history.accepted,
        "feedback_score": history.feedback_score,
    }


# ==================== RAG APIs ====================

@router.post("/retrieve-context")
async def retrieve_context(
    request: RetrieveContextRequest,
    service: RAGService = Depends(get_rag_service),
):
    """
    RAG 向量检索，获取上下文
    """
    results = service.retrieve(
        query=request.query,
        project_id=request.project_id,
        top_k=request.top_k or 5,
        doc_types=request.doc_types,
    )

    return {"contexts": results}


@router.post("/index-document")
async def index_document(
    request: IndexDocumentRequest,
    service: RAGService = Depends(get_rag_service),
):
    """
    索引文档到向量库
    """
    result = service.index_document(
        doc_type=request.doc_type,
        content=request.content,
        project_id=request.project_id,
        metadata=request.metadata,
    )

    return result


@router.get("/docs-stats/{project_id}")
async def get_docs_stats(
    project_id: int,
    service: RAGService = Depends(get_rag_service),
):
    """
    获取项目的向量文档统计
    """
    return service.get_docs_count(project_id)


@router.delete("/docs/{project_id}")
async def delete_project_docs(
    project_id: int,
    service: RAGService = Depends(get_rag_service),
):
    """
    删除项目的所有向量文档
    """
    count = service.delete_docs_by_project(project_id)
    return {"deleted_count": count}


# ==================== Self-Heal APIs ====================

def get_self_heal_service(db: Session = Depends(get_db)) -> SelfHealService:
    return SelfHealService(db)


def get_smart_orch_service(db: Session = Depends(get_db)) -> SmartOrchService:
    return SmartOrchService(db)


class SelfHealRequest(BaseModel):
    failure_log_id: int
    failure_type: Optional[str] = None
    failure_detail: Optional[dict] = None
    auto_approve: bool = False


@router.post("/self-heal")
async def execute_self_heal(
    request: SelfHealRequest,
    req: Request,
    service: SelfHealService = Depends(get_self_heal_service),
):
    """
    执行测试自愈

    自动分析失败原因并执行对应的自愈策略
    """
    user_id = getattr(req.state, "user_id", None) or 1

    # 分类失败类型
    if not request.failure_type:
        classification = service.classify_failure(request.failure_log_id)
        failure_type = classification.get("failure_type", "unknown")
        context = classification.get("context", {})
    else:
        failure_type = request.failure_type
        context = request.failure_detail or {}

    # 获取项目 ID (从 failure_log 关联的 project)
    project_id = 1  # TODO: 从 failure_log 关联的 scenario/project 获取

    # 匹配自愈策略
    strategies = service.match_heal_strategy(failure_type, context, project_id)

    if not strategies:
        return {
            "heal_id": None,
            "action": None,
            "message": "未找到匹配的自愈策略",
            "requires_approval": True,
        }

    # 执行第一个策略（最高优先级）
    result = service.execute_heal(
        failure_log_id=request.failure_log_id,
        strategy=strategies[0],
        auto_approve=request.auto_approve,
        user_id=user_id,
    )

    return result


@router.get("/self-heal/classify/{failure_log_id}")
async def classify_failure(
    failure_log_id: int,
    service: SelfHealService = Depends(get_self_heal_service),
):
    """
    分类失败类型
    """
    return service.classify_failure(failure_log_id)


@router.get("/self-heal/history/{project_id}")
async def get_self_heal_history(
    project_id: int,
    page: int = 1,
    page_size: int = 20,
    service: SelfHealService = Depends(get_self_heal_service),
):
    """
    获取自愈历史
    """
    return service.get_history(project_id, page, page_size)


@router.put("/self-heal/{heal_id}/approve")
async def approve_self_heal(
    heal_id: int,
    approved: bool = True,
    service: SelfHealService = Depends(get_self_heal_service),
):
    """
    人工审批自愈结果
    """
    return service.approve_heal(heal_id, approved)


@router.post("/self-heal/{heal_id}/rollback")
async def rollback_self_heal(
    heal_id: int,
    service: SelfHealService = Depends(get_self_heal_service),
):
    """
    回滚自愈操作
    """
    return service.rollback_heal(heal_id)


# ==================== Smart Orchestration APIs ====================

class OrchRuleCreateRequest(BaseModel):
    name: str
    condition: dict
    action: dict
    project_id: int
    description: Optional[str] = None
    priority: int = 0


class OrchRuleUpdateRequest(BaseModel):
    name: Optional[str] = None
    condition: Optional[dict] = None
    action: Optional[dict] = None
    description: Optional[str] = None
    priority: Optional[int] = None
    enabled: Optional[bool] = None


@router.get("/orch-rules/{project_id}")
async def get_orch_rules(
    project_id: int,
    page: int = 1,
    page_size: int = 20,
    service: SmartOrchService = Depends(get_smart_orch_service),
):
    """
    获取智能编排规则列表
    """
    return service.get_rules(project_id, page, page_size)


@router.get("/orch-rules/detail/{rule_id}")
async def get_orch_rule(
    rule_id: int,
    service: SmartOrchService = Depends(get_smart_orch_service),
):
    """
    获取规则详情
    """
    rule = service.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.post("/orch-rules")
async def create_orch_rule(
    request: OrchRuleCreateRequest,
    service: SmartOrchService = Depends(get_smart_orch_service),
):
    """
    创建编排规则
    """
    return service.create_rule(
        name=request.name,
        condition=request.condition,
        action=request.action,
        project_id=request.project_id,
        description=request.description,
        priority=request.priority,
    )


@router.put("/orch-rules/{rule_id}")
async def update_orch_rule(
    rule_id: int,
    request: OrchRuleUpdateRequest,
    service: SmartOrchService = Depends(get_smart_orch_service),
):
    """
    更新编排规则
    """
    return service.update_rule(
        rule_id=rule_id,
        name=request.name,
        condition=request.condition,
        action=request.action,
        description=request.description,
        priority=request.priority,
        enabled=request.enabled,
    )


@router.delete("/orch-rules/{rule_id}")
async def delete_orch_rule(
    rule_id: int,
    service: SmartOrchService = Depends(get_smart_orch_service),
):
    """
    删除编排规则
    """
    return service.delete_rule(rule_id)


@router.post("/orch-rules/{rule_id}/toggle")
async def toggle_orch_rule(
    rule_id: int,
    service: SmartOrchService = Depends(get_smart_orch_service),
):
    """
    启用/禁用规则
    """
    return service.toggle_rule(rule_id)


@router.post("/orch-rules/{rule_id}/test")
async def test_orch_rule(
    rule_id: int,
    test_context: dict,
    service: SmartOrchService = Depends(get_smart_orch_service),
):
    """
    测试规则
    """
    return service.test_rule(rule_id, test_context)


@router.get("/orch-rules/templates")
async def get_orch_templates(
    service: SmartOrchService = Depends(get_smart_orch_service),
):
    """
    获取规则模板
    """
    return service.get_templates()


@router.post("/orch-rules/{rule_id}/optimize")
async def optimize_orch_rule(
    rule_id: int,
    service: SmartOrchService = Depends(get_smart_orch_service),
):
    """
    优化规则
    """
    return service.optimize_rule(rule_id)
