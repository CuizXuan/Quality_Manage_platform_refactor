# 质量基础能力实现审查返工要求

## 审查目标

请修复 `.ai/tasks/2026-05-25-quality-platform-foundation-project-version-requirement.md` 实现中的关键落地问题。

当前实现已经新增了项目、版本、迭代、需求模型和页面，但 Codex 审查发现：部分接口路由顺序有 bug，主业务对象只在数据库层加了字段，API/schema/service/UI 尚未真正接入，覆盖率统计也存在虚高风险。

## 原始结果文件

- `.ai/results/2026-05-25-quality-platform-foundation-project-version-requirement-result.md`

## 允许修改范围

- `backend/app/routers/quality_foundation.py`
- `backend/app/services/quality_foundation_service.py`
- `backend/app/schemas/quality_foundation.py`
- `backend/app/schemas/test_case.py`
- `backend/app/schemas/scenario.py`
- `backend/app/schemas/report.py`
- `backend/app/services/test_case_service.py`
- `backend/app/services/scenario_service.py`
- `backend/app/services/report_service.py`
- `backend/app/services/defect_service.py`
- `backend/app/repositories/test_case_repository.py`
- `backend/app/repositories/scenario_repository.py`
- `backend/app/repositories/report_repository.py`
- `backend/app/repositories/defect_repository.py`
- `frontend/src/api/qualityFoundation.js`
- `frontend/src/stores/qualityFoundationStore.js`
- `frontend/src/views/foundation/ProjectManagement.vue`
- `frontend/src/views/foundation/RequirementManagement.vue`
- 现有用例、场景、报告、缺陷页面中与项目/版本/迭代/需求筛选和创建编辑相关的最小范围修改
- `.ai/results/2026-05-25-quality-platform-foundation-project-version-requirement-result.md`

## 禁止事项

- 不删除终端控制台。
- 不删除现有用例、场景、报告、缺陷功能。
- 不做无关样式大改。
- 不引入大型依赖。
- 不用 mock 数据替代真实关联。

## 必须修复的问题

### 1. 覆盖率接口路由顺序错误

当前 `backend/app/routers/quality_foundation.py` 中：

```python
@router.get("/requirements/{requirement_id}")
...

@router.get("/requirements/coverage")
...
```

`/requirements/coverage` 放在动态路由后面，FastAPI 可能会先把 `coverage` 当作 `requirement_id`，导致 422。

请修复：

- 把 `/requirements/coverage` 放到 `/requirements/{requirement_id}` 之前。
- 补一个测试或至少用接口验证说明覆盖率接口可访问。

### 2. 用例关联字段只在 DB 模型存在，API 没接入

当前 `backend/app/models/test_case.py` 有：

```python
project_id
version_id
iteration_id
requirement_id
```

但 `backend/app/schemas/test_case.py` 的 `TestCaseCreate` / `TestCaseUpdate` / `TestCaseResponse` 没有这些字段，`TestCaseService.create_case()` 也没有保存这些字段。

请修复：

- `TestCaseCreate` 增加可选 `project_id`, `version_id`, `iteration_id`, `requirement_id`。
- `TestCaseUpdate` 增加这些字段。
- `TestCaseResponse` 返回这些字段。
- `TestCaseService.create_case()` 写入这些字段。
- `TestCaseService.update_case()` 允许更新这些字段。
- `CaseListFilters` 和查询支持这些筛选字段。
- 用例列表接口支持按项目/版本/迭代/需求筛选。

### 3. 场景关联字段只在 DB 模型存在，API 没接入

当前 `backend/app/models/scenario.py` 有：

```python
project_id
version_id
iteration_id
```

但 `ScenarioCreate` / `ScenarioUpdate` / `ScenarioResponse` 没有这些字段。

请修复：

- `ScenarioCreate` 增加可选 `project_id`, `version_id`, `iteration_id`。
- `ScenarioUpdate` 增加这些字段。
- `ScenarioResponse` 返回这些字段。
- `ScenarioService` 创建、更新、列表返回时包含这些字段。
- 场景列表接口支持按项目/版本/迭代筛选。

### 4. 报告和缺陷关联字段没有完整进入 schema/service

报告模型有：

```python
project_id
version_id
iteration_id
```

但 `ReportCreate` / `ReportUpdate` / `ReportResponse` 没有返回或接收这些字段。

缺陷模型有：

```python
version_id
iteration_id
requirement_id
```

但 `DefectCreate` / `DefectUpdate` / `DefectResponse` 目前没有这些字段。

请修复：

