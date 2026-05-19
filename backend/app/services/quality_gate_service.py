"""
QualityGate Service — 质量门禁评估业务逻辑层
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.report import QualityGate
from app.repositories.quality_gate_repository import QualityGateRepository


class QualityGateService:
    """Service for quality gate evaluation business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = QualityGateRepository()

    @staticmethod
    def _serialize_gate(gate: QualityGate) -> Dict[str, Any]:
        """Serialize a QualityGate model to dict."""
        return {
            "id": gate.id,
            "name": gate.name,
            "description": gate.description or "",
            "gate_type": gate.gate_type or "execution",
            "enabled": bool(gate.enabled),
            "conditions": gate.conditions or [],
            "gate_level": gate.gate_level or "warning",
            "scope_filter": gate.scope_filter or {},
            "created_by": gate.created_by,
            "created_at": gate.created_at.isoformat() if gate.created_at else None,
            "updated_at": gate.updated_at.isoformat() if gate.updated_at else None,
            "last_evaluated_at": (
                gate.last_evaluated_at.isoformat() if gate.last_evaluated_at else None
            ),
            "last_result": gate.last_result,
        }

    def create_gate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new quality gate."""
        gate = self.repo.create(self.db, data)
        return self._serialize_gate(gate)

    def list_gates(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        gate_type: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List quality gates with pagination."""
        items, total = self.repo.list(
            self.db,
            page=page,
            page_size=page_size,
            keyword=keyword,
            gate_type=gate_type,
            enabled=enabled,
        )
        return [self._serialize_gate(g) for g in items], total

    def get_gate(self, gate_id: int) -> Optional[Dict[str, Any]]:
        """Get a single quality gate."""
        gate = self.repo.get_by_id(self.db, gate_id)
        if not gate:
            return None
        return self._serialize_gate(gate)

    def update_gate(self, gate_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a quality gate."""
        gate = self.repo.get_by_id(self.db, gate_id)
        if not gate:
            return None
        updated = self.repo.update(self.db, gate, data)
        return self._serialize_gate(updated)

    def delete_gate(self, gate_id: int) -> bool:
        """Delete a quality gate."""
        gate = self.repo.get_by_id(self.db, gate_id)
        if not gate:
            return False
        self.repo.delete(self.db, gate)
        return True

    # ── Gate Evaluation Logic ───────────────────────────────────────────────

    def evaluate_gate(
        self,
        gate_id: int,
        execution_metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Evaluate a quality gate against execution metrics.

        execution_metrics expected shape:
        {
            "pass_rate": 95.5,
            "test_pass_rate": 90.0,
            "defect_count": 3,
            "critical_defects": 1,
            "avg_duration": 1250
        }
        """
        gate = self.repo.get_by_id(self.db, gate_id)
        if not gate:
            raise ValueError(f"Quality gate {gate_id} not found")

        if not gate.enabled:
            return {
                "gate_id": gate.id,
                "gate_name": gate.name,
                "gate_level": gate.gate_level,
                "overall_result": "skipped",
                "details": [],
                "evaluated_at": datetime.utcnow().isoformat(),
            }

        details = []
        all_passed = True

        for condition in (gate.conditions or []):
            metric = condition.get("metric")
            operator = condition.get("operator")
            threshold = condition.get("threshold")
            actual = execution_metrics.get(metric)

            if actual is None:
                result = "skipped"
                passed = False
                reason = f"Metric '{metric}' not available"
            else:
                passed = self._compare(float(actual), operator, float(threshold))
                result = "pass" if passed else "fail"
                reason = f"{actual} {operator} {threshold} → {'✓' if passed else '✗'}"

            if not passed:
                all_passed = False

            details.append({
                "metric": metric,
                "operator": operator,
                "threshold": threshold,
                "actual": actual,
                "result": result,
                "reason": reason,
            })

        if details and all(d["result"] == "skipped" for d in details):
            overall = "skipped"
        elif all_passed:
            overall = "pass"
        else:
            overall = "fail"

        # Update gate with evaluation result
        gate.last_evaluated_at = datetime.utcnow()
        gate.last_result = overall
        self.db.commit()

        return {
            "gate_id": gate.id,
            "gate_name": gate.name,
            "gate_level": gate.gate_level,
            "overall_result": overall,
            "details": details,
            "evaluated_at": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def _compare(actual: float, operator: str, threshold: float) -> bool:
        """Compare actual value with threshold using operator."""
        if operator == ">=":
            return actual >= threshold
        elif operator == "<=":
            return actual <= threshold
        elif operator == ">":
            return actual > threshold
        elif operator == "<":
            return actual < threshold
        elif operator == "==":
            return actual == threshold
        elif operator == "!=":
            return actual != threshold
        return False

    def evaluate_all_gates_for_execution(
        self,
        execution_metrics: Dict[str, Any],
        gate_type: Optional[str] = "execution",
    ) -> List[Dict[str, Any]]:
        """Evaluate all enabled gates of a given type against execution metrics."""
        gates = self.repo.get_enabled_gates(self.db, gate_type=gate_type)
        results = []
        for gate in gates:
            result = self.evaluate_gate(gate.id, execution_metrics)
            results.append(result)
        return results
