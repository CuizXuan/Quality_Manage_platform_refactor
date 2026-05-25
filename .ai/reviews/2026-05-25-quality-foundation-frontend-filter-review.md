# Codex 审查修复包

## 审查目标

复审 `.ai/results/2026-05-25-quality-platform-foundation-project-version-requirement-result.md` 中“只剩前端筛选分阶段接入风险”的结论。

当前结论：该结论不成立。前端仍缺少质量基础能力的核心入口和核心筛选接入，用户无法从业务主链路里真正使用项目/版本/迭代/需求。

## 需要修复的问题

1. `frontend/src/app/AppShell.vue`
   - 左侧菜单 `menuList` 仍然没有 `/foundation/projects` 和 `/foundation/requirements` 入口。
   - 当前用户虽然有路由，但无法从系统主导航进入“项目版本管理”和“需求管理”。
   - 需要在左侧菜单补齐入口，菜单名称、图标、排序和现有风格保持一致。

2. `frontend/src/views/case/CaseModulePage.vue`
   - 用例管理前端筛选仍只有 `methods / priorities / isAutomated / createdRange / keyword / folder_id`。
   - 需要在查询区接入 `project_id / version_id / iteration_id / requirement_id`，并将参数透传到 `caseApi.list`。
   - 同步补齐级联逻辑：选项目后加载版本，选版本后加载迭代，需求列表按当前归属过滤。

3. `frontend/src/views/scenario/ScenarioList.vue` 与 `frontend/src/stores/scenarioStore.js`
   - 场景列表筛选区当前只有 `status / date_range / keyword`。
   - Store 的 `fetchScenarios()` 也只传 `keyword`，没有传 `project_id / version_id / iteration_id / status`。
   - 需要补齐项目/版本/迭代筛选，并让前端查询真正命中已支持的后端 API。

4. `frontend/src/views/report/ReportList.vue` 与 `frontend/src/stores/reportStore.js`
   - 报告列表筛选区当前只有 `report_type / environment / keyword`。
   - Store `fetchReports()` 也没有传 `project_id / version_id / iteration_id`。
   - 需要补齐项目/版本/迭代筛选，保持查询栏中文标签、冒号、对齐和用例管理视觉基准一致。

5. `frontend/src/views/report/DefectList.vue` 与 `frontend/src/stores/reportStore.js`
   - 缺陷列表筛选区当前只有 `severity / priority / status / keyword`。
   - Store `fetchDefects()` 虽已支持 `project_id`，但页面没有项目/版本/迭代/需求筛选入口，也没有把这些筛选传进来。
   - 需要补齐 `project_id / version_id / iteration_id / requirement_id` 筛选，必要时一并支持缺陷统计卡片按当前项目筛选刷新。

6. `frontend/src/views/**` 相关表单
   - 既然基础能力已经接入后端，前端创建/编辑也要至少能维护这些核心归属字段：
     - 用例：项目 / 版本 / 迭代 / 需求
     - 场景：项目 / 版本 / 迭代
     - 缺陷：项目 / 版本 / 迭代 / 需求
   - 如果当前编辑弹窗/抽屉中仍缺少这些字段，请一并补齐，否则列表筛选只是半成品。

7. 结果文档需要同步修正
   - `.ai/results/2026-05-25-quality-platform-foundation-project-version-requirement-result.md` 中“只剩前端页面筛选分阶段接入”的表述已经过时。
   - 本次完成后，请更新结果文档，把真正剩余风险写准确。

## 修复范围

允许修改：

- `frontend/src/app/AppShell.vue`
- `frontend/src/views/case/**`
- `frontend/src/views/scenario/**`
- `frontend/src/views/report/**`
- `frontend/src/stores/scenarioStore.js`
- `frontend/src/stores/reportStore.js`
- `frontend/src/stores/qualityFoundationStore.js`
- `frontend/src/api/**`
- `.ai/results/2026-05-25-quality-platform-foundation-project-version-requirement-result.md`

如果需要复用项目/版本/迭代/需求下拉数据，可在现有 store 内补充最小必要逻辑，不要引入新的大规模状态体系。

## 禁止事项

- 不修改终端调试台保留策略。
- 不改变 `CaseManagement` 既有视觉基准。
- 不把这批前端缺口继续标记为“后续逐步接入”。
- 不为了接筛选重写整页布局。
- 不增加与本次返工无关的新功能。

## 验证方式

修复后至少运行：

```bash
cd frontend
npm run build
```

并人工自查以下页面：

- 左侧菜单可进入“项目版本管理”和“需求管理”
- 用例管理筛选栏存在项目/版本/迭代/需求
- 场景管理筛选栏存在项目/版本/迭代
- 测试报告筛选栏存在项目/版本/迭代
- 缺陷管理筛选栏存在项目/版本/迭代/需求

## Claude 输出要求

结束时必须用中文汇报：

- 已补齐哪些菜单和页面筛选。
- 哪些创建/编辑表单已接入项目/版本/迭代/需求。
- 变更文件。
- 已运行的验证。
- 剩余风险。
