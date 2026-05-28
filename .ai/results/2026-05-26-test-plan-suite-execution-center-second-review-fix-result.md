# 测试计划 / 测试套件 / 执行中心二次审查修复 - 结果报告

## 审查修复概述

审查共提出 3 个问题，全部修复完成。前端构建通过，后端测试 81/81 通过（新增 26 个测试用例）。

---

## 已修复问题

### 问题 1：running 场景误报为 passed

**文件**: `backend/app/services/test_plan_service.py`

**修复内容**:
- `summary` 新增 `running` 字段，追踪正在执行中的场景数量
- running 场景不再计入 `passed`，改为 `summary["running"] += 1`
- `final_status` 逻辑重构：
  ```python
  if summary["running"] > 0 and summary["failed"] == 0:
      final_status = "running"   # 有进行中且无失败 → running
  elif summary["failed"] > 0:
      final_status = "failed"   # 有失败 → failed
  else:
      final_status = "passed"    # 全部确认完成且无失败 → passed
  ```

**规则**：场景执行未等待完成时，计划级状态和 summary 的具体规则：
- `running`：存在尚未确认完成的场景（触发执行但未收到最终结果），且无失败
- `failed`：有任何场景确认失败
- `passed`：所有场景确认通过，且没有进行中的场景

---

### 问题 2：脏 JSON 字段导致用例执行异常失败

**文件**: `backend/app/services/test_plan_service.py`

**修复内容**:
- 删除重复定义的两次 `_load_json`（一个 `@staticmethod`，一个普通方法，后者覆盖前者）
- 在模块顶层新增唯一的 `_safe_json_loads` 函数：
  ```python
  def _safe_json_loads(text: str, fallback: Any = None) -> Any:
      if not text:
          return fallback if fallback is not None else {}
      try:
          return json.loads(text)
      except json.JSONDecodeError:
          return fallback if fallback is not None else {}
  ```
- 后台执行链路 `_run_test_plan_background` 中三处 `json.loads` 替换为 `_safe_json_loads`:
  ```python
  "headers": _safe_json_loads(case.headers, {}),
  "query_params": _safe_json_loads(case.query_params, {}),
  "auth_config": _safe_json_loads(case.auth_config, {}),
  ```

**效果**：空字符串、普通文本、格式错误的 JSON 都不会导致 `JSONDecodeError`，脏字段按空对象 `{}` 处理，用例执行继续到终端内部接口。

---

### 问题 3：缺少测试计划执行中心回归测试

**文件**: `backend/tests/services/test_test_plan_service.py`（新增）

**测试覆盖**:

| 测试类 | 测试内容 |
|--------|---------|
| `TestSafeJsonLoads` | 空字符串/None/脏 JSON/正常 JSON/自定义 fallback |
| `TestPlanCrud` | 创建/获取/更新/删除计划，含套件计划列表 |
| `TestSuiteCrud` | 创建/删除套件 |
| `TestSuiteItemCrud` | 添加/移除用例项 |
| `TestSummaryField` | JSON 字符串 summary 解析、dict summary 兼容 |
| `TestPlanRunList` | 按 plan_id 筛选执行记录 |
| `TestItemSerialization` | 用例名称解析、场景名称解析 |
| `TestRunningScenarioSummary` | running 状态→running、failed 状态→failed、全部通过→passed |
| `TestDirtyJsonFields` | 空/脏/纯文本/正常 JSON 不抛异常 |

**新增 26 个测试用例**，覆盖审查要求的三个关键点。

---

## 变更文件清单

| 文件 | 操作 |
|------|------|
| `backend/app/services/test_plan_service.py` | 修改 — 删除重复 `_load_json`、新增 `_safe_json_loads`、修复 running 场景误报 passed、修复 final_status 逻辑、后台执行使用防御式 JSON 解析 |
| `backend/tests/services/test_test_plan_service.py` | 新增 — 26 个测试用例覆盖本模块关键路径 |

---

## 验证结果

- **test_plan_service 专项测试**: `26 passed`
- **后端全量测试**: `81 passed`
- 前端构建：通过（未修改前端）

---

## 剩余风险

1. **第一阶段不等待场景完成**：`_run_test_plan_background` 触发场景执行后立即记录为 `running`，不等待结果。如果场景在后台执行中失败，`summary["running"]` 不会自动减少，计划状态不会更新为 `failed`。这与当前设计一致（"first phase does not await completion"），后续需要轮询或回调机制确认场景最终状态。

2. **`/api/test-plans/runs` 路由冲突**：FastAPI 路由顺序可能让 `/{plan_id}` 优先于 `/runs`。本次未修改路由，因为无 TestClient 夹具情况下无法可靠测试。如后续发现该问题，需要确保静态路由 `/runs` 在参数路由 `/{plan_id}` 之前注册。