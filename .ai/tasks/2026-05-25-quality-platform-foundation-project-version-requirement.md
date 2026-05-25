# 成熟质量平台基础能力一：项目 / 版本 / 迭代 / 需求模型

## 任务目标

请为当前质量管理平台补齐成熟测试平台的基础质量对象模型：

```text
项目 -> 版本 -> 迭代 -> 需求 -> 用例 -> 场景 -> 执行 -> 报告 -> 缺陷 -> 门禁
```

本任务只做基础模型、接口、页面入口和现有模块关联字段，不做 API 资产中心、测试计划、AI 深度集成。

## 背景说明

当前系统已有用例、场景、执行、报告、缺陷、门禁，但缺少项目、版本、迭代、需求这些上游质量归属。导致后续无法回答：

- 当前版本质量如何？
- 当前迭代测了哪些需求？
- 哪些需求没有测试覆盖？
- 哪些缺陷阻塞发布？
- 报告和门禁属于哪个版本？

## 必读文件

- `AGENTS.md`
- `backend/app/main.py`
- `backend/app/database.py`
- `backend/app/models/`
- `backend/app/routers/`
- `backend/app/schemas/`
- `backend/app/services/platform_seed.py`
- `frontend/src/router/index.js`
- `frontend/src/app/AppShell.vue`
- `frontend/src/views/case/CaseManagement.vue`
- `frontend/src/views/scenario/ScenarioList.vue`
- `frontend/src/views/report/ReportList.vue`
- `frontend/src/views/report/DefectList.vue`

## 允许修改范围

- `backend/app/models/quality_foundation.py`
- `backend/app/schemas/quality_foundation.py`
- `backend/app/routers/quality_foundation.py`
- `backend/app/services/quality_foundation_service.py`
- `backend/app/models/test_case.py`
- `backend/app/models/scenario.py`
- `backend/app/models/report.py`
- `backend/app/database.py`
- `backend/app/main.py`
- `backend/app/services/platform_seed.py`
- `frontend/src/api/qualityFoundation.js`
- `frontend/src/stores/qualityFoundationStore.js`
- `frontend/src/views/foundation/**`
- `frontend/src/router/index.js`
- 现有用例、场景、报告、缺陷页面的筛选字段最小范围修改

## 禁止事项

- 不删除或弱化终端控制台。
- 不重构现有用例、场景、报告核心逻辑。
- 不引入大型依赖。
- 不做无关视觉改版。
- 不破坏现有数据，新增字段必须兼容旧数据为空。

## 实现要求

### 一、后端模型

新增：

- `QualityProject`
  - `id`
  - `name`
  - `code`
  - `description`
  - `status`
  - `created_at`
  - `updated_at`

- `QualityVersion`
  - `id`
  - `project_id`
  - `name`
  - `code`
  - `status`
  - `planned_release_at`
  - `created_at`
  - `updated_at`

- `QualityIteration`
  - `id`
  - `project_id`
  - `version_id`
  - `name`
  - `status`
  - `start_date`
  - `end_date`
  - `created_at`
  - `updated_at`

- `RequirementItem`
  - `id`
  - `project_id`
  - `version_id`
  - `iteration_id`
  - `title`
  - `description`
  - `source_type`
  - `source_key`
  - `priority`
  - `status`
  - `owner_id`
  - `created_at`
  - `updated_at`

给现有对象增加可空关联字段：

- 用例：`project_id`, `version_id`, `iteration_id`, `requirement_id`
- 场景：`project_id`, `version_id`, `iteration_id`
- 报告：`project_id`, `version_id`, `iteration_id`
- 缺陷：`project_id`, `version_id`, `iteration_id`, `requirement_id`

### 二、后端 API

新增前缀：

```text
/api/foundation
```

至少实现：

```text
GET/POST/PUT/DELETE /api/foundation/projects
GET/POST/PUT/DELETE /api/foundation/versions
GET/POST/PUT/DELETE /api/foundation/iterations
GET/POST/PUT/DELETE /api/foundation/requirements
GET /api/foundation/requirements/coverage
```

覆盖率接口返回：

- 需求总数。
- 已关联用例需求数。
- 已关联场景需求数。
- 已执行需求数。
- 有缺陷需求数。

### 三、前端页面

新增路由：

```text
/foundation/projects
/foundation/requirements
```

菜单建议：

```text
质量基础
  项目版本
  需求管理
```

页面必须贴合现有模块样式：

- 使用 CaseManagement/ScenarioList 的流动网格背景。
- 查询栏 label 带中文冒号。
- 表格透明度、分页、按钮风格一致。

### 四、现有模块关联

在用例、场景、报告、缺陷的创建/编辑/查询中逐步支持：

- 项目筛选。
- 版本筛选。
- 迭代筛选。
- 需求关联。

第一阶段可以先做列表筛选和创建时选择，不要求复杂批量迁移。

## 验收标准

- 能创建项目、版本、迭代、需求。
- 能把用例关联到需求。
- 能把场景、报告、缺陷关联到项目/版本/迭代。
- 能看到需求覆盖率。
- 旧数据不报错。
- `python -m pytest backend/tests` 尽量通过。
- `cd frontend && npm run build` 通过。

## Claude 输出要求

结束时用中文汇报：

- 新增模型和接口。
- 新增页面和菜单。
- 哪些现有模块已支持项目/版本/迭代/需求关联。
- 测试和构建结果。
- 剩余风险。

请同步写入：

- `.ai/results/2026-05-25-quality-platform-foundation-project-version-requirement-result.md`
