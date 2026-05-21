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
            "scenario_type": scenario.scenario_type or "functional",
            "priority": scenario.priority or "P2",
            "status": scenario.status or "draft",
            "version": scenario.version or 1,
            "created_by": scenario.created_by,
            "created_at": scenario.created_at.isoformat() if scenario.created_at else "",
            "updated_at": scenario.updated_at.isoformat() if scenario.updated_at else "",
            "step_count": len(scenario.steps) if scenario.steps else 0,
            "steps": [ScenarioService._serialize_step(s) for s in scenario.steps],
        }

    def _serialize_run(self, run: ExecutionRun) -> Dict[str, Any]:
        """Serialize an ExecutionRun model to dict."""
        summary = run.summary
        if isinstance(summary, str):
            try:
                summary = json.loads(summary)
            except Exception:
                summary = {}

        # Resolve scenario_name via JOIN
        scenario_name = None
        if run.run_type == "scenario" and run.target_id:
            from app.models.scenario import Scenario
            scenario = self.db.query(Scenario).filter(Scenario.id == run.target_id).first()
            if scenario:
                scenario_name = scenario.name

        return {
            "id": run.id,
            "run_type": run.run_type,
            "target_id": run.target_id,
            "scenario_name": scenario_name or (str(run.target_id) if run.target_id else None),
            "environment_id": run.environment_id,
            "status": run.status,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            "duration_ms": run.duration_ms,
            "duration": (run.duration_ms / 1000.0) if run.duration_ms else None,
            "total_steps": summary.get("total_steps") if isinstance(summary, dict) else None,
            "passed_steps": summary.get("passed", summary.get("passed_steps", 0)) if isinstance(summary, dict) else 0,
            "failed_steps": summary.get("failed", summary.get("failed_steps", 0)) if isinstance(summary, dict) else 0,
            "executed_steps": summary.get("executed", 0) if isinstance(summary, dict) else 0,
            "summary": summary or {},
            "triggered_by": None,
        }

    # ── Scenario CRUD ────────────────────────────────────────────

    def create_scenario(self, data: dict) -> Dict[str, Any]:
        """Create a new scenario with optional initial steps."""
        scenario_data = {
            "name": data["name"],
            "description": data.get("description", ""),
            "scenario_type": data.get("scenario_type", "functional"),
            "priority": data.get("priority", "P2"),
            "version": data.get("version", 1),
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


# ── Standalone background task (must be at module level for FastAPI BackgroundTasks) ──

def _run_scenario_background(run_id: int, scenario_id: int) -> None:
    """
    Standalone background task: execute all steps of a scenario sequentially.
    Creates its own DB session to avoid session lifetime issues.
    """
    import httpx

    from app.database import SessionLocal
    from app.models.test_case import TestCase
    from app.models.scenario import ScenarioStep, ExecutionRun
    from app.repositories.scenario_repository import ScenarioRepository
    from app.repositories.execution_repository import ExecutionRepository

    db = SessionLocal()
    try:
        repo = ScenarioRepository()
        exec_repo = ExecutionRepository()

        run = exec_repo.get_by_id(db, run_id)
        if not run:
            return
        scenario = repo.get_by_id(db, scenario_id)
        if not scenario or not scenario.steps:
            _update_run_status(
                db, run_id,
                status="failed",
                summary={"total_steps": 0, "executed": 0, "passed": 0, "failed": 0, "error": "No steps found"},
            )
            return

        steps = sorted(scenario.steps, key=lambda s: s.sort_order)
        summary = {"total_steps": len(steps), "executed": 0, "passed": 0, "failed": 0}
        failed = False

        for step in steps:
            if not step.enabled:
                continue

            step_result = {"step_id": step.id, "case_id": step.case_id, "name": step.name, "status": "passed"}

            try:
                case = db.query(TestCase).filter(TestCase.id == step.case_id).first()
                if not case:
                    step_result["status"] = "failed"
                    step_result["error"] = f"Case {step.case_id} not found"
                    summary["failed"] += 1
                else:
                    try:
                        with httpx.Client(timeout=step.timeout_ms / 1000) as client:
                            resp = client.post(
                                "http://localhost:8000/api/terminal/internal/run",
                                json={
                                    "method": case.method or "GET",
                                    "url": case.url or "",
                                    "headers": _load_json(case.headers),
                                    "query_params": _load_json(case.query_params),
                                    "body": case.body or "",
                                    "body_type": case.body_type or "none",
                                    "expected_status": case.expected_status or 200,
                                },
                            )
                            if resp.status_code >= 400:
                                step_result["status"] = "failed"
                                step_result["error"] = f"HTTP {resp.status_code}: {resp.text[:200]}"
                                summary["failed"] += 1
                            else:
                                step_result["response_status"] = resp.status_code
                    except httpx.TimeoutException:
                        step_result["status"] = "failed"
                        step_result["error"] = f"Timeout after {step.timeout_ms}ms"
                        summary["failed"] += 1
                    except Exception as e:
                        step_result["status"] = "failed"
                        step_result["error"] = str(e)
                        summary["failed"] += 1
            except Exception as e:
                step_result["status"] = "failed"
                step_result["error"] = str(e)
                summary["failed"] += 1

            summary["executed"] += 1
            if step_result["status"] == "passed":
                summary["passed"] += 1

            # Apply failure strategy
            if step_result["status"] == "failed":
                if step.failure_strategy == "stop":
                    failed = True
                    break
                elif step.failure_strategy == "skip":
                    continue

        duration_ms = 0
        if run.started_at:
            duration_ms = int((datetime.utcnow() - run.started_at).total_seconds() * 1000)

        _update_run_status(
            db, run_id,
            status="passed" if not failed and summary["failed"] == 0 else "failed",
            finished_at=datetime.utcnow(),
            duration_ms=duration_ms,
            summary=summary,
        )
    finally:
        db.close()


def _update_run_status(
    db,
    run_id: int,
    status: str,
    finished_at=None,
    duration_ms: int | None = None,
    summary: dict | None = None,
) -> None:
    import json as _json
    run = db.query(ExecutionRun).filter(ExecutionRun.id == run_id).first()
    if not run:
        return
    run.status = status
    if finished_at is not None:
        run.finished_at = finished_at
    if duration_ms is not None:
        run.duration_ms = duration_ms
    if summary is not None:
        run.summary = _json.dumps(summary, ensure_ascii=False)
    db.commit()


def _load_json(text: str) -> dict:
    import json as _json
    try:
        return _json.loads(text or "{}")
    except Exception:
        return {}
