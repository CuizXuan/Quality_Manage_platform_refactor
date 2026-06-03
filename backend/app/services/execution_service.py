import json
from typing import Dict, Optional, Tuple

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.models.execution_asset import RunArtifact, RunStepLog, UnifiedRun, UnifiedRunItem
from app.models.scenario import ExecutionRun
from app.models.test_plan import TestPlanRun
from app.services.scenario_service import ScenarioService, _run_scenario_background
from app.services.test_plan_service import TestPlanService, _run_test_plan_background


def _loads(value: str, fallback):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


class ExecutionService:
    def __init__(self, db: Session):
        self.db = db

    def list_runs(
        self,
        page: int = 1,
        page_size: int = 20,
        target_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Tuple[list[Dict], int]:
        query = self.db.query(UnifiedRun)
        if target_type:
            query = query.filter(UnifiedRun.target_type == target_type)
        if status:
            query = query.filter(UnifiedRun.status == status)
        total = query.count()
        items = (
            query.order_by(UnifiedRun.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return [self.serialize_run(item) for item in items], total

    def get_run(self, run_id: int) -> Optional[Dict]:
        run = self.db.query(UnifiedRun).filter(UnifiedRun.id == run_id).first()
        if not run:
            return None
        self._sync_run_from_source(run)
        self.db.refresh(run)
        return self.serialize_run(run)

    def create_run(self, data: dict, background_tasks: BackgroundTasks) -> Dict:
        target_type = data["target_type"]
        target_id = data["target_id"]
        run = UnifiedRun(
            run_type=data.get("run_type", "manual"),
            target_type=target_type,
            target_id=target_id,
            project_id=data.get("project_id"),
            environment_id=data.get("environment_id"),
            status="queued",
            queue_status="queued",
            summary=json.dumps({}, ensure_ascii=False),
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)

        if target_type == "scenario":
            scenario_run = ScenarioService(self.db).start_execution(target_id, data.get("environment_id"))
            if not scenario_run:
                raise ValueError("Scenario not found")
            run.source_run_id = scenario_run["id"]
            run.status = "running"
            run.queue_status = "running"
            self.db.add(
                UnifiedRunItem(
                    run_id=run.id,
                    item_type="scenario",
                    item_id=target_id,
                    item_name=scenario_run.get("scenario_name") or f"Scenario #{target_id}",
                    status="running",
                )
            )
            background_tasks.add_task(_run_scenario_background, scenario_run["id"], target_id)
        elif target_type == "plan":
            plan = TestPlanService(self.db).get_plan(target_id)
            if not plan:
                raise ValueError("Plan not found")
            plan_run = TestPlanRun(plan_id=target_id, status="running")
            self.db.add(plan_run)
            self.db.commit()
            self.db.refresh(plan_run)
            run.source_run_id = plan_run.id
            run.status = "running"
            run.queue_status = "running"
            for suite in plan.get("suites", []):
                for item in suite.get("items", []):
                    self.db.add(
                        UnifiedRunItem(
                            run_id=run.id,
                            item_type=item["item_type"],
                            item_id=item["item_id"],
                            item_name=item.get("item_name") or f"{item['item_type']} #{item['item_id']}",
                            status="queued",
                            sort_order=item.get("sort_order", 0),
                        )
                    )
            background_tasks.add_task(_run_test_plan_background, plan_run.id, target_id)
        else:
            raise ValueError("Unsupported target type")

        self.db.commit()
        self.db.refresh(run)
        return self.serialize_run(run)

    def cancel_run(self, run_id: int) -> Optional[Dict]:
        run = self.db.query(UnifiedRun).filter(UnifiedRun.id == run_id).first()
        if not run:
            return None
        run.status = "stopped"
        run.queue_status = "stopped"
        self.db.commit()
        self.db.refresh(run)
        return self.serialize_run(run)

    def rerun_failed(self, run_id: int) -> Optional[Dict]:
        run = self.db.query(UnifiedRun).filter(UnifiedRun.id == run_id).first()
        if not run:
            return None
        return self.serialize_run(run)

    def list_artifacts(self, run_id: int) -> list[Dict]:
        artifacts = self.db.query(RunArtifact).filter(RunArtifact.run_id == run_id).order_by(RunArtifact.id.desc()).all()
        return [
            {
                "id": artifact.id,
                "artifact_type": artifact.artifact_type,
                "artifact_name": artifact.artifact_name,
                "payload": _loads(artifact.payload, {}),
            }
            for artifact in artifacts
        ]

    def _sync_run_from_source(self, run: UnifiedRun) -> None:
        if run.target_type == "scenario" and run.source_run_id:
            source_run = self.db.query(ExecutionRun).filter(ExecutionRun.id == run.source_run_id).first()
            if source_run:
                summary = _loads(source_run.summary, {})
                run.status = source_run.status
                run.queue_status = "finished" if source_run.finished_at else "running"
                run.started_at = source_run.started_at
                run.finished_at = source_run.finished_at
                run.duration_ms = source_run.duration_ms
                run.summary = json.dumps(summary, ensure_ascii=False)
                item = run.items[0] if run.items else None
                if item:
                    item.status = source_run.status
                    item.summary = json.dumps(summary, ensure_ascii=False)
                self._sync_logs_for_scenario(run, summary)
        elif run.target_type == "plan" and run.source_run_id:
            source_run = self.db.query(TestPlanRun).filter(TestPlanRun.id == run.source_run_id).first()
            if source_run:
                summary = _loads(source_run.summary, {})
                run.status = source_run.status
                run.queue_status = "finished" if source_run.finished_at else "running"
                run.started_at = source_run.started_at
                run.finished_at = source_run.finished_at
                run.duration_ms = source_run.duration_ms
                run.summary = json.dumps(summary, ensure_ascii=False)
                self._sync_items_for_plan(run, summary)

    def _sync_logs_for_scenario(self, run: UnifiedRun, summary: dict) -> None:
        item = run.items[0] if run.items else None
        if not item:
            return
        existing_names = {log.step_name for log in item.step_logs}
        for step in summary.get("steps", []):
            name = step.get("name") or f"Step #{step.get('step_id')}"
            if name in existing_names:
                continue
            self.db.add(
                RunStepLog(
                    run_item_id=item.id,
                    step_name=name,
                    status=step.get("status", "unknown"),
                    request_snapshot=json.dumps({"case_id": step.get("case_id")}, ensure_ascii=False),
                    response_snapshot=json.dumps({"response_status": step.get("response_status")}, ensure_ascii=False),
                    variable_snapshot=json.dumps({}, ensure_ascii=False),
                    assertion_snapshot=json.dumps([], ensure_ascii=False),
                    error_message=step.get("error", ""),
                )
            )
        if summary and not run.artifacts:
            self.db.add(
                RunArtifact(
                    run_id=run.id,
                    artifact_type="scenario_summary",
                    artifact_name="Scenario Summary",
                    payload=json.dumps(summary, ensure_ascii=False),
                )
            )
        self.db.commit()

    def _sync_items_for_plan(self, run: UnifiedRun, summary: dict) -> None:
        item_map = {(item.item_type, item.item_id): item for item in run.items}
        for result in summary.get("items", []):
            item_type = result.get("item_type")
            item_id = result.get("item_id_ref")
            item = item_map.get((item_type, item_id))
            if not item:
                continue
            item.status = result.get("status", item.status)
            item.summary = json.dumps(result, ensure_ascii=False)
        if summary and not run.artifacts:
            self.db.add(
                RunArtifact(
                    run_id=run.id,
                    artifact_type="plan_summary",
                    artifact_name="Plan Summary",
                    payload=json.dumps(summary, ensure_ascii=False),
                )
            )
        self.db.commit()

    def serialize_run(self, run: UnifiedRun) -> Dict:
        return {
            "id": run.id,
            "run_type": run.run_type,
            "target_type": run.target_type,
            "target_id": run.target_id,
            "project_id": run.project_id,
            "environment_id": run.environment_id,
            "source_run_id": run.source_run_id,
            "status": run.status,
            "queue_status": run.queue_status,
            "summary": _loads(run.summary, {}),
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            "duration_ms": run.duration_ms,
            "items": [
                {
                    "id": item.id,
                    "item_type": item.item_type,
                    "item_id": item.item_id,
                    "item_name": item.item_name,
                    "status": item.status,
                    "sort_order": item.sort_order,
                    "summary": _loads(item.summary, {}),
                    "step_logs": [
                        {
                            "id": log.id,
                            "step_name": log.step_name,
                            "status": log.status,
                            "request_snapshot": _loads(log.request_snapshot, {}),
                            "response_snapshot": _loads(log.response_snapshot, {}),
                            "assertion_snapshot": _loads(log.assertion_snapshot, []),
                            "variable_snapshot": _loads(log.variable_snapshot, {}),
                            "error_message": log.error_message or "",
                        }
                        for log in item.step_logs
                    ],
                }
                for item in run.items
            ],
        }
