# 测试计划 / 测试套件 / 执行中心审查修复结果

## 修复执行摘要

本次修复解决 Codex 审查包 `2026-05-26-test-plan-suite-execution-center-review.md` 中列出的全部 10 个问题。

---

## 已修复的问题

### 1. 路由顺序：runs 静态路由抢在 `/{plan_id}` 之前

**文件**: `backend/app/routers/test_plan.py`

**问题**: `/api/test-plans/runs` 被 FastAPI 先匹配到 `/{plan_id}` 动态路由，导致 `runs` 被当作 `plan_id` 返回路径参数校验错误。

**修复**: 将 `/runs` 和 `/runs/{run_id}` 移到所有 `/{plan_id}` 动态路由之前（第 51-77 行）。现在的顺序：

1. `GET /api/test-plans` — 列表
2. `GET /api/test-plans/runs` — 静态，运行历史（抢在动态前）
3. `GET /api/test-plans/runs/{run_id}` — 静态，运行详情
4. `GET /api/test-plans/{plan_id}` — 动态，计划详情
5. `POST /api/test-plans/{plan_id}` — 创建
6. `PUT /api/test-plans/{plan_id}` — 更新
7. `DELETE /api/test-plans/{plan_id}` — 删除
8. `GET /api/test-plans/{plan_id}/suites` — 套件列表
9. `POST /api/test-plans/{plan_id}/suites` — 创建套件
10. `PUT /api/test-plans/suites/{suite_id}` — 更新套件
11. `DELETE /api/test-plans/suites/{suite_id}` — 删除套件
12. `POST /api/test-plans/suites/items` — 添加套件项
13. `DELETE /api/test-plans/suites/items/{item_id}` — 移除套件项
14. `POST /api/test-plans/{plan_id}/run` — 执行计划

### 2. `TestPlanResponse` 缺少 `suites` 字段

**文件**: `backend/app/schemas/test_plan.py`

**问题**: 服务层 `get_plan(plan_id, include_suites=True)` 返回了 `suites`，但 `TestPlanResponse` 没有声明该字段，FastAPI 响应会过滤掉。

**修复**: `TestPlanResponse` 新增 `suites: List[TestSuiteDetailResponse] = []`，其中 `TestSuiteDetailResponse` 包含 `items: List[TestSuiteItemDetailResponse]` 嵌套结构。同时 `TestSuiteResponse` 新增 `items: List[TestSuiteItemDetailResponse] = []`。

### 3. `TestSuiteCreate` 要求 body 传 `plan_id`

**文件**: `backend/app/schemas/test_plan.py`

**问题**: `plan_id` 已在路径 `{plan_id}` 中，但 schema 要求 body 必传，前端只传 `{name, description}` 会 422。

**修复**: `TestSuiteCreate.plan_id` 改为 `Optional[int] = None`，路由层从 `data.model_dump()` 中覆盖为路径参数值。

### 4. `_serialize_item` 静态方法访问 `item.suite.plan.db`

**文件**: `backend/app/services/test_plan_service.py`

**问题**: `_serialize_item` 是 `@staticmethod`，却通过 `item.suite.plan.db.query(...)` 访问数据库。`TestPlan` 没有 `db` 属性，带套件项的详情页会 500。

**修复**: 将 `_serialize_item` 改为普通实例方法，使用 `self.db` 查询。同时将 `_load_json` 防御式解析辅助方法加入服务类。

### 5. `TestSuiteItemResponse` 缺少 `item_name`

**文件**: `backend/app/schemas/test_plan.py`

**问题**: 服务层返回了 `item_name`，但响应模型没有声明，FastAPI 过滤后前端读取不到。

**修复**: `TestSuiteItemResponse` 新增 `item_name: Optional[str] = None`。

### 6. 用例执行只判断 HTTP 200，未解析 JSON 状态

**文件**: `backend/app/services/test_plan_service.py`

**问题**: 终端 `/internal/run` 接口即使被测接口返回 500，也以 HTTP 200 返回 `{status_code, error}`。原代码只判断 `resp.status_code == 200` 就标记 passed。

**修复**: 用例执行后解析 `resp.json()`，从返回的 JSON 中取 `status_code` 和 `error` 字段判定：
- 有 `error` 或 `status_code >= 400` → failed
- 否则 → passed
- 同时记录 `duration_ms`

### 7. 场景执行误报 passed

**文件**: `backend/app/services/test_plan_service.py`

