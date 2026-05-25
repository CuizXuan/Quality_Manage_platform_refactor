"""
Report Service — 报告生成与查询业务逻辑层
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.report import Report
from app.repositories.report_repository import ReportRepository


class ReportService:
    """Service for test report business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = ReportRepository()

    @staticmethod
    def _serialize_report(report: Report) -> Dict[str, Any]:
        """Serialize a Report model to dict."""
        return {
            "id": report.id,
            "name": report.name,
            "report_type": report.report_type,
            "target_id": report.target_id,
            "target_name": report.target_name,
            "environment": report.environment,
            "summary": report.summary or {},
            "metrics": report.metrics or {},
            "executed_at": report.executed_at.isoformat() if report.executed_at else None,
            "duration_ms": report.duration_ms,
            "triggered_by": report.triggered_by,
            "created_at": report.created_at.isoformat() if report.created_at else None,
            # 质量基础关联字段
            "project_id": getattr(report, "project_id", None),
            "version_id": getattr(report, "version_id", None),
            "iteration_id": getattr(report, "iteration_id", None),
        }

    @staticmethod
    def build_summary(execution_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a summary dict from execution data.

        Expected execution_data shape:
        {
            "total": 100,
            "passed": 90,
            "failed": 5,
            "skipped": 5,
            "duration_ms": 12345
        }
        """
        total = execution_data.get("total", 0)
        passed = execution_data.get("passed", 0)
        failed = execution_data.get("failed", 0)
        skipped = execution_data.get("skipped", 0)

        pass_rate = round(passed / total * 100, 2) if total > 0 else 0.0

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "pass_rate": pass_rate,
        }

    def create_report(self, data: Dict[str, Any]) -> Report:
        """Create a new report."""
        # Auto-fill summary if not provided but execution data is available
        if "execution_data" in data and not data.get("summary"):
            data["summary"] = self.build_summary(data.pop("execution_data"))

        return self.repo.create(self.db, data)

    def list_reports(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        report_type: Optional[str] = None,
        environment: Optional[str] = None,
        project_id: Optional[int] = None,
        version_id: Optional[int] = None,
        iteration_id: Optional[int] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List reports with pagination."""
        items, total = self.repo.list(
            self.db,
            page=page,
            page_size=page_size,
            keyword=keyword,
            report_type=report_type,
            environment=environment,
            project_id=project_id,
            version_id=version_id,
            iteration_id=iteration_id,
        )
        return [self._serialize_report(r) for r in items], total

    def get_report(self, report_id: int) -> Optional[Dict[str, Any]]:
        """Get a single report by ID."""
        report = self.repo.get_by_id(self.db, report_id)
        if not report:
            return None
        return self._serialize_report(report)

    def update_report(self, report_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a report."""
        report = self.repo.get_by_id(self.db, report_id)
        if not report:
            return None
        updated = self.repo.update(self.db, report, data)
        return self._serialize_report(updated)

    def delete_report(self, report_id: int) -> bool:
        """Delete a report."""
        report = self.repo.get_by_id(self.db, report_id)
        if not report:
            return False
        self.repo.delete(self.db, report)
        return True
