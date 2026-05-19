"""
Assertion Engine - 执行断言规则
"""
import json
import re
import jsonpath_ng
from typing import Optional, Union


class AssertionEngine:
    """断言引擎，执行状态码/JSONPath/响应头/响应时间等断言"""

    def __init__(self):
        self._results: list[dict] = []

    def execute(self, assertions: list, response: dict) -> list[dict]:
        """
        执行断言列表
        assertions: 断言规则列表（来自用例的 assertions 字段）
        response: 包含 status_code, headers, body, time_ms 的字典
        返回: 每个断言的执行结果
        """
        self._results = []
        assertion_list = assertions if isinstance(assertions, list) else json.loads(assertions or "[]")

        for rule in assertion_list:
            if not rule.get("enabled", True):
                continue
            result = self._execute_rule(rule, response)
            self._results.append(result)

        return self._results

    def _execute_rule(self, rule: dict, response: dict) -> dict:
        rule_id = rule.get("id", "")
        rule_type = rule.get("type", "")
        operator = rule.get("operator", "equals")
        expected = rule.get("expected")
        path = rule.get("path")
        header_name = rule.get("header_name")

        try:
            if rule_type == "status_code":
                actual = response.get("status_code", 0)
                passed = self._compare(actual, operator, int(expected))
                message = f"状态码断言: 期望 {operator} {expected}, 实际 {actual}"

            elif rule_type == "json_path":
                body = response.get("body", {})
                # 确保 body 是 dict/list 类型再提取
                if isinstance(body, str):
                    try:
                        body = json.loads(body)
                    except json.JSONDecodeError:
                        body = {}
                actual = self._extract_json_path(body, path)
                passed = self._compare(actual, operator, expected)
                message = f"JSONPath {path}: 期望 {operator} {expected}, 实际 {actual}"

            elif rule_type == "response_time":
                actual = response.get("time_ms", 0)
                passed = self._compare(actual, operator, int(expected))
                message = f"响应时间: 期望 {operator} {expected}ms, 实际 {actual}ms"

            elif rule_type == "header":
                headers = response.get("headers", {})
                actual = headers.get(header_name, "") if isinstance(headers, dict) else ""
                if operator == "exists":
                    passed = bool(actual)
                    message = f"响应头 {header_name} 存在性: {'通过' if passed else '未找到'}"
                elif operator == "equals":
                    passed = actual == expected
                    message = f"响应头 {header_name}: 期望 {expected}, 实际 {actual}"
                else:  # contains
                    passed = str(expected) in str(actual)
                    message = f"响应头 {header_name} 包含 {expected}: {'通过' if passed else '实际 ' + str(actual)}"

            elif rule_type == "body_contains":
                body = response.get("body", "")
                body_str = json.dumps(body) if isinstance(body, (dict, list)) else str(body)
                if operator == "contains":
                    passed = str(expected) in body_str
                    message = f"响应体包含 '{expected}': {'通过' if passed else '未找到'}"
                else:  # not_contains
                    passed = str(expected) not in body_str
                    message = f"响应体不包含 '{expected}': {'通过' if passed else '找到'}"
            else:
                passed = False
                message = f"未知断言类型: {rule_type}"

        except Exception as e:
            passed = False
            message = f"断言执行异常: {str(e)}"

        return {
            "id": rule_id,
            "type": rule_type,
            "path": path,
            "operator": operator,
            "passed": passed,
            "expected": expected,
            "actual": None,
            "message": message,
        }

    def _extract_json_path(self, body: Union[dict, list, str], path: str) -> Optional[str]:
        """使用 JSONPath 提取值"""
        if not path or not isinstance(body, (dict, list)):
            return None
        try:
            # 支持 $.data.id 或 data.id 两种格式
            if not path.startswith("$"):
                path = "$." + path
            jp = jsonpath_ng.parse(path)
            matches = jp.find(body)
            if matches:
                val = matches[0].value
                if isinstance(val, (dict, list)):
                    return json.dumps(val)
                return str(val)
        except Exception:
            pass
        return None

    def _compare(self, actual: any, operator: str, expected: any) -> bool:
        """比较操作"""
        try:
            if operator == "equals":
                return actual == expected
            elif operator == "not_equals":
                return actual != expected
            elif operator == "contains":
                return str(expected) in str(actual)
            elif operator == "not_contains":
                return str(expected) not in str(actual)
            elif operator == "exists":
                return actual is not None
            elif operator == "not_exists":
                return actual is None
            elif operator == "greater_than":
                return float(actual) > float(expected)
            elif operator == "less_than":
                return float(actual) < float(expected)
            elif operator == "starts_with":
                return str(actual).startswith(str(expected))
            elif operator == "ends_with":
                return str(actual).endswith(str(expected))
            elif operator == "regex":
                return bool(re.search(str(expected), str(actual)))
            return False
        except (ValueError, TypeError):
            return False
