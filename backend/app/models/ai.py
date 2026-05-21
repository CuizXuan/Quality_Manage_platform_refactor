# =============================================================================
# AI Models - AI中枢模型
# =============================================================================
# 包含：AIConfig（模型配置）、AIPromptTemplate（Prompt模板）、
#       AIAnalysis（分析记录）、AISuggestion（AI建议）
# =============================================================================

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class AIConfig(Base):
    """AI模型配置"""

    __tablename__ = "ai_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, default="MiniMax")
    api_key = Column(String(500), nullable=False)
    base_url = Column(String(300), nullable=False, default="https://api.minimaxi.com")
    model = Column(String(100), nullable=False, default="MiniMax-M2.7")
    enabled = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AIPromptTemplate(Base):
    """AI Prompt 模板"""

    __tablename__ = "ai_prompt_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    template_type = Column(
        String(50),
        nullable=False,
    )
    # variant_generation | assertion_generation | failure_analysis | report_summary
    system_prompt = Column(Text, nullable=False, default="")
    user_prompt_template = Column(Text, nullable=False, default="")
    variables = Column(Text, default="[]")  # JSON array of variable names
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def variable_list(self):
        import json

        return json.loads(self.variables or "[]")

    def set_variables(self, value: list):
        import json

        self.variables = json.dumps(value)


class AIAnalysis(Base):
    """AI分析记录"""

    __tablename__ = "ai_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    target_type = Column(String(20), nullable=False)
    # case | variant | scenario | execution | report
    target_id = Column(Integer, nullable=False)
    analysis_type = Column(String(50), nullable=False)
    # variant_generation | assertion_generation | failure_analysis | report_summary
    model_used = Column(String(100), nullable=False)
    raw_response = Column(Text, default="")  # JSON string
    summary = Column(Text, default="")
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    suggestions = relationship(
        "AISuggestion",
        back_populates="analysis",
        cascade="all, delete-orphan",
        order_by="AISuggestion.id",
    )


class AISuggestion(Base):
    """AI建议"""

    __tablename__ = "ai_suggestions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(Integer, ForeignKey("ai_analyses.id"), nullable=False)
    suggestion_type = Column(String(50), nullable=False)
    # e.g. variant_add, assertion_add, defect_create, fix_recommendation
    content = Column(Text, nullable=False)  # JSON string with suggestion details
    accepted = Column(Boolean, nullable=False, default=False)
    accepted_at = Column(DateTime, nullable=True)
    accepted_by = Column(Integer, nullable=True)
    accepted_comment = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    analysis = relationship("AIAnalysis", back_populates="suggestions")
