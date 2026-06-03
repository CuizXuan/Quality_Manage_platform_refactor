import json
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.ai import AISuggestion
from app.repositories.ai_repository import AIRepository
from app.services.ai_service import AIService


class AIAgentService:
    def __init__(self, db: Session, ai_service: Optional[AIService]):
        self.db = db
        self.ai_service = ai_service

    def create_agent_suggestion(
        self,
        agent_type: str,
        target_type: str,
        target_id: int,
        payload: Dict,
        created_by: Optional[int] = None,
        analysis_type: Optional[str] = None,
    ) -> Dict:
        analysis = AIRepository.create_analysis(
            self.db,
            {
                "target_type": target_type,
                "target_id": target_id,
                "analysis_type": analysis_type or self._analysis_type_for_agent(agent_type),
                "model_used": getattr(self.ai_service, "model", "workflow-agent"),
                "raw_response": json.dumps(payload, ensure_ascii=False),
                "summary": payload.get("summary", "")[:200],
                "created_by": created_by,
            },
        )
        suggestion = AISuggestion(
            analysis_id=analysis.id,
            suggestion_type=agent_type,
            content=json.dumps(
                {
                    "agent_type": agent_type,
                    "status": "pending_review",
                    "payload": payload,
                    "trace_meta": {
                        "source_context": payload.get("source_context", {}),
                        "prompt_template_version": payload.get("prompt_template_version", "v1"),
                        "adoption_status": "pending",
                        "adoption_target": payload.get("adoption_target"),
                    },
                },
                ensure_ascii=False,
            ),
        )
        self.db.add(suggestion)
        self.db.commit()
        self.db.refresh(suggestion)
        return self.serialize_suggestion(suggestion)

    def run_asset_understand(self, payload: dict, created_by=None) -> Dict:
        source_name = payload.get("source_name", "Imported API")
        content = {
            "summary": f"已理解资产来源 {source_name}，建议优先生成基线用例和环境变量配置。",
            "source_context": payload,
            "prompt_template_version": "asset-understand-v1",
            "adoption_target": "api_asset",
            "high_risks": ["缺少环境变量配置", "部分接口缺少请求示例"],
        }
        return self.create_agent_suggestion("asset-understander", "scenario", payload.get("target_id", 0), content, created_by)

    def run_design_tests(self, payload: dict, created_by=None) -> Dict:
        content = self._build_test_design_payload(payload)
        return self.create_agent_suggestion(
            "test-designer",
            "case",
            payload.get("target_id", 0),
            content,
            created_by,
            analysis_type="test_design",
        )

    def run_design_scenarios(self, payload: dict, created_by=None) -> Dict:
        content = self._build_scenario_design_payload(payload)
        return self.create_agent_suggestion(
            "scenario-designer",
            "scenario",
            payload.get("target_id", 0),
            content,
            created_by,
            analysis_type="scenario_design",
        )

    def run_plan_execution(self, payload: dict, created_by=None) -> Dict:
        content = self._build_execution_plan_payload(payload)
        return self.create_agent_suggestion(
            "execution-planner",
            "execution",
            payload.get("target_id", 0),
            content,
            created_by,
            analysis_type="execution_plan",
        )

    def run_analyze_requirements(self, payload: dict, created_by=None) -> Dict:
        content = self._build_requirement_payload(payload)
        return self.create_agent_suggestion(
            "requirement-analyst",
            "scenario",
            payload.get("target_id") or 0,
            content,
            created_by,
            analysis_type="requirement_analysis",
        )

    def run_analyze_execution_results(self, payload: dict, created_by=None) -> Dict:
        content = self._build_execution_analysis_payload(payload)
        return self.create_agent_suggestion(
            "execution-result-analyst",
            "execution",
            payload.get("target_id", 0),
            content,
            created_by,
            analysis_type="execution_analysis",
        )

    def run_analyze_failure(self, payload: dict, created_by=None) -> Dict:
        content = {
            "summary": "已结合最近执行记录和缺陷历史生成失败归因建议。",
            "source_context": payload,
            "prompt_template_version": "failure-analysis-v1",
            "adoption_target": "execution",
            "possible_root_causes": payload.get("possible_root_causes", []),
        }
        return self.create_agent_suggestion("failure-analyst", "execution", payload.get("target_id", 0), content, created_by)


    def run_release_advice(self, payload: dict, created_by=None) -> Dict:
        content = {
            "summary": "已基于通过率、缺陷等级和覆盖率生成发布建议。",
            "source_context": payload,
            "prompt_template_version": "release-advice-v1",
            "adoption_target": "quality_gate",
            "release_decision": payload.get("release_decision", "warning"),
        }
        return self.create_agent_suggestion("release-advisor", "report", payload.get("target_id", 0), content, created_by)

    def reject_suggestion(self, suggestion_id: int, comment: str = "") -> Optional[Dict]:
        suggestion = self.db.query(AISuggestion).filter(AISuggestion.id == suggestion_id).first()
        if not suggestion:
            return None
        content = self._parse_content(suggestion.content)
        trace_meta = content.get("trace_meta", {})
        trace_meta["adoption_status"] = "rejected"
        trace_meta["rejection_comment"] = comment
        content["status"] = "rejected"
        content["trace_meta"] = trace_meta
        suggestion.content = json.dumps(content, ensure_ascii=False)
        self.db.commit()
        self.db.refresh(suggestion)
        return self.serialize_suggestion(suggestion)

    def accept_suggestion(self, suggestion_id: int, accepted_by: int, comment: str = "") -> Optional[Dict]:
        suggestion = AIRepository.accept_suggestion(self.db, suggestion_id, accepted_by=accepted_by, comment=comment)
        if not suggestion:
            return None
        content = self._parse_content(suggestion.content)
        trace_meta = content.get("trace_meta", {})
        trace_meta["adoption_status"] = "accepted"
        trace_meta["accepted_by"] = accepted_by
        trace_meta["accepted_comment"] = comment
        content["status"] = "accepted"
        content["trace_meta"] = trace_meta
        suggestion.content = json.dumps(content, ensure_ascii=False)
        self.db.commit()
        self.db.refresh(suggestion)
        return self.serialize_suggestion(suggestion)

    def _analysis_type_for_agent(self, agent_type: str) -> str:
        mapping = {
            "failure-analyst": "failure_analysis",
            "requirement-analyst": "requirement_analysis",
            "release-advisor": "report_summary",
            "scenario-designer": "scenario_design",
            "test-designer": "test_design",
            "execution-planner": "execution_plan",
            "execution-result-analyst": "execution_analysis",
        }
        return mapping.get(agent_type, "report_summary")

    def _build_requirement_payload(self, payload: dict) -> Dict:
        if self.ai_service:
            result = self.ai_service.analyze_requirements(payload)
        else:
            result = self._build_requirement_fallback(payload)
        result = self._normalize_requirement_payload(result)
        result.update(
            {
                "source_context": self._requirement_source_context(payload),
                "prompt_template_version": "requirement-analysis-v1",
                "adoption_target": "requirement_item",
            }
        )
        return result

    @staticmethod
    def _build_requirement_fallback(payload: dict) -> Dict:
        source_name = payload.get("source_name") or "未命名来源"
        return {
            "summary": f"AI 未配置，已生成输入摘要占位结果：{source_name}。",
            "requirements": [],
            "acceptance_criteria": [],
            "business_rules": [],
            "process_flows": [],
            "api_clues": [],
            "ambiguities": ["AI 未配置，需人工补充歧义分析。"],
            "risks": ["AI 未配置，无法自动识别需求风险。"],
            "test_suggestions": ["建议配置 AI 后重新运行需求分析。"],
            "coverage_notes": [],
        }

    @staticmethod
    def _normalize_requirement_payload(payload: Dict) -> Dict:
        keys = [
            "summary", "requirements", "acceptance_criteria", "business_rules", "process_flows",
            "api_clues", "ambiguities", "risks", "test_suggestions", "coverage_notes",
        ]
        normalized = {key: payload.get(key, [] if key != "summary" else "") for key in keys}
        for key in keys:
            if key != "summary" and not isinstance(normalized[key], list):
                normalized[key] = [] if normalized[key] is None else [normalized[key]]
        normalized["summary"] = normalized["summary"] or "需求分析已生成。"
        return normalized

    @staticmethod
    def _requirement_source_context(payload: dict) -> Dict:
        return {
            "source_name": payload.get("source_name"),
            "source_type": payload.get("source_type"),
            "project_id": payload.get("project_id"),
            "version_id": payload.get("version_id"),
            "iteration_id": payload.get("iteration_id"),
            "analysis_focus": payload.get("analysis_focus", []),
        }

    def _build_test_design_payload(self, payload: dict) -> Dict:
        if self.ai_service:
            result = self.ai_service.design_tests_from_requirements(payload)
        else:
            result = self._build_test_design_fallback(payload)
        result = self._normalize_test_design_payload(result)
        source_context = {
            "source_name": payload.get("source_name"),
            "source_type": payload.get("source_type"),
            "project_id": payload.get("project_id"),
            "version_id": payload.get("version_id"),
            "iteration_id": payload.get("iteration_id"),
            "from_requirement_workflow": bool(payload.get("requirement_analysis")),
            "upstream_suggestion_id": payload.get("upstream_suggestion_id"),
        }
        result.update(
            {
                "source_context": source_context,
                "prompt_template_version": "test-design-v1",
                "adoption_target": "test_case",
                "draft_assets": payload.get("draft_assets", []),
            }
        )
        return result

    @staticmethod
    def _build_test_design_fallback(payload: dict) -> Dict:
        requirement_analysis = payload.get("requirement_analysis") or {}
        requirements = (
            payload.get("requirements")
            or requirement_analysis.get("requirements")
            or []
        )
        acceptance = (
            payload.get("acceptance_criteria")
            or requirement_analysis.get("acceptance_criteria")
            or []
        )
        test_points: List[str] = []
        for item in requirements:
            title = item.get("title") if isinstance(item, dict) else str(item)
            if title:
                test_points.append(f"覆盖需求点：{title}")
        for item in acceptance:
            criteria = item.get("criteria") if isinstance(item, dict) else str(item)
            if criteria:
                test_points.append(f"验证验收点：{criteria}")
        if not test_points:
            test_points.append("AI 未配置，已生成基础占位测试点，建议补充需求输入。")
        return {
            "summary": "AI 未配置，已基于需求分析结果生成占位测试设计草稿。",
            "test_points": test_points,
            "functional_cases": [],
            "api_cases": [],
            "scenario_drafts": [],
            "assertion_suggestions": [],
            "coverage_notes": requirement_analysis.get("test_suggestions", []),
            "risks": requirement_analysis.get("risks", []),
        }

    @staticmethod
    def _normalize_test_design_payload(payload: Dict) -> Dict:
        keys = [
            "summary", "test_points", "functional_cases", "api_cases",
            "scenario_drafts", "assertion_suggestions", "coverage_notes", "risks",
        ]
        normalized = {key: payload.get(key, [] if key != "summary" else "") for key in keys}
        for key in keys:
            if key != "summary" and not isinstance(normalized[key], list):
                normalized[key] = [] if normalized[key] is None else [normalized[key]]
        normalized["summary"] = normalized["summary"] or "测试设计草稿已生成。"
        return normalized

    def _build_scenario_design_payload(self, payload: dict) -> Dict:
        requirement_payload = payload.get("requirement_analysis") or {}
        test_design_payload = payload.get("test_design") or {}
        functional_cases = (
            test_design_payload.get("payload", {}).get("functional_cases")
            or test_design_payload.get("functional_cases")
            or []
        )
        api_cases = (
            test_design_payload.get("payload", {}).get("api_cases")
            or test_design_payload.get("api_cases")
            or []
        )
        requirements = self._extract_requirements(requirement_payload)
        # 上游 functional/api 用例均为空时, 不调用真实 LLM(避免 10+ 分钟空跑),
        # 直接走 fallback, 即便有 ai_service 也跳过。
        if not functional_cases and not api_cases:
            result = self._build_scenario_design_fallback(
                functional_cases=[],
                api_cases=[],
                requirements=requirements,
            )
        elif self.ai_service:
            result = self.ai_service.design_scenarios_from_test_design(
                requirement_payload=requirement_payload.get("payload", requirement_payload)
                if isinstance(requirement_payload, dict)
                else {},
                test_design_payload=(
                    test_design_payload.get("payload", test_design_payload)
                    if isinstance(test_design_payload, dict)
                    else {}
                ),
            )
            # LLM 返回结果 normalize 后 scenario_drafts 为空时也强制 fallback
            if not result.get("scenario_drafts"):
                result = self._build_scenario_design_fallback(
                    functional_cases=functional_cases,
                    api_cases=api_cases,
                    requirements=requirements,
                )
        else:
            result = self._build_scenario_design_fallback(
                functional_cases=functional_cases,
                api_cases=api_cases,
                requirements=requirements,
            )
        result = self._normalize_scenario_design_payload(result)
        result.update(
            {
                "source_context": {
                    "source_name": payload.get("source_name"),
                    "source_type": payload.get("source_type"),
                    "project_id": payload.get("project_id"),
                    "version_id": payload.get("version_id"),
                    "iteration_id": payload.get("iteration_id"),
                    "upstream_suggestion_id": payload.get("upstream_suggestion_id"),
                    "from_requirement_workflow": bool(payload.get("requirement_analysis")),
                },
                "prompt_template_version": "scenario-design-v1",
                "adoption_target": "scenario",
            }
        )
        return result

    def _build_execution_plan_payload(self, payload: dict) -> Dict:
        """构造 execution-planner 的 suggestion payload。"""
        scenarios = payload.get("scenarios") or []
        allowed_ids = payload.get("allowed_scenario_ids") or []
        environment_id = payload.get("environment_id")

        if self.ai_service:
            result = self.ai_service.plan_execution_from_scenarios(
                {
                    "scenarios": scenarios,
                    "allowed_scenario_ids": allowed_ids,
                    "environment_id": environment_id,
                }
            )
        else:
            from app.services.ai_service import AIService

            result = AIService._fallback_execution_plan(
                scenarios=scenarios,
                allowed_ids=allowed_ids,
                environment_id=environment_id,
            )
        result = self._normalize_execution_plan_payload(result)
        result.update(
            {
                "source_context": {
                    "source_name": payload.get("source_name"),
                    "source_type": payload.get("source_type"),
                    "project_id": payload.get("project_id"),
                    "version_id": payload.get("version_id"),
                    "iteration_id": payload.get("iteration_id"),
                    "upstream_suggestion_id": payload.get("upstream_suggestion_id"),
                    "workflow_run_id": payload.get("workflow_run_id"),
                },
                "prompt_template_version": "execution-plan-v1",
                "adoption_target": "execution",
            }
        )
        return result

    @staticmethod
    def _normalize_execution_plan_payload(payload: Dict) -> Dict:
        keys = ["summary", "execution_batches", "pre_checks", "risks", "warnings"]
        normalized: Dict[str, Any] = {}
        for key in keys:
            value = payload.get(key)
            if key == "summary":
                normalized[key] = str(value or "执行计划已生成。")[:1000]
            else:
                if isinstance(value, list):
                    normalized[key] = value
                else:
                    normalized[key] = [] if value is None else [value]
        # 二次兜底：execution_batches 元素必须有 scenario_ids 列表字段
        for batch in normalized["execution_batches"]:
            if not isinstance(batch, dict):
                continue
            batch.setdefault("scenario_ids", [])
            batch.setdefault("priority", "P2")
            batch.setdefault("run_mode", "sequential")
        return normalized

    def _build_execution_analysis_payload(self, payload: dict) -> Dict:
        """构造 execution-result-analyst 的 suggestion payload。"""
        runs = payload.get("runs") or []
        workflow_run_id = payload.get("workflow_run_id")

        if self.ai_service:
            result = self.ai_service.analyze_execution_results({"runs": runs})
        else:
            from app.services.ai_service import AIService

            result = AIService._fallback_execution_analysis(runs=runs)
        # service 层兜底：与 AIService._normalize_execution_analysis 复用同样的
        # 白名单规则（runs -> allowed_run_ids / allowed_scenario_ids /
        # allowed_report_ids），再过滤一次 failed_scenarios / report_ids。
        result = self._normalize_execution_analysis_payload(result, runs=runs)
        result.update(
            {
                "source_context": {
                    "source_name": payload.get("source_name"),
                    "source_type": payload.get("source_type"),
                    "project_id": payload.get("project_id"),
                    "version_id": payload.get("version_id"),
                    "iteration_id": payload.get("iteration_id"),
                    "workflow_run_id": workflow_run_id,
                    "confirmation_execution_run_ids": (
                        payload.get("confirmation_execution_run_ids") or []
                    ),
                    "include_running": bool(payload.get("include_running", True)),
                },
                "prompt_template_version": "execution-analysis-v1",
                "adoption_target": "execution",
            }
        )
        return result

    @staticmethod
    def _normalize_execution_analysis_payload(
        payload: Dict, runs: Optional[List[Dict[str, Any]]] = None
    ) -> Dict:
        """归一化 execution-result-analyst 输出结构 + 兜底白名单过滤。

        白名单过滤逻辑与 `AIService._normalize_execution_analysis` 一致：
          - failed_scenarios 条目必须带 execution_run_id（命中 allowed_run_ids）
            或 scenario_id（命中 allowed_scenario_ids），否则丢弃；
          - report_ids 只保留 allowed_report_ids 内的 ID 并去重；
          - 若本 workflow 无 report 输入，report_ids 直接返回空数组。
        """
        keys = [
            "summary",
            "overall_status",
            "risk_level",
            "pass_rate",
            "failed_scenarios",
            "root_causes",
            "recommended_actions",
            "report_ids",
            "warnings",
        ]
        normalized: Dict[str, Any] = {}
        for key in keys:
            value = payload.get(key)
            if key == "summary":
                normalized[key] = str(value or "执行结果分析已生成。")[:1000]
            elif key in {"overall_status", "risk_level"}:
                normalized[key] = str(value or "").strip().lower()
            elif key == "pass_rate":
                try:
                    rate = float(value)
                except (TypeError, ValueError):
                    rate = 0.0
                normalized[key] = max(0.0, min(1.0, rate))
            else:
                if isinstance(value, list):
                    normalized[key] = value
                else:
                    normalized[key] = [] if value is None else [value]

        # 兜底白名单过滤：复用 AIService 规则
        allowed_run_ids, allowed_scenario_ids, allowed_report_ids, _ = (
            AIService._build_execution_analysis_allowed_sets(runs or [])
        )
        failed_filtered: List[Dict[str, Any]] = []
        for fs in normalized["failed_scenarios"]:
            if not isinstance(fs, dict):
                continue
            fs.setdefault("scenario_id", None)
            fs.setdefault("scenario_name", "")
            fs.setdefault("execution_run_id", None)
            fs.setdefault("reason", "")
            if not isinstance(fs.get("evidence"), list):
                fs["evidence"] = []
            execution_run_id = fs.get("execution_run_id")
            scenario_id = fs.get("scenario_id")
            try:
                execution_run_id_int = (
                    int(execution_run_id) if execution_run_id is not None else None
                )
            except (TypeError, ValueError):
                execution_run_id_int = None
            try:
                scenario_id_int = int(scenario_id) if scenario_id is not None else None
            except (TypeError, ValueError):
                scenario_id_int = None
            if not AIService._failed_scenario_in_allowed(
                execution_run_id=execution_run_id_int,
                scenario_id=scenario_id_int,
                allowed_run_ids=allowed_run_ids,
                allowed_scenario_ids=allowed_scenario_ids,
            ):
                continue
            failed_filtered.append(fs)
        normalized["failed_scenarios"] = failed_filtered

        normalized["report_ids"] = AIService._filter_report_ids_to_allowed(
            normalized.get("report_ids"),
            allowed_report_ids,
        )

        # 归一化 recommended_actions 元素
        for act in normalized["recommended_actions"]:
            if not isinstance(act, dict):
                continue
            act.setdefault("type", "manual_check")
            act.setdefault("description", "")
            act.setdefault("priority", "P2")
        return normalized

    @staticmethod
    def _extract_requirements(requirement_payload: Any) -> List[Dict[str, Any]]:
        """从 suggestion / 业务 payload 中提取 requirements 列表。"""
        if not isinstance(requirement_payload, dict):
            return []
        if isinstance(requirement_payload.get("payload"), dict):
            reqs = requirement_payload["payload"].get("requirements")
            if isinstance(reqs, list):
                return reqs
        reqs = requirement_payload.get("requirements")
        return reqs if isinstance(reqs, list) else []

    @staticmethod
    def _build_scenario_design_fallback(
        functional_cases: List[Dict],
        api_cases: List[Dict],
        requirements: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict:
        from app.services.ai_service import AIService
        result = AIService._fallback_scenario_design(
            raw="",
            functional_cases=functional_cases,
            api_cases=api_cases,
        )
        # fallback 必须至少产出 1 个 scenario_draft；
        # 当 functional/api 用例都为空时，先尝试用上游 requirements 直接组织
        # 1 个 placeholder 草稿；requirements 也为空时，再退化为通用占位草稿
        if result.get("scenario_drafts"):
            return result

        req_titles: List[str] = []
        for item in requirements or []:
            if isinstance(item, dict):
                title = (item.get("title") or "").strip()
                if title:
                    req_titles.append(title)
            elif isinstance(item, str):
                title = item.strip()
                if title:
                    req_titles.append(title)

        if req_titles:
            primary_title = req_titles[0]
            step_name = (
                f"覆盖需求：{primary_title}"
                if len(req_titles) == 1
                else f"覆盖核心需求点（共 {len(req_titles)} 条）"
            )
            draft_name = f"AI 场景草稿 - {primary_title[:30]}"
            description = (
                f"AI 未配置，已基于需求「{primary_title}」生成的占位场景草稿。"
            )
        else:
            draft_name = "AI 场景草稿 - 占位场景"
            description = "AI 未配置，且未提供需求/用例输入，生成通用占位场景草稿。"
            step_name = "占位执行步骤"

        result["scenario_drafts"] = [
            {
                "name": draft_name,
                "description": description,
                "scenario_type": "functional",
                "priority": "P2",
                "steps": [
                    {
                        "name": step_name,
                        "case_name": "",
                        "failure_strategy": "stop",
                        "timeout_ms": 30000,
                    }
                ],
            }
        ]
        if not result.get("summary") or "无法生成" in result.get("summary", ""):
            result["summary"] = (
                "AI 未配置，已生成占位场景草稿（fallback）。"
            )
        return result

    @staticmethod
    def _normalize_scenario_design_payload(payload: Dict) -> Dict:
        keys = ["summary", "scenario_drafts", "coverage_notes", "risks"]
        normalized = {key: payload.get(key, [] if key != "summary" else "") for key in keys}
        for key in keys:
            if key != "summary" and not isinstance(normalized[key], list):
                normalized[key] = [] if normalized[key] is None else [normalized[key]]
        normalized["summary"] = normalized["summary"] or "场景设计草稿已生成。"
        return normalized


    def serialize_suggestion(self, suggestion: AISuggestion) -> Dict:
        content = self._parse_content(suggestion.content)
        return {
            "suggestion_id": suggestion.id,
            "agent_type": content.get("agent_type", suggestion.suggestion_type),
            "status": content.get("status", "pending_review"),
            "payload": content.get("payload", {}),
            "trace_meta": content.get("trace_meta", {}),
        }

    def _parse_content(self, content: str) -> Dict:
        try:
            return json.loads(content or "{}")
        except json.JSONDecodeError:
            return {}
