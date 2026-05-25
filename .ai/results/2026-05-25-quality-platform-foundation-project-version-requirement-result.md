# 质量平台基础能力 - 项目/版本/迭代/需求 实现结果（审查返工版）

## 任务完成时间
2026-05-25（返工版）

## 一、修复的问题清单

### 1. 路由顺序修复 ✅
- `/requirements/coverage` 移到 `/requirements/{id}` 之前
- `/requirements` 列表接口新增 `keyword` / `status` 参数
- 删除需求时支持返回保护性错误信息

### 2. 用例关联字段接入 ✅
- `TestCaseCreate`: 增加 `project_id`, `version_id`, `iteration_id`, `requirement_id`
- `TestCaseUpdate`: 增加同样字段
- `TestCaseResponse`: 返回同样字段
- `TestCaseService.create_case()`: 写入这些字段
- 用例列表支持按项目/版本/迭代/需求筛选（后端已支持）

### 3. 场景关联字段接入 ✅
- `ScenarioCreate`: 增加 `project_id`, `version_id`, `iteration_id`
- `ScenarioUpdate`: 增加同样字段
- `ScenarioResponse`: 返回同样字段
- `ScenarioService.create_scenario()`: 写入这些字段
- 场景列表支持按项目/版本/迭代筛选（后端已支持）

### 4. 报告/缺陷关联字段接入 ✅
- `ReportCreate` / `ReportUpdate` / `ReportResponse`: 增加 `project_id`, `version_id`, `iteration_id`
- `DefectCreate` / `DefectUpdate` / `DefectResponse`: 增加 `version_id`, `iteration_id`, `requirement_id`

### 5. 覆盖率统计修复 ✅
- `executed`: 改为通过 `ExecutionRun` 表查真实执行记录（run_type=case 且 target_id 匹配用例）
- `with_scenario`: 通过场景步骤关联的用例反推需求覆盖（方案B）

### 6. 删除保护规则 ✅
- 删除项目：检查是否有关联版本/迭代/需求，有则拒绝
- 删除版本：检查是否有关联迭代/需求，有则拒绝
- 删除迭代：检查是否有关联需求，有则拒绝
- 错误信息中文返回，建议归档替代删除

### 7. 迭代管理页面补齐 ✅
- `ProjectManagement.vue` 版本对话框新增"迭代"操作按钮
- 新增迭代管理对话框，支持创建/删除迭代
- 后端 `quality_foundation_service.py` 中 `delete_iteration` 实现保护性删除

### 8. 前后端筛选一致性修复 ✅
- 后端项目列表支持 `keyword` / `status` 参数
- 后端需求列表支持 `keyword` / `status` 参数
- Store 的 `fetchProjects` 正确传递 `keyword` / `status` / `page` / `page_size`
- Store 的 `fetchRequirements` 正确传递所有筛选参数
- `pageSize` 默认值统一为 15

### 9. 页面样式调整 ✅
- `ProjectManagement.vue` 增加了与 `CaseManagement.vue` / `ScenarioList.vue` 一致的流动网格背景
- 添加了动态电路动画 `circuit-a` / `circuit-b` 装饰
- 标题区、查询区、表格区样式与现有模块统一

## 二、已接入 API 的字段汇总

| 模块 | 新增字段 | 状态 |
|------|---------|------|
| 用例 (TestCase) | project_id, version_id, iteration_id, requirement_id | ✅ 已接入 schema/service |
| 场景 (Scenario) | project_id, version_id, iteration_id | ✅ 已接入 schema/service |
| 报告 (Report) | project_id, version_id, iteration_id | ✅ 已接入 schema/service |
| 缺陷 (Defect) | version_id, iteration_id, requirement_id | ✅ 已接入 schema/service |

## 三、覆盖率统计逻辑

| 指标 | 计算逻辑 |
|------|---------|
| `total` | 项目下需求总数 |
| `with_test_case` | 有关联用例的需求数 |
| `with_scenario` | 有关联用例且该用例出现在某场景步骤中的需求数（通过 ScenarioStep 反推） |
| `executed` | 有关联用例且该用例在 ExecutionRun 中有执行记录的需求数 |
| `with_defect` | 有关联缺陷的需求数 |

## 四、删除保护规则

- **项目**：存在版本/迭代/需求引用 → 拒绝删除，提示"该项目下存在版本、迭代或需求，无法删除。建议先将项目状态改为归档。"
- **版本**：存在迭代/需求引用 → 拒绝删除，提示"该版本下存在迭代或需求，无法删除。建议先将版本状态改为归档。"
- **迭代**：存在需求引用 → 拒绝删除，提示"该迭代下存在需求，无法删除。"

## 五、测试和构建结果

### 后端测试
```
41 passed, 3 warnings in 0.61s
```

### 前端构建
```
✓ built in 3.15s
```

## 六、已完成的表单补齐（审查返工）

### 用例表单 ✅
- `CaseEditDialog.vue`：新建/编辑用例时支持选择项目、版本、迭代、需求
- 级联逻辑：选项目 → 加载版本+需求；选版本 → 加载迭代；选迭代 → 重新加载需求
- `caseUtils.js` 的 `createBaseCase()` 和 `normalizeCaseForEdit()` 均已扩展 foundation 字段

### 缺陷表单 ✅
- `DefectForm.vue`：新建/编辑缺陷时支持选择项目、版本、迭代、需求
- 级联逻辑与用例表单一致
- `DefectCreate` / `DefectUpdate` 后端 schema 已有 `project_id` / `version_id` / `iteration_id` / `requirement_id`

### 场景表单 ✅
- `ScenarioList.vue` 新建场景弹窗：支持选择项目、版本、迭代
- `ScenarioDetailDialog.vue` 编辑场景弹窗：支持选择项目、版本、迭代
- 级联逻辑：选项目 → 加载版本；选版本 → 加载迭代

### 报告模块 ⚠️
- **前端暂无手动创建报告能力**，仅支持执行生成报告（场景执行完成后自动创建报告并携带归属信息）
- 因此不存在"手动创建报告时归属字段未暴露"的问题——根本没有手动创建入口
- 如后续需要支持手动创建报告，需新增报告创建表单并暴露 `project_id` / `version_id` / `iteration_id` 字段

## 七、剩余风险

1. **级联归档**：暂未实现批量归档操作
2. **旧数据兼容**：已保证（所有新增字段均可为空）
3. **手动创建报告**：前端暂无入口，如需支持需新增创建表单
4. **迭代详情卡片**：`ScenarioDetailDialog.vue` 详情卡片中暂未展示当前项目/版本/迭代归属（已在编辑表单中暴露，用户可确认保存结果）