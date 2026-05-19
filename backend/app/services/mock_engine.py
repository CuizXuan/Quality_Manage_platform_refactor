"""
Mock Engine - Mock 引擎
支持精确匹配和通配符路径匹配，条件匹配，响应模板
"""
import re
import json
import random
import time
import uuid
from typing import Optional, Any


class MockEngine:
    """Mock 引擎"""

    def __init__(self):
        self._rules: list[dict] = []

    def load_rules(self, rules: list[dict]):
        """加载 Mock 规则"""
        self._rules = rules

    def add_rule(self, rule: dict):
        """添加单个规则"""
        self._rules.append(rule)

    def match_rule(
        self,
        path: str,
        method: str,
        headers: dict = None,
        body: Any = None
    ) -> Optional[dict]:
        """
        匹配请求对应的 Mock 规则
        path: 请求路径
        method: 请求方法
        headers: 请求头
        body: 请求体
        返回: 匹配的规则，未匹配返回 None
        """
        headers = headers or {}
        body = body or {}

        for rule in self._rules:
            if not rule.get("enabled", True):
                continue

            # 方法匹配
            rule_methods = rule.get("method", [])
            if isinstance(rule_methods, str):
                rule_methods = [rule_methods]
            if rule_methods and method.upper() not in [m.upper() for m in rule_methods]:
                continue

            # 路径匹配
            rule_path = rule.get("path", "")
            if not self._match_path(path, rule_path):
                continue

            # 条件匹配
            conditions = rule.get("conditions", [])
            if not conditions or self._check_conditions(conditions, path, headers, body):
                return rule

        return None

    def _match_path(self, request_path: str, rule_path: str) -> bool:
        """路径匹配：精确匹配或通配符匹配"""
        if "*" in rule_path:
            # 通配符匹配，将 * 转换为正则
            pattern = rule_path.replace("*", ".*")
            pattern = f"^{pattern}$"
            try:
                return bool(re.match(pattern, request_path))
            except re.error:
                return False
        else:
            # 精确匹配
            return request_path == rule_path

    def _check_conditions(
        self,
        conditions: list[dict],
        path: str,
        headers: dict,
        body: Any
    ) -> bool:
        """检查条件是否满足"""
        for cond in conditions:
            cond_type = cond.get("type", "")
            target = cond.get("target", "")
            operator = cond.get("operator", "equals")
            expected = cond.get("value", "")

            if cond_type == "header":
                actual = headers.get(target, headers.get(target.lower(), ""))
                if not self._compare(actual, operator, expected):
                    return False

            elif cond_type == "body_json":
                try:
                    body_dict = body if isinstance(body, dict) else json.loads(body)
                    keys = target.split(".")
                    actual = body_dict
                    for key in keys:
                        if isinstance(actual, dict):
                            actual = actual.get(key)
                        else:
                            actual = None
                            break
                    if not self._compare(str(actual) if actual is not None else "", operator, expected):
                        return False
                except (json.JSONDecodeError, TypeError):
                    return False

            elif cond_type == "path":
                if not self._compare(path, operator, target):
                    return False

            elif cond_type == "exists":
                if operator == "equals":
                    if target == "header":
                        exists = target in headers or target.lower() in headers
                    elif target == "body":
                        exists = body is not None and body != ""
                    else:
                        exists = False
                    if bool(exists) != bool(expected):
                        return False

            elif cond_type == "equals":
                actual = self._get_value_by_target(target, path, headers, body)
                if str(actual) != str(expected):
                    return False

            elif cond_type == "contains":
                actual = self._get_value_by_target(target, path, headers, body)
                if str(expected) not in str(actual):
                    return False

        return True

    def _get_value_by_target(self, target: str, path: str, headers: dict, body: Any) -> Any:
        """根据 target 获取值"""
        if target == "path":
            return path
        elif target.startswith("header."):
            header_name = target[7:]
            return headers.get(header_name, headers.get(header_name.lower(), ""))
        else:
            return None

    def _compare(self, actual: Any, operator: str, expected: Any) -> bool:
        """比较操作"""
        actual_str = str(actual)
        expected_str = str(expected)

        if operator == "equals":
            return actual_str == expected_str
        elif operator == "not_equals":
            return actual_str != expected_str
        elif operator == "contains":
            return expected_str in actual_str
        elif operator == "not_contains":
            return expected_str not in actual_str
        elif operator == "starts_with":
            return actual_str.startswith(expected_str)
        elif operator == "ends_with":
            return actual_str.endswith(expected_str)
        elif operator == "regex":
            try:
                return bool(re.search(expected_str, actual_str))
            except re.error:
                return False
        elif operator == "gt":
            try:
                return float(actual_str) > float(expected_str)
            except ValueError:
                return False
        elif operator == "lt":
            try:
                return float(actual_str) < float(expected_str)
            except ValueError:
                return False
        elif operator == "gte":
            try:
                return float(actual_str) >= float(expected_str)
            except ValueError:
                return False
        elif operator == "lte":
            try:
                return float(actual_str) <= float(expected_str)
            except ValueError:
                return False
        else:
            return actual_str == expected_str

    def generate_response(self, rule: dict, request_data: dict) -> dict:
        """
        生成 Mock 响应
        rule: 匹配的 Mock 规则
        request_data: 请求数据 {path, method, headers, body, query_params}
        返回: 响应数据
        """
        response = rule.get("response", {})
        delay_ms = rule.get("delay_ms", 0)

        # 状态码
        status_code = response.get("status_code", 200)

        # 响应头
        resp_headers = response.get("headers", {})

        # 响应体
        body_template = response.get("body", "")

        # 应用模板
        context = {
            "request": request_data,
            "timestamp": int(time.time()),
            "uuid": str(uuid.uuid4()),
        }
        resp_body = self.apply_template(body_template, context)

        # 尝试解析 JSON
        try:
            resp_body = json.loads(resp_body)
        except (json.JSONDecodeError, TypeError):
            pass

        return {
            "status_code": status_code,
            "headers": resp_headers,
            "body": resp_body,
            "delay_ms": delay_ms,
        }

    def apply_template(self, template: str, context: dict) -> str:
        """
        应用响应模板
        支持 {{变量}} 替换和 {{$函数()}} 内置函数
        """
        if not isinstance(template, str):
            return template

        # 内置函数模式：{{$函数名(参数)}}
        func_pattern = re.compile(r'\{\{\$([a-zA-Z_][a-zA-Z0-9_]*)\(([^)]*)\)\}\}')
        # 变量替换模式：{{变量路径}}
        var_pattern = re.compile(r'\{\{([^}]+)\}\}')

        result = template

        # 先处理内置函数
        def func_replacer(match):
            func_name = match.group(1)
            args_str = match.group(2)
            return self._call_function(func_name, args_str, context)

        result = func_pattern.sub(func_replacer, result)

        # 再处理变量替换
        def var_replacer(match):
            var_path = match.group(1).strip()
            return self._get_context_value(var_path, context)

        result = var_replacer.sub(result, result)

        return result

    def _call_function(self, func_name: str, args_str: str, context: dict) -> str:
        """调用内置函数"""
        try:
            if func_name == "random.int":
                args = [a.strip() for a in args_str.split(",")]
                if len(args) >= 2:
                    return str(random.randint(int(args[0]), int(args[1])))
                return "0"
            elif func_name == "random.float":
                args = [a.strip() for a in args_str.split(",")]
                if len(args) >= 2:
                    return str(random.uniform(float(args[0]), float(args[1])))
                return "0.0"
            elif func_name == "timestamp.now":
                return str(int(time.time()))
            elif func_name == "timestamp.now_ms":
                return str(int(time.time() * 1000))
            elif func_name == "uuid.v4":
                return str(uuid.uuid4())
            elif func_name == "uuid.v1":
                return str(uuid.uuid1())
            elif func_name == "random.string":
                length = int(args_str.strip())
                chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
                return "".join(random.choice(chars) for _ in range(length))
            elif func_name == "random.choice":
                args = [a.strip().strip("'\"") for a in args_str.split(",")]
                return random.choice(args)
            elif func_name == "random.uuid":
                return str(uuid.uuid4())
            elif func_name == "env":
                # 从环境变量获取
                import os
                return os.getenv(args_str.strip(), "")
            elif func_name == "json.stringify":
                return json.dumps(context.get(args_str.strip(), ""))
            else:
                return match.group(0) if hasattr(match, 'group') else "{{$" + func_name + "()}}"
        except Exception:
            return ""

    def _get_context_value(self, path: str, context: dict) -> str:
        """获取上下文中的变量值"""
        keys = path.split(".")
        value = context
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return ""
        if value is None:
            return ""
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        return str(value)
