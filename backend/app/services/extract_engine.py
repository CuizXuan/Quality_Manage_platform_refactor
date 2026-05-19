"""
Extract Engine - 从响应中提取变量
"""
import json
import re
import jsonpath_ng
from typing import Optional, Union


class ExtractEngine:
    """提取引擎，从 HTTP 响应中提取变量"""

    def execute(self, rules: list, response: dict) -> dict[str, str]:
        """
        执行提取规则
        rules: 提取规则列表
        response: 包含 status_code, headers, body, cookies 的字典
        返回: { 变量名: 值 }
        """
        extracted = {}
        rule_list = rules if isinstance(rules, list) else json.loads(rules or "[]")

        for rule in rule_list:
            if not rule.get("enabled", True):
                continue
            name = rule.get("name")
            if not name:
                continue

            value = self._extract_rule(rule, response)
            if value is not None:
                extracted[name] = value

        return extracted

    def _extract_rule(self, rule: dict, response: dict) -> Optional[str]:
        source = rule.get("source", "response_body")
        path = rule.get("path")
        header_name = rule.get("header_name")
        cookie_name = rule.get("cookie_name")
        pattern = rule.get("pattern")

        try:
            if source == "response_body":
                body = response.get("body", {})
                if isinstance(body, str):
                    try:
                        body = json.loads(body)
                    except json.JSONDecodeError:
                        return body
                return self._extract_json_path(body, path)

            elif source == "response_header":
                headers = response.get("headers", {})
                if isinstance(headers, str):
                    try:
                        headers = json.loads(headers)
                    except json.JSONDecodeError:
                        return None
                return headers.get(header_name, "") if header_name else None

            elif source == "response_cookie":
                cookies = response.get("cookies", {})
                return cookies.get(cookie_name, "") if cookie_name else None

            elif source == "regex":
                body_str = response.get("body", "")
                if isinstance(body_str, (dict, list)):
                    body_str = json.dumps(body_str)
                if pattern:
                    match = re.search(pattern, body_str)
                    if match:
                        return match.group(1) if match.groups() else match.group(0)
            return None
        except Exception:
            return None

    def _extract_json_path(self, body: Union[dict, list, str], path: str) -> Optional[str]:
        if not path:
            return None
        if not isinstance(body, (dict, list)):
            return None
        try:
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
