# 质量平台五项能力闭环修复任务

## 任务目标

请在现有实现基础上补齐以下 5 类能力的闭环缺口，使系统从“功能已搭建”推进到“可手工验收、可真实串联”的状态：

1. 质量资产归属贯通。
2. API 资产中心对齐 Apifox 的归属、导入、调试、生成用例链路。
3. 测试计划/套件/执行中心对齐 TestRail 的归属筛选与执行管理。
4. AI 中枢嵌入测试流程，修复建议历史断链。
5. 质量趋势、发布准入和管理看板可运行。

本任务只做完善和修复，**不要提交代码**。实现后由用户手工测试和检查。

## 背景说明

Codex 已核查当前系统，发现这些能力大体已经实现：

- 质量基础模型有项目、版本、迭代、需求。
- 用例、场景、报告、缺陷有归属字段。
- API 资产中心已有分组、API 定义、OpenAPI 导入导出、调试、生成用例。
- 测试计划已有计划、套件、套件项、计划执行、执行历史。
- AI 已接入用例断言、用例变体、执行失败分析、报告总结、场景步骤建议。
- 质量分析已有后端 API 和前端页面。

但目前仍存在几个影响手工验收的断点：

- `frontend/src/views/qualityAnalytics/QualityAnalytics.vue` 调用了 `analyticsStore.setFilters(...)`，但 `frontend/src/stores/qualityAnalyticsStore.js` 没有该 action，质量看板页面存在运行时报错风险。
- API 资产生成用例时，`backend/app/services/api_asset_service.py` 未把 `ApiDefinition.project_id` 继承到 `TestCase.project_id`，也缺少从用例追溯到 API 资产的稳定字段。
- `frontend/src/views/apiAsset/ApiAssetCenter.vue` 没有项目筛选/项目选择，新建 API、分组和 OpenAPI 导入无法从页面维护项目归属。
- `frontend/src/views/testPlan/TestPlanList.vue` 的新建/编辑表单没有暴露项目/版本/迭代字段，添加用例/场景时也没有按计划归属过滤。
- `frontend/src/views/ai/SuggestionHistory.vue` 把建议历史当成 `fetchAnalysis(query)` 调用，但后端只有 `/api/ai/analysis/{analysis_id}`，没有建议列表 API，页面大概率不可用。
- `frontend/src/views/platform/Dashboard.vue` 中部分快捷入口仍指向旧路径，例如 `/cases`、`/quality-gates`，需要对齐当前路由。

## 视觉/交互基准页

- API 资产中心页面：继续基于 `frontend/src/views/apiAsset/ApiAssetCenter.vue`，只补项目筛选和归属字段，不重做页面风格。
- 测试计划列表页：参考 `frontend/src/views/scenario/ScenarioList.vue` 的项目/版本/迭代级联筛选方式。
- 测试计划详情页：继续基于 `frontend/src/views/testPlan/TestPlanDetail.vue`，不要改成新布局。
- 质量看板：继续基于 `frontend/src/views/qualityAnalytics/QualityAnalytics.vue`，只修运行时链路和必要交互。
- 菜单和入口路径：对照 `frontend/src/app/AppShell.vue` 当前 `menuList`。

## 必读文件

- `AGENTS.md`
- `.ai/results/2026-05-25-quality-platform-foundation-project-version-requirement-result.md`
- `.ai/results/2026-05-25-api-asset-center-retain-terminal-result.md`
- `.ai/results/2026-05-26-api-asset-center-retain-terminal-review-fix-result.md`
- `.ai/results/2026-05-26-api-asset-center-retain-terminal-second-review-fix-result.md`
- `.ai/results/2026-05-25-test-plan-suite-execution-center-result.md`
- `.ai/results/2026-05-26-test-plan-suite-execution-center-second-review-fix-result.md`
- `.ai/results/2026-05-26-test-plan-suite-execution-center-third-review-fix-result.md`
- `.ai/results/2026-05-25-ai-center-embed-testing-workflow-result.md`
- `.ai/results/2026-05-25-quality-analytics-release-gate-result.md`
- `.ai/results/2026-05-26-quality-analytics-release-gate-review-fix-result.md`
- `backend/app/models/test_case.py`
- `backend/app/models/api_asset.py`
- `backend/app/models/test_plan.py`
- `backend/app/models/quality_foundation.py`
- `backend/app/routers/api_asset.py`
- `backend/app/routers/test_plan.py`
- `backend/app/routers/ai.py`
- `backend/app/routers/quality_analytics.py`
- `backend/app/services/api_asset_service.py`
- `backend/app/services/test_plan_service.py`
- `backend/app/services/quality_analytics_service.py`
- `backend/app/repositories/ai_repository.py`
- `frontend/src/stores/qualityAnalyticsStore.js`
- `frontend/src/stores/qualityFoundationStore.js`
- `frontend/src/stores/aiStore.js`
- `frontend/src/stores/testPlanStore.js`
- `frontend/src/stores/apiAssetStore.js`
- `frontend/src/api/ai.js`
- `frontend/src/api/apiAsset.js`
- `frontend/src/api/testPlan.js`
- `frontend/src/views/qualityAnalytics/QualityAnalytics.vue`
- `frontend/src/views/apiAsset/ApiAssetCenter.vue`
- `frontend/src/views/testPlan/TestPlanList.vue`
- `frontend/src/views/testPlan/TestPlanDetail.vue`
- `frontend/src/views/testPlan/TestPlanRuns.vue`
- `frontend/src/views/ai/SuggestionHistory.vue`
- `frontend/src/views/platform/Dashboard.vue`
- `backend/tests/services/test_api_asset_service.py`
- `backend/tests/services/test_test_plan_service.py`
- `backend/tests/services/test_quality_analytics_service.py`
- `backend/tests/routers/test_test_plan_routes.py`

