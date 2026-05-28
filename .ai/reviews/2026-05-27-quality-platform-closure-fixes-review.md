# 质量平台五项能力闭环修复 - 审查修复包

## 审查目标

审查 `.ai/tasks/2026-05-27-quality-platform-closure-fixes.md` 的 Claude 实现结果：

- 结果报告：`.ai/results/2026-05-27-quality-platform-closure-fixes-result.md`
- 当前工作区 diff

本次不是要求提交代码。请继续在工作区修复，修完后仍然不要 `git add`、不要 `git commit`、不要 `git push`。

## 需要修复的问题

### 1. `frontend/src/views/apiAsset/ApiAssetCenter.vue`: API 资产中心前端没有真正接入项目归属

任务包要求：

- API 资产中心页面增加项目筛选。
- 查询 API 分组/API 列表时带上 `project_id`。
- 新建 API、新建分组、OpenAPI 导入时把当前选择的 `project_id` 写入请求。
- 编辑 API 时保留原 `project_id`。

实际代码仍存在问题：

- `filters` 只有 `{ keyword, method, status }`，没有 `project_id`。
- 页面没有引入 `useQualityFoundationStore`，没有加载项目列表。
- 筛选栏没有项目选择器。
- `fetchApis()` 未传 `project_id`。
- `store.fetchGroups()` 未传 `project_id`。
- `handleImport()` 未传 `project_id`。
- `openGroupDialog()` 创建分组未传 `project_id`。
- `apiForm` 没有 `project_id`，`handleSaveApi()` 新建/编辑 API 未传项目归属。

请按任务包补齐。后端 `api_asset_service.py` 已支持 `project_id` 过滤和写入，不要重复造接口。

### 2. `backend/app/services/test_plan_service.py`: 测试计划后端层级校验没有实现

任务包要求创建/更新计划时做最小层级校验：

- `version_id` 存在时，其 `project_id` 必须与计划 `project_id` 一致。
- `iteration_id` 存在时，其 `project_id/version_id` 必须与计划一致。
- 不存在的项目/版本/迭代应返回清晰错误。

实际代码：

- `create_plan()` 直接 `TestPlan(**data)`。
- `update_plan()` 直接 setattr。
- 没有查询 `QualityProject`、`QualityVersion`、`QualityIteration`。
- 结果报告把这个列为剩余风险，但这是任务包验收项，不应留作风险。

请在 service 层实现短小的校验 helper，例如 `_validate_plan_scope(data, existing_plan=None)`，并在 `create_plan` 和 `update_plan` 中调用。

路由层也要把 `ValueError` 转为清晰的 `HTTPException(status_code=400 或 404)`，不要让 500 泄漏给前端。

### 3. `backend/tests/services/test_test_plan_service.py`: 缺少层级校验测试

请补充测试覆盖：

- 创建计划时可保存合法 `project_id/version_id/iteration_id`。
- `version_id` 不存在时失败。
- `iteration_id` 不存在时失败。
- `version_id` 与 `project_id` 不一致时失败。
- `iteration_id` 与 `project_id/version_id` 不一致时失败。
- 更新计划时同样校验错误组合。

测试应使用现有 `QualityProject`、`QualityVersion`、`QualityIteration` 模型构造最小数据。

### 4. `frontend/src/views/platform/Dashboard.vue`: 仍有旧路由路径

任务包要求修复 Dashboard 明显不存在的内部路径。

实际代码仍有：

- `/scenarios`，真实路由是 `/scenario`
- `/reports`，真实路由是 `/report`
- `/defects`，真实路由是 `/defect`

请对照 `frontend/src/router/index.js` 修正 `quickEntries` 中所有不存在路径：

- `/scenarios` -> `/scenario`
- `/reports` -> `/report`
- `/defects` -> `/defect`

已修复的 `/case`、`/quality-gate` 保持不变。

### 5. 结果报告需更新

请更新：

- `.ai/results/2026-05-27-quality-platform-closure-fixes-result.md`

要求：

- 不再把“测试计划后端层级校验未实现”列为剩余风险。
- 如仍有风险，必须是本次任务范围外或确实无法验证的风险。
- 明确列出本次审查修复新增的文件变更和测试结果。
- 再次明确未执行 `git add / git commit / git push`。

## 修复范围

只允许修改以下文件：

- `backend/app/services/test_plan_service.py`
- `backend/app/routers/test_plan.py`
- `backend/tests/services/test_test_plan_service.py`
- `frontend/src/views/apiAsset/ApiAssetCenter.vue`
- `frontend/src/views/platform/Dashboard.vue`
- `.ai/results/2026-05-27-quality-platform-closure-fixes-result.md`

如确实需要同步修改 store/API 层，允许最小修改：

- `frontend/src/stores/apiAssetStore.js`
- `frontend/src/api/apiAsset.js`

但优先复用现有能力；当前 store/API 已支持透传参数，不要做无关改造。

## 禁止事项

- 不要执行 `git add`、`git commit`、`git push`。
- 不要重写 API 资产中心页面样式。
- 不要重写测试计划服务。
- 不要修改 AI、质量看板、API 资产生成用例等已经通过核查的部分。
- 不要用前端提示替代后端校验。
- 不要扩大到其它任务结果文件。

## 验证方式

修复后至少运行：

```text
cd backend
python -m pytest tests/services/test_test_plan_service.py -q
python -m pytest tests/routers/test_test_plan_routes.py -q

cd ../frontend
npm run build
```

如时间允许，再运行：

```text
cd backend
python -m pytest tests/services/test_api_asset_service.py tests/services/test_quality_analytics_service.py -q
python -m pytest tests -q
```

## Claude 输出要求

结束时必须用中文汇报：

- 已修复哪些审查问题。
- 变更文件。
- 已运行的测试或检查。
- 每条命令的结果。
- 剩余风险。
- 明确说明：未执行 `git add / git commit / git push`。
