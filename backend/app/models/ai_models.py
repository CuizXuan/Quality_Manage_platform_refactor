# -*- coding: utf-8 -*-
"""
Phase 5 - AI 相关数据模型
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


class AIGenHistory(Base):
    """AI 生成历史表"""
    __tablename__ = "ai_gen_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_type = Column(String(50), nullable=False)  # code/doc/curl/description
    source_content = Column(Text, nullable=False)
    generated_case = Column(Text, nullable=False)  # JSON 格式的生成用例
    accepted = Column(Boolean, default=False)
    modified_after_accept = Column(Boolean, default=False)
    feedback_score = Column(Integer, nullable=True)  # 1-5 分评价
    feedback_comment = Column(Text, nullable=True)
    model_used = Column(String(50), nullable=True)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    project = relationship("Project", back_populates="ai_gen_history")
    creator = relationship("User", back_populates="ai_gen_history")


class VectorDoc(Base):
    """向量文档表"""
    __tablename__ = "vector_doc"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_type = Column(String(50), nullable=False)  # test_case/api_doc/code/issue
    content = Column(Text, nullable=False)
    embedding_id = Column(String(100), nullable=True)  # 向量数据库 ID
    doc_metadata = Column(Text, nullable=True)  # JSON 元数据
    chunk_index = Column(Integer, default=0)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    project = relationship("Project", back_populates="vector_docs")


class EmbeddingCache(Base):
    """Embedding 缓存表"""
    __tablename__ = "embedding_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content_hash = Column(String(64), unique=True, nullable=False)
    embedding = Column(Text, nullable=False)  # JSON 格式的向量
    model = Column(String(50), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=True)


class SelfHealLog(Base):
    """测试自愈日志表"""
    __tablename__ = "self_heal_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    failure_log_id = Column(Integer, ForeignKey("execution_log.id"), nullable=True)
    heal_action = Column(String(50), nullable=True)  # update_locator/update_assertion/add_wait/retry_with_backoff/skip_step
    heal_config = Column(Text, nullable=True)  # JSON
    heal_success = Column(Boolean, nullable=True)
    before_snapshot = Column(Text, nullable=True)
    after_snapshot = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)  # 0-1
    ai_reasoning = Column(Text, nullable=True)
    human_approved = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    failure_log = relationship("ExecutionLog", back_populates="self_heal_logs")


class SmartOrchRule(Base):
    """智能编排规则表"""
    __tablename__ = "smart_orch_rule"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    condition = Column(Text, nullable=False)  # JSON 触发条件
    action = Column(Text, nullable=False)  # JSON 执行动作
    priority = Column(Integer, default=0)
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, nullable=True)
    enabled = Column(Boolean, default=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    project = relationship("Project", back_populates="smart_orch_rules")


class AIAdvisorChat(Base):
    """AI 顾问对话表"""
    __tablename__ = "ai_advisor_chat"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_id = Column(String(50), nullable=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    context = Column(Text, nullable=True)  # JSON 上下文
    referenced_docs = Column(Text, nullable=True)  # JSON 文档 ID 列表
    feedback = Column(String(20), nullable=True)  # helpful/not_helpful
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    user = relationship("User", back_populates="ai_advisor_chats")
