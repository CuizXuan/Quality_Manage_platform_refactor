"""
Data Drive Engine - 数据驱动引擎
支持 CSV/JSON 数据集，变量注入到 VariableEngine 的 "data" 作用域
内置函数：$random.int(min,max), $timestamp.now(), $uuid.v4(), $random.string(length)
"""
import csv
import io
import json
import re
import random
import time
import uuid
from typing import Optional
from app.services.variable_engine import VariableEngine
from app.services.request_executor import RequestExecutor
from app.services.scenario_executor import ScenarioExecutor


class DataDriveEngine:
    """数据驱动引擎，支持 CSV/JSON 数据集批量执行"""

    # 内置函数正则
    BUILTIN_PATTERN = re.compile(
        r'\$\((random\.int|random\.float|timestamp\.now|uuid\.v4|random\.string|random\.choice)\(([^)]*)\)\)'
    )

    def __init__(self):
        self.var_engine = VariableEngine()

    def load_dataset(self, dataset_content: str, dataset_type: str) -> list[dict]:
        """
        加载数据集
        dataset_content: CSV 或 JSON 格式的原始内容
        dataset_type: "csv" 或 "json"
        返回: list[dict] 行数据列表
        """
        if dataset_type.lower() == "csv":
            return self._load_csv(dataset_content)
        elif dataset_type.lower() == "json":
            return self._load_json(dataset_content)
        else:
            raise ValueError(f"Unsupported dataset type: {dataset_type}")

    def _load_csv(self, content: str) -> list[dict]:
        """解析 CSV 数据集"""
        reader = csv.DictReader(io.StringIO(content))
        rows = []
        for row in reader:
            # 处理内置函数
            processed_row = {}
            for k, v in row.items():
                processed_row[k] = self._process_builtin_functions(str(v))
            rows.append(processed_row)
        return rows

    def _load_json(self, content: str) -> list[dict]:
        """解析 JSON 数据集"""
        data = json.loads(content)
        if isinstance(data, list):
            rows = []
            for row in data:
                processed_row = {}
                for k, v in row.items():
                    processed_row[k] = self._process_builtin_functions(v)
                rows.append(processed_row)
            return rows
        elif isinstance(data, dict):
            # 单条记录，包装成列表
            processed = {}
            for k, v in data.items():
                processed[k] = self._process_builtin_functions(v)
            return [processed]
        else:
            raise ValueError("JSON dataset must be an array or object")

    def _process_builtin_functions(self, value):
        """处理内置函数表达式"""
        if not isinstance(value, str):
            return value

        # 递归替换内置函数
        result = value
        max_iter = 10
        for _ in range(max_iter):
            new_result = self._replace_builtin(result)
            if new_result == result:
                break
            result = new_result

        return result

    def _replace_builtin(self, text: str) -> str:
        """单次替换内置函数"""
        def replacer(match):
            func_name = match.group(1)
            args_str = match.group(2)

            try:
                if func_name == "random.int":
                    args = [a.strip() for a in args_str.split(",")]
                    min_val, max_val = int(args[0]), int(args[1])
                    return str(random.randint(min_val, max_val))
                elif func_name == "random.float":
                    args = [a.strip() for a in args_str.split(",")]
                    min_val, max_val = float(args[0]), float(args[1])
                    return str(random.uniform(min_val, max_val))
                elif func_name == "timestamp.now":
                    return str(int(time.time()))
                elif func_name == "uuid.v4":
                    return str(uuid.uuid4())
                elif func_name == "random.string":
                    length = int(args_str.strip())
                    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
                    return "".join(random.choice(chars) for _ in range(length))
                elif func_name == "random.choice":
                    args = [a.strip().strip("'\"") for a in args_str.split(",")]
                    return random.choice(args)
                else:
                    return match.group(0)
            except Exception:
                return match.group(0)

        return self.BUILTIN_PATTERN.sub(replacer, text)

    def execute_case_with_data(self, case_data: dict, env_vars: dict, data_row: dict) -> dict:
        """
        使用单行数据执行用例
        case_data: 用例数据
        env_vars: 环境变量
        data_row: 数据行（会注入到 "data" 作用域）
        返回: 执行结果
        """
        # 构建变量空间
        self.var_engine.clear()
        self.var_engine.set_variables("global", {})
        self.var_engine.set_variables("environment", env_vars or {})
        self.var_engine.set_variables("scenario", {})
        self.var_engine.set_variables("data", data_row)  # 数据驱动注入点
        self.var_engine.set_variables("step", {})

        # 对用例数据进行变量替换（数据行变量优先级最高）
        from app.services.request_executor import RequestExecutor
        executor = RequestExecutor()
        executor.var_engine.build_from_sources(
            global_vars={},
            env_vars=env_vars or {},
            scenario_vars={},
            step_vars=data_row,  # 数据行作为 step 变量注入
            temp_vars={}
        )

        # 先替换数据行中的 {{变量}} 引用
        processed_row = {}
        for k, v in data_row.items():
            if isinstance(v, str):
                processed_row[k] = self.var_engine.replace(v)
            else:
                processed_row[k] = v

        # 重新构建变量空间
        self.var_engine.clear()
        self.var_engine.set_variables("global", {})
        self.var_engine.set_variables("environment", env_vars or {})
        self.var_engine.set_variables("scenario", {})
        self.var_engine.set_variables("data", processed_row)
        self.var_engine.set_variables("step", {})

        # 替换用例数据中的变量
        processed_case = self.var_engine.replace_dict(case_data)

        return executor.execute_case(processed_case, env_vars)

    def execute_scenario_with_data(self, scenario_data: dict, env_vars: dict, data_row: dict) -> dict:
        """
        使用单行数据执行场景
        scenario_data: 场景数据
        env_vars: 环境变量
        data_row: 数据行
        返回: 执行结果
        """
        # 处理数据行中的内置函数和变量引用
        processed_row = {}
        for k, v in data_row.items():
            if isinstance(v, str):
                processed_row[k] = self._process_builtin_functions(v)
            else:
                processed_row[k] = v

        # 构建变量空间
        self.var_engine.clear()
        self.var_engine.set_variables("global", {})
        self.var_engine.set_variables("environment", env_vars or {})
        self.var_engine.set_variables("scenario", scenario_data.get("variables", {}))
        self.var_engine.set_variables("data", processed_row)
        self.var_engine.set_variables("step", {})

        # 替换场景中的变量
        processed_scenario = self.var_engine.replace_dict(scenario_data)

        # 执行场景
        executor = ScenarioExecutor()
        return executor.execute_scenario(processed_scenario, env_vars)

    def execute_all_rows(
        self,
        target: dict,
        dataset: list[dict],
        env_vars: dict,
        mode: str = "continue_on_failure"
    ) -> dict:
        """
        使用数据集批量执行目标（用例或场景）
        target: case_data 或 scenario_data
        dataset: 数据集列表
        env_vars: 环境变量
        mode: continue_on_failure / stop_on_failure
        返回: 汇总结果
        """
        total = len(dataset)
        passed = 0
        failed = 0
        skipped = 0
        results = []
        is_scenario = "steps" in target

        for i, row in enumerate(dataset):
            row_num = i + 1
            try:
                if is_scenario:
                    result = self.execute_scenario_with_data(target, env_vars, row)
                else:
                    result = self.execute_case_with_data(target, env_vars, row)

                status = result.get("status", "unknown")
                results.append({
                    "row_num": row_num,
                    "data": row,
                    "result": result,
                    "status": status
                })

                if status == "success":
                    passed += 1
                else:
                    failed += 1
                    if mode == "stop_on_failure":
                        # 标记后续行为跳过
                        for remaining in range(row_num, total):
                            skipped += 1
                            results.append({
                                "row_num": remaining + 1,
                                "data": dataset[remaining],
                                "result": None,
                                "status": "skipped"
                            })
                        break

            except Exception as e:
                failed += 1
                results.append({
                    "row_num": row_num,
                    "data": row,
                    "result": {"error": str(e), "status": "error"},
                    "status": "error"
                })
                if mode == "stop_on_failure":
                    for remaining in range(row_num, total):
                        skipped += 1
                        results.append({
                            "row_num": remaining + 1,
                            "data": dataset[remaining],
                            "result": None,
                            "status": "skipped"
                        })
                    break

        return {
            "total_rows": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "pass_rate": round(passed / total * 100, 2) if total > 0 else 0,
            "results": results,
            "mode": mode
        }