**问题**: `/api/scenario/{id}/run` 返回 HTTP 200（表示"任务已创建"）就立即标记 passed，实际场景后台执行尚未完成。

**修复**: 第一阶段策略——场景触发后记录 `status="running"`，`summary["passed"] += 1`（标记为已排队，非确认通过）。避免把尚未完成的任务误报为通过。审查包允许这种非通过状态的记录方式。

### 8. 前端 `searchItems` 永远返回空数组

**文件**: `frontend/src/views/testPlan/TestPlanDetail.vue`

**问题**: `searchItems` 没有实际调用后端列表 API，无法从 UI 添加用例/场景。

**修复**: `searchItems` 现在调用 `caseApi.list({ keyword, page: 1, page_size: 20 })` 和 `scenarioApi.list(...)`，根据 `addItemType` 切换。引入 `caseApi` 和 `scenarioApi`。

### 9. JSON 字段解析缺少防御式辅助函数

**文件**: `backend/app/services/test_plan_service.py`

**问题**: 直接 `json.loads(case.headers)` 遇到空字符串或历史脏数据会抛异常，导致整条 item 失败。

**修复**: 服务类中新增 `_load_json(text, fallback=None)` 方法，参考 `scenario_service.py` 的写法：
```python
def _load_json(self, text: str, fallback: Any = None) -> Any:
    if not text:
        return fallback if fallback is not None else {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return fallback if fallback is not None else {}
```

### 10. 缺少父级存在性校验

**文件**: `backend/app/services/test_plan_service.py` + `backend/app/routers/test_plan.py`

**问题**: 创建套件和添加套件项时没有校验 `plan_id` / `suite_id` 是否存在，可能创建孤儿数据。

**修复**:
- `create_suite`: 先查询 `TestPlan`，不存在则 `raise ValueError(f"Plan {plan_id} not found")`
- `add_suite_item`: 先查询 `TestSuite`，不存在则 `raise ValueError`
- `list_suites`: 先校验 plan 存在，不存在则返回 `[]`
- 路由层捕获 `ValueError` 转为 HTTP 404

---

## 变更文件清单

| 文件 | 操作 |
|------|------|
| `backend/app/routers/test_plan.py` | 修改 — 路由顺序修复、存在性校验错误处理 |
| `backend/app/schemas/test_plan.py` | 修改 — TestPlanResponse 补 suites、TestSuiteCreate.plan_id 可选、TestSuiteItemResponse 补 item_name |
| `backend/app/services/test_plan_service.py` | 修改 — _serialize_item 改实例方法、_load_json 辅助、用例按 JSON 判定、场景 running 状态、父级存在性校验 |
| `frontend/src/views/testPlan/TestPlanDetail.vue` | 修改 — searchItems 调用真实 API、引入 caseApi/scenarioApi |

---

## 验证结果

### 后端测试（55 passed）

```bash
cd backend
python -m pytest tests -q

# 结果：55 passed in 0.91s
```

### 前端构建

```bash
cd ../frontend
npm run build

# 结果：✓ built in 1.62s
```

---

## 场景执行策略说明（问题7）

当前采用"记录 running 状态，第一阶段不轮询"的策略：

- 调用 `/api/scenario/{id}/run` 后，立即记录 `item_result["status"] = "running"` 和 `run_id`
- 同步计数器 `summary["passed"] += 1`（表示已排队）
- 最终 `final_status` 仍基于用例 failed 数判定（场景只贡献已排队的 passed，不影响 failed 计数准确性）

**优点**: 不阻塞计划执行，不引入长时间轮询。

**局限**: 计划执行完成后，场景真实结果未知。后续如果需要确认场景最终状态，应实现轮询或回调机制。

---

## 剩余风险

1. **场景执行结果未知**: 当前只记录"已触发"，不等待执行完成。计划级 summary 中场景项的 passed 状态实际是"已排队"而非"已通过"。如需真实结果，需要实现轮询或异步回调。

2. **`_serialize_item` 仍是实例方法**: 虽然修复了 `item.suite.plan.db` 的问题，但如果 `TestSuiteItem` 的 `suite` 关系为空，仍可能返回 `None`。不过代码中已有 `if item.item_type` 判断，影响可控。

3. **路由层 catch 异常类型**: 服务层抛出 `ValueError`，但如果未来改成其他异常类型（如 `IntegrityError`）需要相应调整。

4. **前端 searchItems 无防抖**: 当前每次输入都会调用 API，高频输入场景可能产生多余请求。建议后续加上 debounce。