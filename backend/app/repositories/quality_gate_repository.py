"""
QualityGate Repository — 质量门禁规则 CRUD 操作
"""
from __future__ import annotations

from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.models.report import QualityGate


class QualityGateRepository:
    """Repository for QualityGate database operations."""

    @staticmethod
    def create(db: Session, data: dict) -> QualityGate:
        """Create a new quality gate."""
        gate = QualityGate(**data)
        db.add(gate)
        db.commit()
        db.refresh(gate)
        return gate

    @staticmethod
    def list(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        gate_type: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> Tuple[list[QualityGate], int]:
        """List quality gates with pagination and filtering."""
        query = db.query(QualityGate)

        if keyword:
            query = query.filter(QualityGate.name.ilike(f"%{keyword}%"))

        if gate_type:
            query = query.filter(QualityGate.gate_type == gate_type)

        if enabled is not None:
            query = query.filter(QualityGate.enabled == (1 if enabled else 0))

        total = query.count()
        items = (
            query.order_by(QualityGate.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    @staticmethod
    def get_by_id(db: Session, gate_id: int) -> Optional[QualityGate]:
        """Get a quality gate by ID."""
        return db.query(QualityGate).filter(QualityGate.id == gate_id).first()

    @staticmethod
    def update(db: Session, gate_obj: QualityGate, data: dict) -> QualityGate:
        """Update a quality gate."""
        for key, value in data.items():
            if value is not None and hasattr(gate_obj, key):
                setattr(gate_obj, key, value)
        db.commit()
        db.refresh(gate_obj)
        return gate_obj

    @staticmethod
    def delete(db: Session, gate_obj: QualityGate) -> None:
        """Delete a quality gate."""
        db.delete(gate_obj)
        db.commit()

    @staticmethod
    def get_enabled_gates(
        db: Session, gate_type: Optional[str] = None
    ) -> list[QualityGate]:
        """Get all enabled quality gates, optionally filtered by type."""
        query = db.query(QualityGate).filter(QualityGate.enabled == True)
        if gate_type:
            query = query.filter(QualityGate.gate_type == gate_type)
        return query.all()