## 允许修改范围

- `backend/app/models/test_case.py`
- `backend/app/database.py`
- `backend/app/schemas/api_asset.py`
- `backend/app/schemas/test_plan.py`
- `backend/app/schemas/ai.py`
- `backend/app/routers/api_asset.py`
- `backend/app/routers/test_plan.py`
- `backend/app/routers/ai.py`
- `backend/app/services/api_asset_service.py`
- `backend/app/services/test_plan_service.py`
- `backend/app/repositories/ai_repository.py`
- `frontend/src/api/apiAsset.js`
- `frontend/src/api/testPlan.js`
- `frontend/src/api/ai.js`
- `frontend/src/stores/apiAssetStore.js`
- `frontend/src/stores/testPlanStore.js`
- `frontend/src/stores/qualityAnalyticsStore.js`
- `frontend/src/stores/aiStore.js`
- `frontend/src/views/apiAsset/ApiAssetCenter.vue`
- `frontend/src/views/testPlan/TestPlanList.vue`
- `frontend/src/views/testPlan/TestPlanDetail.vue`
- `frontend/src/views/qualityAnalytics/QualityAnalytics.vue`
- `frontend/src/views/ai/SuggestionHistory.vue`
- `frontend/src/views/platform/Dashboard.vue`
- `backend/tests/services/test_api_asset_service.py`
- `backend/tests/services/test_test_plan_service.py`
- `backend/tests/services/test_quality_analytics_service.py`
- `backend/tests/routers/test_test_plan_routes.py`
- 必要时可新增针对上述修复的小型测试文件。
- 可写入结果报告：`.ai/results/2026-05-27-quality-platform-closure-fixes-result.md`

## 禁止事项

- **不要执行 `git add`、`git commit`、`git push`，不要创建提交。**
- 不做无关重构，不统一改风格，不重写已有页面。
- 不删除已有 API 资产中心、测试计划、AI 中枢、质量看板功能。
- 不改变现有公开接口的成功响应结构，除非是为补齐新增字段且前端同步兼容。
- 不引入新依赖。
- 不使用前端 mock 数据掩盖后端链路问题。
- 不把 `source_debug_id` 误用为 API 资产来源字段；如需追溯 API 来源，请使用清晰命名的字段。
- 不修改允许范围之外的文件，除非先在结果报告中说明原因。

## 实现要求

### 一、修复质量看板运行时断链

1. 在 `frontend/src/stores/qualityAnalyticsStore.js` 增加 `setFilters(nextFilters)` action。
2. `setFilters` 应只合并已知字段：
   - `project_id`
   - `version_id`
   - `iteration_id`
   - `start_date`
   - `end_date`
   - `days`
3. `QualityAnalytics.vue` 的初始化、查询、重置不能再触发 `setFilters is not a function`。
4. 保持 `/api/quality-analytics/*` 的现有后端接口不变。

### 二、补齐 API 资产归属与生成用例追溯

1. API 资产中心页面增加项目筛选：
   - 使用 `qualityFoundationStore.fetchProjects()` 加载项目。
   - 查询 API 分组/API 列表时带上 `project_id`。
   - 重置时清空项目筛选。
2. 新建 API、新建分组、OpenAPI 导入时，应把当前选择的 `project_id` 写入请求。
3. 编辑 API 时保留原 `project_id`，不要意外清空。
4. `generate_case_from_api` 生成 `TestCase` 时至少继承：
   - `project_id=api.project_id`
   - OpenAPI 参数、query、headers、body 已有逻辑必须保留。
5. 增加稳定追溯字段：
   - 在 `TestCase` 增加 `source_api_id` 或等价清晰命名字段，用于记录来源 `ApiDefinition.id`。
   - 如当前项目无 Alembic，请按 `backend/app/database.py` 现有轻量迁移风格补齐 SQLite 字段兼容。
   - 前端无需大展示，但后端生成用例和测试应可验证该字段。
