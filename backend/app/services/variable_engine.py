"""
Variable Engine - 多层级变量替换，支持 {{var}} 语法
"""
import re
import json
from typing import Optional


class VariableEngine:
    """变量引擎，按优先级替换文本中的 {{var}} 占位符"""

    PRIORITY = ["step", "scenario", "data", "environment", "global"]

    def __init__(self):
        self._variables: dict[str, dict[str, any]] = {}

    def set_variable(self, scope: str, key: str, value: any):
        if scope not in self._variables:
            self._variables[scope] = {}
        self._variables[scope][key] = value

    def set_variables(self, scope: str, data: dict):
        for k, v in data.items():
            self.set_variable(scope, k, v)

    def get_variable(self, key: str) -> Optional[str]:
        """按优先级查询变量值"""
        for scope in self.PRIORITY:
            if scope in self._variables and key in self._variables[scope]:
                return str(self._variables[scope][key])
        return None

    def replace(self, text: str) -> str:
        """递归替换文本中所有 {{var}} 占位符"""
        if not isinstance(text, str):
            return text

        pattern = re.compile(r'\{\{([^}]+)\}\}')

        def replacer(match):
            var_name = match.group(1).strip()
            value = self.get_variable(var_name)
            if value is None:
                return match.group(0)  # 未找到，保留原样
            return value

        # 迭代替换，支持嵌套变量
        result = text
        max_iterations = 10
        for _ in range(max_iterations):
            new_result = pattern.sub(replacer, result)
            if new_result == result:
                break
            result = new_result

        return result

    def replace_dict(self, data: dict) -> dict:
        """递归替换字典中的所有字符串值"""
        result = {}
        for k, v in data.items():
            if isinstance(v, str):
                result[k] = self.replace(v)
            elif isinstance(v, dict):
                result[k] = self.replace_dict(v)
            elif isinstance(v, list):
                result[k] = [self.replace(item) if isinstance(item, str) else item for item in v]
            else:
                result[k] = v
        return result

    def clear(self):
        self._variables.clear()

    def build_from_sources(self, global_vars: dict, env_vars: dict,
                           scenario_vars: dict, step_vars: dict, temp_vars: dict):
        """从多个数据源构建变量空间（按从低到高优先级）"""
        self.clear()
        self.set_variables("global", global_vars or {})
        self.set_variables("environment", env_vars or {})
        self.set_variables("scenario", scenario_vars or {})
        self.set_variables("data", {})  # 数据驱动，后续扩展
        self.set_variables("step", step_vars or {})
        self.set_variables("step", temp_vars or {})  # 临时变量最高优先级
