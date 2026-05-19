# -*- coding: utf-8 -*-
"""
Phase 5 - AI 模型配置数据模型
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Index
from sqlalchemy.sql import func
from app.models.base import Base


class AIModelConfig(Base):
    """AI 模型配置表"""
    __tablename__ = "ai_model_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    provider = Column(String(50), nullable=False)  # minimax / openai / anthropic / deepseek / custom
    api_key = Column(String(500))
    base_url = Column(String(500))
    model = Column(String(100), nullable=False)
    group_id = Column(String(100))  # MiniMax 专用
    temperature = Column(Integer, default=7)
    max_tokens = Column(Integer, default=4096)
    enabled = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    extra_config = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_ai_model_provider", "provider"),
    )
