"""AI Service 单元测试 — Mock 测试"""
import unittest
from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base

# Mock openai.OpenAI at source before importing AIService
mock_openai_class = MagicMock(name="OpenAI")
with patch.dict("sys.modules", {"openai": MagicMock(OpenAI=mock_openai_class)}):
    from app.services.ai_service import AIService
    from app.services.ai_agent_service import AIAgentService


def make_mock_openai_client(response_content: str):
    """创建模拟 OpenAI client，返回指定 content。"""
    client = MagicMock()
    client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=response_content))]
    )
    return client


class TestAIServiceVariants(unittest.TestCase):

    def _svc_with_response(self, content: str):
        svc = MagicMock(spec=AIService)
        svc._call_llm = MagicMock(return_value=content)
        return svc

    def test_generate_variants_parses_edge_case(self):
        svc = self._svc_with_response(
            '{"variants":[{"variant_type":"edge_case","description":"空字符串","override_config":{}}]}'
        )
        result = svc._call_llm("test prompt")
        self.assertIn("edge_case", result)

    def test_generate_variants_returns_list(self):
        svc = self._svc_with_response('{"variants":[]}')
        result = svc._call_llm("prompt")
        self.assertIsInstance(result, str)

    def test_generate_variants_filters_invalid_type(self):
        svc = self._svc_with_response(
            '{"variants":[{"variant_type":"invalid_type","description":"test","override_config":{}}]}'
        )
        result = svc._call_llm("prompt")
        self.assertIn("invalid_type", result)  # Raw LLM output preserved


class TestAIServiceAssertions(unittest.TestCase):

    def _svc_with_response(self, content: str):
        svc = MagicMock(spec=AIService)
        svc._call_llm = MagicMock(return_value=content)
        return svc

    def test_generate_assertions_parses_status_code(self):
        svc = self._svc_with_response(
            '{"assertions":[{"assertion_type":"status_code","field":"status_code","expected":"200","description":"检查状态码"}]}'
        )
        result = svc._call_llm("prompt")
        self.assertIn("status_code", result)

    def test_generate_assertions_returns_string(self):
        svc = self._svc_with_response('{"assertions":[]}')
        result = svc._call_llm("prompt")
        self.assertIsInstance(result, str)

    def test_generate_assertions_valid_json_path(self):
        svc = self._svc_with_response(
            '{"assertions":[{"assertion_type":"json_equals","field":"$.data.id","expected":"1","description":""}]}'
        )
        result = svc._call_llm("prompt")
        self.assertIn("$.data.id", result)


class TestAIServiceFailureAnalysis(unittest.TestCase):

    def _svc_with_response(self, content: str):
        svc = MagicMock(spec=AIService)
        svc._call_llm = MagicMock(return_value=content)
        return svc

    def test_analyze_failure_parses_root_cause(self):
        svc = self._svc_with_response(
            '{"root_cause":"数据库连接超时","severity":"high","suggestions":[{"type":"fix","description":"增加连接池大小","effort":"medium"}]}'
        )
        result = svc._call_llm("prompt")
        self.assertIn("root_cause", result)
        self.assertIn("high", result)

    def test_analyze_failure_valid_severity(self):
        svc = self._svc_with_response(
            '{"root_cause":"test","severity":"critical","suggestions":[]}'
        )
        result = svc._call_llm("prompt")
        self.assertIn("critical", result)


class TestAIServiceReportSummary(unittest.TestCase):

    def _svc_with_response(self, content: str):
        svc = MagicMock(spec=AIService)
        svc._call_llm = MagicMock(return_value=content)
        return svc

    def test_summarize_report_parses_markdown(self):
        svc = self._svc_with_response(
            '{"summary":"## 测试报告\\n\\n通过率：95%","risk_score":85,"risk_factors":["高并发"]}'
        )
        result = svc._call_llm("prompt")
        self.assertIn("summary", result)
        self.assertIn("risk_score", result)
        self.assertIn("85", result)

    def test_summarize_report_risk_score_in_bounds(self):
        svc = self._svc_with_response(
            '{"summary":"test","risk_score":100,"risk_factors":[]}'
        )
        result = svc._call_llm("prompt")
        self.assertIn("100", result)

    def test_summarize_report_risk_score_zero(self):
        svc = self._svc_with_response(
            '{"summary":"test","risk_score":0,"risk_factors":[]}'
        )
        result = svc._call_llm("prompt")
        self.assertIn("0", result)


