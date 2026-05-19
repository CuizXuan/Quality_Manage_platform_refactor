"""
Defect Service — 缺陷状态流转业务逻辑层

状态流转图：
  open → confirmed → fixed → verified → closed
                ↑_______↓ (confirmed 可回到 open)
                ↑_______↓ (fixed 可回到 confirmed)
        (任何状态都可由 closed 回到 open)
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.report import Defect
from app.repositories.defect_repository import DefectRepository


class DefectService:
    """Service for defect tracking business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = DefectRepository()

    @staticmethod
    def _serialize_defect(defect: Defect) -> Dict[str, Any]:
        """Serialize a Defect model to dict."""
        return {
            "id": defect.id,
            "title": defect.title,
            "description": defect.description or "",
            "severity": defect.severity or "medium",
            "priority": defect.priority or "P2",
            "status": defect.status or "open",
            "defect_type": defect.defect_type or "functional",
            "project_id": defect.project_id,
            "case_id": defect.case_id,
            "execution_id": defect.execution_id,
            "assigned_to": defect.assigned_to,
            "reported_by": defect.reported_by,
            "opened_at": defect.opened_at.isoformat() if defect.opened_at else None,
            "confirmed_at": defect.confirmed_at.isoformat() if defect.confirmed_at else None,
            "fixed_at": defect.fixed_at.isoformat() if defect.fixed_at else None,
            "verified_at": defect.verified_at.isoformat() if defect.verified_at else None,
            "closed_at": defect.closed_at.isoformat() if defect.closed_at else None,
            "tags": defect.tags or [],
            "attachments": defect.attachments or [],
        }

    def create_defect(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new defect."""
        defect = self.repo.create(self.db, data)
        return self._serialize_defect(defect)

    def list_defects(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        priority: Optional[str] = None,
        defect_type: Optional[str] = None,
        assigned_to: Optional[int] = None,
        project_id: Optional[int] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List defects with pagination and filtering."""
        items, total = self.repo.list(
            self.db,
            page=page,
            page_size=page_size,
            keyword=keyword,
            status=status,
            severity=severity,
            priority=priority,
            defect_type=defect_type,
            assigned_to=assigned_to,
            project_id=project_id,
        )
        return [self._serialize_defect(d) for d in items], total

    def get_defect(self, defect_id: int) -> Optional[Dict[str, Any]]:
        """Get a single defect by ID."""
        defect = self.repo.get_by_id(self.db, defect_id)
        if not defect:
            return None
        return self._serialize_defect(defect)

    def update_defect(self, defect_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a defect."""
        defect = self.repo.get_by_id(self.db, defect_id)
        if not defect:
            return None
        # Prevent direct status change via update — use transition_status instead
        data.pop("status", None)
        updated = self.repo.update(self.db, defect, data)
        return self._serialize_defect(updated)

    def delete_defect(self, defect_id: int) -> bool:
        """Delete a defect."""
        defect = self.repo.get_by_id(self.db, defect_id)
        if not defect:
            return False
        self.repo.delete(self.db, defect)
        return True

    def transition_status(self, defect_id: int, target_status: str) -> Dict[str, Any]:
        """
        Transition defect to a new status.

        Valid transitions:
          open → confirmed, closed
          confirmed → fixed, open
          fixed → verified, confirmed
          verified → closed
          closed → open
        """
        defect = self.repo.get_by_id(self.db, defect_id)
        if not defect:
            raise ValueError(f"Defect {defect_id} not found")

        updated = self.repo.transition_status(self.db, defect, target_status)
        return self._serialize_defect(updated)

    def get_statistics(
        self, project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get defect statistics."""
        return self.repo.get_statistics(self.db, project_id=project_id)
