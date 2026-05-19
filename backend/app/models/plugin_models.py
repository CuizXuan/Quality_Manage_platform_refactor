# -*- coding: utf-8 -*-
"""
Phase 5 - 开发者生态数据库模型
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from app.models.base import Base


class Plugin(Base):
    """插件表"""
    __tablename__ = "plugin"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    version = Column(String(20), nullable=False)
    category = Column(String(50), nullable=False)  # executor/assertion/reporter/integration
    description = Column(Text)
    author = Column(String(100))
    author_url = Column(String(500))
    homepage = Column(String(500))
    license = Column(String(50), default="MIT")
    price = Column(Float, default=0)  # 0 = free
    rating = Column(Float, default=0)
    rating_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    install_count = Column(Integer, default=0)
    is_official = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)
    tags = Column(JSON)  # ["grpc", "authentication", "oauth2"]
    requirements = Column(JSON)  # {"python": ">=3.8"}
    config_schema = Column(JSON)  # 插件配置 schema
    manifest = Column(JSON)  # 插件清单
    readme = Column(Text)
    changelog = Column(Text)
    logo_url = Column(String(500))
    screenshots = Column(JSON)  # ["url1", "url2"]
    status = Column(String(20), default="draft")  # draft/pending/approved/rejected
    review_comment = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    published_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class PluginVersion(Base):
    """插件版本表"""
    __tablename__ = "plugin_version"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plugin_id = Column(Integer, ForeignKey("plugin.id"), nullable=False)
    version = Column(String(20), nullable=False)
    release_notes = Column(Text)
    download_url = Column(String(500))
    file_size = Column(Integer)  # bytes
    checksum = Column(String(64))
    compatibility = Column(JSON)  # {"platform": "windows", "arch": "x64"}
    downloads = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())


class PluginReview(Base):
    """插件评论表"""
    __tablename__ = "plugin_review"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plugin_id = Column(Integer, ForeignKey("plugin.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    title = Column(String(200))
    content = Column(Text)
    pros = Column(Text)
    cons = Column(Text)
    is_verified_purchase = Column(Boolean, default=False)
    helpful_count = Column(Integer, default=0)
    status = Column(String(20), default="approved")  # pending/approved/rejected
    created_at = Column(DateTime, server_default=func.now())


class PluginInstall(Base):
    """插件安装记录表"""
    __tablename__ = "plugin_install"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plugin_id = Column(Integer, ForeignKey("plugin.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"))
    version = Column(String(20))
    config = Column(JSON)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class CLIKey(Base):
    """CLI API Key 表"""
    __tablename__ = "cli_key"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    key_hash = Column(String(64), unique=True, nullable=False)
    key_prefix = Column(String(10), nullable=False)  # 前缀用于识别
    name = Column(String(100))
    description = Column(Text)
    permissions = Column(JSON)  # ["read", "write", "execute"]
    rate_limit = Column(Integer, default=100)  # 每分钟请求数
    last_used_at = Column(DateTime)
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class CLIUsageLog(Base):
    """CLI 使用日志表"""
    __tablename__ = "cli_usage_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cli_key_id = Column(Integer, ForeignKey("cli_key.id"), nullable=False)
    endpoint = Column(String(200), nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer)
    response_time_ms = Column(Integer)
    request_size_bytes = Column(Integer)
    response_size_bytes = Column(Integer)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    created_at = Column(DateTime, server_default=func.now())