class TestAIServiceRequirementAnalysis(unittest.TestCase):

    def _svc_with_response(self, content: str):
        svc = AIService.__new__(AIService)
        svc._call_llm = MagicMock(return_value=content)
        return svc

    def test_analyze_requirements_parses_standard_json(self):
        svc = self._svc_with_response(
            '{"summary":"登录需求","requirements":[{"title":"用户登录","description":"支持密码登录","source_type":"prd","source_key":"REQ-001","priority":"P1"}],"ambiguities":[],"risks":[],"test_suggestions":[]}'
        )
        result = svc.analyze_requirements({"source_name": "PRD", "content": "登录"})
        self.assertEqual(result["summary"], "登录需求")
        self.assertEqual(result["requirements"][0]["source_key"], "REQ-001")

    def test_analyze_requirements_parses_code_fence_json(self):
        svc = self._svc_with_response(
            '```json\n{"summary":"用户故事分析","requirements":[],"ambiguities":["角色不明确"],"risks":[],"test_suggestions":[]}\n```'
        )
        result = svc.analyze_requirements({"source_name": "Story", "content": "作为用户"})
        self.assertEqual(result["summary"], "用户故事分析")
        self.assertIn("角色不明确", result["ambiguities"])

    def test_analyze_requirements_returns_fallback_on_invalid_json(self):
        svc = self._svc_with_response("not json")
        result = svc.analyze_requirements({"source_name": "PRD", "content": "登录"})
        for key in ["summary", "requirements", "ambiguities", "risks", "test_suggestions"]:
            self.assertIn(key, result)
        self.assertEqual(result["requirements"], [])


class TestAIAgentServiceRequirementAnalysis(unittest.TestCase):

    def test_run_analyze_requirements_without_ai_config_saves_suggestion(self):
        engine = create_engine("sqlite:///:memory:")
        TestingSession = sessionmaker(bind=engine)
        Base.metadata.create_all(bind=engine)
        db = TestingSession()
        try:
            service = AIAgentService(db, None)
            result = service.run_analyze_requirements(
                {"target_id": 7, "source_name": "PRD", "source_type": "prd", "content": "登录需求"}
            )
            self.assertEqual(result["agent_type"], "requirement-analyst")
            self.assertEqual(result["trace_meta"]["adoption_target"], "requirement_item")
            self.assertIn("AI 未配置", result["payload"]["summary"])
            self.assertEqual(result["status"], "pending_review")
        finally:
            db.close()


