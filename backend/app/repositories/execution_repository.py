"""
Execution Repository — 执行记录 CRUD 操作
"""
import json
from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.models.scenario import ExecutionRun


class ExecutionRepository:
    """Repository for ExecutionRun database operations."""

    @staticmethod
    def create(db: Session, data: dict) -> ExecutionRun:
        """Create a new execution run record."""
        run = ExecutionRun(**data)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def list(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        run_type: Optional[str] = None,
        target_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> Tuple[list[ExecutionRun], int]:
        """List execution runs with pagination and filtering."""
        query = db.query(ExecutionRun)

        if run_type:
            query = query.filter(ExecutionRun.run_type == run_type)

        if target_id is not None:
            query = query.filter(ExecutionRun.target_id == target_id)

        if status:
            query = query.filter(ExecutionRun.status == status)

        total = query.count()
        items = (
            query.order_by(ExecutionRun.started_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    @staticmethod
    def get_by_id(db: Session, run_id: int) -> Optional[ExecutionRun]:
        """Get an execution run by ID."""
        return db.query(ExecutionRun).filter(ExecutionRun.id == run_id).first()

    @staticmethod
    def update_status(
        db: Session,
        run_id: int,
        status: str,
        finished_at: Optional[datetime] = None,
        duration_ms: Optional[int] = None,
        summary: Optional[dict] = None,
    ) -> Optional[ExecutionRun]:
        """Update execution status."""
        run = db.query(ExecutionRun).filter(ExecutionRun.id == run_id).first()
        if not run:
            return None
        run.status = status
        if finished_at is not None:
            run.finished_at = finished_at
        if duration_ms is not None:
            run.duration_ms = duration_ms
        if summary is not None:
            run.summary = json.dumps(summary, ensure_ascii=False)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def delete(db: Session, run_obj: ExecutionRun) -> None:
        """Delete an execution run record."""
        db.delete(run_obj)
        db.commit()
