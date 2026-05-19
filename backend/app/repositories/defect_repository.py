"""
Defect Repository — 缺陷 CRUD + 状态流转操作
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.models.report import Defect


# 状态流转图：open -> confirmed -> fixed -> verified -> closed
VALID_TRANSITIONS = {
    "open": ["confirmed", "closed"],
    "confirmed": ["fixed", "open"],
    "fixed": ["verified", "confirmed"],
    "verified": ["closed"],
    "closed": ["open"],
}


class DefectRepository:
    """Repository for Defect database operations."""

    @staticmethod
    def create(db: Session, data: dict) -> Defect:
        """Create a new defect."""
        defect = Defect(**data)
        db.add(defect)
        db.commit()
        db.refresh(defect)
        return defect

    @staticmethod
    def list(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        priority: Optional[str] = None,
        defect_type: Optional[str] = None,
        assigned_to: Optional[int] = None,
        project_id: Optional[int] = None,
    ) -> Tuple[list[Defect], int]:
        """List defects with pagination and filtering."""
        query = db.query(Defect)

        if keyword:
            query = query.filter(Defect.title.ilike(f"%{keyword}%"))

        if status:
            query = query.filter(Defect.status == status)

        if severity:
            query = query.filter(Defect.severity == severity)

        if priority:
            query = query.filter(Defect.priority == priority)

        if defect_type:
            query = query.filter(Defect.defect_type == defect_type)

        if assigned_to is not None:
            query = query.filter(Defect.assigned_to == assigned_to)

        if project_id is not None:
            query = query.filter(Defect.project_id == project_id)

        total = query.count()
        items = (
            query.order_by(Defect.opened_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    @staticmethod
    def get_by_id(db: Session, defect_id: int) -> Optional[Defect]:
        """Get a defect by ID."""
        return db.query(Defect).filter(Defect.id == defect_id).first()

    @staticmethod
    def update(db: Session, defect_obj: Defect, data: dict) -> Defect:
        """Update a defect."""
        for key, value in data.items():
            if value is not None and hasattr(defect_obj, key):
                setattr(defect_obj, key, value)
        db.commit()
        db.refresh(defect_obj)
        return defect_obj

    @staticmethod
    def delete(db: Session, defect_obj: Defect) -> None:
        """Delete a defect."""
        db.delete(defect_obj)
        db.commit()

    @staticmethod
    def transition_status(db: Session, defect_obj: Defect, target_status: str) -> Defect:
        """Transition defect to a new status with timestamp update."""
        current = defect_obj.status

        # Validate transition
        if target_status not in VALID_TRANSITIONS.get(current, []):
            raise ValueError(
                f"Invalid status transition: {current} -> {target_status}. "
                f"Allowed: {VALID_TRANSITIONS.get(current, [])}"
            )

        defect_obj.status = target_status
        now = datetime.utcnow()

        if target_status == "confirmed":
            defect_obj.confirmed_at = now
        elif target_status == "fixed":
            defect_obj.fixed_at = now
        elif target_status == "verified":
            defect_obj.verified_at = now
        elif target_status == "closed":
            defect_obj.closed_at = now
        elif target_status == "open":
            # Reopen: clear closure timestamps
            defect_obj.closed_at = None
            defect_obj.verified_at = None
            defect_obj.fixed_at = None
            defect_obj.confirmed_at = None

        db.commit()
        db.refresh(defect_obj)
        return defect_obj

    @staticmethod
    def get_statistics(db: Session, project_id: Optional[int] = None) -> dict:
        """Get defect statistics."""
        query = db.query(Defect)
        if project_id is not None:
            query = query.filter(Defect.project_id == project_id)

        total = query.count()
        by_status = {}
        for status in ["open", "confirmed", "fixed", "verified", "closed"]:
            by_status[status] = query.filter(Defect.status == status).count()

        by_severity = {}
        for sev in ["critical", "high", "medium", "low"]:
            by_severity[sev] = query.filter(Defect.severity == sev).count()

        return {
            "total": total,
            "by_status": by_status,
            "by_severity": by_severity,
        }
