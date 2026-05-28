# 测试计划 / 测试套件 / 执行中心三次审查修复包

## 审查目标

审查 `.ai/results/2026-05-26-test-plan-suite-execution-center-second-review-fix-result.md` 对二次审查包的修复结果。

本轮代码主逻辑已基本修正：`/runs` 静态路由在 `/{plan_id}` 前注册，场景触发后记录为 `running`，脏 JSON 解析已改为 `_safe_json_loads`。但二次审查要求的关键回归测试没有真正覆盖实现链路，仍需补齐。

## 需要修复的问题

1. `backend/tests/services/test_test_plan_service.py`: `TestRunningScenarioSummary` 只是复制 `_run_test_plan_background` 中的 `if/elif/else` 逻辑，没有调用真实后台执行函数，也没有验证 scenario item 触发成功后 run 记录实际写入 `status="running"`、`passed=0`、`summary.running=1`。如果生产代码回退为 `summary["passed"] += 1` 或 `final_status="passed"`，当前测试仍可能通过。

2. `backend/tests/services/test_test_plan_service.py`: 脏 JSON 测试只验证 `_safe_json_loads` helper，没有验证 `_run_test_plan_background` 会把脏 `case.headers` / `case.query_params` / `case.auth_config` 转成 `{}` 并继续调用终端内部接口。二次审查要求的是“脏 JSON 字段不导致用例项因 `JSONDecodeError` 直接失败，而是按空对象继续执行到终端内部接口”，当前测试覆盖不到这个行为。

3. `backend/tests/services/test_test_plan_service.py` 或新增最小 router 测试：二次审查要求覆盖 `/api/test-plans/runs` 静态路由不会被 `/{plan_id}` 抢占。实现代码中 `backend/app/routers/test_plan.py` 已把 `/runs` 放在 `/{plan_id}` 前面，但没有测试锁住该行为。

4. `backend/app/services/test_plan_service.py`: `delete_suite` 仍重复定义两次（第一个定义会被第二个覆盖）。这不是当前功能 bug，但违反项目“小而清晰、无重复”的规范，请删除其中一个重复定义。

## 修复范围

只允许修改以下文件中解决上述问题所必需的部分：

- `backend/app/services/test_plan_service.py`
- `backend/tests/services/test_test_plan_service.py`
- 如确需 TestClient，可新增或修改一个最小路由测试文件，例如 `backend/tests/routers/test_test_plan_routes.py`

## 禁止事项

- 不改前端页面。
- 不重写测试计划服务。
- 不引入新依赖。
- 不改终端执行、场景执行引擎或认证逻辑。
- 不把测试写成复制生产条件判断的“同义反复”。

## 实现要求

### 1. 后台执行链路测试

为 `_run_test_plan_background` 补真实链路级服务测试：

- 使用临时数据库创建 `TestPlan`、`TestSuite`、`TestSuiteItem`、`TestPlanRun`。
- monkeypatch `app.services.test_plan_service.SessionLocal` 指向测试数据库 session factory。
- monkeypatch `httpx.Client`，让：
  - 场景执行接口返回 `status_code=200` 和 `{"id": 123}`。
  - 终端内部接口返回 `status_code=200` 和 `{"status_code": 200, "duration_ms": 10}`。
- 对 scenario item 验证真实 run 记录：
  - `run.status == "running"`
  - `run.passed == 0`
  - `run.failed == 0`
  - `json.loads(run.summary)["running"] == 1`
  - `json.loads(run.summary)["items"][0]["status"] == "running"`
- 对 dirty JSON case item 验证：
  - `case.headers`、`case.query_params`、`case.auth_config` 为非法 JSON 时，执行不会因 `JSONDecodeError` 失败。
  - mock 的终端内部接口收到的 `headers`、`query_params`、`auth_config` 都是 `{}`。
  - 最终 run 为 `passed`，不是 `failed`。

### 2. `/runs` 路由覆盖

优先补一个极小测试，不必依赖完整认证流程：

- 可以直接检查 `backend/app/routers/test_plan.py` 的 `router.routes` 顺序和 path：
  - `/api/test-plans/runs` 或 router 内部 path `/runs` 出现在 `/{plan_id}` 前。
  - `/runs/{run_id}` 也出现在 `/{plan_id}` 前。
- 如果已有可靠 TestClient 夹具，也可以用 TestClient 覆盖，但不要为此大改 `conftest.py`。

### 3. 删除重复方法

- 删除 `TestPlanService.delete_suite` 的重复定义之一，保留一个实现即可。

## 验收标准

1. 如果生产代码把 scenario item 又改成 passed，新增测试会失败。
2. 如果生产代码把 `_safe_json_loads` 又改回 `json.loads(case.headers)`，新增 dirty JSON 链路测试会失败。
3. 如果 `/runs` 静态路由被移到 `/{plan_id}` 后面，新增路由顺序测试会失败。
4. `backend/app/services/test_plan_service.py` 不再存在重复的 `delete_suite` 定义。

## 验证方式

```bash
cd backend
python -m pytest tests/services/test_test_plan_service.py -q
python -m pytest tests/routers/test_test_plan_routes.py -q
python -m pytest tests -q
```

如果没有新增 router 测试文件，只运行实际新增的对应测试文件即可。

## Claude 输出要求

结束时必须用中文汇报：

- 补了哪些真实链路测试。
- 删除了哪个重复定义。
- 已运行的测试命令和结果。
- `/api/test-plans/runs` 路由顺序验证结果。
- 剩余风险。

请同步写入：

- `.ai/results/2026-05-26-test-plan-suite-execution-center-third-review-fix-result.md`
