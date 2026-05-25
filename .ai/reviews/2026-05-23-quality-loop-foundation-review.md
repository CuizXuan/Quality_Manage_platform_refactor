# 质量闭环第一阶段实现返工要求

## 审查目标

请修复 `.ai/tasks/2026-05-23-quality-loop-foundation.md` 实现中的真实运行时问题，并补齐测试覆盖。

当前实现报告称“场景执行 -> 自动生成报告 -> 报告一键评估门禁”已完成，但 Codex 复核发现：自动报告生成在真实场景执行路径中仍会失败或生成错误数据。

## 必读文件

- `.ai/tasks/2026-05-23-quality-loop-foundation.md`
- `.ai/results/2026-05-23-quality-loop-foundation-result.md`
- `backend/app/services/scenario_service.py`
- `backend/app/models/scenario.py`
- `backend/app/models/report.py`
- `backend/app/repositories/execution_repository.py`
- `backend/app/repositories/report_repository.py`
- `backend/tests/services/test_report_service.py`
- `backend/pytest.ini`

## 允许修改范围

- `backend/app/services/scenario_service.py`
- `backend/tests/services/test_report_service.py`
- 如确需保证根目录 pytest 命令通过，可最小范围修改：
  - `backend/pytest.ini`
  - `backend/tests/conftest.py`
  - `backend/requirements.txt`
- 可更新 `.ai/results/2026-05-23-quality-loop-foundation-result.md`

## 禁止事项

- 不做无关重构。
- 不改变已有 API 响应结构。
- 不引入大型依赖。
- 不把只在 `backend` 目录下通过的命令，汇报成根目录命令也通过。
- 不删除已有测试。

## 必须修复的问题

### 1. 自动报告使用了不存在的 `ExecutionRun.triggered_by`

当前代码：

```python
"triggered_by": run.triggered_by,
```

但 `backend/app/models/scenario.py` 中 `ExecutionRun` 没有 `triggered_by` 字段。

这会导致 `_create_report_from_run()` 在真实执行路径中抛出：

```text
AttributeError: 'ExecutionRun' object has no attribute 'triggered_by'
```

请修复：

- 不要读取不存在字段。
- 如果当前执行记录无法知道触发人，报告中 `triggered_by` 应填 `None`。
- 如未来要支持触发人，应另起任务设计认证上下文传递，不在本次扩展。

### 2. 自动报告 total 取错字段，导致通过率错误

当前场景执行 summary 实际结构：

```python
summary = {
    "total_steps": len(steps),
    "executed": 0,
    "passed": 0,
    "failed": 0,
}
```

但自动报告代码使用：

```python
"total": summary.get("total", 0)
```

因此真实场景报告 `total` 会变成 0，`pass_rate` 也会变成 0。

请修复：

- `total` 应优先取 `summary["total"]`，不存在时取 `summary["total_steps"]`。
- `skipped` 可按 `max(total - executed, 0)` 计算；如果 summary 已有 skipped，优先使用。
- `passed`、`failed` 继续取 summary 对应字段。
- 确保报告 summary 对场景执行结构正确：
  - total = total_steps
  - passed = passed
  - failed = failed
  - skipped = total_steps - executed
  - pass_rate = passed / total * 100

### 3. `step_results` 永远为空

当前代码：

```python
"step_results": summary.get("steps", [])
```

但场景执行循环中没有把 `step_result` 加入 `summary["steps"]`。

请修复：

- 初始化 summary 时包含 `"steps": []`。
- 每个步骤执行后把 `step_result` append 到 `summary["steps"]`。
- 即使遇到 `failure_strategy == "stop"` 也要保留已执行步骤结果。
- 报告 `metrics.step_results` 应能看到步骤摘要。

### 4. 测试没有覆盖真实自动报告路径

当前新增测试覆盖了 `ReportService.create_report()` 和门禁评估，但没有覆盖 `_create_report_from_run()` 使用真实 `ExecutionRun` + `Scenario` + 场景 summary 的路径，因此漏掉了上面的运行时错误。

请补充测试：

- 直接测试 `_create_report_from_run()`。
- 构造 `Scenario` 和 `ExecutionRun`，summary 使用真实场景执行结构：

```python
{
    "total_steps": 2,
    "executed": 2,
    "passed": 1,
    "failed": 1,
    "steps": [
        {"step_id": 1, "status": "passed"},
        {"step_id": 2, "status": "failed"},
    ],
}
```

断言：

- 创建一条 Report。
- `report.summary["total"] == 2`
- `report.summary["passed"] == 1`
- `report.summary["failed"] == 1`
- `report.summary["pass_rate"] == 50.0`
- `report.metrics["run_id"] == run.id`
- `report.metrics["scenario_id"] == scenario.id`
- `report.metrics["step_results"]` 长度为 2
- `report.triggered_by is None`

还要测试幂等：

- 同一个 run 调用 `_create_report_from_run()` 两次，只创建一条报告。

### 5. 根目录 pytest 命令未通过

Codex 复核结果：

从项目根目录执行：

```text
python -m pytest backend\tests --collect-only
```

当前失败：

```text
ModuleNotFoundError: No module named 'app'
```

但从 `backend` 目录执行：

```text
python -m pytest tests --collect-only
```

可以收集 38 个测试。

原任务验收要求包含根目录命令：

```text
python -m pytest backend/tests --collect-only
python -m pytest backend/tests
```

请修复或明确调整验证方式。优先修复，让根目录命令也能通过。

建议方案：

- 在 `backend/tests/conftest.py` 中把 `backend` 目录加入 `sys.path`。
- 或在 pytest 配置中设置合理 pythonpath。
- 不要依赖用户手工设置 `PYTHONPATH`。

## 验证方式

请至少运行并汇报：

```text
python -m pytest backend/tests --collect-only
python -m pytest backend/tests
cd backend && python -m pytest tests --collect-only
cd backend && python -m pytest tests
cd frontend && npm run build
```

如果 Windows PowerShell 使用 `cd backend && ...` 不兼容，请分别进入目录或说明实际执行命令。

## 输出要求

结束时必须用中文汇报：

- 修复了哪些真实问题。
- 为什么之前测试没有覆盖到。
- 新增了哪些测试。
- 根目录 pytest 命令是否通过。
- backend 目录 pytest 命令是否通过。
- 前端 build 是否通过。
- 剩余风险。

请同步更新：

- `.ai/results/2026-05-23-quality-loop-foundation-result.md`
