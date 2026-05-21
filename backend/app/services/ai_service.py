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
            f"  expected: 期望值\n"
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

    # ── LLM Call ───────────────────────────────────────────────────────────────

    def _call_llm(self, prompt: str, system_prompt: str = "") -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
            max_tokens=2048,
        )
        return response.choices[0].message.content or ""

    # ── Response Parsers ────────────────────────────────────────────────────────

    @staticmethod
    def _extract_json(raw: str) -> Optional[str]:
        match = re.search(r"\{[\s\S]*\}|\[[\s\S]*\]", raw)
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
