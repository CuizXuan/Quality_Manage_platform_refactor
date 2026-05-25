# 质量闭环第一阶段实施结果（修订版）

## 概述

本次任务基于 Codex 审查反馈，修复了真实运行时问题并补齐了测试覆盖。

**验证结果：**
- pytest 根目录命令：✅ **41 个测试全部通过**
- pytest backend 目录命令：✅ **41 个测试全部通过**
- 前端构建：✅ 构建成功（8.90s）

---

## 一、Codex 审查发现并修复的 5 个问题

### 问题 1：使用了不存在的 `ExecutionRun.triggered_by` 字段

**原因**：`ExecutionRun` 模型没有 `triggered_by` 字段，导致 `_create_report_from_run()` 在真实执行路径中会抛出 `AttributeError`。

**修复**：将 `"triggered_by": run.triggered_by` 改为 `"triggered_by": None`。

---

### 问题 2：`total` 取错字段导致通过率永远为 0

**原因**：场景执行 summary 结构是 `{total_steps, executed, passed, failed, steps}`，但原代码取 `summary.get("total", 0)` 实际取到的是 `None`，导致 `pass_rate` 错误。

**修复**：
- `total` → 取 `summary["total_steps"]`
- `skipped` → 按 `max(total_steps - executed, 0)` 计算
- `passed`、`failed` → 继续取对应字段

---

### 问题 3：`step_results` 永远为空

**原因**：执行循环中 `step_result` 只在内存里处理，从未 append 到 `summary["steps"]`。

**修复**：
1. 初始化 summary 时添加 `"steps": []`
2. 每步执行后 `summary["steps"].append(step_result)` 保留结果
3. 即使遇到 `failure_strategy == "stop"` 也会保留已执行步骤

---

### 问题 4：测试没有覆盖真实自动报告路径

**原因**：原测试只覆盖了 `ReportService.create_report()` 和门禁评估，没有直接测试 `_create_report_from_run()` 使用真实 `ExecutionRun + Scenario + 场景 summary` 的路径。

**新增测试**：
- `TestCreateReportFromRun.test_create_report_from_run_with_real_summary`：验证 5 项断言（total=2, passed=1, failed=1, pass_rate=50.0, step_results 长度=2, triggered_by=None）
- `TestCreateReportFromRun.test_create_report_from_run_idempotent`：验证幂等
- `TestCreateReportFromRun.test_create_report_skipped_calculation`：验证 skipped 计算逻辑

---

### 问题 5：根目录 pytest 命令 ModuleNotFoundError

**原因**：从项目根目录执行 `python -m pytest backend/tests` 时，`sys.path` 不包含 `backend` 目录，导致无法导入 `app` 模块。

**修复**：新增 `backend/tests/conftest.py`，在模块加载时自动将 `backend` 目录加入 `sys.path`。

---

## 二、修复后的 `_create_report_from_run` 逻辑

```python
def _create_report_from_run(db: Session, run: ExecutionRun, scenario: Scenario, summary: dict, duration_ms: int) -> None:
    """从执行记录自动创建报告"""
    # 幂等检查
    existing = db.query(Report).filter(Report.target_id == run.id, Report.report_type == "execution").first()
    if existing:
        return

    # 从真实 summary 结构提取字段
    total_steps = summary.get("total_steps", 0)
    executed = summary.get("executed", 0)
    passed = summary.get("passed", 0)
    failed = summary.get("failed", 0)
    skipped = max(total_steps - executed, 0)

    execution_data = {
        "total": total_steps,        # 用 total_steps
        "passed": passed,
        "failed": failed,
        "skipped": skipped,          # 主动计算 skipped
        "duration_ms": duration_ms,
    }
    report_summary = ReportService.build_summary(execution_data)

    report_data = {
        "name": f"{scenario.name} - 执行报告",
        "report_type": "execution",
        "target_id": run.id,
        "target_name": scenario.name,
        "summary": report_summary,
        "metrics": {
            "run_id": run.id,
            "scenario_id": scenario.id,
            "status": run.status,
            "duration_ms": duration_ms,
            "step_results": summary.get("steps", []),  # 现在有真实步骤数据
        },
        "executed_at": run.finished_at or datetime.utcnow(),
        "duration_ms": duration_ms,
        "triggered_by": None,  # ExecutionRun 无此字段，填 None
    }

    ReportRepository.create(db, report_data)
```

---

## 三、测试覆盖补充

新增 `TestCreateReportFromRun` 测试类，3 个测试用例：

| 测试 | 验证内容 |
|------|----------|
| `test_create_report_from_run_with_real_summary` | 真实 summary 结构 → 正确计算 total=2, passed=1, failed=1, skipped=0, pass_rate=50.0 |
| `test_create_report_from_run_idempotent` | 同一 run 调用两次只创建一条报告 |
| `test_create_report_skipped_calculation` | 5 total_steps - 3 executed → skipped=2, pass_rate=40.0 |

---

## 四、验证命令与结果

| 命令 | 结果 |
|------|------|
| `python3 -m pytest backend/tests --collect-only`（根目录） | ✅ 41 tests collected |
| `python3 -m pytest backend/tests`（根目录） | ✅ **41 passed** in 0.65s |
| `python3 -m pytest tests`（backend 目录） | ✅ **41 passed** in 0.64s |
| `cd frontend && npm run build` | ✅ built in 8.90s |

---

## 五、剩余风险

| 风险项 | 说明 |
|--------|------|
| 触发人信息缺失 | `triggered_by` 填 None，需缺陷/执行记录关联后才能从认证上下文获取真实用户 |
| 步骤详情粒度 | `step_results` 当前记录了 step_id、case_id、name、status、error，但未记录完整请求/响应 |
| 未在真实服务中验证 | 单元测试通过，但真实服务启动后场景执行 → 报告 → 门禁链路需实际验证 |