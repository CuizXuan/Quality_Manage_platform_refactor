"""
AI Router — AI中枢所有 API 端点

按 phase06-ai-central.md §3 实现所有端点。
Router 只接收参数并调用 Service，Service 负责业务规则和外部调用。
"""

import json
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.ai import AIConfig
from app.repositories.ai_repository import AIRepository
from app.services.ai_service import AIService
from app.schemas.ai import (
    AIConfigCreate,
    AIConfigUpdate,
    AIConfigResponse,
    AIPromptTemplateCreate,
    AIPromptTemplateUpdate,
    AIPromptTemplateResponse,
    AIAnalysisResponse,
    AISuggestionResponse,
    GenerateVariantsRequest,
    GenerateAssertionsRequest,
    AnalyzeFailureRequest,
    SummarizeReportRequest,
    AcceptSuggestionRequest,
    GenerateVariantsResponse,
    GenerateAssertionsResponse,
    AnalyzeFailureResponse,
    SummarizeReportResponse,
    PaginatedTemplateResponse,
    PaginatedAnalysisResponse,
)

router = APIRouter(prefix="/api/ai", tags=["ai"])


def _get_db() -> Session:
    return next(get_db())


def _get_ai_service(db: Session = Depends(_get_db)) -> AIService:
    config = AIRepository.get_config(db)
    if not config:
        raise HTTPException(status_code=400, detail="AI not configured")
    return AIService(config)


def _require_ai_config(db: Session = Depends(_get_db)) -> AIConfig:
    config = AIRepository.get_config(db)
    if not config:
        raise HTTPException(status_code=400, detail="AI not configured, please set config first")
    return config


# ── AI Config ───────────────────────────────────────────────────────────────

@router.get("/config", response_model=AIConfigResponse)
def get_ai_config(db: Session = Depends(_get_db)):
    """GET /api/ai/config — 获取当前AI配置。"""
    config = AIRepository.get_config(db)
    if not config:
        raise HTTPException(status_code=404, detail="AI config not found")
    return config


@router.put("/config", response_model=AIConfigResponse)
def update_ai_config(
    data: AIConfigUpdate,
    db: Session = Depends(_get_db),
):
    """PUT /api/ai/config — 更新AI配置（upsert语义）。"""
    upserted = AIRepository.upsert_config(db, data.model_dump(exclude_unset=True))
    return upserted


@router.post("/config/test")
def test_ai_connection(
    db: Session = Depends(_get_db),
):
    """POST /api/ai/config/test — 测试AI连接。"""
    config = AIRepository.get_config(db)
    if not config:
        raise HTTPException(status_code=400, detail="AI not configured")
    svc = AIService(config)
    result = svc.test_connection()
    return result


# ── Prompt Templates ─────────────────────────────────────────────────────────

