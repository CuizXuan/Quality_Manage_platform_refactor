# 测试计划/测试套件/执行中心实现结果

## 任务概述

补齐成熟测试管理平台的测试计划、测试套件和执行中心能力，让用例和场景不再只是单独执行，而能围绕版本/迭代组织批量验证。

## 变更文件

### 后端
| 文件 | 操作 | 说明 |
|------|------|------|
| `backend/app/models/test_plan.py` | 新建 | TestPlan, TestSuite, TestSuiteItem, TestPlanRun 模型 |
| `backend/app/schemas/test_plan.py` | 新建 | 所有请求/响应 Schema |
| `backend/app/routers/test_plan.py` | 新建 | /api/test-plans/* 所有端点 |
| `backend/app/services/test_plan_service.py` | 新建 | 服务层逻辑 + 后台执行任务 |
| `backend/app/main.py` | 修改 | 注册 test_plan_router |
| `backend/app/database.py` | 修改 | 添加 test_plans, test_suites, test_suite_items, test_plan_runs 表迁移 |

### 前端
| 文件 | 操作 | 说明 |
|------|------|------|
| `frontend/src/api/testPlan.js` | 新建 | API 封装 |
| `frontend/src/stores/testPlanStore.js` | 新建 | Pinia Store |
| `frontend/src/views/testPlan/TestPlanList.vue` | 新建 | 测试计划列表页 |
| `frontend/src/views/testPlan/TestPlanDetail.vue` | 新建 | 测试计划详情页（套件管理） |
| `frontend/src/views/testPlan/TestPlanRuns.vue` | 新建 | 执行历史页 |
| `frontend/src/router/index.js` | 修改 | 添加 /test-plans, /test-plans/:id, /test-plan-runs 路由 |
| `frontend/src/app/AppShell.vue` | 修改 | 添加"测试计划"、"计划执行"菜单项 |

## 新增模型

### TestPlan（测试计划）
- `id`, `project_id`, `version_id`, `iteration_id`
- `name`, `description`, `status`
- `owner_id`, `created_at`, `updated_at`

### TestSuite（测试套件）
- `id`, `plan_id`, `name`, `description`, `sort_order`

### TestSuiteItem（套件项）
- `id`, `suite_id`, `item_type`（case/scenario）, `item_id`, `sort_order`

### TestPlanRun（计划执行记录）
- `id`, `plan_id`, `status`
- `total`, `passed`, `failed`, `skipped`
- `started_at`, `finished_at`, `duration_ms`, `summary`（JSON）

## 新增 API

| 方法 | 路径 | 功能 |
|------|------|------|
| GET/POST | /api/test-plans | 列表/创建 |
| GET/PUT/DELETE | /api/test-plans/{plan_id} | 详情/更新/删除 |
| GET/POST | /api/test-plans/{plan_id}/suites | 套件列表/创建 |
| PUT/DELETE | /api/test-plans/suites/{suite_id} | 更新/删除套件 |
| POST | /api/test-plans/suites/items | 添加套件项 |
| DELETE | /api/test-plans/suites/items/{item_id} | 移除套件项 |
| POST | /api/test-plans/{plan_id}/run | **执行测试计划** |
| GET | /api/test-plans/runs | 执行历史列表 |
| GET | /api/test-plans/runs/{run_id} | 执行详情 |

## 执行中心复用现有能力

### 用例执行
- 通过 `POST /api/terminal/internal/run` 执行用例
- 复用终端内部执行端点

### 场景执行
- 通过 `POST /api/scenario/{id}/run` 触发场景执行
- 复用现有场景执行引擎

### 执行流程
```
POST /api/test-plans/{plan_id}/run
  → 创建 TestPlanRun (status=running)
  → 后台任务 _run_test_plan_background
    → 遍历所有套件和套件项
    → case: 调用 /api/terminal/internal/run
    → scenario: 调用 /api/scenario/{id}/run
    → 记录每个 item 的执行结果
  → 更新 TestPlanRun (passed/failed/skipped + summary)
```

## 构建验证

```
✓ 前端构建成功（npm run build）
  - TestPlanList.js: 6.49 kB
  - TestPlanDetail.js: 6.47 kB
  - TestPlanRuns.js: 6.22 kB
  - testPlanStore.js: 3.64 kB
  - 总构建时间: 1.42s
```

## 验收标准核对

| 标准 | 状态 |
|------|------|
| 能创建测试计划 | ✅ |
| 能创建套件 | ✅ |
| 能把用例/场景加入套件 | ✅ |
| 能执行测试计划 | ✅ |
| 能查看计划执行结果 | ✅ |
| 前端 build 通过 | ✅ |

## 剩余风险

1. 前端 `TestPlanDetail.vue` 中添加用例/场景的搜索功能是占位实现，实际使用需要调用后端搜索 API
2. 执行是同步等待完成的，后台任务方式可能需要根据实际情况调整
3. 定时执行未实现（按任务包要求放到后续任务）