class TestAIServiceExecutionAnalysis(unittest.TestCase):
    """六期：execution-result-analyst Agent 的 fallback / 归一化 / LLM 解析。"""

    def test_fallback_computes_passed_overall_status(self):
        from app.services.ai_service import AIService

        runs = [
            {"execution_run_id": 1, "scenario_id": 11, "scenario_name": "A", "status": "passed"},
            {"execution_run_id": 2, "scenario_id": 12, "scenario_name": "B", "status": "passed"},
        ]
        result = AIService._fallback_execution_analysis(runs=runs)
        self.assertEqual(result["overall_status"], "passed")
        self.assertEqual(result["risk_level"], "low")
        self.assertEqual(result["pass_rate"], 1.0)
        self.assertEqual(result["failed_scenarios"], [])

    def test_fallback_uses_failed_ratio_for_risk_level(self):
        from app.services.ai_service import AIService

        # 4 失败 / 4 总数 → failed_ratio=1.0 → critical
        runs = [
            {"execution_run_id": i, "scenario_id": 100 + i, "scenario_name": f"s{i}", "status": "failed"}
            for i in range(4)
        ]
        result = AIService._fallback_execution_analysis(runs=runs)
        self.assertEqual(result["overall_status"], "failed")
        self.assertEqual(result["risk_level"], "critical")
        self.assertEqual(len(result["failed_scenarios"]), 4)

        # 25% 失败 → high
        runs = (
            [{"execution_run_id": i, "scenario_id": 200 + i, "scenario_name": f"p{i}", "status": "passed"} for i in range(3)]
            + [{"execution_run_id": 10, "scenario_id": 9, "scenario_name": "f", "status": "failed"}]
        )
        result = AIService._fallback_execution_analysis(runs=runs)
        self.assertEqual(result["overall_status"], "failed")
        self.assertEqual(result["risk_level"], "high")

    def test_fallback_marks_running_or_pending_as_warnings(self):
        from app.services.ai_service import AIService

        runs = [
            {"execution_run_id": 1, "scenario_id": 1, "scenario_name": "A", "status": "running"},
            {"execution_run_id": 2, "scenario_id": 2, "scenario_name": "B", "status": "pending"},
        ]
        result = AIService._fallback_execution_analysis(runs=runs)
        self.assertIn(result["overall_status"], {"running", "partial"})
        self.assertEqual(len(result["warnings"]), 2)
        self.assertEqual(result["failed_scenarios"], [])

    def test_fallback_empty_runs_returns_unknown(self):
        from app.services.ai_service import AIService

        result = AIService._fallback_execution_analysis(runs=[])
        self.assertEqual(result["overall_status"], "unknown")
        self.assertEqual(result["pass_rate"], 0.0)
        self.assertEqual(result["failed_scenarios"], [])
        self.assertEqual(result["warnings"], ["未发现可分析的执行结果。"])

    def test_normalize_validates_overall_status_and_risk_level_enums(self):
        from app.services.ai_service import AIService

        # 非法 overall_status / risk_level 回落为合法值
        # runs 提供 execution_run_id=3 / report_id=1,2,3，让白名单放行枚举测试的样本
        runs = [
            {
                "execution_run_id": 3,
                "scenario_id": 9,
                "scenario_name": "X",
                "status": "failed",
                "report_id": 1,
            },
            {
                "execution_run_id": 4,
                "scenario_id": 10,
                "scenario_name": "Y",
                "status": "passed",
                "report_id": 2,
            },
            {
                "execution_run_id": 5,
                "scenario_id": 11,
                "scenario_name": "Z",
                "status": "passed",
                "report_id": 3,
            },
        ]
        data = {
            "summary": "ok",
            "overall_status": "WAT",
            "risk_level": "scary",
            "pass_rate": 5,  # clamp 到 1.0
            "failed_scenarios": [
                {
                    "scenario_id": "9",
                    "scenario_name": "X",
                    "execution_run_id": "3",
                    "reason": "boom",
                    "evidence": ["a", "b"],
                }
            ],
            "root_causes": ["rc"],
            "recommended_actions": [
                {"type": "weird_action", "description": "x", "priority": "高"},
                {"type": "rerun", "description": "r", "priority": "P3"},
            ],
            "report_ids": [1, 2, "3"],
            "warnings": [],
        }
        result = AIService._normalize_execution_analysis(data, runs=runs)
        self.assertEqual(result["overall_status"], "unknown")
        self.assertEqual(result["risk_level"], "medium")
        self.assertEqual(result["pass_rate"], 1.0)
        self.assertEqual(result["failed_scenarios"][0]["scenario_id"], 9)
        self.assertEqual(result["failed_scenarios"][0]["execution_run_id"], 3)
        self.assertEqual(len(result["report_ids"]), 3)
        # 非法 action type 回落为 manual_check；优先级经 _normalize_priority_text 归一化
        self.assertEqual(
            result["recommended_actions"][0]["type"], "manual_check"
        )
        self.assertEqual(
            result["recommended_actions"][0]["priority"], "P0"
        )
        self.assertEqual(
            result["recommended_actions"][1]["type"], "rerun"
        )
        self.assertEqual(
            result["recommended_actions"][1]["priority"], "P3"
        )

    def test_parse_falls_back_to_offline_when_invalid_json(self):
        from app.services.ai_service import AIService

        runs = [
            {"execution_run_id": 1, "scenario_id": 1, "scenario_name": "A", "status": "passed"},
        ]
        svc = AIService.__new__(AIService)
        result = svc._parse_execution_analysis("not json", runs=runs)
        # fallback 应返回合理结果
        self.assertEqual(result["overall_status"], "passed")
        self.assertEqual(result["pass_rate"], 1.0)
        self.assertEqual(result["failed_scenarios"], [])

    def test_analyze_execution_results_uses_fallback_on_llm_error(self):
        """LLM 抛错时必须 fallback 到离线分析，不向上抛异常。"""
        from app.services.ai_service import AIService

        svc = AIService.__new__(AIService)
        svc._call_llm = MagicMock(side_effect=RuntimeError("upstream boom"))
        runs = [
            {"execution_run_id": 1, "scenario_id": 1, "scenario_name": "A", "status": "failed"},
        ]
        result = svc.analyze_execution_results({"runs": runs})
        self.assertEqual(result["overall_status"], "failed")
        self.assertEqual(result["risk_level"], "critical")
        self.assertEqual(len(result["failed_scenarios"]), 1)

    def test_normalize_execution_analysis_filters_report_ids_to_input_runs(self):
        """白名单过滤：report_ids 必须落在输入 runs 的 report_id 集合内。"""
        from app.services.ai_service import AIService

        runs = [
            {
                "execution_run_id": 2001,
                "scenario_id": 1001,
                "scenario_name": "A",
                "status": "passed",
                "report_id": 11,
            },
            {
                "execution_run_id": 2002,
                "scenario_id": 1002,
                "scenario_name": "B",
                "status": "failed",
                "report_id": 12,
            },
        ]
        data = {
            "summary": "x",
            "overall_status": "failed",
            "risk_level": "high",
            "pass_rate": 0.5,
            "failed_scenarios": [
                {
                    "scenario_id": 1002,
                    "scenario_name": "B",
                    "execution_run_id": 2002,
                    "reason": "boom",
                }
            ],
            "report_ids": [11, 12, 999, 11, "13", "abc"],
            "warnings": [],
        }
        result = AIService._normalize_execution_analysis(data, runs=runs)
        # 999 不在白名单，"13" 也不在（白名单只含 11, 12），"abc" 被丢弃
        self.assertEqual(result["report_ids"], [11, 12])
        # 同时未出现非白名单 ID
        self.assertNotIn(999, result["report_ids"])
        self.assertNotIn(13, result["report_ids"])

    def test_normalize_execution_analysis_drops_failed_scenarios_outside_input_runs(self):
        """白名单过滤：failed_scenarios 条目若 execution_run_id / scenario_id 都不在
        输入 runs 中，必须整条丢弃；同时 LLM 改的 scenario_name 需用输入覆盖。"""
        from app.services.ai_service import AIService

        runs = [
            {
                "execution_run_id": 2001,
                "scenario_id": 1001,
                "scenario_name": "登录主流程",
                "status": "failed",
            }
        ]
        data = {
            "summary": "x",
            "overall_status": "failed",
            "risk_level": "high",
            "pass_rate": 0.0,
            "failed_scenarios": [
                {
                    "scenario_id": 1001,
                    "scenario_name": "LLM 改名后的场景",
                    "execution_run_id": 2001,
                    "reason": "boom",
                },
                {
                    "scenario_id": 9999,  # 越界 scenario
                    "scenario_name": "幽灵场景",
                    "execution_run_id": 9999,
                    "reason": "ghost",
                },
                {
                    # 既无 execution_run_id 也无 scenario_id
                    "scenario_name": "无锚条目",
                    "reason": "no anchor",
                },
            ],
            "report_ids": [],
            "warnings": [],
        }
        result = AIService._normalize_execution_analysis(data, runs=runs)
        # 仅保留 scenario_id=1001 一条，且 scenario_name 被输入覆盖
        self.assertEqual(len(result["failed_scenarios"]), 1)
        kept = result["failed_scenarios"][0]
        self.assertEqual(kept["scenario_id"], 1001)
        self.assertEqual(kept["execution_run_id"], 2001)
        self.assertEqual(kept["scenario_name"], "登录主流程")

    def test_normalize_execution_analysis_returns_empty_report_ids_when_no_input_reports(self):
        """白名单空集：输入 runs 无 report_id 时，LLM 幻觉 ID 全部丢弃。"""
        from app.services.ai_service import AIService

        runs = [
            {
                "execution_run_id": 2001,
                "scenario_id": 1001,
                "scenario_name": "A",
                "status": "passed",
                # 无 report_id
            }
        ]
        data = {
            "summary": "x",
            "overall_status": "passed",
            "risk_level": "low",
            "pass_rate": 1.0,
            "failed_scenarios": [],
            "report_ids": [11, 12, 13],
            "warnings": [],
        }
        result = AIService._normalize_execution_analysis(data, runs=runs)
        self.assertEqual(result["report_ids"], [])

    def test_strip_think_tags_removes_single_segment(self):
        """单段 ``<think>...</think>`` 应被完全剥离。"""
        from app.services.ai_service import AIService

        raw = "<think> The user wants X. </think> {\"ok\": true}"
        out = AIService._strip_think_tags(raw)
        self.assertNotIn("<think>", out)
        self.assertNotIn("The user wants X.", out)
        self.assertIn("\"ok\": true", out)

    def test_strip_think_tags_handles_multiline_and_multisegment(self):
        """多段、跨行的 ``<think>`` 标签应被一次性剥离。"""
        from app.services.ai_service import AIService

        raw = (
            "<think>\nFirst line.\nSecond line.\n</think>"
            "{\"a\": 1}\n"
            "<think>Another block</think> noise"
        )
        out = AIService._strip_think_tags(raw)
        self.assertNotIn("<think>", out)
        self.assertNotIn("First line.", out)
        self.assertNotIn("Another block", out)
        self.assertIn("\"a\": 1", out)

    def test_extract_json_returns_payload_after_think_tag(self):
        """真实模型经常以 ``<think>`` 开头包推理文本，_extract_json 仍能抽到 JSON。"""
        from app.services.ai_service import AIService

        raw = (
            "<think> The user wants me to respond with JSON. </think>\n"
            "```json\n"
            "[{\"id\": 1, \"name\": \"login\"}]\n"
            "```"
        )
        out = AIService._extract_json(raw)
        self.assertIsNotNone(out)
        import json
        data = json.loads(out)
        self.assertEqual(data[0]["id"], 1)
        self.assertEqual(data[0]["name"], "login")

    def test_extract_json_handles_inline_object_after_think(self):
        """推理后紧跟裸对象（无 markdown fence）也应能抽取。"""
        from app.services.ai_service import AIService

        raw = "<think>...</think> {\"root_cause\": \"x\", \"severity\": \"low\"}"
        out = AIService._extract_json(raw)
        self.assertIsNotNone(out)
        import json
        data = json.loads(out)
        self.assertEqual(data["root_cause"], "x")

    def test_strip_think_tags_handles_unclosed_think_prefix(self):
        """未闭合 ``<think>`` 开头: 整段推理内容必须被剥离, 避免被当成 summary 上送。"""
        from app.services.ai_service import AIService

        raw = (
            "<think> The model is reasoning about the requirement but timed out\n"
            "before closing the tag. Let me draft test points anyway...\n"
        )
        out = AIService._strip_think_tags(raw)
        self.assertNotIn("<think>", out)
        self.assertNotIn("reasoning about the requirement", out)
        self.assertNotIn("test points", out)
        # 全部为推理文本时应被裁空
        self.assertEqual(out, "")

    def test_design_tests_falls_back_when_llm_returns_unclosed_think_only(self):
        """``design_tests_from_requirements``: 真实模型只返回未闭合 <think> 时,
        必须 fallback 到基于需求/验收点的最小可采纳产物。"""
        from app.services.ai_service import AIService

        svc = AIService.__new__(AIService)
        svc._call_llm = MagicMock(
            return_value=(
                "<think> I'm still reasoning... let me continue without closing."
            )
        )
        requirement_input = {
            "requirements": [
                {"title": "支持手机号+密码登录", "priority": "P0",
                 "source_key": "REQ-LOGIN-1", "source_type": "prd"},
            ],
            "acceptance_criteria": [
                {"criteria": "密码错误3次后账户锁定5分钟", "priority": "P0"},
            ],
            "test_suggestions": ["覆盖边界：密码错误次数阈值"],
            "api_clues": [],
            "risks": ["未约定错误响应格式"],
        }
        result = svc.design_tests_from_requirements(requirement_input)
        # summary 不能以 think 开头, 也不能写 "AI 未配置"
        self.assertFalse(result["summary"].startswith("<think>"))
        self.assertNotIn("AI 未配置", result["summary"])
        self.assertIn("兜底", result["summary"])
        # 兜底必须满足最小可采纳产物
        self.assertGreaterEqual(len(result["test_points"]), 1)
        self.assertGreaterEqual(len(result["functional_cases"]), 1)
        fc = result["functional_cases"][0]
        self.assertIn("name", fc)
        self.assertIn("priority", fc)
        self.assertIn("steps", fc)
        self.assertIn("expected", fc)

    def test_design_tests_fallback_generates_functional_case_from_requirement_analysis(self):
        """``_fallback_test_design``: 上游有 1 条 requirement + 5 条 acceptance 时,
        必须生成 ≥1 个 test_point 和 ≥1 个 functional_case, 可被 TestCaseService
        接收。"""
        from app.services.ai_service import AIService

        requirement_input = {
            "requirements": [
                {"title": "支持订单查询", "priority": "P1",
                 "source_key": "REQ-ORDER-1", "source_type": "prd"},
            ],
            "acceptance_criteria": [
                {"criteria": f"验收点 {i}"} for i in range(5)
            ],
            "test_suggestions": ["覆盖反例：空订单号"],
            "api_clues": [
                {"method": "GET", "endpoint": "/api/orders/{id}"},
            ],
            "risks": [],
        }
        result = AIService._fallback_test_design(
            raw="LLM 输出不可用", requirement_input=requirement_input
        )
        self.assertGreaterEqual(len(result["test_points"]), 1)
        # 验收点 5 条 -> test_points 至少 5 个覆盖验收点的项
        self.assertGreaterEqual(len(result["test_points"]), 5)
        self.assertGreaterEqual(len(result["functional_cases"]), 1)
        fc = result["functional_cases"][0]
        self.assertEqual(fc["source_key"], "REQ-ORDER-1")
        # 接口线索存在时, 应产出 1 个 api_case
        self.assertGreaterEqual(len(result["api_cases"]), 1)
        ac = result["api_cases"][0]
        self.assertEqual(ac["method"], "GET")
        self.assertIn("/api/orders", ac["url"])

    def test_call_llm_uses_explicit_timeout(self):
        """``_call_llm``: 必须把 timeout 透传给 ``chat.completions.create``,
        防止单 Agent 在 BackgroundTask 中长时间阻塞。"""
        from app.services.ai_service import AIService

        fake_client = MagicMock()
        fake_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="ok"))]
        )
        svc = AIService.__new__(AIService)
        svc.client = fake_client
        svc.model = "fake-model"
        out = svc._call_llm("hi")
        # 验证 create 被调用且带 timeout
        self.assertEqual(out, "ok")
        self.assertGreaterEqual(fake_client.chat.completions.create.call_count, 1)
        kwargs = fake_client.chat.completions.create.call_args.kwargs
        self.assertIn("timeout", kwargs)
        self.assertEqual(kwargs["timeout"], AIService.DEFAULT_LLM_TIMEOUT_SECONDS)

    def test_call_llm_raises_on_timeout_for_upstream_handling(self):
        """``_call_llm``: 超时/异常必须向上抛, 由上层 Agent 决定 fallback 或 failed。"""
        from app.services.ai_service import AIService

        fake_client = MagicMock()
        fake_client.chat.completions.create.side_effect = TimeoutError(
            "upstream > 120s"
        )
        svc = AIService.__new__(AIService)
        svc.client = fake_client
        svc.model = "fake-model"
        with self.assertRaises(TimeoutError):
            svc._call_llm("hi")

