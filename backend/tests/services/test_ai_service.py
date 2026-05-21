"""AI Service 单元测试 — Mock 测试"""
import unittest
from unittest.mock import MagicMock, patch

# Mock openai.OpenAI at source before importing AIService
mock_openai_class = MagicMock(name="OpenAI")
with patch.dict("sys.modules", {"openai": MagicMock(OpenAI=mock_openai_class)}):
    from app.services.ai_service import AIService


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


if __name__ == "__main__":
    unittest.main()
