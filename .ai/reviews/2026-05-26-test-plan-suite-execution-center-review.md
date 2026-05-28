# 测试计划 / 测试套件 / 执行中心审查修复包

## 审查目标

审查 `.ai/tasks/2026-05-25-test-plan-suite-execution-center.md` 对应实现，以及结果文件：

- `.ai/results/2026-05-25-test-plan-suite-execution-center-result.md`

当前实现已新增测试计划、测试套件、计划执行记录和前端页面，但存在多处会阻断验收的后端路由、响应模型、序列化和执行判定问题。请按本修复包做最小必要返工。

## 需要修复的问题

1. `backend/app/routers/test_plan.py`: `/api/test-plans/runs` 和 `/api/test-plans/runs/{run_id}` 当前定义在 `/{plan_id}`、`/{plan_id}/run` 之后。FastAPI 会先匹配 `/{plan_id}`，导致访问 `/api/test-plans/runs` 时把 `runs` 当成 `plan_id`，返回路径参数校验错误。请把静态 runs 路由放到所有 `/{plan_id}` 动态路由之前，参考 `backend/app/routers/scenario.py` 的写法。

2. `backend/app/routers/test_plan.py` + `backend/app/schemas/test_plan.py`: `GET /api/test-plans/{plan_id}` 服务层返回了 `suites`，但 `response_model=TestPlanResponse` 没有声明 `suites`，FastAPI 会过滤掉该字段，前端详情页无法展示套件。请补齐计划详情响应模型，或为详情单独定义包含 `suites/items` 的 response model。

3. `backend/app/schemas/test_plan.py` + `frontend/src/api/testPlan.js` + `frontend/src/views/testPlan/TestPlanDetail.vue`: `POST /api/test-plans/{plan_id}/suites` 的 `plan_id` 已在路径里，但 `TestSuiteCreate` 仍要求 body 必传 `plan_id`。当前前端只传 `{ name, description }`，创建套件会 422。请让 `plan_id` 只来自路径参数，body schema 不要求 `plan_id`。

4. `backend/app/services/test_plan_service.py`: `_serialize_item` 是静态方法，却通过 `item.suite.plan.db.query(...)` 查询用例/场景名称；`TestPlan` 没有 `db` 属性，详情页一旦存在套件项就会 500。请改为使用当前 `TestPlanService.db` 查询，或批量预取名称后传入序列化函数。保持函数短小，避免把复杂查询逻辑塞进一个长函数。

5. `backend/app/schemas/test_plan.py`: `TestSuiteItemResponse` 当前没有声明 `item_name`，即使服务层返回名称也会被响应模型过滤。前端 `TestPlanDetail.vue` 表格读取 `row.item_name`，需要在响应模型中保留。

6. `backend/app/services/test_plan_service.py`: 用例执行通过 `/api/terminal/internal/run` 后，只判断 HTTP 响应码是否为 200。该内部接口即使被测接口返回 500，也会以 HTTP 200 返回业务结果，真实状态在响应 JSON 的 `status_code` / `error` 中。请按终端执行结果判断通过/失败，并记录真实 `response_status`、`duration_ms`、`error`。

7. `backend/app/services/test_plan_service.py`: 场景执行调用 `/api/scenario/{id}/run` 只拿到“已创建执行任务”的 HTTP 200，就立即把场景标记为 passed。现有场景接口是后台执行，返回 run id 不代表执行成功。第一阶段至少不能误报通过：请改为记录 `running`/`skipped`/`pending` 这类非通过状态，或在合理范围内轮询 `/api/scenario/runs/{run_id}` 等待完成后再判定。验收标准是计划级 summary 不得把尚未完成或实际失败的场景记为 passed。

8. `frontend/src/views/testPlan/TestPlanDetail.vue`: 添加用例/场景弹窗的 `searchItems` 目前永远返回空数组，导致无法从 UI 完成“把用例/场景加入套件”的验收项。请复用现有用例和场景列表 API 做搜索/列表加载，至少支持按名称搜索和点击添加。不要新发明页面样式，沿用当前弹窗结构即可。

9. `backend/app/services/test_plan_service.py`: JSON 字段解析直接使用 `json.loads(case.headers)` 等，遇到空字符串或历史脏数据会导致整条 item 失败。请抽一个小的 `_load_json` 辅助函数，复用 `scenario_service.py` 的防御式写法。

10. `backend/app/routers/test_plan.py` / `backend/app/services/test_plan_service.py`: 创建套件、添加套件项前缺少父级存在性校验。不存在的 `plan_id` / `suite_id` 可能创建孤儿数据或数据库错误。请在服务层或路由层返回明确 404。

## 修复范围

只允许修改以下文件中解决上述问题所必需的部分：

- `backend/app/schemas/test_plan.py`
- `backend/app/routers/test_plan.py`
- `backend/app/services/test_plan_service.py`
- `frontend/src/api/testPlan.js`
- `frontend/src/stores/testPlanStore.js`
- `frontend/src/views/testPlan/TestPlanDetail.vue`
- 如必须复用现有列表 API，可小范围读取并调用已有 `frontend/src/api/**` 文件，但不要重写无关模块。

## 禁止事项

- 不删除现有测试计划、套件、执行中心功能。
- 不重写终端控制台、场景执行引擎或路由体系。
- 不引入 Celery、Redis、复杂任务队列或新的大型依赖。
- 不实现定时执行；本任务仍只修复第一阶段手动执行。
- 不做无关 UI 改版，不新建一套页面视觉语言。
- 不修改本审查修复包。

## 验证方式

修复后请至少运行：

```bash
cd backend
python -m pytest
```

```bash
cd frontend
npm run build
```

并做一轮手工接口/页面冒烟：

1. 创建测试计划成功。
2. 进入计划详情能看到 `suites` 字段，不被 response model 过滤。
3. 创建套件成功，body 不需要传 `plan_id`。
4. 用弹窗能搜索并添加至少一个用例或场景。
5. 刷新详情页后套件项仍显示类型、ID、名称。
6. 访问 `/api/test-plans/runs` 返回执行历史列表，不被 `/{plan_id}` 抢占。
7. 执行包含失败用例的计划时，计划执行结果不能误报全部 passed。

## Claude 输出要求

结束时必须用中文汇报：

- 已修复哪些审查问题。
- 变更文件清单。
- 已运行的测试、构建和手工验证。
- 如果场景执行采用轮询或非通过状态记录，请说明具体策略。
- 剩余风险。
