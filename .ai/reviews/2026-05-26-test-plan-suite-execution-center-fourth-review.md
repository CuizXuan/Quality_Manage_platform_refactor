# 测试计划 / 测试套件 / 执行中心四次审查修复包

## 审查目标

审查 `.ai/results/2026-05-26-test-plan-suite-execution-center-third-review-fix-result.md` 对三次审查包的修复结果。

服务层真实链路测试已基本补齐，`delete_suite` 重复定义已删除，dirty JSON 和 running 场景主逻辑也有覆盖。但新增的路由测试存在测试隔离问题，导致当前后端全量测试并未通过。

## 当前验证结果

Codex 本地运行：

```bash
cd backend
python -m pytest tests -q
```

实际结果：

```text
85 passed, 1 error
```

错误发生在：

```text
tests/routers/test_test_plan_routes.py::TestRunsRouteOrder::test_runs_list_route_before_plan_id
```

核心异常：

```text
sqlalchemy.exc.IntegrityError: UNIQUE constraint failed: platform_roles.code
```

触发路径是 `TestClient(app)` 进入 startup，调用 `init_db()` / `seed_platform()`，重复插入 `platform_roles.code='super_admin'`。

## 需要修复的问题

1. `backend/tests/routers/test_test_plan_routes.py`: `auth_headers` fixture 中再次创建 `TestClient(app)` 获取 token，会触发 app startup seed；而 `client` fixture 本身也创建 `TestClient(app)`。多次 startup + 共享真实 `app.database.engine` 造成平台种子数据重复插入，当前全量测试失败。

2. `backend/tests/routers/test_test_plan_routes.py`: 测试直接使用 `app.database.engine` 并在 fixture 中执行 `Base.metadata.drop_all(engine)`。这是高风险测试写法，可能清空本地开发数据库或影响同一测试进程中的其他测试。路由顺序测试不应 drop 全局 app engine。

3. 三次审查的目标只是验证 `/api/test-plans/runs` 静态路由不会被 `/{plan_id}` 抢占。当前 TestClient + 登录 + 真实数据库 seed 的测试过重，且引入了与目标无关的认证和数据库副作用。

## 修复范围

只允许修改：

- `backend/tests/routers/test_test_plan_routes.py`

如确有必要，可极小修改 `backend/tests/conftest.py`，但优先不要改。

不要修改业务代码、数据库 seed、认证逻辑或测试计划服务实现。

## 禁止事项

- 不在测试中对 `app.database.engine` 执行 `drop_all`。
- 不为了通过路由顺序测试修改生产认证逻辑。
- 不把测试改成只断言状态码但仍依赖真实全局数据库 seed。
- 不引入新依赖。

## 实现要求

推荐改为纯路由顺序测试，不走 TestClient：

- 直接导入 `backend/app/routers/test_plan.py` 中的 `router`。
- 检查 `router.routes` 内部 path 顺序：
  - `/runs` 出现在 `/{plan_id}` 前。
  - `/runs/{run_id}` 出现在 `/{plan_id}` 前。
  - `/suites/{suite_id}`、`/suites/items` 等静态路径如有需要，也应在容易冲突的动态路径前。
- 测试应只验证路由注册顺序，不创建数据库、不启动 app、不登录、不触发 startup。

如果坚持使用 TestClient，必须：

- 使用隔离的临时数据库 engine。
- 通过 dependency override 替换 `get_db` 和认证依赖。
- 禁止 `drop_all(app.database.engine)`。

但本任务优先选择纯路由顺序测试，因为足以覆盖三次审查要求，且最小、稳定。

## 验收标准

1. `python -m pytest tests/routers/test_test_plan_routes.py -q` 通过。
2. `python -m pytest tests -q` 通过。
3. 路由测试不再创建 `TestClient(app)` 来登录获取 token。
4. 路由测试不再调用 `Base.metadata.drop_all(app.database.engine)`。
5. `/runs` 和 `/runs/{run_id}` 顺序仍被测试锁住。

## 验证方式

```bash
cd backend
python -m pytest tests/routers/test_test_plan_routes.py -q
python -m pytest tests/services/test_test_plan_service.py -q
python -m pytest tests -q
```

## Claude 输出要求

结束时必须用中文汇报：

- 路由测试如何改为隔离/无副作用。
- 是否仍覆盖 `/api/test-plans/runs` 不被 `/{plan_id}` 抢占。
- 已运行的测试命令和结果。
- 是否还有剩余风险。

请同步写入：

- `.ai/results/2026-05-26-test-plan-suite-execution-center-fourth-review-fix-result.md`
