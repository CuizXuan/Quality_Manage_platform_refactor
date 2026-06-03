"""
AIService — AI中枢服务层

职责：
  - 封装 AI 模型调用（MiniMax / OpenAI Compatible）
  - 生成用例变体
  - 生成断言建议
  - 失败归因分析
  - 报告总结

所有外部调用由本层处理，Router 只调用 Service，Repository 只做 DB 操作。
"""

import json
import re
from typing import Any, Dict, List, Optional

from app.models.ai import AIConfig, AIPromptTemplate


class AIService:
    """AI 服务封装，函数不超过 40 行，单一职责。"""

    def __init__(self, config: AIConfig):
        from openai import OpenAI

        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
        )
        self.model = config.model

    # ── Public API ──────────────────────────────────────────────────────────────

    def generate_variants(self, case_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从用例数据生成变体列表。"""
        prompt = self._build_variant_prompt(case_data)
        response = self._call_llm(prompt)
        return self._parse_variants(response)

    def generate_assertions(
        self, case_data: Dict[str, Any], response_body: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """从响应内容生成断言建议。"""
        prompt = self._build_assertion_prompt(case_data, response_body)
        response = self._call_llm(prompt)
        return self._parse_assertions(response)

    def analyze_failure(
        self,
        execution_step: Dict[str, Any],
        case_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """执行失败归因分析。"""
        prompt = self._build_failure_prompt(execution_step, case_data)
        response = self._call_llm(prompt)
        return self._parse_failure_analysis(response)

    def summarize_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """报告总结与风险预测。"""
        prompt = self._build_report_summary_prompt(report_data)
        response = self._call_llm(prompt)
        return self._parse_report_summary(response)

    def analyze_requirements(self, requirement_input: Dict[str, Any]) -> Dict[str, Any]:
        """分析多来源需求文本并返回结构化结果。"""
        prompt = self._build_requirement_analysis_prompt(requirement_input)
        response = self._call_llm(prompt)
        return self._parse_requirement_analysis(response)

    def design_tests_from_requirements(self, requirement_payload: Dict[str, Any]) -> Dict[str, Any]:
        """根据需求分析结果生成测试设计建议。

        输入来源：需求分析师 Agent 的结构化输出。
        输出：测试设计草稿（test_points / functional_cases / api_cases / ...）。

        LLM 输出不可用（未闭合 think / 非 JSON / 结构全空）时，自动 fallback
        到基于需求/验收点的最小可采纳产物，确保下游 scenario 设计与采纳不空跑。
        """
        prompt = self._build_test_design_prompt(requirement_payload)
        response = self._call_llm(prompt)
        return self._parse_test_design(response, requirement_input=requirement_payload)

    def design_scenarios_from_test_design(
        self,
        requirement_payload: Dict[str, Any],
        test_design_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """从需求分析 + 测试设计 + 用例草稿，生成业务流程级场景草稿。

        输入来源：test-designer Agent 的结构化输出。
        输出：scenario_drafts / coverage_notes / risks。
        """
        prompt = self._build_scenario_design_prompt(requirement_payload, test_design_payload)
        response = self._call_llm(prompt)
        return self._parse_scenario_design(response)

    def plan_execution_from_scenarios(
        self, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """基于已采纳的场景生成执行计划。

        输入来源：人工采纳的 `scenarios` / `scenario_steps`。
        输出：execution_batches / pre_checks / risks / warnings。
        调用 LLM 失败或解析失败时回落为按优先级分批的最小可用计划。
        """
        allowed_ids = payload.get("allowed_scenario_ids") or []
        try:
            prompt = self._build_execution_plan_prompt(payload)
            response = self._call_llm(prompt)
            return self._parse_execution_plan(response, allowed_ids=allowed_ids)
        except Exception:
            return self._fallback_execution_plan(
                scenarios=payload.get("scenarios") or [],
                allowed_ids=allowed_ids,
                environment_id=payload.get("environment_id"),
            )

    def analyze_execution_results(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """基于 execution_runs / scenarios / reports 生成质量闭环分析。

        输入来源：本 workflow 启动的 execution_runs（已白名单过滤）+ 关联 scenarios + 自动生成的 reports。
        输出：summary / overall_status / risk_level / pass_rate / failed_scenarios /
              root_causes / recommended_actions / report_ids / warnings。
        调用 LLM 失败或解析失败时回落到基于 passed/failed/running 的离线分析。
        """
        try:
            prompt = self._build_execution_analysis_prompt(payload)
            response = self._call_llm(prompt)
            return self._parse_execution_analysis(response, runs=payload.get("runs") or [])
        except Exception:
            return self._fallback_execution_analysis(runs=payload.get("runs") or [])

    def test_connection(self) -> Dict[str, Any]:
        """测试 AI 连接是否可用。"""
        try:
            response = self._call_llm("Respond with exactly: OK")
            ok = "ok" in response.lower()
            return {"ok": ok, "message": response[:200]}
        except Exception as e:
            return {"ok": False, "message": str(e)[:200]}

    # ── Prompt Builders ─────────────────────────────────────────────────────────

    @staticmethod
    def _build_variant_prompt(case_data: Dict[str, Any]) -> str:
        case_name = case_data.get("name", "")
        method = case_data.get("method", "")
        url = case_data.get("url", "")
        headers = json.dumps(case_data.get("headers", {}), ensure_ascii=False)
        body = json.dumps(case_data.get("body", {}), ensure_ascii=False, indent=2)
        return (
            f"你是一个测试用例变体生成专家。请为以下用例生成 5-8 个变体。\n"
            f"每个变体需要改变：URL参数、请求头、请求体、或者方法。\n"
            f"用例信息：\n"
            f"  名称：{case_name}\n"
            f"  方法：{method}\n"
            f"  URL：{url}\n"
            f"  请求头：{headers}\n"
            f"  请求体：{body}\n\n"
            f"请以 JSON 数组格式返回，每个元素包含：\n"
            f'  variant_type: 变体类型 (param_modify|header_add|body_vary|method_change|auth_modify|timeout_adjust)\n'
            f"  description: 变体描述\n"
            f"  override: 需要覆盖的字段及新值\n"
            f"直接返回 JSON，不要解释。"
        )

    @staticmethod
    def _build_assertion_prompt(
        case_data: Dict[str, Any], response_body: Dict[str, Any]
    ) -> str:
        case_name = case_data.get("name", "")
        response_str = json.dumps(response_body, ensure_ascii=False, indent=2)
        return (
            f"你是一个断言生成专家。请为以下响应生成断言建议。\n"
            f"用例：{case_name}\n"
            f"响应内容：\n{response_str}\n\n"
            f"请生成 3-6 个断言，涵盖：\n"
            f"  1. HTTP 状态码断言\n"
            f"  2. 响应时间断言（如果可提取）\n"
            f"  3. JSON 关键字段存在性断言\n"
            f"  4. 关键字段值断言\n"
            f"返回 JSON 数组，每个元素包含：\n"
            f'  assertion_type: status_code|response_time|json_exists|json_equals|json_contains\n'
            f"  field: 字段路径（JSONPath格式）\n"
            f"  expected_value: 期望值\n"
            f"  description: 断言描述\n"
            f"直接返回 JSON，不要解释。"
        )

    @staticmethod
    def _build_failure_prompt(
        execution_step: Dict[str, Any], case_data: Optional[Dict[str, Any]] = None
    ) -> str:
        step_str = json.dumps(execution_step, ensure_ascii=False, indent=2)
        case_str = json.dumps(case_data or {}, ensure_ascii=False, indent=2)
        return (
            f"你是一个测试失败归因分析专家。请分析以下执行失败原因并给出修复建议。\n"
            f"执行步骤信息：\n{step_str}\n\n"
            f"用例信息（如果有）：\n{case_str}\n\n"
            f"请返回 JSON 对象：\n"
            f'  root_cause: 根本原因分析（中文，50字以内）\n'
            f"  severity: 严重程度 (critical|high|medium|low)\n"
            f"  suggestions: 修复建议数组，每个包含：\n"
            f'    type: fix_type\n'
            f"    description: 具体描述\n"
            f"    effort: 预估工作量 (low|medium|high)\n"
            f"直接返回 JSON，不要解释。"
        )

    @staticmethod
    def _build_report_summary_prompt(report_data: Dict[str, Any]) -> str:
        summary = json.dumps(report_data.get("summary", {}), ensure_ascii=False, indent=2)
        metrics = json.dumps(report_data.get("metrics", {}), ensure_ascii=False, indent=2)
        return (
            f"你是一个测试报告分析专家。请总结以下测试报告并给出风险评估。\n"
            f"执行摘要：\n{summary}\n\n"
            f"详细指标：\n{metrics}\n\n"
            f"请返回 JSON 对象：\n"
            f'  summary_md: markdown 格式的总结（100-200字）\n'
            f"  risk_score: 0-100 的风险评分（整数）\n"
            f"  risk_factors: 风险因素数组（3-5个）\n"
            f"直接返回 JSON，不要解释。"
        )

    @staticmethod
    def _build_requirement_analysis_prompt(requirement_input: Dict[str, Any]) -> str:
        source_json = json.dumps(requirement_input, ensure_ascii=False, indent=2)
        return (
            "你是一个资深质量工程需求分析 Agent。请分析多种需求来源文本，"
            "来源可能包括 PRD、SRS、用户故事、Axure 导出文档、Figma 说明、"
            "原型截图 OCR 结果、流程图、接口文档，也可能混合出现。\n"
            "输出必须是中文分析结果，字段名必须保持英文 snake_case。\n"
            "请只返回一个 JSON 对象，不要 Markdown，不要解释。\n"
            "输入：\n"
            f"{source_json}\n\n"
            "JSON 结构必须包含：summary, requirements, acceptance_criteria, "
            "business_rules, process_flows, api_clues, ambiguities, risks, "
            "test_suggestions, coverage_notes。\n"
            "requirements 每项至少包含 title, description, source_type, source_key, priority。"
        )

    @staticmethod
    def _build_test_design_prompt(requirement_payload: Dict[str, Any]) -> str:
        payload_json = json.dumps(requirement_payload, ensure_ascii=False, indent=2)
        return (
            "你是一个测试设计 Agent。输入来自需求分析师 Agent 的结构化分析结果，"
            "请基于该结果生成可落地的测试设计草稿。\n"
            "输出必须是中文，字段名必须保持英文 snake_case。\n"
            "请只返回一个 JSON 对象，不要 Markdown，不要解释。\n"
            "输入：\n"
            f"{payload_json}\n\n"
            "JSON 结构必须包含：summary, test_points, functional_cases, "
            "api_cases, scenario_drafts, assertion_suggestions, coverage_notes, risks。\n"
            "functional_cases 每项至少包含 name, type, priority, steps, expected。\n"
            "api_cases 每项至少包含 name, method, path, priority, expected_status。\n"
            "scenario_drafts 每项至少包含 name, steps, expected_outcome。"
        )

    @staticmethod
    def _build_scenario_design_prompt(
        requirement_payload: Dict[str, Any],
        test_design_payload: Dict[str, Any],
    ) -> str:
        requirement_json = json.dumps(requirement_payload, ensure_ascii=False, indent=2)
        test_design_json = json.dumps(test_design_payload, ensure_ascii=False, indent=2)
        return (
            "你是一个场景编排 Agent。请基于需求分析和测试设计草稿，组织业务流程级场景。\n"
            "输出必须是中文，字段名必须保持英文 snake_case。\n"
            "请只返回一个 JSON 对象，不要 Markdown，不要解释。\n"
            "需求分析输入：\n"
            f"{requirement_json}\n\n"
            "测试设计输入：\n"
            f"{test_design_json}\n\n"
            "JSON 结构必须包含：summary, scenario_drafts, coverage_notes, risks。\n"
            "scenario_drafts 每项至少包含 name, description, scenario_type, priority, "
            "steps, expected_outcome。\n"
            "steps 每项至少包含 name, case_index, case_name, failure_strategy, "
            "timeout_ms。case_index 引用 functional_cases / api_cases 的下标。"
        )

    @staticmethod
    def _build_execution_plan_prompt(payload: Dict[str, Any]) -> str:
        allowed_ids = payload.get("allowed_scenario_ids") or []
        scenarios = payload.get("scenarios") or []
        scenarios_lite: List[Dict[str, Any]] = []
        for item in scenarios:
            if not isinstance(item, dict):
                continue
            scenarios_lite.append(
                {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "scenario_type": item.get("scenario_type"),
                    "priority": item.get("priority"),
                    "step_count": item.get("step_count", 0),
                }
            )
        payload_json = json.dumps(
            {
                "allowed_scenario_ids": allowed_ids,
                "scenarios": scenarios_lite,
                "environment_id": payload.get("environment_id"),
            },
            ensure_ascii=False,
            indent=2,
        )
        return (
            "你是一个执行计划 Agent。请基于已采纳的场景列表，输出可执行的批次计划。\n"
            "输出必须是中文，字段名必须保持英文 snake_case。\n"
            "请只返回一个 JSON 对象，不要 Markdown，不要解释。\n"
            "输入：\n"
            f"{payload_json}\n\n"
            "JSON 结构必须包含 summary, execution_batches, pre_checks, risks, warnings。\n"
            "execution_batches 每项至少包含 name, scenario_ids, priority(P0-P3), "
            "run_mode(sequential|parallel), environment_id, rationale。\n"
            "pre_checks 每项至少包含 name, status(pending), description。\n"
            "scenario_ids 只能从 allowed_scenario_ids 中选择。"
        )

    # ── LLM Call ───────────────────────────────────────────────────────────────

    DEFAULT_LLM_TIMEOUT_SECONDS = 120

    def _call_llm(
        self, prompt: str, system_prompt: str = "", timeout: Optional[float] = None
    ) -> str:
        """调用 OpenAI 兼容的 chat.completions。

        显式设置 ``timeout``，避免单 Agent 在 BackgroundTask 中长时间阻塞 workflow
        状态机。默认 120s，可由调用方覆盖。超时/异常会向上抛，由上层
        ``_build_*_payload`` 转换为 fallback 或 step failure。
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 2048,
        }
        # openai >= 1.x: chat.completions.create 接受 ``timeout`` (seconds, float)
        effective_timeout = (
            timeout if timeout is not None else self.DEFAULT_LLM_TIMEOUT_SECONDS
        )
        try:
            response = self.client.chat.completions.create(
                timeout=effective_timeout, **kwargs
            )
        except TypeError:
            # 极少数 mock / 老 client 不接受 timeout kw, 退回到不带 timeout
            response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

    # ── Response Parsers ────────────────────────────────────────────────────────

    @staticmethod
    def _strip_think_tags(raw: str) -> str:
        """剥离 LLM 推理标签 ``<think>...</think>``，支持多段、跨行、未闭合。

        真实模型（MiniMax / DeepSeek 等）常在 ``content`` 头部带推理标签，
        会阻断后续 JSON 抽取。剥离后所有 ``_parse_*`` 解析路径自动受益。

        处理策略：
        1. 优先剥离所有闭合段 ``<think>...</think>``；
        2. 若原文以 ``<think>`` 开头但找不到 ``</think>``，整段视为推理内容
           全部丢弃，避免把推理文本误当成 ``summary`` 上送。
        """
        if not raw:
            return raw
        cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL)
        if "<think>" in cleaned:
            cleaned = re.sub(r"<think>.*$", "", cleaned, flags=re.DOTALL)
        return cleaned.strip()

    @staticmethod
    def _extract_json(raw: str) -> Optional[str]:
        cleaned = AIService._strip_think_tags(raw or "")
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", cleaned, re.IGNORECASE)
        if fence:
            return fence.group(1).strip()
        match = re.search(r"\{[\s\S]*\}|\[[\s\S]*\]", cleaned)
        return match.group(0) if match else None

    def _parse_variants(self, raw: str) -> List[Dict[str, Any]]:
        text = self._extract_json(raw) or "[]"
        try:
            data = json.loads(text)
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []

    def _parse_assertions(self, raw: str) -> List[Dict[str, Any]]:
        text = self._extract_json(raw) or "[]"
        try:
            data = json.loads(text)
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []

    def _parse_failure_analysis(self, raw: str) -> Dict[str, Any]:
        text = self._extract_json(raw)
        if text:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass
        return {
            "root_cause": raw[:100] if raw else "解析失败",
            "severity": "medium",
            "suggestions": [],
        }

    def _parse_report_summary(self, raw: str) -> Dict[str, Any]:
        text = self._extract_json(raw)
        if text:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass
        return {
            "summary_md": raw[:200] if raw else "总结生成失败",
            "risk_score": 50,
            "risk_factors": [],
        }

    def _parse_requirement_analysis(self, raw: str) -> Dict[str, Any]:
        text = self._extract_json(raw)
        if text:
            try:
                data = json.loads(text)
                if isinstance(data, dict):
                    return self._normalize_requirement_analysis(data)
            except json.JSONDecodeError:
                pass
        return self._fallback_requirement_analysis(raw)

    @staticmethod
    def _normalize_requirement_analysis(data: Dict[str, Any]) -> Dict[str, Any]:
        defaults = AIService._fallback_requirement_analysis("")
        normalized = {key: data.get(key, defaults[key]) for key in defaults}
        for key in normalized:
            if key != "summary" and not isinstance(normalized[key], list):
                normalized[key] = [] if normalized[key] is None else [normalized[key]]
        normalized["summary"] = normalized.get("summary") or defaults["summary"]
        return normalized

    @staticmethod
    def _fallback_requirement_analysis(raw: str) -> Dict[str, Any]:
        summary = raw[:200] if raw else "需求分析结果解析失败，请人工复核原始输入。"
        return {
            "summary": summary,
            "requirements": [],
            "acceptance_criteria": [],
            "business_rules": [],
            "process_flows": [],
            "api_clues": [],
            "ambiguities": [],
            "risks": [],
            "test_suggestions": [],
            "coverage_notes": [],
        }

    def _parse_test_design(
        self, raw: str, requirement_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        text = self._extract_json(raw)
        if text:
            try:
                data = json.loads(text)
                if isinstance(data, dict):
                    normalized = self._normalize_test_design(data)
                    if not self._is_test_design_payload_empty(normalized, raw):
                        return normalized
            except json.JSONDecodeError:
                pass
        # LLM 输出不可用 / 结构全空 / summary 仍以 think 开头 -> 业务兜底
        return self._fallback_test_design(raw, requirement_input=requirement_input)

    @staticmethod
    def _is_test_design_payload_empty(payload: Dict[str, Any], raw: str) -> bool:
        """判断 LLM 解析后的测试设计是否实质为空（用例 0 + 场景 0 + 测试点 0）。"""
        keys = ("test_points", "functional_cases", "api_cases", "scenario_drafts")
        if any(payload.get(key) for key in keys):
            return False
        stripped = AIService._strip_think_tags(raw or "")
        summary = (payload.get("summary") or "").strip()
        if summary.startswith("<think>") or "<think>" in stripped[:200]:
            return True
        return True  # 全部空列表时即视为需要兜底

    @staticmethod
    def _normalize_test_design(data: Dict[str, Any]) -> Dict[str, Any]:
        defaults = AIService._fallback_test_design("")
        normalized: Dict[str, Any] = {key: data.get(key, defaults[key]) for key in defaults}
        for key in normalized:
            if key == "summary":
                continue
            value = normalized[key]
            if not isinstance(value, list):
                normalized[key] = [] if value is None else [value]
        normalized["summary"] = normalized.get("summary") or defaults["summary"]
        return normalized

    @staticmethod
    def _fallback_test_design(
        raw: str,
        requirement_input: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """测试设计 fallback：基于上游需求/验收点生成最小可采纳产物。

        - 至少 1 个 test_point；
        - 至少 1 个 functional_case（带 name / priority / steps / expected_result）；
        - 若能从 ``requirement_input`` 推断接口线索（test_suggestions / api_clues），
          则至少 1 个 api_case；无法推断时不强制。
        - summary 文案不写 "AI 未配置"，因为真实模型可能已配置但输出不可用。
        """
        requirement_input = requirement_input or {}
        requirements = requirement_input.get("requirements") or []
        acceptance = requirement_input.get("acceptance_criteria") or []
        test_suggestions = requirement_input.get("test_suggestions") or []
        api_clues = requirement_input.get("api_clues") or []
        coverage_notes = requirement_input.get("coverage_notes") or []
        risks = requirement_input.get("risks") or []

        # 1. test_points 兜底
        test_points: List[str] = []
        for item in requirements:
            title = item.get("title") if isinstance(item, dict) else str(item)
            if title:
                test_points.append(f"覆盖需求点：{title}")
        for item in acceptance:
            criteria = item.get("criteria") if isinstance(item, dict) else str(item)
            if criteria:
                test_points.append(f"验证验收点：{criteria}")
        for item in test_suggestions:
            if isinstance(item, str) and item.strip():
                test_points.append(f"验证测试建议：{item.strip()}")
        if not test_points:
            test_points.append("基于需求分析生成基础测试点（LLM 输出不可用）。")

        # 2. functional_cases 兜底 - 至少 1 个，且可被 TestCaseService.create_case 接收
        functional_cases: List[Dict[str, Any]] = []
        primary_req = next(
            (item for item in requirements if isinstance(item, dict)),
            None,
        )
        if primary_req:
            req_title = primary_req.get("title") or "未命名需求"
            req_source_key = primary_req.get("source_key")
            req_source_type = primary_req.get("source_type") or "prd"
            functional_cases.append(
                {
                    "name": f"验证 {req_title} - 主路径",
                    "description": (
                        f"基于需求《{req_title}》生成的主路径功能用例。"
                        "由 AI 兜底生成，可被 TestCaseService.create_case 直接采纳。"
                    ),
                    "priority": AIService._normalize_priority_text(
                        primary_req.get("priority")
                    ),
                    "type": "functional",
                    "case_type": "functional",
                    "steps": [
                        "准备符合前置条件的数据",
                        "执行主路径操作",
                        "验证系统响应与验收点一致",
                    ],
                    "expected_result": "主路径操作成功，结果与需求一致。",
                    "expected": "主路径操作成功，结果与需求一致。",
                    "source_key": req_source_key,
                    "source_type": req_source_type,
                }
            )
        else:
            # 没有结构化 requirement 时, 也要保证 1 个可采纳 functional_case
            functional_cases.append(
                {
                    "name": "主路径功能验证",
                    "description": "基于需求输入生成的主路径功能用例（LLM 输出不可用）。",
                    "priority": "P2",
                    "type": "functional",
                    "case_type": "functional",
                    "steps": [
                        "准备符合前置条件的数据",
                        "执行主路径操作",
                        "验证系统响应与验收点一致",
                    ],
                    "expected_result": "主路径操作成功，结果与需求一致。",
                    "expected": "主路径操作成功，结果与需求一致。",
                }
            )

        # 3. api_cases 兜底 - 仅在能推断接口时生成
        api_cases: List[Dict[str, Any]] = []
        api_hints: List[str] = []
        for item in api_clues:
            if isinstance(item, dict):
                endpoint = item.get("endpoint") or item.get("url")
                method = item.get("method") or "GET"
                if endpoint:
                    api_hints.append(f"{method} {endpoint}")
            elif isinstance(item, str) and item.strip():
                api_hints.append(item.strip())
        for sug in test_suggestions:
            if not isinstance(sug, str):
                continue
            if "/" in sug and any(
                m in sug.upper() for m in ("GET", "POST", "PUT", "DELETE", "PATCH")
            ):
                api_hints.append(sug.strip())
        if api_hints:
            hint = api_hints[0]
            api_cases.append(
                {
                    "name": f"接口验证 {hint}",
                    "description": f"基于需求输入生成的接口用例 {hint}。",
                    "method": hint.split()[0].upper() if hint.split() else "GET",
                    "url": hint.split()[-1] if len(hint.split()) >= 2 else hint,
                    "expected_status": 200,
                    "priority": "P1",
                    "type": "api",
                    "case_type": "api",
                    "assertions": [
                        {"type": "status_code", "value": 200}
                    ],
                }
            )

        summary = (
            "AI 返回结构不可用，已基于需求分析生成兜底测试设计。"
            if (raw or "").strip()
            else "已基于需求分析生成兜底测试设计。"
        )
        return {
            "summary": summary,
            "test_points": test_points,
            "functional_cases": functional_cases,
            "api_cases": api_cases,
            "scenario_drafts": [],
            "assertion_suggestions": [],
            "coverage_notes": coverage_notes,
            "risks": risks,
        }

    def _parse_scenario_design(self, raw: str) -> Dict[str, Any]:
        text = self._extract_json(raw)
        if text:
            try:
                data = json.loads(text)
                if isinstance(data, dict):
                    return self._normalize_scenario_design(data)
            except json.JSONDecodeError:
                pass
        return self._fallback_scenario_design(raw)

    @staticmethod
    def _normalize_scenario_design(data: Dict[str, Any]) -> Dict[str, Any]:
        defaults = AIService._fallback_scenario_design("")
        normalized: Dict[str, Any] = {key: data.get(key, defaults[key]) for key in defaults}
        # list 字段归一化
        for key in ("scenario_drafts", "coverage_notes", "risks"):
            value = normalized[key]
            if not isinstance(value, list):
                normalized[key] = [] if value is None else [value]
        # 归一化 scenario_drafts 内每个 step
        normalized_drafts: List[Dict[str, Any]] = []
        for draft in normalized["scenario_drafts"]:
            if not isinstance(draft, dict):
                continue
            normalized_drafts.append(AIService._normalize_scenario_draft(draft))
        normalized["scenario_drafts"] = normalized_drafts
        normalized["summary"] = normalized.get("summary") or defaults["summary"]
        return normalized

    @staticmethod
    def _normalize_scenario_draft(draft: Dict[str, Any]) -> Dict[str, Any]:
        allowed_types = {"functional", "api", "e2e"}
        allowed_strategies = {"stop", "continue", "retry", "skip"}
        scenario_type = str(draft.get("scenario_type", "functional") or "functional").lower()
        if scenario_type not in allowed_types:
            scenario_type = "functional"
        priority = AIService._normalize_priority_text(draft.get("priority"))
        steps_in = draft.get("steps", [])
        if not isinstance(steps_in, list):
            steps_in = []
        steps_out: List[Dict[str, Any]] = []
        for step in steps_in:
            if not isinstance(step, dict):
                continue
            strategy = str(step.get("failure_strategy", "stop") or "stop").lower()
            if strategy not in allowed_strategies:
                strategy = "stop"
            timeout_ms = step.get("timeout_ms", 30000)
            try:
                timeout_ms = int(timeout_ms)
            except (TypeError, ValueError):
                timeout_ms = 30000
            if timeout_ms <= 0:
                timeout_ms = 30000
            case_index = step.get("case_index")
            try:
                case_index = int(case_index) if case_index not in (None, "") else None
            except (TypeError, ValueError):
                case_index = None
            steps_out.append(
                {
                    "name": str(step.get("name") or step.get("case_name") or f"Step {len(steps_out) + 1}"),
                    "case_id": step.get("case_id"),
                    "case_index": case_index,
                    "case_name": step.get("case_name") or step.get("name") or "",
                    "failure_strategy": strategy,
                    "timeout_ms": timeout_ms,
                }
            )
        return {
            "name": str(draft.get("name") or "AI 场景草稿"),
            "description": str(draft.get("description") or ""),
            "scenario_type": scenario_type,
            "priority": priority,
            "steps": steps_out,
            "expected_outcome": str(draft.get("expected_outcome") or ""),
        }

    @staticmethod
    def _normalize_priority_text(value: Optional[str]) -> str:
        if not value:
            return "P2"
        text = str(value).strip()
        upper = text.upper()
        if upper in {"P0", "P1", "P2", "P3"}:
            return upper
        if "高" in text or "P0" in upper:
            return "P0"
        if "中" in text or "P1" in upper:
            return "P1"
        if "低" in text or "P3" in upper:
            return "P3"
        return "P2"

    @staticmethod
    def _fallback_scenario_design(
        raw: str,
        functional_cases: Optional[List[Dict[str, Any]]] = None,
        api_cases: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """离线 fallback：基于 functional_cases + api_cases 组织 1-2 个流程级场景。"""
        functional_cases = functional_cases or []
        api_cases = api_cases or []
        case_total = len(functional_cases) + len(api_cases)
        if case_total == 0:
            summary = "AI 未配置，且无用例草稿，无法生成场景草稿。"
        else:
            summary = "AI 未配置，已基于测试设计用例草稿生成占位场景草稿。"
        scenario_drafts: List[Dict[str, Any]] = []
        if functional_cases or api_cases:
            # 端到端主路径
            steps: List[Dict[str, Any]] = []
            for idx, item in enumerate(functional_cases):
                steps.append(
                    {
                        "name": item.get("name") or f"功能用例 {idx + 1}",
                        "case_id": None,
                        "case_index": idx,
                        "case_name": item.get("name") or f"功能用例 {idx + 1}",
                        "failure_strategy": "stop",
                        "timeout_ms": 30000,
                    }
                )
            for offset, item in enumerate(api_cases):
                steps.append(
                    {
                        "name": item.get("name") or f"接口用例 {offset + 1}",
                        "case_id": None,
                        "case_index": len(functional_cases) + offset,
                        "case_name": item.get("name") or f"接口用例 {offset + 1}",
                        "failure_strategy": "stop",
                        "timeout_ms": 30000,
                    }
                )
            scenario_drafts.append(
                {
                    "name": "AI 未配置 · 主路径回归",
                    "description": "AI 未配置，已基于测试设计草稿自动组织主路径回归场景。",
                    "scenario_type": "e2e",
                    "priority": "P1",
                    "steps": steps,
                    "expected_outcome": "全部步骤通过；失败按 stop 策略终止。",
                }
            )
        return {
            "summary": summary,
            "scenario_drafts": scenario_drafts,
            "coverage_notes": [],
            "risks": [],
        }

    # ── Execution Plan (Phase 5) ───────────────────────────────────────────────

    def _parse_execution_plan(
        self, raw: str, allowed_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        text = self._extract_json(raw)
        if text:
            try:
                data = json.loads(text)
                if isinstance(data, dict):
                    return self._normalize_execution_plan(data, allowed_ids=allowed_ids)
            except json.JSONDecodeError:
                pass
        return self._fallback_execution_plan_from_raw(raw, allowed_ids=allowed_ids)

    @staticmethod
    def _normalize_execution_plan(
        data: Dict[str, Any],
        allowed_ids: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        allowed_set = {int(x) for x in (allowed_ids or []) if x is not None}
        summary = str(data.get("summary") or "").strip() or "执行计划已生成。"

        batches_in = data.get("execution_batches") or []
        if not isinstance(batches_in, list):
            batches_in = []
        batches_out: List[Dict[str, Any]] = []
        for idx, item in enumerate(batches_in):
            if not isinstance(item, dict):
                continue
            scenario_ids_raw = item.get("scenario_ids") or []
            if not isinstance(scenario_ids_raw, list):
                scenario_ids_raw = []
            scenario_ids: List[int] = []
            for sid in scenario_ids_raw:
                try:
                    sid_int = int(sid)
                except (TypeError, ValueError):
                    continue
                if allowed_set and sid_int not in allowed_set:
                    continue
                if sid_int in scenario_ids:
                    continue
                scenario_ids.append(sid_int)
            run_mode = str(item.get("run_mode") or "sequential").strip().lower()
            if run_mode not in {"sequential", "parallel"}:
                run_mode = "sequential"
            priority = AIService._normalize_priority_text(item.get("priority"))
            try:
                environment_id = (
                    int(item.get("environment_id"))
                    if item.get("environment_id") is not None
                    else None
                )
            except (TypeError, ValueError):
                environment_id = None
            batches_out.append(
                {
                    "name": str(item.get("name") or f"批次 {idx + 1}")[:200],
                    "scenario_ids": scenario_ids,
                    "priority": priority,
                    "run_mode": run_mode,
                    "environment_id": environment_id,
                    "rationale": str(item.get("rationale") or "")[:500],
                }
            )

        pre_checks_in = data.get("pre_checks") or []
        if not isinstance(pre_checks_in, list):
            pre_checks_in = []
        pre_checks: List[Dict[str, Any]] = []
        for idx, item in enumerate(pre_checks_in):
            if not isinstance(item, dict):
                continue
            pre_checks.append(
                {
                    "name": str(item.get("name") or f"前置检查 {idx + 1}")[:200],
                    "status": "pending",
                    "description": str(item.get("description") or "")[:500],
                }
            )

        def _coerce_list(value: Any) -> List[str]:
            if not isinstance(value, list):
                return []
            return [str(x) for x in value if x is not None][:50]

        return {
            "summary": summary[:1000],
            "execution_batches": batches_out,
            "pre_checks": pre_checks,
            "risks": _coerce_list(data.get("risks")),
            "warnings": _coerce_list(data.get("warnings")),
        }

    @staticmethod
    def _fallback_execution_plan_from_raw(
        raw: str,
        allowed_ids: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        return AIService._fallback_execution_plan(
            scenarios=[],
            allowed_ids=allowed_ids,
            environment_id=None,
        )

    @staticmethod
    def _fallback_execution_plan(
        scenarios: Optional[List[Dict[str, Any]]] = None,
        allowed_ids: Optional[List[int]] = None,
        environment_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """离线 fallback：按优先级分批，默认 sequential。"""
        allowed_set = {int(x) for x in (allowed_ids or []) if x is not None}
        items = scenarios or []
        buckets: Dict[str, List[int]] = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            sid = item.get("id")
            try:
                sid_int = int(sid)
            except (TypeError, ValueError):
                continue
            if allowed_set and sid_int not in allowed_set:
                continue
            priority = AIService._normalize_priority_text(item.get("priority"))
            buckets.setdefault(priority, []).append(sid_int)

        batch_names = {"P0": "P0 主路径批次", "P1": "P1 高优先级批次", "P2": "P2 一般批次", "P3": "P3 低优先级批次"}
        execution_batches: List[Dict[str, Any]] = []
        for priority in ("P0", "P1", "P2", "P3"):
            sids = buckets.get(priority) or []
            if not sids:
                continue
            execution_batches.append(
                {
                    "name": batch_names[priority],
                    "scenario_ids": sids,
                    "priority": priority,
                    "run_mode": "sequential",
                    "environment_id": environment_id,
                    "rationale": "AI 未配置，已按场景优先级分组生成批次。",
                }
            )
        if not execution_batches and items:
            # 兜底：若 priority 全部异常，仍产 1 个 batch，纳入前 N 个允许范围内的 scenario
            sids: List[int] = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                sid = item.get("id")
                try:
                    sid_int = int(sid)
                except (TypeError, ValueError):
                    continue
                if allowed_set and sid_int not in allowed_set:
                    continue
                sids.append(sid_int)
                if len(sids) >= 20:
                    break
            if sids:
                execution_batches.append(
                    {
                        "name": "AI 未配置 · 默认批次",
                        "scenario_ids": sids,
                        "priority": "P2",
                        "run_mode": "sequential",
                        "environment_id": environment_id,
                        "rationale": "AI 未配置，已基于场景 ID 顺序生成兜底批次。",
                    }
                )

        pre_checks: List[Dict[str, Any]] = [
            {
                "name": "环境可用性",
                "status": "pending",
                "description": "确认目标环境与执行环境一致，避免连接失败。",
            },
            {
                "name": "用例可达性",
                "status": "pending",
                "description": "确认 scenario_steps 关联的 test_case 仍存在且可执行。",
            },
        ]
        summary = "AI 未配置，已生成按优先级分批的兜底执行计划。"
        return {
            "summary": summary,
            "execution_batches": execution_batches,
            "pre_checks": pre_checks,
            "risks": ["AI 未配置，无法给出更细粒度的批次建议。"],
            "warnings": [],
        }

    # ── Execution Result Analysis (Phase 6) ─────────────────────────────────

    @staticmethod
    def _build_execution_analysis_prompt(payload: Dict[str, Any]) -> str:
        runs = payload.get("runs") or []
        runs_lite: List[Dict[str, Any]] = []
        for item in runs:
            if not isinstance(item, dict):
                continue
            runs_lite.append(
                {
                    "execution_run_id": item.get("execution_run_id"),
                    "scenario_id": item.get("scenario_id"),
                    "scenario_name": item.get("scenario_name"),
                    "status": item.get("status"),
                    "duration_ms": item.get("duration_ms"),
                    "passed_steps": item.get("passed_steps"),
                    "failed_steps": item.get("failed_steps"),
                    "total_steps": item.get("total_steps"),
                    "report_summary": item.get("report_summary"),
                    "report_id": item.get("report_id"),
                    "report_metrics": item.get("report_metrics"),
                    "error_message": item.get("error_message"),
                }
            )
        runs_json = json.dumps(runs_lite, ensure_ascii=False, indent=2)
        return (
            "你是一个执行结果分析 Agent。请基于本 workflow 启动的 execution_runs 列表，"
            "输出质量闭环分析。输出必须是中文，字段名必须保持英文 snake_case。\n"
            "请只返回一个 JSON 对象，不要 Markdown，不要解释。\n"
            f"输入 runs（{len(runs_lite)} 条）：\n{runs_json}\n\n"
            "JSON 结构必须包含：\n"
            "  summary: 一段话总结整体执行情况\n"
            "  overall_status: passed|failed|running|partial|unknown\n"
            "  risk_level: low|medium|high|critical\n"
            "  pass_rate: 0.0-1.0 的小数\n"
            "  failed_scenarios: 数组，每项含 scenario_id, scenario_name, "
            "execution_run_id, reason, evidence(数组)\n"
            "  root_causes: 字符串数组\n"
            "  recommended_actions: 数组，每项含 type "
            "(rerun|fix_case|fix_env|create_defect|review_requirement|manual_check), "
            "description, priority(P0-P3)\n"
            "  report_ids: 数字数组\n"
            "  warnings: 字符串数组"
        )

    def _parse_execution_analysis(
        self, raw: str, runs: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        text = self._extract_json(raw)
        if text:
            try:
                data = json.loads(text)
                if isinstance(data, dict):
                    return self._normalize_execution_analysis(data, runs=runs or [])
            except json.JSONDecodeError:
                pass
        return self._fallback_execution_analysis(runs=runs or [], raw=raw)

    @staticmethod
    def _normalize_execution_analysis(
        data: Dict[str, Any], runs: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        runs = runs or []
        # 基于输入 runs 构建白名单，避免 LLM 幻觉出不属于本 workflow 的
        # execution_run_id / scenario_id / report_id
        allowed_run_ids, allowed_scenario_ids, allowed_report_ids, scenario_name_lookup = (
            AIService._build_execution_analysis_allowed_sets(runs)
        )

        summary = str(data.get("summary") or "").strip() or "执行结果分析已生成。"

        overall = str(data.get("overall_status") or "").strip().lower()
        if overall not in {"passed", "failed", "running", "partial", "unknown"}:
            overall = "unknown"

        risk = str(data.get("risk_level") or "").strip().lower()
        if risk not in {"low", "medium", "high", "critical"}:
            risk = "medium"

        try:
            pass_rate = float(data.get("pass_rate"))
        except (TypeError, ValueError):
            pass_rate = 0.0
        pass_rate = max(0.0, min(1.0, pass_rate))

        failed_in = data.get("failed_scenarios") or []
        if not isinstance(failed_in, list):
            failed_in = []
        failed_out: List[Dict[str, Any]] = []
        for item in failed_in:
            if not isinstance(item, dict):
                continue
            scenario_id_raw = item.get("scenario_id")
            try:
                scenario_id = int(scenario_id_raw) if scenario_id_raw is not None else None
            except (TypeError, ValueError):
                scenario_id = None
            try:
                execution_run_id_raw = item.get("execution_run_id")
                execution_run_id = (
                    int(execution_run_id_raw) if execution_run_id_raw is not None else None
                )
            except (TypeError, ValueError):
                execution_run_id = None

            if not AIService._failed_scenario_in_allowed(
                execution_run_id=execution_run_id,
                scenario_id=scenario_id,
                allowed_run_ids=allowed_run_ids,
                allowed_scenario_ids=allowed_scenario_ids,
            ):
                continue

            # 用输入的 scenario_name 覆盖或补齐，避免 LLM 改名
            if scenario_id is not None and scenario_id in scenario_name_lookup:
                final_name = scenario_name_lookup[scenario_id] or str(
                    item.get("scenario_name") or ""
                )
            else:
                final_name = str(item.get("scenario_name") or "")

            evidence_in = item.get("evidence") or []
            if not isinstance(evidence_in, list):
                evidence_in = []
            evidence = [str(x) for x in evidence_in if x is not None][:20]
            failed_out.append(
                {
                    "scenario_id": scenario_id,
                    "scenario_name": final_name[:200],
                    "execution_run_id": execution_run_id,
                    "reason": str(item.get("reason") or "")[:500],
                    "evidence": evidence,
                }
            )

        root_causes_in = data.get("root_causes") or []
        if not isinstance(root_causes_in, list):
            root_causes_in = []
        root_causes = [str(x) for x in root_causes_in if x is not None][:20]

        actions_in = data.get("recommended_actions") or []
        if not isinstance(actions_in, list):
            actions_in = []
        actions_out: List[Dict[str, Any]] = []
        valid_action_types = {
            "rerun",
            "fix_case",
            "fix_env",
            "create_defect",
            "review_requirement",
            "manual_check",
        }
        for item in actions_in:
            if not isinstance(item, dict):
                continue
            action_type = str(item.get("type") or "").strip().lower()
            if action_type not in valid_action_types:
                action_type = "manual_check"
            priority = AIService._normalize_priority_text(item.get("priority"))
            actions_out.append(
                {
                    "type": action_type,
                    "description": str(item.get("description") or "")[:500],
                    "priority": priority,
                }
            )

        report_ids = AIService._filter_report_ids_to_allowed(
            data.get("report_ids"),
            allowed_report_ids,
        )

        warnings_in = data.get("warnings") or []
        if not isinstance(warnings_in, list):
            warnings_in = []
        warnings = [str(x) for x in warnings_in if x is not None][:20]

        return {
            "summary": summary[:1000],
            "overall_status": overall,
            "risk_level": risk,
            "pass_rate": round(pass_rate, 4),
            "failed_scenarios": failed_out,
            "root_causes": root_causes,
            "recommended_actions": actions_out,
            "report_ids": report_ids,
            "warnings": warnings,
        }

    @staticmethod
    def _build_execution_analysis_allowed_sets(
        runs: Optional[List[Dict[str, Any]]] = None,
    ):
        """从输入 runs 提取 allowed_run_ids / allowed_scenario_ids /
        allowed_report_ids 与 scenario_id -> scenario_name 映射。

        提取为静态方法供 `AIAgentService._normalize_execution_analysis_payload`
        复用，保证 service 层兜底与 AIService 层过滤规则一致。
        """
        runs = runs or []
        allowed_run_ids: set = set()
        allowed_scenario_ids: set = set()
        allowed_report_ids: set = set()
        scenario_name_lookup: Dict[int, str] = {}
        for item in runs:
            if not isinstance(item, dict):
                continue
            rid_raw = item.get("execution_run_id")
            try:
                if rid_raw is not None:
                    allowed_run_ids.add(int(rid_raw))
            except (TypeError, ValueError):
                continue
            sid_raw = item.get("scenario_id")
            try:
                if sid_raw is not None:
                    sid_int = int(sid_raw)
                    allowed_scenario_ids.add(sid_int)
                    sname = item.get("scenario_name")
                    if sname and sid_int not in scenario_name_lookup:
                        scenario_name_lookup[sid_int] = str(sname)
            except (TypeError, ValueError):
                continue
            rep_raw = item.get("report_id")
            try:
                if rep_raw is not None:
                    allowed_report_ids.add(int(rep_raw))
            except (TypeError, ValueError):
                continue
        return (
            allowed_run_ids,
            allowed_scenario_ids,
            allowed_report_ids,
            scenario_name_lookup,
        )

    @staticmethod
    def _failed_scenario_in_allowed(
        execution_run_id: Optional[int],
        scenario_id: Optional[int],
        allowed_run_ids: set,
        allowed_scenario_ids: set,
    ) -> bool:
        """白名单判断：execution_run_id 命中放行；否则 scenario_id 命中放行；
        都缺失或都越界则丢弃。"""
        if execution_run_id is not None:
            return not allowed_run_ids or execution_run_id in allowed_run_ids
        if scenario_id is not None:
            return not allowed_scenario_ids or scenario_id in allowed_scenario_ids
        return False

    @staticmethod
    def _filter_report_ids_to_allowed(
        report_ids_in: Any,
        allowed_report_ids: set,
    ) -> List[int]:
        """白名单过滤 + 去重（保持首次出现顺序）。若 allowed_report_ids 为空
        （本 workflow 无 report 输入），则直接返回空数组，不接受 LLM 幻觉 ID。"""
        if not isinstance(report_ids_in, list):
            return []
        if not allowed_report_ids:
            return []
        seen: set = set()
        result: List[int] = []
        for rid in report_ids_in:
            try:
                rid_int = int(rid)
            except (TypeError, ValueError):
                continue
            if rid_int not in allowed_report_ids:
                continue
            if rid_int in seen:
                continue
            seen.add(rid_int)
            result.append(rid_int)
        return result

    @staticmethod
    def _fallback_execution_analysis(
        runs: Optional[List[Dict[str, Any]]] = None,
        raw: str = "",
    ) -> Dict[str, Any]:
        """基于 passed/failed/running 计算 overall_status / pass_rate / risk_level。"""
        runs = runs or []
        total = len(runs)
        if total == 0:
            summary = (
                "本 workflow 未启动 execution_runs 或所选范围为空，无法进行执行结果分析。"
            )
            return {
                "summary": summary,
                "overall_status": "unknown",
                "risk_level": "low",
                "pass_rate": 0.0,
                "failed_scenarios": [],
                "root_causes": [],
                "recommended_actions": [],
                "report_ids": [],
                "warnings": ["未发现可分析的执行结果。"],
            }

        passed = 0
        failed = 0
        running = 0
        pending = 0
        stopped = 0
        failed_scenarios: List[Dict[str, Any]] = []
        warnings: List[str] = []
        report_ids: List[int] = []
        for item in runs:
            if not isinstance(item, dict):
                continue
            status = str(item.get("status") or "").strip().lower()
            if status == "passed":
                passed += 1
            elif status == "failed":
                failed += 1
                scenario_id = item.get("scenario_id")
                try:
                    scenario_id_int = int(scenario_id) if scenario_id is not None else None
                except (TypeError, ValueError):
                    scenario_id_int = None
                try:
                    execution_run_id_int = int(item.get("execution_run_id"))
                except (TypeError, ValueError):
                    execution_run_id_int = None
                failed_scenarios.append(
                    {
                        "scenario_id": scenario_id_int,
                        "scenario_name": str(item.get("scenario_name") or ""),
                        "execution_run_id": execution_run_id_int,
                        "reason": str(item.get("error_message") or "执行失败"),
                        "evidence": [],
                    }
                )
            elif status == "running":
                running += 1
                warnings.append(
                    f"场景 #{item.get('scenario_id')} 仍在执行中，结果尚未稳定。"
                )
            elif status == "pending":
                pending += 1
                warnings.append(
                    f"场景 #{item.get('scenario_id')} 仍为 pending，未启动或启动失败。"
                )
            else:
                stopped += 1
                warnings.append(
                    f"场景 #{item.get('scenario_id')} 状态 {status or 'unknown'}，需人工确认。"
                )
            rid = item.get("report_id")
            try:
                if rid is not None:
                    report_ids.append(int(rid))
            except (TypeError, ValueError):
                continue

        finished = passed + failed + stopped
        pass_rate = (passed / finished) if finished > 0 else 0.0

        if failed == 0 and running == 0 and pending == 0 and stopped == 0:
            overall_status = "passed"
            risk_level = "low"
        elif running > 0 or pending > 0:
            overall_status = "running" if failed == 0 and stopped == 0 else "partial"
            if failed > 0:
                risk_level = "high"
            else:
                risk_level = "medium"
        elif stopped > 0 and failed == 0:
            overall_status = "partial"
            risk_level = "medium"
        elif failed == 0:
            overall_status = "passed"
            risk_level = "low"
        else:
            failed_ratio = failed / total
            if failed_ratio >= 0.5:
                risk_level = "critical"
            elif failed_ratio >= 0.25:
                risk_level = "high"
            else:
                risk_level = "medium"
            overall_status = "failed"

        recommended_actions: List[Dict[str, Any]] = []
        for fs in failed_scenarios:
            recommended_actions.append(
                {
                    "type": "manual_check",
                    "description": f"复核场景 #{fs.get('scenario_id') or '?'} 失败原因，"
                    f"定位是否环境/用例/被测系统问题。",
                    "priority": "P1" if risk_level in {"high", "critical"} else "P2",
                }
            )
        if running > 0 or pending > 0:
            recommended_actions.append(
                {
                    "type": "manual_check",
                    "description": "存在仍在执行或未启动的 run，建议稍后重新分析或检查后台执行状态。",
                    "priority": "P2",
                }
            )
        if risk_level in {"high", "critical"}:
            recommended_actions.append(
                {
                    "type": "create_defect",
                    "description": "失败率较高，建议针对失败场景批量登记缺陷。",
                    "priority": "P0" if risk_level == "critical" else "P1",
                }
            )

        summary_lines = [
            f"本次共 {total} 个 execution_runs，其中 passed {passed}，failed {failed}，"
            f"running {running}，pending {pending}，其他 {stopped}。"
        ]
        if pass_rate:
            summary_lines.append(f"通过率 {pass_rate:.0%}。")
        if failed_scenarios:
            summary_lines.append(
                f"失败场景 {len(failed_scenarios)} 个："
                + "、".join(
                    str(fs.get("scenario_name") or f"#{fs.get('scenario_id')}")
                    for fs in failed_scenarios[:5]
                )
            )
        if not raw:
            summary_lines.append("(AI 未配置，已基于执行结果离线计算)")
        summary = " ".join(summary_lines)

        return {
            "summary": summary[:1000],
            "overall_status": overall_status,
            "risk_level": risk_level,
            "pass_rate": round(pass_rate, 4),
            "failed_scenarios": failed_scenarios,
            "root_causes": [],
            "recommended_actions": recommended_actions,
            "report_ids": report_ids,
            "warnings": warnings,
        }
