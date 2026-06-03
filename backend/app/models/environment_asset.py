from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class Environment(Base):
    """Execution environment with ordered variable sets."""

    __tablename__ = "execution_environments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, nullable=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False, default="")
    base_url = Column(String(500), nullable=True)
    description = Column(Text, default="")
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    variable_sets = relationship(
        "VariableSet",
        back_populates="environment",
        cascade="all, delete-orphan",
        order_by="VariableSet.sort_order",
    )


class VariableSet(Base):
    """Variable set attached to an environment."""

    __tablename__ = "variable_sets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    environment_id = Column(Integer, ForeignKey("execution_environments.id"), nullable=False)
    name = Column(String(100), nullable=False)
    scope = Column(String(30), nullable=False, default="shared")
    sort_order = Column(Integer, nullable=False, default=0)
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    environment = relationship("Environment", back_populates="variable_sets")
    variables = relationship(
        "SecretVariable",
        back_populates="variable_set",
        cascade="all, delete-orphan",
        order_by="SecretVariable.id",
    )


class SecretVariable(Base):
    """Plain or secret variable for request templating."""

    __tablename__ = "secret_variables"

    id = Column(Integer, primary_key=True, autoincrement=True)
    variable_set_id = Column(Integer, ForeignKey("variable_sets.id"), nullable=False)
    key = Column(String(100), nullable=False)
    value = Column(Text, default="")
    is_secret = Column(Boolean, nullable=False, default=False)
    masked_value = Column(String(100), nullable=False, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    variable_set = relationship("VariableSet", back_populates="variables")
