# Codex 审查修复包

## 审查目标

审查 Claude 已完成的 `.ai/results/2026-05-25-quality-platform-foundation-project-version-requirement-result.md` 对应实现，重点确认“项目/版本/迭代/需求”是否已经真实接入用例、场景、执行、报告、缺陷的质量管理主链路。

当前结论：构建与已有测试通过，但主链路仍未完成闭环。请继续修复以下问题。

## 需要修复的问题

1. `backend/app/routers/quality_foundation.py`
   - 所有 `/api/foundation/**` 接口当前只依赖 `get_db`，没有接入 `get_current_platform_user`。
   - 项目、版本、迭代、需求属于管理域数据，必须与用例管理等接口保持一致，至少要求登录用户鉴权。
   - 创建、更新、删除操作建议同步记录操作日志，按项目现有 `LogService` 模式处理。

2. `backend/app/routers/report.py`
   - 路由顺序错误：`/{report_id}`、`/{report_id}/quality-gates/evaluate` 位于 `/defects`、`/quality-gates` 前面。
   - `/api/reports/defects`、`/api/reports/quality-gates` 容易被动态 `{report_id}` 捕获，导致前端缺陷中心或质量门禁接口返回 422。
   - 必须将静态路由放在动态路由之前，并补充路由顺序测试。

3. `backend/app/services/quality_foundation_service.py`
   - `create_version`、`create_iteration`、`create_requirement`、`update_*` 没有校验层级关系。
   - 需要校验：
     - version.project_id 必须存在。
     - iteration.project_id 必须与 version.project_id 一致。
     - requirement.version_id 必须属于 requirement.project_id。
     - requirement.iteration_id 必须属于 requirement.version_id 与 requirement.project_id。
     - 用例、场景、报告、缺陷写入 project/version/iteration/requirement 时也要做同样校验。
   - 校验失败返回明确 400，不要静默写入脏关联。

4. `backend/app/services/quality_foundation_service.py`
   - 删除保护只检查版本、迭代、需求，未检查已有用例、场景、报告、缺陷对 project/version/iteration 的引用。
   - 删除项目/版本/迭代前必须检查 TestCase、Scenario、Report、Defect 中的对应引用。
   - 如果存在引用，返回 400，并提示改为归档。

5. `backend/app/services/quality_foundation_service.py`
   - `with_scenario` 计算逻辑不准确：只要任意一个用例进入场景，就把所有 `req_ids_with_case` 都计入场景覆盖。
   - 需要按需求逐个判断：该需求下任意用例出现在 `ScenarioStep` 中，才计入该需求的 `with_scenario`。

6. `backend/app/services/quality_foundation_service.py`
   - `executed` 只统计 `ExecutionRun.run_type == "case"` 的直接用例执行。
   - 当前平台核心真实链路是“场景执行包含用例步骤”，因此需求执行覆盖必须同时统计：
     - 直接用例执行。
     - 场景执行中包含该需求关联用例的执行。
   - 建议只统计终态执行记录，例如 `passed`、`failed`，不要把 `running`、`pending` 计入已执行。

7. `backend/app/services/test_case_service.py` 与 `backend/app/repositories/test_case_repository.py`
   - Schema 已加入 `project_id/version_id/iteration_id/requirement_id`，但序列化、列表过滤、更新、复制没有完整接入。
   - 需要：
     - 列表响应、详情响应返回这四个字段。
     - 创建、更新、复制均保留/允许维护这些字段。
     - 列表接口支持按 project/version/iteration/requirement 过滤。
     - 批量更新如需支持归属变更，要显式限制字段并校验层级。

8. `backend/app/services/scenario_service.py` 与 `backend/app/repositories/scenario_repository.py`
   - 场景创建虽然写入了 `project_id/version_id/iteration_id`，但序列化没有返回，列表也不支持这些筛选。
   - 自动生成执行报告时没有把场景的 project/version/iteration 带入 Report。
   - `metrics.status` 使用旧 `run.status`，在 `_update_run_status` 后可能仍是 `running`。报告应使用最终执行状态。

9. `backend/app/services/report_service.py` 与 `backend/app/repositories/report_repository.py`
   - Report schema 已加 `project_id/version_id/iteration_id`，但序列化与列表过滤未接入。
   - 报告列表、详情、创建、更新都必须完整支持项目/版本/迭代归属。

10. `backend/app/services/defect_service.py` 与 `backend/app/repositories/defect_repository.py`
    - Defect schema 已加 `version_id/iteration_id/requirement_id`，但序列化与列表过滤未完整接入。
    - 缺陷列表、详情、创建、更新、统计需要支持 project/version/iteration/requirement 维度。