- 报告 schema 增加并返回 `project_id`, `version_id`, `iteration_id`。
- 缺陷 schema 增加并返回 `version_id`, `iteration_id`, `requirement_id`。
- 报告列表接口支持项目/版本/迭代筛选。
- 缺陷列表接口支持项目/版本/迭代/需求筛选。

### 5. 覆盖率统计“已执行”逻辑错误

当前 `get_requirement_coverage()` 里：

```python
if tc.created_at:
    executed += 1
```

这不代表需求已执行，只代表用例已创建，会导致覆盖率虚高。

请修复为更可信的逻辑：

- 第一阶段可按关联用例是否存在 execution/report 计算。
- 如果现有执行模型无法直接按 case_id 查执行，可至少不要把 created_at 当执行。
- 推荐先定义：
  - `executed` = 需求关联的用例或场景中，有对应执行报告 / ExecutionRun 的需求数。
  - 如果暂时查不到执行关系，则返回 0，并在结果说明中标记“执行覆盖待接入执行模型”。

不要继续用 `created_at` 判断。

### 6. `with_scenario` 不能永远为 0

当前报告里承认场景与需求关联未实现，`with_scenario` 始终为 0。

请至少实现一个可信的第一阶段逻辑：

- 方案 A：给场景增加 `requirement_id` 字段，并接入 schema/service/UI。
- 方案 B：通过场景步骤关联的用例反推需求覆盖：
  - 如果场景包含某个用例，而该用例关联了 requirement_id，则该需求算 `with_scenario`。

推荐方案 B，因为当前场景步骤已经关联用例，不必新增场景 requirement_id 也能计算场景覆盖。

### 7. 项目/版本/迭代管理页面没有迭代管理入口

`ProjectManagement.vue` 目前只有项目和版本管理，没有迭代创建/列表/删除。

请补齐：

- 在版本管理弹窗中增加“迭代”操作。
- 或新增迭代管理区域。
- 能为某个版本创建迭代。
- 能查看和删除迭代。

### 8. 前端筛选和后端筛选不一致

`ProjectManagement.vue` 有项目名称和状态筛选，但后端 `list_projects()` 没有 keyword/status 参数，store 也没有传递这些筛选。

请修复：

- 后端项目列表支持 `keyword` / `status`。
- 前端 store 正确传递筛选参数。
- 分页 pageSize 不要写死 20，要使用当前分页值。

需求页面：

- 选择版本后应拉取对应迭代。
- 查询应包含 `status`，当前后端列表没有 status 参数。
- 后端需求列表支持 `status` 和 `keyword`。

### 9. 页面样式未完全贴合现有模块

新增页面目前背景只是 `var(--bg-page)`，没有 CaseManagement/ScenarioList 那种偏绿蓝的流动网格背景。

请调整：

- 参考 `ScenarioList.vue` 或 `DefectList.vue` 页面背景、标题区、查询区、表格区。
- 不需要过度美化，但要与现有模块统一。
- 查询栏 label 继续保持中文冒号。

## 关于用户提到的剩余风险处理

用户关注：

```text
场景与需求关联暂未实现，with_scenario 覆盖率为 0
删除项目/版本/迭代时无级联清理
旧数据兼容已保证
现有页面筛选栏暂未添加项目/版本/迭代筛选项
```

请本轮处理：

- 必须处理 `with_scenario` 覆盖率，不要继续恒为 0。
- 删除项目/版本/迭代时不要级联删除业务数据；改为保护性删除：
  - 如果存在版本/迭代/需求/用例/场景/报告/缺陷引用，则拒绝删除并返回中文错误。
  - 项目、版本、迭代可以改状态为 archived 作为推荐操作。
- 旧数据兼容继续保持。
- 至少在用例和场景列表增加项目/版本/迭代筛选；报告/缺陷可同步补上，如果范围过大，至少后端支持并在结果中说明前端分阶段接入状态。

## 验证方式

请至少运行：

```text
python -m pytest backend/tests --collect-only
python -m pytest backend/tests
cd frontend
npm run build
```

并手工或脚本验证：

```text
GET /api/foundation/requirements/coverage
POST /api/foundation/projects
POST /api/foundation/versions
POST /api/foundation/iterations
POST /api/foundation/requirements
POST /api/case 带 requirement_id
GET /api/case?requirement_id=...
GET /api/foundation/requirements/coverage
```

## 输出要求

结束时必须用中文汇报：

- 修复了哪些问题。
- 用例/场景/报告/缺陷哪些字段已真正接入 API。
- 覆盖率统计现在如何计算。
- 删除保护规则是什么。
- 哪些页面筛选已接入。
- 测试和构建结果。
- 剩余风险。

请同步更新：

- `.ai/results/2026-05-25-quality-platform-foundation-project-version-requirement-result.md`
