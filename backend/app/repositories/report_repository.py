"""
Report Repository — 报告 CRUD 操作
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.models.report import Report


class ReportRepository:
    """Repository for Report database operations."""

    @staticmethod
    def create(db: Session, data: dict) -> Report:
        """Create a new report."""
        report = Report(**data)
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def list(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        report_type: Optional[str] = None,
        environment: Optional[str] = None,
        project_id: Optional[int] = None,
        version_id: Optional[int] = None,
        iteration_id: Optional[int] = None,
    ) -> Tuple[list[Report], int]:
        """List reports with pagination and filtering."""
        query = db.query(Report)

        if keyword:
            query = query.filter(Report.name.ilike(f"%{keyword}%"))

        if report_type:
            query = query.filter(Report.report_type == report_type)

        if environment:
            query = query.filter(Report.environment == environment)

        if project_id is not None:
            query = query.filter(Report.project_id == project_id)
        if version_id is not None:
            query = query.filter(Report.version_id == version_id)
        if iteration_id is not None:
            query = query.filter(Report.iteration_id == iteration_id)

        total = query.count()
        items = (
            query.order_by(Report.executed_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    @staticmethod
    def get_by_id(db: Session, report_id: int) -> Optional[Report]:
        """Get a report by ID."""
        return db.query(Report).filter(Report.id == report_id).first()

    @staticmethod
    def update(db: Session, report_obj: Report, data: dict) -> Report:
        """Update a report."""
        for key, value in data.items():
            if value is not None and hasattr(report_obj, key):
                setattr(report_obj, key, value)
        db.commit()
        db.refresh(report_obj)
        return report_obj

    @staticmethod
    def delete(db: Session, report_obj: Report) -> None:
        """Delete a report."""
        db.delete(report_obj)
        db.commit()
