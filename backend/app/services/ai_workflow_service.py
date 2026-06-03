"""AIWorkflowService — 多 Agent 编排工作流服务层。

一期实现：
- workflow_type = requirement_to_test_design
- step 1 = requirement-analyst
- step 2 = test-designer
- 顺序执行、上下文传递、状态记录、错误处理。

二期新增：
- 人工触发的工作流结果采纳：
  - 需求条目写入 requirement_items
  - 功能/接口用例草稿写入 test_cases
  - 建立用例到需求的 requirement_id 关联

三期新增：
- 采纳幂等：默认阻止重复采纳，force=True 时放行
- adoption 状态写回 run.result_payload，含累计 force_adoption_count 与累计 ID
- force 路径下对 requirement_items.source_key 做去重，避免重复入库

四期新增：
- workflow 第三步 scenario-designer：基于 test-designer 输出组织场景草稿
- 场景采纳写入 scenarios / scenario_steps，步骤通过 case_id / case_index /
  case_name / name 反查 test_cases.id；至少一个 step 能解析才落库
"""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.ai import AIWorkflowRun, AIWorkflowStep
from app.models.report import Report
from app.models.scenario import ExecutionRun, Scenario
from app.repositories.ai_repository import AIRepository
from app.services.ai_agent_service import AIAgentService
from app.services.ai_service import AIService
from app.services.quality_foundation_service import create_requirement
from app.services.scenario_service import ScenarioService, _run_scenario_background
from app.services.test_case_service import TestCaseService
from app.schemas.quality_foundation import RequirementItemCreate

try:
    from app.models.test_case import TestCase
except Exception:  # pragma: no cover - 防止模型层未注册时导入失败
    TestCase = None  # type: ignore[assignment]