11. 前端核心列表页仍未接入基础筛选，不应作为“可后续分阶段”的剩余风险。
    - 至少修复以下页面，使查询栏样式、字段顺序、中文冒号、背景/表格层级继续对齐 `CaseManagement`：
      - 用例管理
      - 场景管理
      - 测试报告
      - 缺陷中心
    - 每个页面查询栏增加项目、版本、迭代筛选。
    - 用例创建/编辑增加需求关联选择；缺陷创建/编辑增加需求、版本、迭代关联。
    - 场景创建/编辑增加项目、版本、迭代归属，并在选择步骤用例时能按当前归属辅助过滤。

12. `frontend/src/app/AppShell.vue`
    - 虽然 `frontend/src/router/index.js` 已存在 `/foundation/projects` 与 `/foundation/requirements` 路由，`backend/app/services/platform_seed.py` 也有种子菜单，但当前左侧菜单实际使用 `AppShell.vue` 里的硬编码 `menuList`。
    - `menuList` 没有“项目版本管理”和“需求管理”入口，用户无法从左侧菜单进入这些页面。
    - 需要在合适分组增加入口。推荐新增“质量基础”或放入“质量中心”，包含：
      - 项目版本：`/foundation/projects`
      - 需求管理：`/foundation/requirements`
    - 菜单名称、图标、排序要与现有侧栏风格一致。

13. `frontend/src/stores/qualityFoundationStore.js`
    - Store 传递的是 `page/page_size`，后端目前使用的是 `skip/limit`，并且接口返回 List，导致 `projectTotal/requirementTotal` 只是当前页长度，不是真实总数。
    - 需要统一分页契约：
      - 后端返回 `{ items, total, page, page_size }`；或
      - 前端明确使用 `skip/limit` 且不展示假分页。
    - 推荐与现有用例、场景、报告列表保持一致，使用统一分页响应。

14. 测试覆盖不足。
    - 现有 `41 passed` 不能证明新基础链路正确。
    - 必须新增覆盖：
      - `/api/foundation/**` 未登录返回 401 或项目统一未授权响应。
      - `/api/reports/defects`、`/api/reports/quality-gates` 不被 `{report_id}` 拦截。
      - 创建项目、版本、迭代、需求后，创建用例关联需求，创建场景引用用例，执行场景后生成报告，并能按项目/版本/迭代查询报告与覆盖率。
      - 需求覆盖率中 `with_test_case/with_scenario/executed/with_defect` 的逐项正确性。
      - 删除项目/版本/迭代时，如存在用例、场景、报告、缺陷引用，返回 400。
      - 层级不一致时返回 400。

## 修复范围

允许修改：

- `backend/app/routers/quality_foundation.py`
- `backend/app/services/quality_foundation_service.py`
- `backend/app/schemas/quality_foundation.py`
- `backend/app/routers/testcase.py`
- `backend/app/services/test_case_service.py`
- `backend/app/repositories/test_case_repository.py`
- `backend/app/routers/scenario.py`
- `backend/app/services/scenario_service.py`
- `backend/app/repositories/scenario_repository.py`
- `backend/app/routers/report.py`
- `backend/app/services/report_service.py`
- `backend/app/repositories/report_repository.py`
- `backend/app/services/defect_service.py`
- `backend/app/repositories/defect_repository.py`
- `backend/app/schemas/report.py`
- `frontend/src/api/**`
- `frontend/src/stores/**`
- `frontend/src/app/AppShell.vue`
- `frontend/src/views/**`
- `backend/tests/**`

如模型字段缺失，可以补充模型字段，但不要引入新的大型重构。

## 禁止事项

- 不要删除终端控制台相关功能。
- 不要改变现有 CaseManagement 的视觉基准。
- 不要把“前端筛选未接入”继续标记为可接受剩余风险。
- 不要只改 schema，不接入 service/repository/router/frontend。
- 不要用新的视觉风格重写页面；基础查询栏、背景、表格透明度和层级必须贴合现有用例管理。
- 不要新增无关功能或大范围格式化。

## 验证方式

修复后至少运行：

```bash
python -m pytest backend/tests
cd frontend
npm run build
```

如果新增了针对前端筛选的自动化测试，也一并运行。

## Claude 输出要求

结束时必须用中文汇报：

- 已修复哪些问题。
- 变更文件。
- 已运行的测试或检查。
- 剩余风险。
- 对“用例/场景/报告/缺陷是否已完整接入项目/版本/迭代/需求”的明确结论。