6. 补充或更新 `backend/tests/services/test_api_asset_service.py`，覆盖：
   - 从 API 资产生成用例会继承 `project_id`。
   - 从 API 资产生成用例会写入 `source_api_id`。
   - 仍会写入 headers/query/body 到 `TestCase` 主表。

### 三、补齐测试计划归属维护和按归属添加项

1. `TestPlanList.vue` 新建/编辑计划表单增加项目/版本/迭代字段。
2. 项目、版本、迭代选择采用级联：
   - 选项目后加载该项目版本，清空版本和迭代。
   - 选版本后加载该版本迭代，清空迭代。
3. 列表筛选增加项目筛选，调用 `testPlanStore.fetchPlans` 时传 `project_id`。
4. 后端创建/更新计划时增加最小层级校验：
   - `version_id` 存在时，其 `project_id` 必须与计划 `project_id` 一致。
   - `iteration_id` 存在时，其 `project_id/version_id` 必须与计划一致。
   - 不存在的项目/版本/迭代应返回清晰错误。
5. `TestPlanDetail.vue` 添加用例/场景弹窗搜索时，应默认按当前计划的 `project_id/version_id/iteration_id` 过滤。
6. 如果计划没有归属字段，则保持现有全量搜索行为。
7. 补充或更新测试，覆盖：
   - 创建计划可保存项目/版本/迭代。
   - 错误层级组合会失败。
   - 列表可按 `project_id` 筛选。

### 四、修复 AI 建议历史列表

1. 后端新增建议列表接口：
   - `GET /api/ai/suggestions`
   - 支持 `page`、`page_size`、`accepted`、`suggestion_type`。
   - 返回分页结构，字段至少包含 `id`、`analysis_id`、`suggestion_type`、`content`、`accepted`、`accepted_at`、`accepted_by`、`accepted_comment`、`created_at`。
2. 复用 `AIRepository.list_suggestions`，不要在 router 写复杂查询。
3. `frontend/src/api/ai.js` 增加 `listSuggestions(params)`。
4. `frontend/src/stores/aiStore.js` 增加 `fetchSuggestions(params)`，不要再用 `fetchAnalysis(query)` 伪装列表查询。
5. `SuggestionHistory.vue` 改为调用 `aiStore.fetchSuggestions(buildQueryParams())`。
6. 保持 `GET /api/ai/analysis/{analysis_id}` 原行为不变。
7. 如 `content` 是 JSON 字符串，前端展示时要防御式解析，不能因脏数据白屏。

### 五、修复管理看板入口和明显断链

1. 检查 `frontend/src/views/platform/Dashboard.vue` 的快捷入口路径。
2. 至少修复以下旧路径：
   - `/cases` 应改为 `/case`
   - `/quality-gates` 应改为 `/quality-gate`
3. 如发现其它明显不存在的内部路径，也一并改为 `frontend/src/router/index.js` 中真实存在的路径。
4. 不要求本次重做 Dashboard 数据来源；若仍有静态展示，请在结果报告中说明。

## 验收标准

- 打开 `/quality-analytics` 不再因 `setFilters` 报错，查询和重置可正常触发请求。
- API 资产中心可按项目筛选，导入 OpenAPI、新建分组、新建 API 能写入项目归属。
- 从 API 资产生成用例后，生成的用例保留 OpenAPI 参数/请求体，并带有 `project_id` 和 `source_api_id`。
- 测试计划可维护项目/版本/迭代归属，列表可按项目筛选。
- 在测试计划详情中添加用例/场景时，默认按计划归属过滤候选项。
- AI 建议历史页面调用真实建议列表接口，不再把对象 query 传给 `/api/ai/analysis/{id}`。
- Dashboard 快捷入口能跳到当前真实路由。
- 不产生提交；`git status` 可以有工作区改动，但不能出现本任务产生的 commit。

## 验证方式

请至少运行：

```text
cd backend
python -m pytest tests/services/test_api_asset_service.py tests/services/test_test_plan_service.py tests/services/test_quality_analytics_service.py -q
python -m pytest tests/routers -q

cd ../frontend
npm run build
```

如时间允许，再运行：

```text
cd backend
python -m pytest tests -q
```

建议手工验证路径：

```text
/api-assets
/test-plans
/test-plans/:id
/test-plan-runs
/quality-analytics
/ai/suggestion-history
/
```

## Claude 输出要求

结束时必须用中文汇报：

- 修复了哪些闭环断点。
- 变更文件清单。
- 新增/修改的接口字段。
- 已运行的测试或构建命令及结果。
- 未运行的验证和原因。
- 剩余风险。
- 明确说明：**未执行 git add / git commit / git push**。

请同步写入：

- `.ai/results/2026-05-27-quality-platform-closure-fixes-result.md`
