"""
Test Plan Service — 测试计划业务逻辑层

封装 TestPlan + TestSuite + TestSuiteItem + TestPlanRun 的业务操作
"""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.test_plan import TestPlan, TestSuite, TestSuiteItem, TestPlanRun
from app.models.test_case import TestCase
from app.models.scenario import Scenario
from app.models.quality_foundation import QualityProject, QualityVersion, QualityIteration


# ── JSON parsing helper ────────────────────────────────────────────────────────

def _safe_json_loads(text: str, fallback: Any = None) -> Any:
    """Defensively parse JSON string, returning fallback for empty/dirty data."""
    if not text:
        return fallback if fallback is not None else {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return fallback if fallback is not None else {}


def _validate_plan_scope(data: Dict[str, Any], db: Session, existing_plan: Optional[Dict[str, Any]] = None) -> None:
    """Validate project/version/iteration hierarchy consistency.

    Raises ValueError with clear message if:
    - version_id exists but does not belong to plan's project_id
    - iteration_id exists but does not belong to plan's project_id/version_id
    - referenced project/version/iteration does not exist

    Note: when project_id is provided but no matching QualityProject exists in DB,
    validation is skipped to maintain backward compatibility with existing data.
    """
    project_id = data.get("project_id")
    version_id = data.get("version_id")
    iteration_id = data.get("iteration_id")

    if not project_id:
        return

    project = db.query(QualityProject).filter(QualityProject.id == project_id).first()
    if not project:
        # Backward compatibility: if project doesn't exist, skip hierarchy validation
        return

    if version_id:
        version = db.query(QualityVersion).filter(QualityVersion.id == version_id).first()
        if not version:
            raise ValueError(f"版本 {version_id} 不存在")
        if version.project_id != project_id:
            raise ValueError(f"版本 {version_id} 不属于项目 {project_id}")

        if iteration_id:
            iteration = db.query(QualityIteration).filter(QualityIteration.id == iteration_id).first()
            if not iteration:
                raise ValueError(f"迭代 {iteration_id} 不存在")
            if iteration.project_id != project_id or iteration.version_id != version_id:
                raise ValueError(f"迭代 {iteration_id} 不属于项目 {project_id} / 版本 {version_id}")


class TestPlanService:
    """Service for test plan business logic."""

    def __init__(self, db: Session):
        self.db = db

    # ── TestPlan ─────────────────────────────────────────────────

    def list_plans(
        self,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        query = self.db.query(TestPlan)
        if project_id:
            query = query.filter(TestPlan.project_id == project_id)
        if status:
            query = query.filter(TestPlan.status == status)
        if keyword:
            query = query.filter(TestPlan.name.contains(keyword))

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(TestPlan.updated_at.desc()).offset(offset).limit(page_size).all()
        return [self._serialize_plan(p) for p in items], total

    def get_plan(self, plan_id: int) -> Optional[Dict[str, Any]]:
        plan = self.db.query(TestPlan).filter(TestPlan.id == plan_id).first()
        if not plan:
            return None
        return self._serialize_plan(plan, include_suites=True)

    def create_plan(self, data: Dict[str, Any]) -> Dict[str, Any]:
        _validate_plan_scope(data, self.db)
        plan = TestPlan(**data)
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        return self._serialize_plan(plan)

    def update_plan(self, plan_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        existing = self.db.query(TestPlan).filter(TestPlan.id == plan_id).first()
        if not existing:
            return None
        # Build merged data for validation (None fields from data should not override existing values)
        merged = {k: getattr(existing, k) for k in ("project_id", "version_id", "iteration_id")}
        for k, v in data.items():
            if v is not None:
                merged[k] = v
        # If project_id or version_id changes, iteration_id is no longer valid — clear it to avoid false mismatch
        if data.get("project_id") is not None or data.get("version_id") is not None:
            merged["iteration_id"] = None
        _validate_plan_scope(merged, self.db)
        for key, value in data.items():
            if value is not None:
                setattr(existing, key, value)
        self.db.commit()
        self.db.refresh(existing)
        return self._serialize_plan(existing)

    def delete_plan(self, plan_id: int) -> bool:
        plan = self.db.query(TestPlan).filter(TestPlan.id == plan_id).first()
        if not plan:
            return False
        self.db.delete(plan)
        self.db.commit()
        return True

    # ── TestSuite ─────────────────────────────────────────────────

    def delete_suite(self, suite_id: int) -> bool:
        suite = self.db.query(TestSuite).filter(TestSuite.id == suite_id).first()
        if not suite:
            return False
        self.db.delete(suite)
        self.db.commit()
        return True

    def list_suites(self, plan_id: int) -> List[Dict[str, Any]]:
        plan = self.db.query(TestPlan).filter(TestPlan.id == plan_id).first()
        if not plan:
            return []
        suites = self.db.query(TestSuite).filter(TestSuite.plan_id == plan_id).order_by(TestSuite.sort_order).all()
        return [self._serialize_suite(s, include_items=True) for s in suites]

    def create_suite(self, data: Dict[str, Any]) -> Dict[str, Any]:
        plan_id = data.get("plan_id")
        plan = self.db.query(TestPlan).filter(TestPlan.id == plan_id).first()
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")
        suite = TestSuite(**data)
        self.db.add(suite)
        self.db.commit()
        self.db.refresh(suite)
        return self._serialize_suite(suite)

    def update_suite(self, suite_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        suite = self.db.query(TestSuite).filter(TestSuite.id == suite_id).first()
        if not suite:
            return None
        for key, value in data.items():
            if value is not None:
                setattr(suite, key, value)
        self.db.commit()
        self.db.refresh(suite)
        return self._serialize_suite(suite)

    # ── TestSuiteItem ─────────────────────────────────────────────

    def add_suite_item(self, data: Dict[str, Any]) -> Dict[str, Any]:
        suite_id = data.get("suite_id")
        suite = self.db.query(TestSuite).filter(TestSuite.id == suite_id).first()
        if not suite:
            raise ValueError(f"Suite {suite_id} not found")
        item = TestSuiteItem(**data)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return self._serialize_item(item)

    def remove_suite_item(self, item_id: int) -> bool:
        item = self.db.query(TestSuiteItem).filter(TestSuiteItem.id == item_id).first()
        if not item:
            return False
        self.db.delete(item)
        self.db.commit()
        return True

    # ── TestPlanRun ───────────────────────────────────────────────

    def list_runs(
        self,
        plan_id: Optional[int] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        query = self.db.query(TestPlanRun)
        if plan_id:
            query = query.filter(TestPlanRun.plan_id == plan_id)
        if status:
            query = query.filter(TestPlanRun.status == status)

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(TestPlanRun.started_at.desc()).offset(offset).limit(page_size).all()
        return [self._serialize_run(r) for r in items], total

    def get_run(self, run_id: int) -> Optional[Dict[str, Any]]:
        run = self.db.query(TestPlanRun).filter(TestPlanRun.id == run_id).first()
        if not run:
            return None
        return self._serialize_run(run)

    # ── Serialization ─────────────────────────────────────────────

    def _serialize_plan(self, plan: TestPlan, include_suites: bool = False) -> Dict[str, Any]:
        result = {
            "id": plan.id,
            "project_id": plan.project_id,
            "version_id": plan.version_id,
            "iteration_id": plan.iteration_id,
            "name": plan.name,
            "description": plan.description or "",
            "status": plan.status or "draft",
            "owner_id": plan.owner_id,
            "created_at": plan.created_at.isoformat() if plan.created_at else "",
            "updated_at": plan.updated_at.isoformat() if plan.updated_at else "",
        }
        if include_suites:
            result["suites"] = [self._serialize_suite(s, include_items=True) for s in (plan.suites or [])]
        return result

    def _serialize_suite(self, suite: TestSuite, include_items: bool = False) -> Dict[str, Any]:
        result = {
            "id": suite.id,
            "plan_id": suite.plan_id,
            "name": suite.name,
            "description": suite.description or "",
            "sort_order": suite.sort_order or 0,
        }
        if include_items:
            result["items"] = [self._serialize_item(i) for i in (suite.items or [])]
        return result

    def _serialize_item(self, item: TestSuiteItem) -> Dict[str, Any]:
        """Serialize a suite item, resolving name from DB via self.db."""
        item_name = None
        if item.item_type == "case":
            case = self.db.query(TestCase).filter(TestCase.id == item.item_id).first()
            item_name = case.name if case else None
        elif item.item_type == "scenario":
            scenario = self.db.query(Scenario).filter(Scenario.id == item.item_id).first()
            item_name = scenario.name if scenario else None

        return {
            "id": item.id,
            "suite_id": item.suite_id,
            "item_type": item.item_type,
            "item_id": item.item_id,
            "item_name": item_name,
            "sort_order": item.sort_order or 0,
        }

    @staticmethod
    def _serialize_run(run: TestPlanRun) -> Dict[str, Any]:
        summary = run.summary
        if isinstance(summary, str):
            try:
                summary = json.loads(summary)
            except Exception:
                summary = {}
        return {
            "id": run.id,
            "plan_id": run.plan_id,
            "status": run.status,
            "total": run.total or 0,
            "passed": run.passed or 0,
            "failed": run.failed or 0,
            "skipped": run.skipped or 0,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            "duration_ms": run.duration_ms,
            "summary": summary,
        }


# ── Standalone background task ────────────────────────────────────────────────

def _run_test_plan_background(run_id: int, plan_id: int) -> None:
    """
    Execute all items in a test plan sequentially.
    Creates its own DB session to avoid session lifetime issues.
    """
    import httpx

    from app.database import SessionLocal
    from app.models.test_plan import TestPlan, TestSuite, TestSuiteItem, TestPlanRun
    from app.models.test_case import TestCase
    from app.models.scenario import Scenario

    db = SessionLocal()
    try:
        plan = db.query(TestPlan).filter(TestPlan.id == plan_id).first()
        if not plan:
            _update_run_status(db, run_id, status="failed", summary={"error": "Plan not found"})
            return

        suites = db.query(TestSuite).filter(TestSuite.plan_id == plan_id).order_by(TestSuite.sort_order).all()
        all_items: List[TestSuiteItem] = []
        for suite in suites:
            items = db.query(TestSuiteItem).filter(TestSuiteItem.suite_id == suite.id).order_by(TestSuiteItem.sort_order).all()
            all_items.extend(items)

        if not all_items:
            _update_run_status(db, run_id, status="failed", summary={"total": 0, "executed": 0, "passed": 0, "failed": 0, "error": "No items found"})
            return

        summary = {"total": len(all_items), "executed": 0, "passed": 0, "failed": 0, "skipped": 0, "running": 0, "items": []}
        start_time = datetime.utcnow()

        for item in all_items:
            item_result = {"item_id": item.id, "item_type": item.item_type, "item_id_ref": item.item_id, "status": "passed"}

            try:
                if item.item_type == "case":
                    case = db.query(TestCase).filter(TestCase.id == item.item_id).first()
                    if not case:
                        item_result["status"] = "failed"
                        item_result["error"] = f"Case {item.item_id} not found"
                        summary["failed"] += 1
                    else:
                        # Execute via terminal internal endpoint
                        with httpx.Client(timeout=30) as client:
                            resp = client.post(
                                "http://localhost:8000/api/terminal/internal/run",
                                json={
                                    "method": case.method or "GET",
                                    "url": case.url or "",
                                    "headers": _safe_json_loads(case.headers, {}),
                                    "query_params": _safe_json_loads(case.query_params, {}),
                                    "body_type": case.body_type or "none",
                                    "body": case.body or "",
                                    "auth_config": _safe_json_loads(case.auth_config, {}),
                                },
                            )
                            item_result["response_status"] = resp.status_code
                            if resp.status_code == 200:
                                result_data = resp.json()
                                # Determine pass/fail from JSON status, not just HTTP code
                                status_code = result_data.get("status_code", 0)
                                error_msg = result_data.get("error")
                                if error_msg or status_code >= 400:
                                    item_result["status"] = "failed"
                                    item_result["error"] = error_msg or f"HTTP {status_code}"
                                    summary["failed"] += 1
                                else:
                                    item_result["status"] = "passed"
                                    item_result["duration_ms"] = result_data.get("duration_ms")
                                    summary["passed"] += 1
                            else:
                                item_result["status"] = "failed"
                                item_result["error"] = f"HTTP {resp.status_code}"
                                summary["failed"] += 1

                elif item.item_type == "scenario":
                    scenario = db.query(Scenario).filter(Scenario.id == item.item_id).first()
                    if not scenario:
                        item_result["status"] = "failed"
                        item_result["error"] = f"Scenario {item.item_id} not found"
                        summary["failed"] += 1
                    else:
                        # Trigger scenario execution via API — returns run_id immediately
                        with httpx.Client(timeout=60) as client:
                            resp = client.post(f"http://localhost:8000/api/scenario/{item.item_id}/run")
                            if resp.status_code == 200:
                                run_data = resp.json()
                                run_id_ref = run_data.get("id")
                                # Record as running; first phase does not await completion
                                # Do NOT count as passed until confirmed complete
                                item_result["status"] = "running"
                                item_result["run_id"] = run_id_ref
                                summary["running"] += 1
                            else:
                                item_result["status"] = "failed"
                                item_result["error"] = f"HTTP {resp.status_code}"
                                summary["failed"] += 1

                else:
                    item_result["status"] = "skipped"
                    summary["skipped"] += 1

            except Exception as e:
                item_result["status"] = "failed"
                item_result["error"] = str(e)
                summary["failed"] += 1

            summary["executed"] += 1
            summary["items"].append(item_result)

        finished_at = datetime.utcnow()
        duration_ms = int((finished_at - start_time).total_seconds() * 1000)
        # If there are still running items with no failures, status is "running", not "passed"
        if summary["running"] > 0 and summary["failed"] == 0:
            final_status = "running"
        elif summary["failed"] > 0:
            final_status = "failed"
        else:
            final_status = "passed"

        # Update run record
        run = db.query(TestPlanRun).filter(TestPlanRun.id == run_id).first()
        if run:
            run.status = final_status
            run.total = summary["total"]
            run.passed = summary["passed"]
            run.failed = summary["failed"]
            run.skipped = summary["skipped"]
            run.started_at = start_time
            run.finished_at = finished_at
            run.duration_ms = duration_ms
            run.summary = json.dumps(summary)
            db.commit()

    except Exception as e:
        _update_run_status(db, run_id, status="failed", summary={"error": str(e)})
    finally:
        db.close()


def _update_run_status(db, run_id: int, status: str, summary: Dict[str, Any]) -> None:
    """Update test plan run status."""
    from datetime import datetime
    run = db.query(TestPlanRun).filter(TestPlanRun.id == run_id).first()
    if run:
        run.status = status
        run.summary = json.dumps(summary)
        run.finished_at = datetime.utcnow()
        db.commit()