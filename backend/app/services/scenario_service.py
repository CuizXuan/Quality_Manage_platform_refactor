"""
Scenario Service — 场景编排业务逻辑层

封装 Scenario + ExecutionRun 的业务操作，包括：
  - 场景 CRUD（含步骤管理）
  - 执行引擎核心逻辑
  - 执行历史记录
"""
import json
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.scenario import Scenario, ScenarioStep, ExecutionRun
from app.repositories.scenario_repository import ScenarioRepository
from app.repositories.execution_repository import ExecutionRepository


class ScenarioService:
    """Service for scenario orchestration business logic."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = ScenarioRepository()
        self.exec_repo = ExecutionRepository()

    # ── Serialization helpers ─────────────────────────────────────

    @staticmethod
    def _serialize_step(step: ScenarioStep) -> Dict[str, Any]:
        """Serialize a ScenarioStep model to dict."""
        return {
            "id": step.id,
            "scenario_id": step.scenario_id,
            "case_id": step.case_id,
            "variant_id": step.variant_id,
            "name": step.name,
            "sort_order": step.sort_order,
            "enabled": bool(step.enabled),
            "retry_count": step.retry_count,
            "timeout_ms": step.timeout_ms,
            "failure_strategy": step.failure_strategy or "stop",
            "extract_rules": json.loads(step.extract_rules) if step.extract_rules else [],
            "inject_rules": json.loads(step.inject_rules) if step.inject_rules else [],
        }

    @staticmethod
    def _serialize_scenario(scenario: Scenario) -> Dict[str, Any]:
        """Serialize a Scenario model to dict with steps."""
        return {
            "id": scenario.id,
            "name": scenario.name,
            "description": scenario.description or "",
            "status": scenario.status or "draft",
            "version": scenario.version or 1,
            "created_by": scenario.created_by,
            "created_at": scenario.created_at.isoformat() if scenario.created_at else "",
            "steps": [ScenarioService._serialize_step(s) for s in scenario.steps],
        }

    @staticmethod
    def _serialize_run(run: ExecutionRun) -> Dict[str, Any]:
        """Serialize an ExecutionRun model to dict."""
        summary = run.summary
        if isinstance(summary, str):
            try:
                summary = json.loads(summary)
            except Exception:
                summary = {}
        return {
            "id": run.id,
            "run_type": run.run_type,
            "target_id": run.target_id,
            "environment_id": run.environment_id,
            "status": run.status,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            "duration_ms": run.duration_ms,
            "summary": summary or {},
        }

    # ── Scenario CRUD ────────────────────────────────────────────

    def create_scenario(self, data: dict) -> Dict[str, Any]:
        """Create a new scenario with optional initial steps."""
        scenario_data = {
            "name": data["name"],
            "description": data.get("description", ""),
            "status": data.get("status", "draft"),
            "created_by": data.get("created_by"),
        }
        scenario = self.repo.create(self.db, scenario_data)
        self.db.flush()

        # Create initial steps if provided
        steps_data = data.get("steps", [])
        for idx, step_data in enumerate(steps_data):
            self.repo.add_step(
                self.db,
                scenario.id,
                {
                    "case_id": step_data["case_id"],
                    "variant_id": step_data.get("variant_id"),
                    "name": step_data.get("name", f"Step {idx + 1}"),
                    "sort_order": step_data.get("sort_order", idx),
                    "enabled": step_data.get("enabled", True),
                    "retry_count": step_data.get("retry_count", 0),
                    "timeout_ms": step_data.get("timeout_ms", 30000),
                    "failure_strategy": step_data.get("failure_strategy", "stop"),
                    "extract_rules": json.dumps(step_data.get("extract_rules", [])),
                    "inject_rules": json.dumps(step_data.get("inject_rules", [])),
                },
            )

        self.db.commit()
        scenario = self.repo.get_by_id(self.db, scenario.id)
        return self._serialize_scenario(scenario)

    def list_scenarios(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Tuple[list[Dict[str, Any]], int]:
        """List scenarios with pagination."""
        scenarios, total = self.repo.list(
            self.db, page=page, page_size=page_size, keyword=keyword, status=status
        )
        return [self._serialize_scenario(s) for s in scenarios], total

    def get_scenario(self, scenario_id: int) -> Optional[Dict[str, Any]]:
        """Get a scenario by ID."""
        scenario = self.repo.get_by_id(self.db, scenario_id)
        if not scenario:
            return None
        return self._serialize_scenario(scenario)

    def update_scenario(self, scenario_id: int, data: dict) -> Optional[Dict[str, Any]]:
        """Update a scenario."""
        scenario = self.repo.get_by_id(self.db, scenario_id)
        if not scenario:
            return None
        update_data = {k: v for k, v in data.items() if k not in ("id", "steps")}
        scenario = self.repo.update(self.db, scenario, update_data)
        self.db.commit()
        scenario = self.repo.get_by_id(self.db, scenario_id)
        return self._serialize_scenario(scenario)

    def delete_scenario(self, scenario_id: int) -> bool:
        """Delete a scenario."""
        scenario = self.repo.get_by_id(self.db, scenario_id)
        if not scenario:
            return False
        self.repo.delete(self.db, scenario)
        return True

    # ── Step management ─────────────────────────────────────────

    def add_step(self, scenario_id: int, data: dict) -> Optional[Dict[str, Any]]:
        """Add a step to a scenario."""
        scenario = self.repo.get_by_id(self.db, scenario_id)
        if not scenario:
            return None
        step_data = {
            "case_id": data["case_id"],
            "variant_id": data.get("variant_id"),
            "name": data.get("name", ""),
            "sort_order": data.get("sort_order", 0),
            "enabled": data.get("enabled", True),
            "retry_count": data.get("retry_count", 0),
            "timeout_ms": data.get("timeout_ms", 30000),
            "failure_strategy": data.get("failure_strategy", "stop"),
            "extract_rules": json.dumps(data.get("extract_rules", [])),
            "inject_rules": json.dumps(data.get("inject_rules", [])),
        }
        step = self.repo.add_step(self.db, scenario_id, step_data)
        self.db.commit()
        return self._serialize_step(step)

    def update_step(self, step_id: int, data: dict) -> Optional[Dict[str, Any]]:
        """Update a scenario step."""
        from app.models.scenario import ScenarioStep

        step = self.db.query(ScenarioStep).filter(ScenarioStep.id == step_id).first()
        if not step:
            return None
        update_data = dict(data)
        for json_field in ("extract_rules", "inject_rules"):
            if json_field in update_data and isinstance(update_data[json_field], list):
                update_data[json_field] = json.dumps(update_data[json_field])
        step = self.repo.update_step(self.db, step, update_data)
        self.db.commit()
        return self._serialize_step(step)

    def delete_step(self, step_id: int) -> bool:
        """Delete a scenario step."""
        from app.models.scenario import ScenarioStep

        step = self.db.query(ScenarioStep).filter(ScenarioStep.id == step_id).first()
        if not step:
            return False
        self.repo.delete_step(self.db, step)
        return True

    def reorder_steps(self, scenario_id: int, step_ids: list[int]) -> bool:
        """Reorder steps of a scenario."""
        scenario = self.repo.get_by_id(self.db, scenario_id)
        if not scenario:
            return False
        self.repo.reorder_steps(self.db, scenario_id, step_ids)
        return True

    # ── Execution engine ────────────────────────────────────────

    def start_execution(
        self,
        scenario_id: int,
        environment_id: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """Start a scenario execution, return execution run record."""
        scenario = self.repo.get_by_id(self.db, scenario_id)
        if not scenario:
            return None

        run_data = {
            "run_type": "scenario",
            "target_id": scenario_id,
            "environment_id": environment_id,
            "status": "running",
            "started_at": datetime.utcnow(),
            "summary": json.dumps({"total_steps": len(scenario.steps), "executed": 0, "passed": 0, "failed": 0}),
        }
        run = self.exec_repo.create(self.db, run_data)
        self.db.commit()
        return self._serialize_run(run)

    def update_execution_status(
        self,
        run_id: int,
        status: str,
        finished_at: Optional[datetime] = None,
        duration_ms: Optional[int] = None,
        summary: Optional[dict] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update execution run status (used by execution engine callbacks)."""
        run = self.exec_repo.update_status(
            self.db, run_id, status, finished_at, duration_ms, summary
        )
        if run:
            self.db.commit()
            return self._serialize_run(run)
        return None

    def get_execution(self, run_id: int) -> Optional[Dict[str, Any]]:
        """Get an execution run by ID."""
        run = self.exec_repo.get_by_id(self.db, run_id)
        if not run:
            return None
        return self._serialize_run(run)

    def list_executions(
        self,
        page: int = 1,
        page_size: int = 20,
        run_type: Optional[str] = None,
        target_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> Tuple[list[Dict[str, Any]], int]:
        """List execution runs with pagination."""
        runs, total = self.exec_repo.list(
            self.db, page=page, page_size=page_size,
            run_type=run_type, target_id=target_id, status=status
        )
        return [self._serialize_run(r) for r in runs], total
