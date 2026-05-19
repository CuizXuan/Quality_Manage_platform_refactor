"""
Scenario Executor - 场景步骤串联执行器
"""
import json
import time
from app.services.variable_engine import VariableEngine
from app.services.assertion_engine import AssertionEngine
from app.services.extract_engine import ExtractEngine


class ScenarioExecutor:
    """场景执行器，按顺序执行多个用例步骤，支持变量传递和失败处理"""

    def __init__(self):
        self.var_engine = VariableEngine()
        self.assert_engine = AssertionEngine()
        self.extract_engine = ExtractEngine()

    async def execute_scenario(self, scenario_data: dict, env_vars: dict = None,
                               temp_vars: dict = None) -> dict:
        """
        执行场景
        scenario_data: 包含 steps 列表的场景数据
        env_vars: 环境变量
        temp_vars: 临时变量
        返回: 场景执行结果
        """
        steps = scenario_data.get("steps", [])
        scenario_vars = scenario_data.get("variables", {})

        # 初始化变量空间
        self.var_engine.clear()
        self.var_engine.set_variables("global", {})
        self.var_engine.set_variables("environment", env_vars or {})
        self.var_engine.set_variables("scenario", scenario_vars or {})
        self.var_engine.set_variables("data", {})
        self.var_engine.set_variables("step", temp_vars or {})

        total_steps = len(steps)
        passed_steps = 0
        failed_steps = 0
        skipped_steps = 0
        step_results = []
        all_extracted = {}

        execution_id = f"scenario_{int(time.time()*1000)}"

        for step in steps:
            if not step.get("enabled", True):
                skipped_steps += 1
                continue

            case_id = step.get("case_id")
            step_order = step.get("step_order", 0)
            skip_on_failure = step.get("skip_on_failure", True)
            extract_rules = step.get("extract_rules", [])

            # 获取用例数据（需要外部传入，这里假设 step 中已包含 case_data）
            case_data = step.get("case_data")
            if not case_data:
                # 如果步骤中没有用例数据，跳过
                step_results.append({
                    "step_order": step_order,
                    "case_id": case_id,
                    "case_name": step.get("case_name", f"Case #{case_id}"),
                    "status": "skipped",
                    "error": "Case data not found",
                })
                skipped_steps += 1
                continue

            # 变量替换
            from app.services.request_executor import RequestExecutor
            executor = RequestExecutor()
            executor.var_engine.build_from_sources(
                global_vars={},
                env_vars=env_vars or {},
                scenario_vars=dict(self.var_engine._variables.get("scenario", {})),
                step_vars=dict(self.var_engine._variables.get("step", {})),
                temp_vars=temp_vars or {}
            )

            try:
                result = await executor.execute_case(
                    case_data=case_data,
                    env_vars=env_vars,
                    temp_vars=dict(self.var_engine._variables.get("step", {}))
                )
            except Exception as e:
                result = {
                    "status": "error",
                    "error_message": str(e),
                    "response": {},
                    "assertion_results": [],
                }

            step_status = result.get("status", "error")
            if step_status == "success":
                passed_steps += 1
            else:
                failed_steps += 1

            # 提取变量
            step_extracted = result.get("extracted_variables", {})
            if extract_rules:
                resp = result.get("response", {})
                step_extracted = self.extract_engine.execute(extract_rules, resp)

            # 更新步骤变量到场景变量空间
            for var_name, var_value in step_extracted.items():
                self.var_engine.set_variable("scenario", var_name, var_value)
            all_extracted.update(step_extracted)

            step_results.append({
                "step_order": step_order,
                "case_id": case_id,
                "case_name": case_data.get("name", f"Case #{case_id}"),
                "status": step_status,
                "response_time_ms": result.get("response", {}).get("time_ms", 0),
                "extracted": step_extracted,
                "assertion_results": result.get("assertion_results", []),
            })

            # 失败时跳过后续步骤
            if step_status != "success" and skip_on_failure:
                remaining = total_steps - step_results.__len__()
                skipped_steps += remaining
                break

        # 汇总场景最终状态
        overall_status = "success" if failed_steps == 0 else "failure"

        return {
            "execution_id": execution_id,
            "scenario_id": scenario_data.get("id"),
            "status": overall_status,
            "summary": {
                "total_steps": total_steps,
                "passed_steps": passed_steps,
                "failed_steps": failed_steps,
                "skipped_steps": skipped_steps,
                "total_time_ms": sum(s.get("response_time_ms", 0) for s in step_results),
            },
            "steps": step_results,
            "final_variables": dict(self.var_engine._variables.get("scenario", {})),
        }