class AIWorkflowService:
    def __init__(self, db: Session, ai_service: Optional[AIService]):
        self.db = db
        self.ai_service = ai_service
        self.agent_service = AIAgentService(db, ai_service)

    def start_requirement_to_test_design(
        self,
        payload: Dict[str, Any],
        created_by: Optional[int] = None,
        existing_run: Optional["AIWorkflowRun"] = None,
    ) -> Dict[str, Any]:
        """启动需求到测试设计工作流。

        三步 Agent：
          1. requirement-analyst
          2. test-designer
          3. scenario-designer

        返回值包含完整 run 与 steps 列表。

        ``existing_run`` 异步化路径使用: 复用已创建的 run row,跳过 ``_create_run``。
        """
        if existing_run is not None:
            run = existing_run
            run.status = "running"
            run.current_step = "requirement-analyst"
            self.db.commit()
            self.db.refresh(run)
        else:
            run = self._create_run(payload, created_by)
            # 老路径: 同步入口,确保 status 由 pending 推进到 running
            run.status = "running"
            run.current_step = "requirement-analyst"
            self.db.commit()
            self.db.refresh(run)
        requirement_step = self._run_step(
            run=run,
            step_order=1,
            agent_type="requirement-analyst",
            input_payload=self._build_requirement_step_input(payload),
        )
        requirement_output = self._suggestion_payload(requirement_step)
        if requirement_step.get("status") == "failed":
            return self._serialize_run(run, error="需求分析步骤失败")

        design_step = self._run_step(
            run=run,
            step_order=2,
            agent_type="test-designer",
            input_payload=self._build_design_step_input(payload, requirement_output, requirement_step),
        )
        design_output = self._suggestion_payload(design_step)
        if design_step.get("status") == "failed":
            return self._serialize_run(run, error="测试设计步骤失败")

        scenario_step = self._run_step(
            run=run,
            step_order=3,
            agent_type="scenario-designer",
            input_payload=self._build_scenario_step_input(
                payload, requirement_output, design_output, design_step
            ),
        )
        scenario_output = self._suggestion_payload(scenario_step)
        if scenario_step.get("status") == "failed":
            return self._serialize_run(run, error="场景设计步骤失败")

        return self._finish_run(
            run,
            requirement_output,
            design_output,
            scenario_output,
            original_payload=payload,
        )

    def get_run(self, run_id: int) -> Optional[Dict[str, Any]]:
        run = self.db.query(AIWorkflowRun).filter(AIWorkflowRun.id == run_id).first()
        if not run:
            return None
        return self._serialize_run(run)

    # ── 七期 A：按业务来源查询 / 从需求启动 ──────────────────────────────

    def list_workflows_by_source(
        self,
        origin_module: str,
        origin_type: str,
        origin_id: int,
        limit: int = 5,
    ) -> Dict[str, Any]:
        """按业务来源返回最近 N 个 workflow run。

        - 不新增表 / 索引；解析 ``input_payload`` 中的 ``origin_*`` 字段。
        - 找不到记录时返回 ``{"items": [], "total": 0}``，不要 404。
        - ``limit`` 钳制到 ``[1, 20]``。
        - 排序：``updated_at`` 倒序（兜底 ``created_at`` 倒序）。
        """
        safe_limit = max(1, min(int(limit or 5), 20))
        if not origin_module or not origin_type or not origin_id:
            return {"items": [], "total": 0}
        # 全表扫 → 内存过滤；现有 ai_workflow_runs 数据量级（百级），不引入索引
        all_runs = (
            self.db.query(AIWorkflowRun)
            .order_by(AIWorkflowRun.updated_at.desc(), AIWorkflowRun.created_at.desc())
            .all()
        )
        matched: List[AIWorkflowRun] = []
        for run in all_runs:
            input_payload = self._safe_json_loads(run.input_payload, {})
            if not input_payload:
                continue
            if input_payload.get("origin_module") != origin_module:
                continue
            if input_payload.get("origin_type") != origin_type:
                continue
            origin_ids = input_payload.get("origin_ids") or []
            try:
                if int(origin_id) not in {int(x) for x in origin_ids}:
                    continue
            except (TypeError, ValueError):
                continue
            matched.append(run)
        sliced = matched[:safe_limit]
        items = [self._serialize_run(run) for run in sliced]
        return {"items": items, "total": len(matched)}

    def start_workflow_from_requirements(
        self,
        payload: Dict[str, Any],
        created_by: Optional[int] = None,
    ) -> Dict[str, Any]:
        """从 ``requirement_items`` 启动 ``requirement_to_test_design`` workflow(同步入口)。

        行为：
        1. ``requirement_ids`` 缺一不可，少 1 个 / 超过 20 个直接 400（在 schema 层约束）。
        2. 缺失需求 ID → 返回 ``{"error": {"code": "REQUIREMENT_NOT_FOUND", ...}}``。
        3. 跨 project_id → 返回 ``{"error": {"code": "REQUIREMENT_PROJECT_MISMATCH", ...}}``。
        4. 组装 ``source_name`` / ``content`` 后复用 ``start_requirement_to_test_design``。
        5. 不采纳结果，不写入用例 / 场景。
        """
        workflow_payload, validation_error = self._build_requirements_workflow_payload(
            payload, db=self.db
        )
        if validation_error is not None:
            return validation_error
        return self.start_requirement_to_test_design(
            workflow_payload, created_by=created_by
        )

    def create_workflow_run_from_requirements(
        self,
        payload: Dict[str, Any],
        created_by: Optional[int] = None,
    ) -> Dict[str, Any]:
        """异步入口第一步: 仅做业务校验 + 创建 run row, 不执行 LLM。

        行为与 ``start_workflow_from_requirements`` 一致, 但在 run 创建后立即返回,
        后续三步 Agent 由 router 用 BackgroundTasks 派发 ``execute_workflow_steps_async``。

        返回值:
            - 业务校验失败: ``{"error": {"code": ..., "message": ...}}``
            - 成功: ``_serialize_run`` dict(``status="pending"``, ``steps=[]``)
        """
        workflow_payload, validation_error = self._build_requirements_workflow_payload(
            payload, db=self.db
        )
        if validation_error is not None:
            return validation_error
        run = self._create_run(workflow_payload, created_by)
        return self._serialize_run(run)

    @staticmethod
    def _build_requirements_workflow_payload(
        payload: Dict[str, Any],
        db: Session,
    ) -> tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """共享业务校验 + payload 装配逻辑, 返回 ``(workflow_payload, None)`` 或 ``(None, error)``。"""
        from app.models.quality_foundation import RequirementItem

        requirement_ids: List[int] = list(payload.get("requirement_ids") or [])
        analysis_focus: List[str] = list(payload.get("analysis_focus") or [])
        if not requirement_ids:
            return None, AIWorkflowService._from_requirements_error(
                "REQUIREMENT_NOT_FOUND",
                "未提供任何需求 ID",
            )

        # 去重, 保持首次出现顺序, 避免同一需求重复加载
        seen = set()
        unique_ids: List[int] = []
        for rid in requirement_ids:
            try:
                item_id = int(rid)
            except (TypeError, ValueError):
                continue
            if item_id in seen:
                continue
            seen.add(item_id)
            unique_ids.append(item_id)

        rows = (
            db.query(RequirementItem)
            .filter(RequirementItem.id.in_(unique_ids))
            .all()
        )
        found_ids = {int(row.id) for row in rows}
        missing = [rid for rid in unique_ids if rid not in found_ids]
        if missing:
            return None, AIWorkflowService._from_requirements_error(
                "REQUIREMENT_NOT_FOUND",
                f"以下需求 ID 不存在：{', '.join(str(x) for x in missing)}",
            )

        project_ids = {int(row.project_id) for row in rows if row.project_id is not None}
        if len(project_ids) > 1:
            return None, AIWorkflowService._from_requirements_error(
                "REQUIREMENT_PROJECT_MISMATCH",
                "所选需求不属于同一个 project_id, 无法统一启动 workflow",
            )

        # version_id / iteration_id 取首个非空值; 不一致情况不强行报错, 写入 origin_meta
        project_id = next(iter(project_ids)) if project_ids else None
        version_id = next(
            (int(row.version_id) for row in rows if row.version_id is not None),
            None,
        )
        iteration_id = next(
            (int(row.iteration_id) for row in rows if row.iteration_id is not None),
            None,
        )

        version_ids = {int(row.version_id) for row in rows if row.version_id is not None}
        iteration_ids = {int(row.iteration_id) for row in rows if row.iteration_id is not None}
        origin_meta: Dict[str, Any] = {
            "requirement_count": len(rows),
            "titles": [
                (row.title or "").strip()[:200] for row in rows[:5]
            ],
        }
        if len(version_ids) > 1:
            origin_meta["version_ids_inconsistent"] = sorted(version_ids)
        if len(iteration_ids) > 1:
            origin_meta["iteration_ids_inconsistent"] = sorted(iteration_ids)

        content = AIWorkflowService._render_requirements_content(rows)
        source_name = f"需求管理：{len(rows)} 条需求"

        workflow_payload: Dict[str, Any] = {
            "source_name": source_name,
            "source_type": "requirement_item",
            "content": content,
            "project_id": project_id,
            "version_id": version_id,
            "iteration_id": iteration_id,
            "analysis_focus": analysis_focus,
            "origin_module": "requirement",
            "origin_type": "requirement_item",
            "origin_ids": unique_ids,
            "origin_meta": origin_meta,
        }
        return workflow_payload, None

    @staticmethod
    def _resolve_async_workflow_payload(
        payload: Dict[str, Any],
        stored_input: Dict[str, Any],
        db: Session,
    ) -> tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """异步入口重建完整 workflow payload。

        两种入口需要兼容:
            - from-requirements 路由: 原始 payload 只含 ``requirement_ids`` + ``analysis_focus``,
              缺 ``content/source_name/project_id/...``,必须用后台 session 重新调
              ``_build_requirements_workflow_payload`` 构造完整字段再传给 Agent.
            - 直接传 ``workflow_payload`` 入口: payload 已含 content, 合并 ``origin_*`` 兜底即可.

        返回 ``(workflow_payload, None)`` 成功; ``(None, error_dict)`` 失败.
        失败时调用方应把 run 标记 failed, 不应继续用空 payload 跑 Agent.
        """
        if (payload or {}).get("requirement_ids") and not (payload or {}).get("content"):
            workflow_payload, validation_error = (
                AIWorkflowService._build_requirements_workflow_payload(payload, db)
            )
            if validation_error is not None:
                return None, validation_error
            return workflow_payload, None

        merged = dict(payload or {})
        for key in ("origin_module", "origin_type", "origin_ids", "origin_meta"):
            if key in stored_input and key not in merged:
                merged[key] = stored_input[key]
        return merged, None

    @staticmethod
    def execute_workflow_steps_async(
        run_id: int,
        payload: Dict[str, Any],
        created_by: Optional[int] = None,
    ) -> None:
        """异步执行 workflow 三步 Agent. 由 FastAPI BackgroundTasks 派发。

        生命周期:
            1. 自行创建 db session (router 的 session 已 close, 不能复用)
            2. 加载已创建的 run row, 复用而不重建
            3. 用 ``_resolve_async_workflow_payload`` 重建完整 workflow payload
               (含 content/source_name/project_id/version_id/iteration_id/origin_*)
            4. 重建失败时把 run 写 status='failed' + 业务 error, 不继续空跑 Agent
            5. 调 ``start_requirement_to_test_design(payload, created_by, existing_run=run)`` 跑三步
            6. ``_finish_run`` / ``_fail_step`` 内部已写 status='completed' / 'failed'
            7. 异常兜底: 写 status='failed' + error_message, 避免 run 永远 running
        """
        from app.database import SessionLocal
        from app.repositories.ai_repository import AIRepository

        db = SessionLocal()
        try:
            run = db.get(AIWorkflowRun, run_id)
            if not run:
                return
            stored_input = AIWorkflowService._safe_json_loads(run.input_payload, {})
            workflow_payload, validation_error = (
                AIWorkflowService._resolve_async_workflow_payload(payload, stored_input, db)
            )
            if validation_error is not None:
                run.status = "failed"
                run.current_step = "failed:async_payload_rebuild"
                # 解一层 error, 保持与 ``start_workflow_from_requirements`` 同步错误格式一致
                error_detail = (
                    validation_error.get("error")
                    if isinstance(validation_error, dict)
                    else {"code": "PAYLOAD_REBUILD_FAILED", "message": str(validation_error)}
                )
                run.result_payload = json.dumps(
                    {"error": error_detail, "trace": "async_payload_rebuild"},
                    ensure_ascii=False,
                )
                run.finished_at = datetime.utcnow()
                run.updated_at = datetime.utcnow()
                db.commit()
                return
            config = AIRepository.get_config(db)
            ai_service = AIService(config) if config else None
            svc = AIWorkflowService(db, ai_service)
            svc.start_requirement_to_test_design(
                workflow_payload, created_by=created_by, existing_run=run
            )
        except Exception as exc:
            # 兜底: 后台任务 crash 时把 run 写为 failed, 避免永远 running
            try:
                run = db.get(AIWorkflowRun, run_id)
                if run is not None:
                    run.status = "failed"
                    run.current_step = f"failed:async_dispatch"
                    run.result_payload = json.dumps(
                        {"error": f"async dispatch: {str(exc)[:800]}"},
                        ensure_ascii=False,
                    )
                    run.finished_at = datetime.utcnow()
                    run.updated_at = datetime.utcnow()
                    db.commit()
            except Exception:  # noqa: BLE001
                db.rollback()
        finally:
            db.close()

    @staticmethod
    def _from_requirements_error(code: str, message: str) -> Dict[str, Any]:
        return {
            "error": {"code": code, "message": message},
        }

    @staticmethod
    def _render_requirements_content(rows: List[Any]) -> str:
        """把多条需求渲染成 ``content`` 文本，可读且不为空。"""
        lines: List[str] = []
        for row in rows:
            title = (row.title or "").strip()
            description = (row.description or "").strip()
            source_key = (row.source_key or "").strip()
            priority = (row.priority or "").strip()
            status = (row.status or "").strip()
            head = f"#{int(row.id)}"
            if source_key:
                head = f"{head} [{source_key}]"
            lines.append(f"{head} {title}".strip())
            meta_parts = [p for p in [priority, status] if p]
            if meta_parts:
                lines.append(f"  - 优先级/状态：{' / '.join(meta_parts)}")
            if description:
                lines.append(f"  - 描述：{description[:500]}")
        return "\n".join(lines) or "（无需求内容）"

    # ── Phase 5: Execution Planner ───────────────────────────────────────

    def plan_execution_for_workflow(
        self,
        run_id: int,
        request: Union[Dict[str, Any], Any],
        created_by: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """生成执行计划。**不会**启动 execution_runs。

        返回值结构：
            None                — run 不存在
            {"error": ...}      — 状态/类型/无场景等
            {"run_id": ..., "suggestion_id": ..., "payload": ...}
        """
        run = self.db.query(AIWorkflowRun).filter(AIWorkflowRun.id == run_id).first()
        if not run:
            return None
        if run.workflow_type != "requirement_to_test_design":
            return self._execution_plan_error(
                run_id=run_id,
                code="WORKFLOW_TYPE_MISMATCH",
                message=f"当前工作流类型 {run.workflow_type} 不支持执行计划",
            )
        if run.status != "completed":
            return self._execution_plan_error(
                run_id=run_id,
                code="WORKFLOW_NOT_COMPLETED",
                message=f"工作流状态 {run.status}，仅 completed 可生成执行计划",
            )

        params = self._coerce_execution_plan_request(request)
        result_payload = self._safe_json_loads(run.result_payload, {})
        adoption = result_payload.get("adoption") or {}
        cumulative_scenario_ids = list(adoption.get("cumulative_scenario_ids") or [])

        # 显式 scenario_ids 与累计取交集，避免执行非本 workflow 采纳的场景
        if params["scenario_ids"]:
            requested = {int(s) for s in params["scenario_ids"] if s is not None}
            allowed_ids = sorted(requested & set(cumulative_scenario_ids))
        else:
            allowed_ids = list(cumulative_scenario_ids)

        if not allowed_ids:
            return self._execution_plan_error(
                run_id=run_id,
                code="WORKFLOW_NO_SCENARIOS",
                message="本工作流累计采纳的场景为空，无法生成执行计划",
            )

        # 从业务表查询场景详情
        scenario_objs = (
            self.db.query(Scenario)
            .filter(Scenario.id.in_(allowed_ids))
            .all()
        )
        scenario_payloads = [self._scenario_to_planner_payload(s) for s in scenario_objs]

        plan_input = {
            "scenarios": scenario_payloads,
            "allowed_scenario_ids": allowed_ids,
            "environment_id": params["environment_id"],
        }
        suggestion = self.agent_service.run_plan_execution(
            plan_input, created_by=created_by
        )
        plan_payload = suggestion.get("payload") or {}

        execution_plan_entry = {
            "suggestion_id": suggestion.get("suggestion_id"),
            "agent_type": suggestion.get("agent_type", "execution-planner"),
            "status": "pending_confirm",
            "payload": plan_payload,
        }
        result_payload["execution_plan"] = execution_plan_entry
        run.result_payload = json.dumps(result_payload, ensure_ascii=False)
        run.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(run)

        return {
            "run_id": run_id,
            "suggestion_id": suggestion.get("suggestion_id"),
            "agent_type": suggestion.get("agent_type", "execution-planner"),
            "status": "pending_confirm",
            "payload": plan_payload,
        }

    def confirm_execution_plan_for_workflow(
        self,
        run_id: int,
        request: Union[Dict[str, Any], Any],
        background_tasks=None,
        confirmed_by: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """人工确认执行计划，启动场景执行（创建 execution_runs）。

        返回值结构：
            None                 — run 不存在
            {"error": ...}       — 错误
            {"run_id": ..., "execution_run_ids": [...], ...}
        """
        run = self.db.query(AIWorkflowRun).filter(AIWorkflowRun.id == run_id).first()
        if not run:
            return None
        result_payload = self._safe_json_loads(run.result_payload, {})
        execution_plan = result_payload.get("execution_plan")
        if not isinstance(execution_plan, dict) or not execution_plan.get("payload"):
            return self._execution_confirm_error(
                run_id=run_id,
                code="WORKFLOW_EXECUTION_PLAN_MISSING",
                message="尚未生成执行计划，无法确认执行",
            )

        params = self._coerce_execution_confirm_request(request)
        plan_payload = execution_plan.get("payload") or {}
        batches = plan_payload.get("execution_batches") or []
        if not isinstance(batches, list) or not batches:
            return self._execution_confirm_error(
                run_id=run_id,
                code="WORKFLOW_EXECUTION_PLAN_MISSING",
                message="执行计划为空，无法启动",
            )

        # 收集 plan 内允许的 scenario_id 集合
        allowed_ids: set = set()
        for batch in batches:
            if not isinstance(batch, dict):
                continue
            for sid in batch.get("scenario_ids") or []:
                try:
                    allowed_ids.add(int(sid))
                except (TypeError, ValueError):
                    continue

        # 计算实际要执行的 scenario_id
        selected_ids: List[int]
        if params["batch_indexes"]:
            target_batches = [
                batches[i] for i in params["batch_indexes"] if 0 <= i < len(batches)
            ]
            selected_ids = []
            for batch in target_batches:
                if not isinstance(batch, dict):
                    continue
                for sid in batch.get("scenario_ids") or []:
                    try:
                        selected_ids.append(int(sid))
                    except (TypeError, ValueError):
                        continue
        elif params["scenario_ids"]:
            requested = {int(s) for s in params["scenario_ids"] if s is not None}
            selected_ids = sorted(requested & allowed_ids)
        else:
            selected_ids = sorted(allowed_ids)

        # 跨 batch / 显式 scenario_ids 可能出现同一 scenario_id 多次；
        # 必须在 TARGET_EMPTY 判断之前去重，避免重复创建 execution_runs
        selected_ids = self._unique_ints(selected_ids)

        if not selected_ids:
            return self._execution_confirm_error(
                run_id=run_id,
                code="WORKFLOW_EXECUTION_TARGET_EMPTY",
                message="计划内无可执行场景，请先生成执行计划或检查 batch 配置",
            )

        environment_id = params["environment_id"]
        service = ScenarioService(self.db)
        execution_run_ids: List[int] = []
        started_scenarios: List[int] = []
        for scenario_id in selected_ids:
            run_dict = service.start_execution(scenario_id, environment_id=environment_id)
            if not run_dict:
                continue
            execution_run_ids.append(int(run_dict["id"]))
            started_scenarios.append(scenario_id)
            if background_tasks is not None:
                background_tasks.add_task(
                    _run_scenario_background, run_dict["id"], scenario_id
                )

        if not execution_run_ids:
            return self._execution_confirm_error(
                run_id=run_id,
                code="WORKFLOW_EXECUTION_TARGET_EMPTY",
                message="未能创建任何 execution_runs",
            )

        confirmation_entry = {
            "status": "started",
            "confirmed_at": datetime.utcnow().isoformat() + "Z",
            "confirmed_by": confirmed_by,
            "environment_id": environment_id,
            "execution_run_ids": execution_run_ids,
            "scenario_ids": started_scenarios,
        }
        result_payload["execution_confirmation"] = confirmation_entry
        run.result_payload = json.dumps(result_payload, ensure_ascii=False)
        run.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(run)

        return {
            "run_id": run_id,
            "status": "started",
            "execution_run_ids": execution_run_ids,
            "scenario_ids": started_scenarios,
            "environment_id": environment_id,
        }

    # ── Phase 6: Execution Result Analyst ──────────────────────────────────

    def analyze_execution_results_for_workflow(
        self,
        run_id: int,
        request: Union[Dict[str, Any], Any],
        created_by: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """基于本 workflow 启动的 execution_runs 生成质量闭环分析。

        返回值结构：
            None                                         — run 不存在
            {"error": ..., "code": ...}                  — 业务校验失败
            {"run_id", "suggestion_id", "agent_type", "status", "payload"}
        """
        run = self.db.query(AIWorkflowRun).filter(AIWorkflowRun.id == run_id).first()
        if not run:
            return None
        if run.workflow_type != "requirement_to_test_design":
            return self._execution_analysis_error(
                run_id=run_id,
                code="WORKFLOW_TYPE_MISMATCH",
                message=f"当前工作流类型 {run.workflow_type} 不支持执行结果分析",
            )

        params = self._coerce_execution_analysis_request(request)
        result_payload = self._safe_json_loads(run.result_payload, {})
        confirmation = result_payload.get("execution_confirmation") or {}
        if not isinstance(confirmation, dict) or not confirmation.get("execution_run_ids"):
            return self._execution_analysis_error(
                run_id=run_id,
                code="WORKFLOW_EXECUTION_CONFIRMATION_MISSING",
                message="尚未确认执行计划，无法进行执行结果分析",
            )

        # 白名单：仅允许分析本 workflow 启动的 execution_run_ids
        whitelist = self._unique_ints(confirmation.get("execution_run_ids") or [])

        if params["execution_run_ids"]:
            requested = self._unique_ints(params["execution_run_ids"])
            allowed_ids = [sid for sid in requested if sid in set(whitelist)]
        else:
            allowed_ids = list(whitelist)

        if not allowed_ids:
            return self._execution_analysis_error(
                run_id=run_id,
                code="WORKFLOW_EXECUTION_ANALYSIS_TARGET_EMPTY",
                message="请求的 execution_run_ids 与本工作流的执行白名单无交集",
            )

        # 采集 execution_runs 及其关联 scenario / report
        runs_payload = self._collect_execution_runs_payload(
            execution_run_ids=allowed_ids,
            include_running=bool(params["include_running"]),
        )
        if not runs_payload:
            return self._execution_analysis_error(
                run_id=run_id,
                code="WORKFLOW_EXECUTION_ANALYSIS_TARGET_EMPTY",
                message="本工作流暂无可分析的执行结果（execution_runs 可能尚未落库）",
            )

        agent_input = {
            "target_id": run_id,
            "workflow_run_id": run_id,
            "source_name": run.source_name or "",
            "source_type": run.source_type or "execution",
            "project_id": None,
            "version_id": None,
            "iteration_id": None,
            "include_running": bool(params["include_running"]),
            "confirmation_execution_run_ids": whitelist,
            "runs": runs_payload,
        }
        suggestion = self.agent_service.run_analyze_execution_results(
            agent_input, created_by=created_by
        )
        analysis_payload = suggestion.get("payload") or {}

        entry = {
            "suggestion_id": suggestion.get("suggestion_id"),
            "agent_type": suggestion.get("agent_type", "execution-result-analyst"),
            "status": "completed",
            "payload": analysis_payload,
        }
        result_payload["execution_analysis"] = entry
        run.result_payload = json.dumps(result_payload, ensure_ascii=False)
        run.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(run)

        return {
            "run_id": run_id,
            "suggestion_id": suggestion.get("suggestion_id"),
            "agent_type": suggestion.get("agent_type", "execution-result-analyst"),
            "status": "completed",
            "payload": analysis_payload,
        }

    def _collect_execution_runs_payload(
        self,
        execution_run_ids: List[int],
        include_running: bool = True,
    ) -> List[Dict[str, Any]]:
        """收集 execution_runs / scenarios / reports，组装 Agent 输入 runs 列表。"""
        if not execution_run_ids:
            return []

        # 防御性：即便 caller 已去重，这里再过一遍 unique_ints 避免 SQL IN 重复
        execution_run_ids = self._unique_ints(execution_run_ids)
        if not execution_run_ids:
            return []

        run_rows = (
            self.db.query(ExecutionRun)
            .filter(ExecutionRun.id.in_(execution_run_ids))
            .all()
        )
        if not run_rows:
            return []

        # 关联 scenarios
        scenario_ids: List[int] = []
        seen_sids: set = set()
        for r in run_rows:
            if r.run_type != "scenario" or r.target_id is None:
                continue
            try:
                sid_int = int(r.target_id)
            except (TypeError, ValueError):
                continue
            if sid_int in seen_sids:
                continue
            seen_sids.add(sid_int)
            scenario_ids.append(sid_int)
        scenario_lookup: Dict[int, str] = {}
        if scenario_ids:
            scenarios = (
                self.db.query(Scenario)
                .filter(Scenario.id.in_(scenario_ids))
                .all()
            )
            for s in scenarios:
                scenario_lookup[int(s.id)] = s.name or f"场景 {s.id}"

        # 关联 reports：report_type='execution' + target_id=execution_run.id
        report_rows = (
            self.db.query(Report)
            .filter(
                Report.report_type == "execution",
                Report.target_id.in_([int(r.id) for r in run_rows]),
            )
            .all()
        )
        report_by_run: Dict[int, Report] = {}
        for rep in report_rows:
            try:
                rep_target = int(rep.target_id)
            except (TypeError, ValueError):
                continue
            # 同一 run_id 多个 report 时保留第一个（按 id 升序）
            if rep_target not in report_by_run:
                report_by_run[rep_target] = rep

        payloads: List[Dict[str, Any]] = []
        for r in run_rows:
            status = (r.status or "").strip().lower()
            if not include_running and status in {"running", "pending"}:
                continue
            scenario_id = None
            if r.run_type == "scenario" and r.target_id is not None:
                try:
                    scenario_id = int(r.target_id)
                except (TypeError, ValueError):
                    scenario_id = None
            scenario_name = (
                scenario_lookup.get(scenario_id)
                if scenario_id is not None
                else None
            )
            summary = self._safe_json_loads(getattr(r, "summary", "") or "{}", {})
            report = report_by_run.get(int(r.id))
            payloads.append(
                {
                    "execution_run_id": int(r.id),
                    "run_type": r.run_type,
                    "scenario_id": scenario_id,
                    "scenario_name": scenario_name,
                    "environment_id": r.environment_id,
                    "status": r.status,
                    "started_at": r.started_at.isoformat() if r.started_at else None,
                    "finished_at": r.finished_at.isoformat() if r.finished_at else None,
                    "duration_ms": r.duration_ms,
                    "passed_steps": summary.get("passed_steps"),
                    "failed_steps": summary.get("failed_steps"),
                    "total_steps": summary.get("total_steps"),
                    "error_message": summary.get("error_message"),
                    "report_id": int(report.id) if report else None,
                    "report_summary": (
                        {**(report.summary or {}), **({"report_id": int(report.id)} if report else {})}
                        if report
                        else None
                    ),
                    "report_metrics": (report.metrics or {}) if report else None,
                }
            )
        return payloads

    # ── Phase 2: Workflow Result Adoption ─────────────────────────────────────

    def adopt_requirement_to_test_design(
        self,
        run_id: int,
        request: Union[Dict[str, Any], Any],
        created_by: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """人工采纳 workflow 结果写入业务表。

        返回值结构:
            None                        — run 不存在
            {"error": "...", ...}       — run 类型/状态不合法
            摘要 dict                    — 成功执行
        """
        run = self.db.query(AIWorkflowRun).filter(AIWorkflowRun.id == run_id).first()
        if not run:
            return None

        if run.workflow_type != "requirement_to_test_design":
            return self._adopt_error_response(
                run_id=run_id,
                request=request,
                code="WORKFLOW_TYPE_MISMATCH",
                message=f"当前工作流类型 {run.workflow_type} 不支持采纳",
            )
        if run.status != "completed":
            return self._adopt_error_response(
                run_id=run_id,
                request=request,
                code="WORKFLOW_NOT_COMPLETED",
                message=f"工作流状态 {run.status}，仅 completed 可被采纳",
            )

        params = self._coerce_adopt_request(request)
        result_payload = self._safe_json_loads(run.result_payload, {})
        requirement_payload = result_payload.get("requirement_analysis", {}).get("payload", {}) or {}
        test_design_payload = result_payload.get("test_design", {}).get("payload", {}) or {}

        # 默认阻止重复采纳；force=True 时放行
        previous_adoption = result_payload.get("adoption") or {}
        if previous_adoption.get("status") == "completed" and not params["force"]:
            return self._adopt_error_response(
                run_id=run_id,
                request=request,
                code="WORKFLOW_ALREADY_ADOPTED",
                message="该工作流已采纳，避免重复创建数据",
            )

        # force 路径下构建 (project_id, source_key) 已存在集合，用于需求去重
        # 同时构建 source_key/title -> requirement_id 的 lookup，
        # 让 force 跳过的需求在下游用例中能反查到既有需求 ID
        existing_source_keys: set = set()
        existing_requirement_lookup: Dict[str, int] = {}
        if params["force"]:
            rows = (
                self.db.execute(
                    text(
                        "SELECT id, source_key, title FROM requirement_items "
                        "WHERE project_id = :pid"
                    ),
                    {"pid": params["project_id"]},
                )
                .mappings()
                .all()
            )
            for row in rows:
                source_key = row.get("source_key")
                if source_key:
                    existing_source_keys.add(source_key)
                    existing_requirement_lookup[source_key] = row["id"]
                title = row.get("title")
                if title:
                    # title 命中仅作辅助映射；不要用空标题覆盖已有 source_key 的确定映射
                    existing_requirement_lookup.setdefault(title, row["id"])

        created_requirements: List[Dict[str, Any]] = []
        created_cases: List[Dict[str, Any]] = []
        skipped: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []

        # 1) 需求
        requirement_id_by_index: Dict[int, int] = {}
        if params["adopt_requirements"]:
            (
                created_requirements,
                requirement_id_by_index,
                req_skipped,
                req_errors,
            ) = self._adopt_requirements(
                requirement_payload=requirement_payload,
                project_id=params["project_id"],
                version_id=params["version_id"],
                iteration_id=params["iteration_id"],
                source_type=run.source_type,
                selected_indexes=params["selected_requirement_indexes"],
                created_by=created_by,
                existing_source_keys=existing_source_keys,
                existing_requirement_lookup=existing_requirement_lookup,
            )
            skipped.extend(req_skipped)
            errors.extend(req_errors)

        # 2) 功能用例
        if params["adopt_functional_cases"]:
            (
                functional_results,
                func_skipped,
                func_errors,
            ) = self._adopt_cases(
                case_items=test_design_payload.get("functional_cases", []) or [],
                case_type="functional",
                project_id=params["project_id"],
                version_id=params["version_id"],
                iteration_id=params["iteration_id"],
                requirement_payload=requirement_payload,
                requirement_id_by_index=requirement_id_by_index,
                selected_indexes=params["selected_functional_case_indexes"],
                link_cases=params["link_cases_to_requirements"],
                created_by=created_by,
                existing_requirement_lookup=existing_requirement_lookup or None,
            )
            created_cases.extend(functional_results)
            skipped.extend(func_skipped)
            errors.extend(func_errors)

        # 3) 接口用例
        if params["adopt_api_cases"]:
            (
                api_results,
                api_skipped,
                api_errors,
            ) = self._adopt_cases(
                case_items=test_design_payload.get("api_cases", []) or [],
                case_type="api",
                project_id=params["project_id"],
                version_id=params["version_id"],
                iteration_id=params["iteration_id"],
                requirement_payload=requirement_payload,
                requirement_id_by_index=requirement_id_by_index,
                selected_indexes=params["selected_api_case_indexes"],
                link_cases=params["link_cases_to_requirements"],
                created_by=created_by,
                existing_requirement_lookup=existing_requirement_lookup or None,
            )
            created_cases.extend(api_results)
            skipped.extend(api_skipped)
            errors.extend(api_errors)

        # 3.5) 场景草稿（四期）
        created_scenarios: List[Dict[str, Any]] = []
        scenario_payload: Dict[str, Any] = {}
        if params["adopt_scenario_drafts"]:
            scenario_payload = self._extract_scenario_drafts_payload(result_payload)
            (
                scenario_results,
                scenario_skipped,
                scenario_errors,
            ) = self._adopt_scenario_drafts(
                scenario_payload=scenario_payload,
                project_id=params["project_id"],
                version_id=params["version_id"],
                iteration_id=params["iteration_id"],
                created_cases=created_cases,
                cumulative_case_ids=(
                    previous_adoption.get("cumulative_case_ids", []) or []
                ),
                selected_indexes=params["selected_scenario_draft_indexes"],
                link_steps=params["link_scenario_steps_to_cases"],
                run_id=run_id,
                created_by=created_by,
            )
            created_scenarios.extend(scenario_results)
            skipped.extend(scenario_skipped)
            errors.extend(scenario_errors)

        # 4) 写回 adoption 状态
        adoption = self._build_adoption_record(
            created_requirements=created_requirements,
            created_cases=created_cases,
            created_scenarios=created_scenarios,
            skipped=skipped,
            errors=errors,
            adopted_by=created_by,
            force=bool(params["force"]),
            previous_adoption=previous_adoption,
        )
        result_payload["adoption"] = adoption
        run.result_payload = json.dumps(result_payload, ensure_ascii=False)
        run.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(run)

        summary = dict(adoption.get("summary") or {})
        summary["force"] = bool(params["force"])
        summary["force_adoption_count"] = adoption.get("force_adoption_count", 0)
        summary["cumulative_requirement_ids"] = adoption.get(
            "cumulative_requirement_ids", []
        )
        summary["cumulative_case_ids"] = adoption.get("cumulative_case_ids", [])
        summary["scenarios_created"] = adoption.get("scenarios_created", 0)
        summary["cumulative_scenario_ids"] = adoption.get(
            "cumulative_scenario_ids", []
        )
        return {
            "run_id": run_id,
            "project_id": params["project_id"],
            "version_id": params["version_id"],
            "iteration_id": params["iteration_id"],
            "created_requirements": created_requirements,
            "created_cases": created_cases,
            "created_scenarios": created_scenarios,
            "skipped": skipped,
            "errors": errors,
            "summary": summary,
            # 三期加固：顶层累计字段，避免 response_model 用 schema 默认值覆盖
            "force_adoption_count": adoption.get("force_adoption_count", 0),
            "cumulative_requirement_ids": adoption.get(
                "cumulative_requirement_ids", []
            ),
            "cumulative_case_ids": adoption.get("cumulative_case_ids", []),
            # 四期加固：累计场景 ID
            "cumulative_scenario_ids": adoption.get("cumulative_scenario_ids", []),
        }

    @staticmethod
    def _build_adoption_record(
        created_requirements: List[Dict[str, Any]],
        created_cases: List[Dict[str, Any]],
        skipped: List[Dict[str, Any]],
        errors: List[Dict[str, Any]],
        adopted_by: Optional[int],
        force: bool,
        previous_adoption: Optional[Dict[str, Any]] = None,
        created_scenarios: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """把采纳结果封装成可写回 run.result_payload 的 adoption 结构。

        累计语义：
        - `force_adoption_count` 累加（首次为 0，force=True 时 +1）。
        - `cumulative_requirement_ids` / `cumulative_case_ids` /
          `cumulative_scenario_ids` 合并历史 ID，去重保持顺序，便于审计回溯。
        """
        previous_adoption = previous_adoption or {}
        created_scenarios = created_scenarios or []
        previous_force_count = int(previous_adoption.get("force_adoption_count") or 0)
        new_force_count = previous_force_count + (1 if force else 0)

        def _merge_ids(prev_ids: List[int], new_items: List[Dict[str, Any]], key: str) -> List[int]:
            seen = set()
            merged: List[int] = []
            for value in (prev_ids or []) + [
                item.get(key) for item in new_items
            ]:
                if value is None or value in seen:
                    continue
                seen.add(value)
                merged.append(value)
            return merged

        cumulative_req_ids = _merge_ids(
            previous_adoption.get("cumulative_requirement_ids"),
            created_requirements,
            "requirement_id",
        )
        cumulative_case_ids = _merge_ids(
            previous_adoption.get("cumulative_case_ids"),
            created_cases,
            "case_id",
        )
        cumulative_scenario_ids = _merge_ids(
            previous_adoption.get("cumulative_scenario_ids"),
            created_scenarios,
            "scenario_id",
        )

        return {
            "status": "completed",
            "adopted_at": datetime.utcnow().isoformat() + "Z",
            "adopted_by": adopted_by,
            "force": force,
            "force_adoption_count": new_force_count,
            "requirements_created": len(created_requirements),
            "cases_created": len(created_cases),
            "scenarios_created": len(created_scenarios),
            "requirement_ids": [
                item.get("requirement_id")
                for item in created_requirements
                if item.get("requirement_id") is not None
            ],
            "case_ids": [
                item.get("case_id")
                for item in created_cases
                if item.get("case_id") is not None
            ],
            "scenario_ids": [
                item.get("scenario_id")
                for item in created_scenarios
                if item.get("scenario_id") is not None
            ],
            "cumulative_requirement_ids": cumulative_req_ids,
            "cumulative_case_ids": cumulative_case_ids,
            "cumulative_scenario_ids": cumulative_scenario_ids,
            "skipped_count": len(skipped),
            "error_count": len(errors),
            "summary": {
                "requirements_created": len(created_requirements),
                "cases_created": len(created_cases),
                "scenarios_created": len(created_scenarios),
                "skipped_count": len(skipped),
                "error_count": len(errors),
            },
        }

    def _adopt_error_response(
        self,
        run_id: int,
        request: Union[Dict[str, Any], Any],
        code: str,
        message: str,
    ) -> Dict[str, Any]:
        params = self._coerce_adopt_request(request)
        return {
            "run_id": run_id,
            "project_id": params.get("project_id", 0),
            "version_id": params.get("version_id"),
            "iteration_id": params.get("iteration_id"),
            "created_requirements": [],
            "created_cases": [],
            "created_scenarios": [],
            "skipped": [],
            "errors": [{"code": code, "message": message}],
            "summary": {
                "requirements_created": 0,
                "cases_created": 0,
                "scenarios_created": 0,
                "skipped_count": 0,
                "error_count": 1,
                "code": code,
                "message": message,
            },
            "force_adoption_count": 0,
            "cumulative_requirement_ids": [],
            "cumulative_case_ids": [],
            "cumulative_scenario_ids": [],
        }

    @staticmethod
    def _coerce_adopt_request(request: Union[Dict[str, Any], Any]) -> Dict[str, Any]:
        """兼容 Pydantic v2 模型 / dict / 缺失字段的请求归一化。"""
        if hasattr(request, "model_dump"):
            data = request.model_dump()
        elif isinstance(request, dict):
            data = dict(request)
        else:
            data = {}
        defaults = {
            "project_id": 0,
            "version_id": None,
            "iteration_id": None,
            "adopt_requirements": True,
            "adopt_functional_cases": True,
            "adopt_api_cases": True,
            "selected_requirement_indexes": None,
            "selected_functional_case_indexes": None,
            "selected_api_case_indexes": None,
            "link_cases_to_requirements": True,
            "force": False,
            "adopt_scenario_drafts": False,
            "selected_scenario_draft_indexes": None,
            "link_scenario_steps_to_cases": True,
        }
        merged = {**defaults, **data}
        # 空版本/迭代 ID 归一为 None，便于后续 SQL 写入
        for key in ("version_id", "iteration_id"):
            if merged.get(key) in (0, "", "0"):
                merged[key] = None
        return merged

    def _adopt_requirements(
        self,
        requirement_payload: Dict[str, Any],
        project_id: int,
        version_id: Optional[int],
        iteration_id: Optional[int],
        source_type: Optional[str],
        selected_indexes: Optional[List[int]],
        created_by: Optional[int],
        existing_source_keys: Optional[set] = None,
        existing_requirement_lookup: Optional[Dict[str, int]] = None,
    ):
        items = requirement_payload.get("requirements", []) or []
        created: List[Dict[str, Any]] = []
        skipped: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []
        index_to_id: Dict[int, int] = {}
        existing_source_keys = existing_source_keys or set()
        existing_requirement_lookup = existing_requirement_lookup or {}

        for index, item in enumerate(items):
            if selected_indexes is not None and index not in selected_indexes:
                skipped.append(
                    {
                        "type": "requirement",
                        "index": index,
                        "reason": "未在 selected_requirement_indexes 中",
                    }
                )
                continue

            source_key = self._pick_text(item, "source_key")
            if existing_source_keys and source_key and source_key in existing_source_keys:
                # force 路径下命中已有 source_key：跳过创建，但要把 index 映射到既有需求 ID，
                # 方便下游用例正确反查 requirement_id，避免关联到任意一条历史需求
                existing_req_id = existing_requirement_lookup.get(source_key)
                if existing_req_id is not None:
                    index_to_id[index] = existing_req_id
                skipped.append(
                    {
                        "type": "requirement",
                        "index": index,
                        "title": self._pick_text(item, "title") or "",
                        "source_key": source_key,
                        "existing_requirement_id": existing_req_id,
                        "reason": "force 路径下 source_key 已存在，跳过",
                    }
                )
                continue

            title = self._pick_text(item, "title") or f"AI 需求 {index + 1}"
            try:
                requirement_data = RequirementItemCreate(
                    project_id=project_id,
                    version_id=version_id,
                    iteration_id=iteration_id,
                    title=title[:300],
                    description=self._pick_text(item, "description") or "",
                    source_type=(
                        self._pick_text(item, "source_type")
                        or source_type
                        or "other"
                    ),
                    source_key=self._pick_text(item, "source_key"),
                    priority=self._normalize_priority(
                        self._pick_text(item, "priority")
                    ),
                    status="open",
                    owner_id=created_by,
                )
                req = create_requirement(self.db, requirement_data)
                created.append(
                    {
                        "index": index,
                        "title": title,
                        "requirement_id": req.id,
                        "status": "created",
                    }
                )
                index_to_id[index] = req.id
            except Exception as exc:
                errors.append(
                    {
                        "type": "requirement",
                        "index": index,
                        "title": title,
                        "code": "CREATE_REQUIREMENT_FAILED",
                        "message": str(exc),
                    }
                )

        # 在 source_key / title 维度补充映射，便于下游用例关联
        self._enrich_requirement_index_map(
            items=items,
            index_to_id=index_to_id,
            created=created,
        )

        return created, index_to_id, skipped, errors

    def _enrich_requirement_index_map(
        self,
        items: List[Any],
        index_to_id: Dict[int, int],
        created: List[Dict[str, Any]],
    ) -> None:
        """为按 source_key / title 关联的用例预留入口；当前 index 已经覆盖。"""
        # 当前用例关联逻辑以 index 为主，此处保留 source_key 索引以便后续扩展。
        # 不修改 index_to_id 即可，避免污染主流程。
        for entry in created:
            if not isinstance(entry, dict):
                continue
            _ = items  # 占位，避免未使用参数告警
            _ = index_to_id

    def _adopt_cases(
        self,
        case_items: List[Any],
        case_type: str,
        project_id: int,
        version_id: Optional[int],
        iteration_id: Optional[int],
        requirement_payload: Dict[str, Any],
        requirement_id_by_index: Dict[int, int],
        selected_indexes: Optional[List[int]],
        link_cases: bool,
        created_by: Optional[int],
        existing_requirement_lookup: Optional[Dict[str, int]] = None,
    ):
        created: List[Dict[str, Any]] = []
        skipped: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []

        if not case_items:
            return created, skipped, errors

        requirement_lookup = self._build_requirement_lookup(
            requirement_payload=requirement_payload,
            requirement_id_by_index=requirement_id_by_index,
        )
        if existing_requirement_lookup:
            # force 路径下补充既有需求 lookup；
            # 仅在当前 lookup 缺失对应 key 时回落到既有需求，避免覆盖刚创建的需求 ID
            for key, req_id in existing_requirement_lookup.items():
                requirement_lookup.setdefault(key, req_id)

        service = TestCaseService(self.db)

        for index, item in enumerate(case_items):
            if selected_indexes is not None and index not in selected_indexes:
                skipped.append(
                    {
                        "type": f"{case_type}_case",
                        "index": index,
                        "reason": f"未在 selected_{case_type}_case_indexes 中",
                    }
                )
                continue

            try:
                case_data = self._build_case_payload(
                    case_item=item,
                    case_type=case_type,
                    project_id=project_id,
                    version_id=version_id,
                    iteration_id=iteration_id,
                    requirement_id=self._resolve_requirement_id(
                        case_item=item,
                        index=index,
                        requirement_lookup=requirement_lookup,
                        requirement_id_by_index=requirement_id_by_index,
                        link_cases=link_cases,
                    ),
                    created_by=created_by,
                )
                result = service.create_case(case_data)
                created.append(
                    {
                        "index": index,
                        "name": case_data["name"],
                        "case_id": result.get("id"),
                        "case_type": case_type,
                        "requirement_id": case_data.get("requirement_id"),
                        "status": "created",
                    }
                )
            except Exception as exc:
                name = self._pick_text(item, "name") or self._pick_text(item, "title") or f"AI 用例 {index + 1}"
                errors.append(
                    {
                        "type": f"{case_type}_case",
                        "index": index,
                        "name": name,
                        "code": "CREATE_CASE_FAILED",
                        "message": str(exc),
                    }
                )

        return created, skipped, errors

    def _build_case_payload(
        self,
        case_item: Any,
        case_type: str,
        project_id: int,
        version_id: Optional[int],
        iteration_id: Optional[int],
        requirement_id: Optional[int],
        created_by: Optional[int],
    ) -> Dict[str, Any]:
        name = self._pick_text(case_item, "name") or self._pick_text(case_item, "title") or "AI 草稿用例"
        description = self._pick_text(case_item, "description") or ""
        priority = self._normalize_priority(self._pick_text(case_item, "priority"))
        pre_condition = self._pick_text(case_item, "pre_condition") or ""

        payload: Dict[str, Any] = {
            "name": name[:200],
            "description": description,
            "priority": priority,
            "case_type": case_type,
            "pre_condition": pre_condition,
            "project_id": project_id,
            "version_id": version_id,
            "iteration_id": iteration_id,
            "requirement_id": requirement_id,
            "created_by": created_by,
        }

        if case_type == "functional":
            steps = self._pick_steps(case_item, "steps")
            expected = (
                self._pick_text(case_item, "expected_result")
                or self._pick_text(case_item, "expected")
                or ""
            )
            payload["functional_case"] = {
                "steps": steps,
                "expected_result": expected,
                "test_data": self._pick_value(case_item, "test_data", {}),
                "post_action": self._pick_text(case_item, "post_action") or "",
            }
        else:
            method = (self._pick_text(case_item, "method") or "GET").upper()
            if method not in {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}:
                method = "GET"
            url = self._pick_text(case_item, "url") or self._pick_text(case_item, "path") or "/"
            expected_status = self._pick_int(
                case_item, "expected_status", 200
            ) or 200
            payload["api_case"] = {
                "method": method,
                "url": url,
                "headers": self._pick_value(case_item, "headers", {}),
                "params": self._pick_value(
                    case_item, "params", self._pick_value(case_item, "query_params", {})
                ),
                "body_type": self._pick_text(case_item, "body_type") or "none",
                "body": self._pick_text(case_item, "body") or "",
                "auth_config": self._pick_value(case_item, "auth_config", {}),
                "expected_status": expected_status,
                "assertions": self._pick_value(case_item, "assertions", []),
            }

        return payload

    @staticmethod
    def _build_requirement_lookup(
        requirement_payload: Dict[str, Any],
        requirement_id_by_index: Dict[int, int],
    ) -> Dict[str, int]:
        """建立 source_key/title -> requirement_id 的辅助索引。"""
        lookup: Dict[str, int] = {}
        items = requirement_payload.get("requirements", []) or []
        for index, item in enumerate(items):
            req_id = requirement_id_by_index.get(index)
            if not req_id:
                continue
            for key in (
                AIWorkflowService._pick_text(item, "source_key"),
                AIWorkflowService._pick_text(item, "title"),
            ):
                if key:
                    lookup[key] = req_id
        return lookup

    @staticmethod
    def _resolve_requirement_id(
        case_item: Any,
        index: int,
        requirement_lookup: Dict[str, int],
        requirement_id_by_index: Dict[int, int],
        link_cases: bool,
    ) -> Optional[int]:
        if not link_cases:
            return None
        for key_attr in ("requirement_key", "requirement_id_ref", "source_key", "title"):
            key = AIWorkflowService._pick_text(case_item, key_attr)
            if key and key in requirement_lookup:
                return requirement_lookup[key]
        return requirement_id_by_index.get(index)

    @staticmethod
    def _pick_text(item: Any, key: str) -> Optional[str]:
        if not isinstance(item, dict):
            return None
        value = item.get(key)
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _pick_int(item: Any, key: str, default: Optional[int] = None) -> Optional[int]:
        if not isinstance(item, dict):
            return default
        value = item.get(key)
        if value is None or value == "":
            return default
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _pick_value(item: Any, key: str, default: Any) -> Any:
        if not isinstance(item, dict):
            return default
        value = item.get(key)
        if value is None:
            return default
        return value

    @staticmethod
    def _pick_steps(item: Any, key: str) -> List[Any]:
        if not isinstance(item, dict):
            return []
        value = item.get(key)
        if isinstance(value, list):
            return value
        if isinstance(value, str) and value.strip():
            return [value]
        return []

    @staticmethod
    def _normalize_priority(value: Optional[str]) -> str:
        if not value:
            return "P2"
        upper = value.strip().upper()
        if upper in {"P0", "P1", "P2", "P3"}:
            return upper
        # 兼容中文/混合格式（如 P0 / 高）
        if "高" in value or "P0" in upper:
            return "P0"
        if "中" in value or "P1" in upper:
            return "P1"
        if "低" in value or "P3" in upper:
            return "P3"
        return "P2"

    @staticmethod
    def _normalize_scenario_type(value: Optional[str]) -> str:
        """归一化场景类型：仅保留 functional/api/e2e，其他回落为 functional。"""
        if not value:
            return "functional"
        normalized = str(value).strip().lower()
        if normalized in {"functional", "api", "e2e"}:
            return normalized
        # 兼容常见别名
        alias_map = {
            "function": "functional",
            "interface": "api",
            "api_case": "api",
            "end_to_end": "e2e",
            "end2end": "e2e",
            "场景": "functional",
            "接口": "api",
            "端到端": "e2e",
        }
        return alias_map.get(normalized, "functional")

    @staticmethod
    def _normalize_failure_strategy(value: Optional[str]) -> str:
        """归一化失败策略；非法值回落为 stop。"""
        valid = {"stop", "continue", "retry", "skip"}
        if not value:
            return "stop"
        normalized = str(value).strip().lower()
        return normalized if normalized in valid else "stop"

    @staticmethod
    def _normalize_timeout_ms(value: Any) -> int:
        """归一化超时时间（毫秒），默认 30000。"""
        if value is None or value == "":
            return 30000
        try:
            return int(value)
        except (TypeError, ValueError):
            return 30000

    @staticmethod
    def _extract_scenario_drafts_payload(result_payload: Dict[str, Any]) -> Dict[str, Any]:
        """从 result_payload 中提取场景草稿的 source payload。

        优先级：
          1. `result_payload["scenario_design"]["payload"]`（四期）
          2. 兼容旧结构：`result_payload["test_design"]["payload"]`
        """
        if not isinstance(result_payload, dict):
            return {}
        scenario_design = result_payload.get("scenario_design") or {}
        if isinstance(scenario_design, dict) and scenario_design.get("payload"):
            payload = scenario_design.get("payload") or {}
            if isinstance(payload, dict) and payload.get("scenario_drafts"):
                return payload
        test_design = result_payload.get("test_design") or {}
        if isinstance(test_design, dict):
            payload = test_design.get("payload") or {}
            if isinstance(payload, dict):
                return payload
        return {}

    def _adopt_scenario_drafts(
        self,
        scenario_payload: Dict[str, Any],
        project_id: int,
        version_id: Optional[int],
        iteration_id: Optional[int],
        created_cases: List[Dict[str, Any]],
        cumulative_case_ids: List[int],
        selected_indexes: Optional[List[int]],
        link_steps: bool,
        run_id: int,
        created_by: Optional[int],
    ):
        """采纳场景草稿写入 `scenarios` / `scenario_steps`。

        步骤的 `case_id` 解析优先级：
          1. 直接 `case_id` 字段
          2. `case_index` 字段（功能用例 + 接口用例拼接后的索引）
          3. `case_name` / `name` 在已采纳用例/历史用例中匹配

        若一个场景下没有任何 step 能解析到 `case_id`，整场景跳过并报错
        `SCENARIO_CASE_LINK_MISSING`，避免写入悬挂的场景。
        """
        created: List[Dict[str, Any]] = []
        skipped: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []

        scenario_drafts = (
            scenario_payload.get("scenario_drafts")
            if isinstance(scenario_payload, dict)
            else None
        ) or []
        if not scenario_drafts:
            return created, skipped, errors

        case_lookup = self._build_scenario_case_lookup(
            created_cases=created_cases,
            cumulative_case_ids=cumulative_case_ids,
        )

        service = ScenarioService(self.db)
        version_tag = f"workflow:{run_id}"

        for index, draft in enumerate(scenario_drafts):
            if selected_indexes is not None and index not in selected_indexes:
                skipped.append(
                    {
                        "type": "scenario",
                        "index": index,
                        "name": self._pick_text(draft, "name") or "",
                        "reason": "未在 selected_scenario_draft_indexes 中",
                    }
                )
                continue

            # 用户主动关闭 link_scenario_steps_to_cases 时视为显式跳过，
            # 写 skipped 而非 errors，避免与前端"跳过场景草稿"提示冲突
            if not link_steps:
                skipped.append(
                    {
                        "type": "scenario",
                        "index": index,
                        "name": self._pick_text(draft, "name") or "",
                        "reason": "link_scenario_steps_to_cases 已关闭，跳过场景草稿",
                    }
                )
                continue

            try:
                resolved_steps, step_debug = self._resolve_scenario_steps(
                    draft=draft,
                    case_lookup=case_lookup,
                    link_steps=link_steps,
                )
                if not resolved_steps:
                    name = self._pick_text(draft, "name") or f"AI 场景 {index + 1}"
                    errors.append(
                        {
                            "type": "scenario",
                            "index": index,
                            "name": name,
                            "code": "SCENARIO_CASE_LINK_MISSING",
                            "message": "场景下没有任何 step 能解析到 test_case，放弃整场景",
                            "step_debug": step_debug,
                        }
                    )
                    continue

                name = (self._pick_text(draft, "name") or f"AI 场景 {index + 1}")[:200]
                description = self._pick_text(draft, "description") or ""
                scenario_type = self._normalize_scenario_type(
                    self._pick_text(draft, "scenario_type")
                )
                priority = self._normalize_priority(
                    self._pick_text(draft, "priority")
                )

                create_data = {
                    "name": name,
                    "description": description,
                    "scenario_type": scenario_type,
                    "priority": priority,
                    "version": 1,
                    "status": "draft",
                    "project_id": project_id,
                    "version_id": version_id,
                    "iteration_id": iteration_id,
                    "source_type": "ai_workflow",
                    "source_id": run_id,
                    "version_tag": version_tag,
                    "steps": resolved_steps,
                }
                result = service.create_scenario(create_data)
                created.append(
                    {
                        "index": index,
                        "name": name,
                        "scenario_id": result.get("id"),
                        "step_count": len(resolved_steps),
                        "status": "created",
                    }
                )
            except Exception as exc:
                name = self._pick_text(draft, "name") or f"AI 场景 {index + 1}"
                errors.append(
                    {
                        "type": "scenario",
                        "index": index,
                        "name": name,
                        "code": "CREATE_SCENARIO_FAILED",
                        "message": str(exc),
                    }
                )

        return created, skipped, errors

    def _build_scenario_case_lookup(
        self,
        created_cases: List[Dict[str, Any]],
        cumulative_case_ids: List[int],
    ) -> Dict[str, Any]:
        """构建场景步骤反查 test_case 所需的 lookup。

        返回结构：
          {
              "by_id": {case_id: case_id},
              "by_name": {name_lower: case_id},
              "by_index": {index: case_id},
          }

        - `by_id` 来自 `created_cases` 的 `case_id` 字段
        - `by_name` 兼顾 created_cases.case_name 与 test_cases.name
        - `by_index` 允许 draft 用 `case_index` 引用本次新建的用例
        - `cumulative_case_ids` 兜底：补全历史采纳累积的 case_id，便于
          force 路径下场景继续引用已存在的用例
        """
        by_id: Dict[int, int] = {}
        by_name: Dict[str, int] = {}
        by_index: Dict[int, int] = {}

        for index, item in enumerate(created_cases or []):
            if not isinstance(item, dict):
                continue
            case_id = item.get("case_id")
            if not case_id:
                continue
            by_id[case_id] = case_id
            by_index[index] = case_id
            # 优先用 name 字段，回落到 case_name
            name_key = item.get("name") or item.get("case_name")
            if not name_key and isinstance(item, dict):
                # 通过 case_id 反查真实 name（避免依赖前端字段名）
                case_row = (
                    self.db.query(TestCase)
                    .filter(TestCase.id == case_id)
                    .first()
                ) if TestCase else None
                if case_row and case_row.name:
                    name_key = case_row.name
            if name_key:
                by_name.setdefault(str(name_key).strip().lower(), case_id)

        # 兜底：cumulative_case_ids 对应的 case 也应可被引用
        # 索引策略：
        #   - `by_id` / `by_name` 用 setdefault 兜底，避免覆盖本次 created_cases 的解析
        #   - `by_index` 用 setdefault 按 cumulative_case_ids 原顺序补 index；
        #     已被 created_cases 占用的 index 不会被覆盖
        for index, case_id in enumerate(cumulative_case_ids or []):
            if not case_id:
                continue
            by_id[case_id] = case_id
            by_index.setdefault(index, case_id)
            case_row = (
                self.db.query(TestCase)
                .filter(TestCase.id == case_id)
                .first()
            ) if TestCase else None
            if case_row and case_row.name:
                by_name.setdefault(case_row.name.strip().lower(), case_id)

        return {"by_id": by_id, "by_name": by_name, "by_index": by_index}

    def _resolve_scenario_steps(
        self,
        draft: Any,
        case_lookup: Dict[str, Dict[Any, Any]],
        link_steps: bool,
    ):
        """从草稿步骤中解析可写入 scenario_steps 的结构。

        返回 (resolved_steps, debug_list)。`resolved_steps` 每项结构：
            {
                "case_id": int,
                "name": str,
                "sort_order": int,
                "enabled": bool,
                "retry_count": int,
                "timeout_ms": int,
                "failure_strategy": str,
                "extract_rules": [...],
                "inject_rules": [...],
            }
        """
        if not isinstance(draft, dict):
            return [], []
        raw_steps = draft.get("steps")
        if not isinstance(raw_steps, list):
            return [], []
        if not link_steps:
            return [], []

        by_id = case_lookup.get("by_id", {}) or {}
        by_name = case_lookup.get("by_name", {}) or {}
        by_index = case_lookup.get("by_index", {}) or {}

        resolved: List[Dict[str, Any]] = []
        debug: List[Dict[str, Any]] = []

        for sort_order, raw_step in enumerate(raw_steps):
            if not isinstance(raw_step, dict):
                debug.append({"reason": "step 非字典结构", "raw": raw_step})
                continue

            case_id = self._pick_int(raw_step, "case_id")
            resolved_id: Optional[int] = None

            if case_id and case_id in by_id:
                resolved_id = case_id
            else:
                # case_index 兜底
                case_index = self._pick_int(raw_step, "case_index")
                if case_index is not None and case_index in by_index:
                    resolved_id = by_index[case_index]
                else:
                    # name 兜底：case_name / name 任一命中
                    for key in ("case_name", "name"):
                        text = self._pick_text(raw_step, key)
                        if text:
                            candidate = by_name.get(text.strip().lower())
                            if candidate:
                                resolved_id = candidate
                                break

            if resolved_id is None:
                debug.append(
                    {
                        "sort_order": sort_order,
                        "raw_case_id": case_id,
                        "raw_name": self._pick_text(raw_step, "name"),
                        "reason": "case_id/case_index/case_name 未命中",
                    }
                )
                continue

            resolved.append(
                {
                    "case_id": resolved_id,
                    "name": (self._pick_text(raw_step, "name") or "")[:200],
                    "sort_order": sort_order,
                    "enabled": True,
                    "retry_count": self._pick_int(raw_step, "retry_count") or 0,
                    "timeout_ms": self._normalize_timeout_ms(
                        raw_step.get("timeout_ms")
                    ),
                    "failure_strategy": self._normalize_failure_strategy(
                        self._pick_text(raw_step, "failure_strategy")
                    ),
                    "extract_rules": self._pick_value(
                        raw_step, "extract_rules", []
                    ),
                    "inject_rules": self._pick_value(
                        raw_step, "inject_rules", []
                    ),
                }
            )

        return resolved, debug

    # ── Run Lifecycle ──────────────────────────────────────────────────────────

    def _create_run(self, payload: Dict[str, Any], created_by: Optional[int]) -> AIWorkflowRun:
        # 状态机: pending → running → completed/failed
        # 起点统一为 pending;同步入口 ``start_requirement_to_test_design`` 会立即
        # 把 status 推进到 running;异步入口 (BackgroundTask) 复用 run row 时同理。
        run = AIWorkflowRun(
            workflow_type="requirement_to_test_design",
            status="pending",
            source_name=payload.get("source_name", ""),
            source_type=payload.get("source_type", "other"),
            input_payload=json.dumps(self._workflow_input_summary(payload), ensure_ascii=False),
            result_payload="{}",
            current_step="requirement-analyst",
            created_by=created_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def _run_step(
        self,
        run: AIWorkflowRun,
        step_order: int,
        agent_type: str,
        input_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        step = AIWorkflowStep(
            run_id=run.id,
            step_order=step_order,
            agent_type=agent_type,
            status="running",
            input_payload=json.dumps(input_payload, ensure_ascii=False),
            output_payload="{}",
            started_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )
        self.db.add(step)
        self.db.commit()
        self.db.refresh(step)

        # step 启动时立即把 run 状态/当前 step 推进, 让前端轮询能看到真实 running agent
        # (而不是停留在上一步的 current_step)。失败时 _fail_step 会覆盖。
        run.status = "running"
        run.current_step = agent_type
        run.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(run)

        try:
            if agent_type == "requirement-analyst":
                suggestion = self.agent_service.run_analyze_requirements(input_payload, created_by=run.created_by)
            elif agent_type == "test-designer":
                suggestion = self.agent_service.run_design_tests(input_payload, created_by=run.created_by)
            elif agent_type == "scenario-designer":
                suggestion = self.agent_service.run_design_scenarios(input_payload, created_by=run.created_by)
            else:
                raise ValueError(f"Unsupported agent_type: {agent_type}")

            step.suggestion_id = suggestion.get("suggestion_id")
            step.output_payload = json.dumps(
                {
                    "suggestion_id": suggestion.get("suggestion_id"),
                    "agent_type": suggestion.get("agent_type"),
                    "status": suggestion.get("status"),
                    "payload": suggestion.get("payload", {}),
                },
                ensure_ascii=False,
            )
            step.status = "completed"
            step.finished_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(step)

            run.current_step = agent_type
            run.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(run)
            return self._serialize_step(step)
        except Exception as exc:
            self._fail_step(step, run, exc)
            return self._serialize_step(step)

    def _finish_run(
        self,
        run: AIWorkflowRun,
        requirement_output: Dict[str, Any],
        design_output: Dict[str, Any],
        scenario_output: Optional[Dict[str, Any]] = None,
        original_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        run.status = "completed"
        run.current_step = "completed"
        result_payload: Dict[str, Any] = {
            "requirement_analysis": requirement_output,
            "test_design": design_output,
        }
        if scenario_output is not None:
            result_payload["scenario_design"] = scenario_output
        # 七期 A：审计 trace_meta，至少包含 workflow_run_id 与 origin 字段；
        # 即使 original_payload 缺失也不会破坏既有 run 形态。
        trace_meta: Dict[str, Any] = {
            "workflow_run_id": run.id,
        }
        if original_payload:
            module = original_payload.get("origin_module")
            origin_type = original_payload.get("origin_type")
            origin_ids = original_payload.get("origin_ids")
            origin_meta = original_payload.get("origin_meta")
            if module:
                trace_meta["origin_module"] = module
            if origin_type:
                trace_meta["origin_type"] = origin_type
            if origin_ids:
                trace_meta["origin_ids"] = list(origin_ids)
            if origin_meta:
                trace_meta["origin_meta"] = dict(origin_meta)
        result_payload["trace_meta"] = trace_meta
        run.result_payload = json.dumps(result_payload, ensure_ascii=False)
        run.finished_at = datetime.utcnow()
        run.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(run)
        return self._serialize_run(run)

    def _fail_step(self, step: AIWorkflowStep, run: AIWorkflowRun, exc: Exception) -> None:
        step.status = "failed"
        step.error_message = str(exc)[:2000]
        step.finished_at = datetime.utcnow()
        run.status = "failed"
        run.current_step = f"failed:{step.agent_type}"
        run.finished_at = datetime.utcnow()
        run.updated_at = datetime.utcnow()
        run.result_payload = json.dumps(
            {"error": str(exc)[:1000], "failed_step": step.agent_type},
            ensure_ascii=False,
        )
        self.db.commit()
        self.db.refresh(step)
        self.db.refresh(run)

    # ── Step Input Builders ────────────────────────────────────────────────────

    @staticmethod
    def _build_requirement_step_input(payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "target_id": payload.get("target_id") or 0,
            "source_name": payload.get("source_name", ""),
            "source_type": payload.get("source_type", "other"),
            "content": payload.get("content", ""),
            "extra_sources": payload.get("extra_sources", []),
            "project_id": payload.get("project_id"),
            "version_id": payload.get("version_id"),
            "iteration_id": payload.get("iteration_id"),
            "analysis_focus": payload.get("analysis_focus", []),
            # 七期 A：保留 origin 上下文，便于后续 agent 追溯
            **AIWorkflowService._origin_subpayload(payload),
        }

    @staticmethod
    def _agent_payload(suggestion_output: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """从上游 suggestion 输出中取出业务 payload（summary/requirements/...）。"""
        if not suggestion_output:
            return {}
        return suggestion_output.get("payload", {}) or {}

    @staticmethod
    def _build_design_step_input(
        original_payload: Dict[str, Any],
        requirement_output: Dict[str, Any],
        requirement_step: Dict[str, Any],
    ) -> Dict[str, Any]:
        requirement_payload = AIWorkflowService._agent_payload(requirement_output)
        return {
            "target_id": original_payload.get("target_id") or 0,
            "source_name": original_payload.get("source_name", ""),
            "source_type": original_payload.get("source_type", "other"),
            "project_id": original_payload.get("project_id"),
            "version_id": original_payload.get("version_id"),
            "iteration_id": original_payload.get("iteration_id"),
            "requirement_analysis": requirement_output,
            "requirements": requirement_payload.get("requirements", []),
            "acceptance_criteria": requirement_payload.get("acceptance_criteria", []),
            "test_suggestions": requirement_payload.get("test_suggestions", []),
            "upstream_suggestion_id": requirement_step.get("suggestion_id"),
            **AIWorkflowService._origin_subpayload(original_payload),
        }

    @staticmethod
    def _build_scenario_step_input(
        original_payload: Dict[str, Any],
        requirement_output: Dict[str, Any],
        design_output: Dict[str, Any],
        design_step: Dict[str, Any],
    ) -> Dict[str, Any]:
        requirement_payload = AIWorkflowService._agent_payload(requirement_output)
        test_design_payload = AIWorkflowService._agent_payload(design_output)
        functional_cases = test_design_payload.get("functional_cases", []) or []
        api_cases = test_design_payload.get("api_cases", []) or []
        return {
            "target_id": original_payload.get("target_id") or 0,
            "source_name": original_payload.get("source_name", ""),
            "source_type": original_payload.get("source_type", "other"),
            "project_id": original_payload.get("project_id"),
            "version_id": original_payload.get("version_id"),
            "iteration_id": original_payload.get("iteration_id"),
            "requirement_analysis": requirement_output,
            "requirements": requirement_payload.get("requirements", []),
            "test_design": design_output,
            "functional_cases": functional_cases,
            "api_cases": api_cases,
            "upstream_suggestion_id": design_step.get("suggestion_id"),
            **AIWorkflowService._origin_subpayload(original_payload),
        }

    @staticmethod
    def _workflow_input_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
        """`_create_run` 写入 ``input_payload`` 的摘要。

        七期 A：在摘要中保留 ``origin_*`` 字段，便于按业务来源追溯，
        但不持久化完整 content，避免敏感内容扩散到审计列。
        """
        return {
            "target_id": payload.get("target_id"),
            "source_name": payload.get("source_name", ""),
            "source_type": payload.get("source_type", "other"),
            "content_length": len(payload.get("content", "")),
            "extra_sources_count": len(payload.get("extra_sources", [])),
            "project_id": payload.get("project_id"),
            "version_id": payload.get("version_id"),
            "iteration_id": payload.get("iteration_id"),
            "origin_module": payload.get("origin_module"),
            "origin_type": payload.get("origin_type"),
            "origin_ids": list(payload.get("origin_ids") or []),
            "origin_meta": dict(payload.get("origin_meta") or {}),
        }

    @staticmethod
    def _origin_subpayload(payload: Dict[str, Any]) -> Dict[str, Any]:
        """把 origin 字段整理成 step input 子字典（仅保留有值字段）。"""
        sub: Dict[str, Any] = {}
        module = payload.get("origin_module")
        origin_type = payload.get("origin_type")
        origin_ids = payload.get("origin_ids")
        origin_meta = payload.get("origin_meta")
        if module:
            sub["origin_module"] = module
        if origin_type:
            sub["origin_type"] = origin_type
        if origin_ids:
            sub["origin_ids"] = list(origin_ids)
        if origin_meta:
            sub["origin_meta"] = dict(origin_meta)
        return sub

    @staticmethod
    def _suggestion_payload(step_dict: Dict[str, Any]) -> Dict[str, Any]:
        if step_dict.get("status") == "failed":
            return {}
        return step_dict.get("output_payload", {}) or {}

    # ── Serializers ───────────────────────────────────────────────────────────

    @staticmethod
    def _serialize_step(step: AIWorkflowStep) -> Dict[str, Any]:
        return {
            "id": step.id,
            "run_id": step.run_id,
            "step_order": step.step_order,
            "agent_type": step.agent_type,
            "status": step.status,
            "input_payload": AIWorkflowService._safe_json_loads(step.input_payload, {}),
            "output_payload": AIWorkflowService._safe_json_loads(step.output_payload, {}),
            "suggestion_id": step.suggestion_id,
            "error_message": step.error_message or "",
            "started_at": step.started_at.isoformat() if step.started_at else None,
            "finished_at": step.finished_at.isoformat() if step.finished_at else None,
            "created_at": step.created_at.isoformat() if step.created_at else None,
        }

    def _serialize_run(self, run: AIWorkflowRun, error: Optional[str] = None) -> Dict[str, Any]:
        steps = (
            self.db.query(AIWorkflowStep)
            .filter(AIWorkflowStep.run_id == run.id)
            .order_by(AIWorkflowStep.step_order.asc())
            .all()
        )
        serialized_steps = [self._serialize_step(step) for step in steps]
        return {
            "id": run.id,
            "workflow_type": run.workflow_type,
            "status": run.status,
            "source_name": run.source_name or "",
            "source_type": run.source_type or "other",
            "input_payload": self._safe_json_loads(run.input_payload, {}),
            "result_payload": self._safe_json_loads(run.result_payload, {}),
            "current_step": run.current_step or "",
            "created_by": run.created_by,
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "updated_at": run.updated_at.isoformat() if run.updated_at else None,
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            "steps": serialized_steps,
            "error": error,
        }

    @staticmethod
    def _safe_json_loads(raw, fallback):
        if not raw:
            return fallback
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return fallback

    # ── Phase 5 helpers ──────────────────────────────────────────────

    @staticmethod
    def _coerce_execution_plan_request(request: Union[Dict[str, Any], Any]) -> Dict[str, Any]:
        if hasattr(request, "model_dump"):
            data = request.model_dump()
        elif isinstance(request, dict):
            data = dict(request)
        else:
            data = {}
        defaults = {
            "scenario_ids": None,
            "environment_id": None,
            "include_draft_scenarios": True,
        }
        merged = {**defaults, **data}
        if merged.get("scenario_ids") is not None and not isinstance(merged["scenario_ids"], list):
            merged["scenario_ids"] = None
        if merged.get("environment_id") in (0, "", "0"):
            merged["environment_id"] = None
        return merged

    @staticmethod
    def _coerce_execution_confirm_request(
        request: Union[Dict[str, Any], Any],
    ) -> Dict[str, Any]:
        if hasattr(request, "model_dump"):
            data = request.model_dump()
        elif isinstance(request, dict):
            data = dict(request)
        else:
            data = {}
        defaults = {
            "batch_indexes": None,
            "scenario_ids": None,
            "environment_id": None,
        }
        merged = {**defaults, **data}
        if merged.get("batch_indexes") is not None and not isinstance(merged["batch_indexes"], list):
            merged["batch_indexes"] = None
        if merged.get("scenario_ids") is not None and not isinstance(merged["scenario_ids"], list):
            merged["scenario_ids"] = None
        if merged.get("environment_id") in (0, "", "0"):
            merged["environment_id"] = None
        return merged

    @staticmethod
    def _scenario_to_planner_payload(scenario: Scenario) -> Dict[str, Any]:
        return {
            "id": scenario.id,
            "name": scenario.name,
            "description": scenario.description or "",
            "scenario_type": scenario.scenario_type or "functional",
            "priority": scenario.priority or "P2",
            "step_count": len(scenario.steps) if scenario.steps is not None else 0,
        }

    @staticmethod
    def _unique_ints(values: Any) -> List[int]:
        """对可迭代值做去重 + 类型转换，保持首次出现顺序。

        - 跳过非整数 / 不可转换的项；
        - 同一整数仅保留首次出现位置；
        - 避免跨 batch / 显式 scenario_ids 出现重复时启动多次执行。
        """
        seen: set = set()
        result: List[int] = []
        for value in values or []:
            try:
                item = int(value)
            except (TypeError, ValueError):
                continue
            if item in seen:
                continue
            seen.add(item)
            result.append(item)
        return result

    @staticmethod
    def _execution_plan_error(
        run_id: int,
        code: str,
        message: str,
    ) -> Dict[str, Any]:
        return {
            "run_id": run_id,
            "suggestion_id": None,
            "agent_type": "execution-planner",
            "status": "error",
            "payload": {
                "summary": message,
                "execution_batches": [],
                "pre_checks": [],
                "risks": [],
                "warnings": [],
            },
            "error": {"code": code, "message": message},
        }

    @staticmethod
    def _execution_confirm_error(
        run_id: int,
        code: str,
        message: str,
    ) -> Dict[str, Any]:
        return {
            "run_id": run_id,
            "status": "error",
            "execution_run_ids": [],
            "scenario_ids": [],
            "environment_id": None,
            "error": {"code": code, "message": message},
        }

    @staticmethod
    def _execution_analysis_error(
        run_id: int,
        code: str,
        message: str,
    ) -> Dict[str, Any]:
        return {
            "run_id": run_id,
            "suggestion_id": None,
            "agent_type": "execution-result-analyst",
            "status": "error",
            "payload": {
                "summary": message,
                "overall_status": "unknown",
                "risk_level": "low",
                "pass_rate": 0.0,
                "failed_scenarios": [],
                "root_causes": [],
                "recommended_actions": [],
                "report_ids": [],
                "warnings": [message],
            },
            "error": {"code": code, "message": message},
        }

    @staticmethod
    def _coerce_execution_analysis_request(
        request: Union[Dict[str, Any], Any],
    ) -> Dict[str, Any]:
        if hasattr(request, "model_dump"):
            data = request.model_dump()
        elif isinstance(request, dict):
            data = dict(request)
        else:
            data = {}
        defaults = {
            "execution_run_ids": None,
            "include_running": True,
        }
        merged = {**defaults, **data}
        if merged.get("execution_run_ids") is not None and not isinstance(
            merged["execution_run_ids"], list
        ):
            merged["execution_run_ids"] = None
        merged["include_running"] = bool(merged.get("include_running", True))
        return merged
