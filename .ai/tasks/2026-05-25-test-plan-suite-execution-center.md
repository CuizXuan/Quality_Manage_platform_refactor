# 成熟质量平台基础能力三：测试计划 / 测试套件 / 执行中心

## 任务目标

请补齐成熟测试管理平台的测试计划、测试套件和执行中心能力，让用例和场景不再只是单独执行，而能围绕版本/迭代组织批量验证。

## 背景说明

当前系统已有用例、场景、执行记录，但缺少：

- 测试计划。
- 测试套件。
- 批量执行。
- 计划执行历史。
- 执行进度。
- 计划级报告。

这部分是对齐 TestRail 类测试管理平台的关键。

## 必读文件

- `backend/app/models/test_case.py`
- `backend/app/models/scenario.py`
- `backend/app/routers/scenario.py`
- `backend/app/services/scenario_service.py`
- `backend/app/services/report_service.py`
- `frontend/src/views/case/CaseManagement.vue`
- `frontend/src/views/scenario/ScenarioList.vue`
- `frontend/src/views/scenario/ExecutionHistory.vue`
- `frontend/src/views/report/ReportList.vue`

## 允许修改范围

- `backend/app/models/test_plan.py`
- `backend/app/schemas/test_plan.py`
- `backend/app/routers/test_plan.py`
- `backend/app/services/test_plan_service.py`
- `backend/app/main.py`
- `backend/app/database.py`
- `backend/app/services/platform_seed.py`
- `frontend/src/api/testPlan.js`
- `frontend/src/stores/testPlanStore.js`
- `frontend/src/views/testPlan/**`
- `frontend/src/router/index.js`

## 禁止事项

- 不删除现有场景执行。
- 不重写终端控制台。
- 不引入复杂任务队列；第一阶段可同步或复用现有后台任务。
- 不做定时执行，定时执行后续任务再做。

## 实现要求

### 一、后端模型

新增：

- `TestPlan`
  - `id`
  - `project_id`
  - `version_id`
  - `iteration_id`
  - `name`
  - `description`
  - `status`
  - `owner_id`
  - `created_at`
  - `updated_at`

- `TestSuite`
  - `id`
  - `plan_id`
  - `name`
  - `description`
  - `sort_order`

- `TestSuiteItem`
  - `id`
  - `suite_id`
  - `item_type`：`case` / `scenario`
  - `item_id`
  - `sort_order`

- `TestPlanRun`
  - `id`
  - `plan_id`
  - `status`
  - `total`
  - `passed`
  - `failed`
  - `skipped`
  - `started_at`
  - `finished_at`
  - `duration_ms`
  - `summary`

### 二、后端 API

前缀：

```text
/api/test-plans
```

接口：

```text
GET/POST/PUT/DELETE /api/test-plans
GET/POST/PUT/DELETE /api/test-plans/{plan_id}/suites
POST /api/test-plans/suites/{suite_id}/items
DELETE /api/test-plans/suites/items/{item_id}
POST /api/test-plans/{plan_id}/run
GET /api/test-plans/runs
GET /api/test-plans/runs/{run_id}
```

执行要求：

- 套件可包含用例和场景。
- 第一阶段允许场景项调用现有场景执行。
- 用例项可通过终端内部执行能力执行。
- 计划执行结束后生成计划级 summary。
- 后续可接报告中心，本任务至少记录 TestPlanRun。

### 三、前端页面

新增路由：

```text
/test-plans
/test-plans/:id
/test-plan-runs
```

页面：

- 测试计划列表。
- 测试计划详情。
- 套件管理。
- 添加用例/场景。
- 执行计划。
- 执行历史。

样式必须与现有模块一致。

## 验收标准

- 能创建测试计划。
- 能创建套件。
- 能把用例/场景加入套件。
- 能执行测试计划。
- 能查看计划执行结果。
- 前端 build 通过。

## Claude 输出要求

中文汇报：

- 新增模型、接口、页面。
- 执行中心如何复用现有用例/场景执行。
- 测试和构建结果。
- 剩余风险。

请同步写入：

- `.ai/results/2026-05-25-test-plan-suite-execution-center-result.md`
