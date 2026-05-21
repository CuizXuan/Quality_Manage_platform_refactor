# -*- coding: utf-8 -*-
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import Base


class DictType(Base):
    """字典类型"""
    __tablename__ = "dict_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), default="")
    sort_order = Column(Integer, default=0)
    status = Column(String(20), default="active")  # active/disabled
    created_at = Column(DateTime, default=datetime.now)

    items = relationship("DictItem", back_populates="dict_type", cascade="all, delete-orphan")


class DictItem(Base):
    """字典项"""
    __tablename__ = "dict_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type_id = Column(Integer, ForeignKey("dict_types.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    value = Column(String(100), default="")  # 存储值，可与 name 不同
    sort_order = Column(Integer, default=0)
    status = Column(String(20), default="active")  # active/disabled
    color = Column(String(20), default="")  # 前端展示颜色
    is_default = Column(Integer, default=0)  # Boolean (SQLite不支持Boolean)
    created_at = Column(DateTime, default=datetime.now)

    dict_type = relationship("DictType", back_populates="items")