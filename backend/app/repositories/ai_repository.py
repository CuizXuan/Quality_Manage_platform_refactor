"""
AI Repository — AI配置 / Prompt模板 / 分析记录的数据库操作
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple, List

from sqlalchemy.orm import Session

from app.models.ai import AIConfig, AIPromptTemplate, AIAnalysis, AISuggestion


class AIRepository:
    """Repository for AI-related database operations."""

    # ── AI Config ───────────────────────────────────────────────────────────────

    @staticmethod
    def get_config(db: Session) -> Optional[AIConfig]:
        """获取当前启用的AI配置，只返回一条。"""
        return db.query(AIConfig).filter(AIConfig.enabled == True).first()

    @staticmethod
    def upsert_config(db: Session, data: dict) -> AIConfig:
        """创建或更新AI配置（全局只有一条，upsert）。"""
        config = db.query(AIConfig).first()
        if not config:
            config = AIConfig(**data)
            db.add(config)
        else:
            for key, value in data.items():
                setattr(config, key, value)
            config.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(config)
        return config

    # ── Prompt Template ─────────────────────────────────────────────────────────

    @staticmethod
    def create_template(db: Session, data: dict) -> AIPromptTemplate:
        """创建Prompt模板。"""
        import json

        template = AIPromptTemplate(
            name=data["name"],
            description=data.get("description", ""),
            template_type=data["template_type"],
            system_prompt=data.get("system_prompt", ""),
            user_prompt_template=data["user_prompt_template"],
            variables=json.dumps(data.get("variables", [])),
            enabled=data.get("enabled", True),
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    @staticmethod
    def list_templates(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        template_type: Optional[str] = None,
    ) -> Tuple[List[AIPromptTemplate], int]:
        """分页查询Prompt模板。"""
        query = db.query(AIPromptTemplate)
        if keyword:
            query = query.filter(AIPromptTemplate.name.ilike(f"%{keyword}%"))
        if template_type:
            query = query.filter(AIPromptTemplate.template_type == template_type)
        total = query.count()
        items = (
            query.order_by(AIPromptTemplate.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    @staticmethod
    def get_template(db: Session, template_id: int) -> Optional[AIPromptTemplate]:
        """根据ID获取单个模板。"""
        return db.query(AIPromptTemplate).filter(AIPromptTemplate.id == template_id).first()

    @staticmethod
    def update_template(
        db: Session, template_id: int, data: dict
    ) -> Optional[AIPromptTemplate]:
        """更新Prompt模板。"""
        import json

        template = db.query(AIPromptTemplate).filter(
            AIPromptTemplate.id == template_id
        ).first()
        if not template:
            return None
        for key, value in data.items():
            if key == "variables":
                setattr(template, "variables", json.dumps(value))
            elif value is not None:
                setattr(template, key, value)
        template.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(template)
        return template

    @staticmethod
    def delete_template(db: Session, template_id: int) -> bool:
        """删除Prompt模板。"""
        template = db.query(AIPromptTemplate).filter(
            AIPromptTemplate.id == template_id
        ).first()
        if not template:
            return False
        db.delete(template)
        db.commit()
        return True

    # ── AI Analysis ─────────────────────────────────────────────────────────────

    @staticmethod
    def create_analysis(db: Session, data: dict) -> AIAnalysis:
        """创建分析记录。"""
        analysis = AIAnalysis(**data)
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return analysis

    @staticmethod
    def get_analysis(db: Session, analysis_id: int) -> Optional[AIAnalysis]:
        """获取分析记录（含suggestions）。"""
        return (
            db.query(AIAnalysis)
            .filter(AIAnalysis.id == analysis_id)
            .first()
        )

    @staticmethod
    def list_analyses(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        target_type: Optional[str] = None,
        analysis_type: Optional[str] = None,
    ) -> Tuple[List[AIAnalysis], int]:
        """分页查询分析记录。"""
        query = db.query(AIAnalysis)
        if target_type:
            query = query.filter(AIAnalysis.target_type == target_type)
        if analysis_type:
            query = query.filter(AIAnalysis.analysis_type == analysis_type)
        total = query.count()
        items = (
            query.order_by(AIAnalysis.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    # ── AI Suggestion ───────────────────────────────────────────────────────────

    @staticmethod
    def create_suggestions(
        db: Session, analysis_id: int, suggestions: List[dict]
    ) -> List[AISuggestion]:
        """批量创建建议。"""
        records = []
        for s in suggestions:
            record = AISuggestion(
                analysis_id=analysis_id,
                suggestion_type=s.get("type", "general"),
                content=s.get("content", "{}"),
                accepted=False,
            )
            db.add(record)
            records.append(record)
        db.commit()
        for r in records:
            db.refresh(r)
        return records

    @staticmethod
    def accept_suggestion(
        db: Session,
        suggestion_id: int,
        accepted_by: int,
        comment: Optional[str] = None,
    ) -> Optional[AISuggestion]:
        """采纳建议。"""
        suggestion = db.query(AISuggestion).filter(
            AISuggestion.id == suggestion_id
        ).first()
        if not suggestion:
            return None
        suggestion.accepted = True
        suggestion.accepted_at = datetime.utcnow()
        suggestion.accepted_by = accepted_by
        if comment:
            suggestion.accepted_comment = comment
        db.commit()
        db.refresh(suggestion)
        return suggestion

    @staticmethod
    def list_suggestions(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        accepted: Optional[bool] = None,
        suggestion_type: Optional[str] = None,
    ) -> Tuple[List[AISuggestion], int]:
        """分页查询建议列表。"""
        query = db.query(AISuggestion)
        if accepted is not None:
            query = query.filter(AISuggestion.accepted == accepted)
        if suggestion_type:
            query = query.filter(AISuggestion.suggestion_type == suggestion_type)
        total = query.count()
        items = (
            query.order_by(AISuggestion.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total