@router.get("/templates", response_model=PaginatedTemplateResponse)
def list_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    template_type: Optional[str] = None,
    db: Session = Depends(_get_db),
):
    """GET /api/ai/templates — 分页查询Prompt模板列表。"""
    items, total = AIRepository.list_templates(
        db, page=page, page_size=page_size,
        keyword=keyword, template_type=template_type,
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/templates", response_model=AIPromptTemplateResponse, status_code=201)
def create_template(
    data: AIPromptTemplateCreate,
    db: Session = Depends(_get_db),
):
    """POST /api/ai/templates — 创建Prompt模板。"""
    template = AIRepository.create_template(db, data.model_dump())
    return template


@router.put("/templates/{template_id}", response_model=AIPromptTemplateResponse)
def update_template(
    template_id: int,
    data: AIPromptTemplateUpdate,
    db: Session = Depends(_get_db),
):
    """PUT /api/ai/templates/{id} — 更新Prompt模板。"""
    template = AIRepository.update_template(
        db, template_id, data.model_dump(exclude_unset=True)
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.delete("/templates/{template_id}")
def delete_template(template_id: int, db: Session = Depends(_get_db)):
    """DELETE /api/ai/templates/{id} — 删除Prompt模板。"""
    ok = AIRepository.delete_template(db, template_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"ok": True}


# ── AI Generation ────────────────────────────────────────────────────────────

@router.post("/generate-variants", response_model=GenerateVariantsResponse)
def generate_variants(
    data: GenerateVariantsRequest,
    svc: AIService = Depends(_get_ai_service),
    db: Session = Depends(_get_db),
):
    """POST /api/ai/generate-variants — 从用例生成变体。"""
    if not data.case_id and not data.case_data:
        raise HTTPException(status_code=400, detail="case_id or case_data required")

    # 如果只提供 case_id，需要从库中查询完整用例数据
    if data.case_id and not data.case_data:
        from app.repositories.test_case_repository import TestCaseRepository
        case_model = TestCaseRepository.get_by_id(db, data.case_id)
        if not case_model:
            raise HTTPException(status_code=404, detail="Case not found")
        case_data = {
            "name": case_model.name,
            "method": case_model.method,
            "url": case_model.url,
            "headers": json.loads(case_model.headers or "{}"),
            "body": json.loads(case_model.body or "{}"),
        }
    else:
        case_data = data.case_data

    variants = svc.generate_variants(case_data)

    # 保存分析记录
    analysis = AIRepository.create_analysis(db, {
        "target_type": "case",
        "target_id": data.case_id or 0,
        "analysis_type": "variant_generation",
        "model_used": svc.model,
        "raw_response": json.dumps(variants),
        "summary": f"Generated {len(variants)} variants",
    })

    # 保存建议
    if variants:
        AIRepository.create_suggestions(
            db, analysis.id,
            [{"type": "variant_add", "content": json.dumps(v)} for v in variants],
        )

    return {"analysis_id": analysis.id, "variants": variants}


@router.post("/generate-assertions", response_model=GenerateAssertionsResponse)
def generate_assertions(
    data: GenerateAssertionsRequest,
    svc: AIService = Depends(_get_ai_service),
    db: Session = Depends(_get_db),
):
    """POST /api/ai/generate-assertions — 从响应生成断言。"""
    if not data.response_body and not data.execution_step_id:
        raise HTTPException(status_code=400, detail="response_body or execution_step_id required")

    if data.execution_step_id and not data.response_body:
        # 从执行步骤中提取响应
        from app.models.scenario import ExecutionRun
        step = db.query(ExecutionRun).filter(
            ExecutionRun.id == data.execution_step_id
        ).first()
        if step:
            response_body = json.loads(step.response_body or "{}")
        else:
            raise HTTPException(status_code=404, detail="Execution step not found")
    else:
        response_body = data.response_body

    case_data = {}
    if data.case_id:
        from app.repositories.test_case_repository import TestCaseRepository
        case_model = TestCaseRepository.get_by_id(db, data.case_id)
        if case_model:
            case_data = {
                "name": case_model.name,
                "method": case_model.method,
                "url": case_model.url,
            }

    assertions = svc.generate_assertions(case_data, response_body)

    # 保存分析记录
    analysis = AIRepository.create_analysis(db, {
        "target_type": "case",
        "target_id": data.case_id or 0,
        "analysis_type": "assertion_generation",
        "model_used": svc.model,
        "raw_response": json.dumps(assertions),
        "summary": f"Generated {len(assertions)} assertions",
    })

    if assertions:
        AIRepository.create_suggestions(
            db, analysis.id,
            [{"type": "assertion_add", "content": json.dumps(a)} for a in assertions],
        )

    return {"analysis_id": analysis.id, "assertions": assertions}


@router.post("/analyze-failure", response_model=AnalyzeFailureResponse)
def analyze_failure(
    data: AnalyzeFailureRequest,
    svc: AIService = Depends(_get_ai_service),
    db: Session = Depends(_get_db),
):
    """POST /api/ai/analyze-failure — 失败归因分析。"""
    from app.models.scenario import ExecutionRun

    step = db.query(ExecutionRun).filter(
        ExecutionRun.id == data.execution_step_id
    ).first()
    if not step:
        raise HTTPException(status_code=404, detail="Execution step not found")

    execution_data = {
        "step_id": step.id,
        "status": step.status,
        "error_message": step.error_message or "",
        "response_body": step.response_body or "",
    }

    result = svc.analyze_failure(execution_data)

    # 保存分析记录
    analysis = AIRepository.create_analysis(db, {
        "target_type": "execution",
        "target_id": data.execution_step_id,
        "analysis_type": "failure_analysis",
        "model_used": svc.model,
        "raw_response": json.dumps(result),
        "summary": result.get("root_cause", "")[:200],
    })

    suggestions = result.get("suggestions", [])
    if suggestions:
        AIRepository.create_suggestions(
            db, analysis.id,
            [{"type": "fix_recommendation", "content": json.dumps(s)} for s in suggestions],
        )

    return {
        "analysis_id": analysis.id,
        "root_cause": result.get("root_cause", ""),
        "suggestions": suggestions,
    }


@router.post("/summarize-report", response_model=SummarizeReportResponse)
def summarize_report(
    data: SummarizeReportRequest,
    svc: AIService = Depends(_get_ai_service),
    db: Session = Depends(_get_db),
):
    """POST /api/ai/summarize-report — 报告总结。"""
    from app.models.report import Report

    report = db.query(Report).filter(Report.id == data.report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report_data = {
        "summary": {
            "total": report.summary.get("total") if report.summary else None,
            "passed": report.summary.get("passed") if report.summary else None,
            "failed": report.summary.get("failed") if report.summary else None,
            "pass_rate": report.summary.get("pass_rate") if report.summary else None,
        },
        "metrics": report.metrics or {},
    }

    result = svc.summarize_report(report_data)

    # 保存分析记录
    analysis = AIRepository.create_analysis(db, {
        "target_type": "report",
        "target_id": data.report_id,
        "analysis_type": "report_summary",
        "model_used": svc.model,
        "raw_response": json.dumps(result),
        "summary": result.get("summary_md", "")[:200],
    })

    if result.get("risk_factors"):
        AIRepository.create_suggestions(
            db, analysis.id,
            [
                {
                    "type": "risk_factor",
                    "content": json.dumps({
                        "risk_score": result.get("risk_score"),
                        "factor": f,
                    }),
                }
                for f in result.get("risk_factors", [])
            ],
        )

    return {
        "analysis_id": analysis.id,
        "summary_md": result.get("summary_md", ""),
        "risk_score": result.get("risk_score", 50),
        "risk_factors": result.get("risk_factors", []),
    }


# ── Suggestions ─────────────────────────────────────────────────────────────

@router.post("/suggestions/{suggestion_id}/accept")
def accept_suggestion(
    suggestion_id: int,
    data: AcceptSuggestionRequest,
    db: Session = Depends(_get_db),
):
    """POST /api/ai/suggestions/{id}/accept — 采纳AI建议。"""
    suggestion = AIRepository.accept_suggestion(
        db,
        suggestion_id,
        accepted_by=0,  # TODO: 从 auth context 获取
        comment=data.accepted_comment,
    )
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    return {"ok": True, "id": suggestion.id}


@router.get("/analysis/{analysis_id}", response_model=AIAnalysisResponse)
def get_analysis(
    analysis_id: int,
    db: Session = Depends(_get_db),
):
    """GET /api/ai/analysis/{id} — 查看分析结果。"""
    analysis = AIRepository.get_analysis(db, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis
