# Codex 实现任务包：统一查询栏字段对齐、冒号和背景样式

## 任务目标

修复多个前端页面查询条件区域的展示问题：

- 查询字段名与输入框没有对齐。
- 字段名和输入框之间缺少中文冒号 `：`。
- 缺陷中心页面背景色与其他同类页面不一致。

目标效果示例：

```text
严重程度： [输入框/下拉框]
关键词：   [输入框]
```

## 背景说明

用户在缺陷中心页面发现查询栏展示不符合规范：

- 当前类似展示为 `严重程度 [输入框]`。
- 正常应展示为 `严重程度： [输入框]`。
- 查询字段 label 与输入控件应在同一基线上视觉对齐。
- 缺陷中心页面当前背景色与其他页面不一致，需要调整为与同类页面一致。

同类问题也存在于以下页面：

- Prompt 模板
- 角色管理
- 组织管理
- 菜单管理
- 字典管理
- 日志管理

## 必读文件

- `AGENTS.md`
- `CLAUDE.md`
- `.ai/INDEX.md`
- `frontend/src/views/report/DefectList.vue`
- `frontend/src/views/ai/AIPromptTemplates.vue`
- `frontend/src/views/platform/RoleManagement.vue`
- `frontend/src/views/platform/OrganizationManagement.vue`
- `frontend/src/views/platform/MenuManagement.vue`
- `frontend/src/views/platform/DictionaryManagement.vue`
- `frontend/src/views/platform/LogManagement.vue`

可参考这些已经带中文冒号且对齐较好的页面：

- `frontend/src/views/report/ReportList.vue`
- `frontend/src/views/scenario/ScenarioList.vue`
- `frontend/src/views/scenario/ExecutionHistory.vue`
- `frontend/src/views/report/QualityGate.vue`
- `frontend/src/views/case/CaseList.vue`

## 允许修改范围

只允许修改以下文件：

- `frontend/src/views/report/DefectList.vue`
- `frontend/src/views/ai/AIPromptTemplates.vue`
- `frontend/src/views/platform/RoleManagement.vue`
- `frontend/src/views/platform/OrganizationManagement.vue`
- `frontend/src/views/platform/MenuManagement.vue`
- `frontend/src/views/platform/DictionaryManagement.vue`
- `frontend/src/views/platform/LogManagement.vue`

如果发现查询栏样式有项目级公共组件或公共样式可以安全复用，可以先汇报原因，再决定是否需要新增公共样式；不要默认扩大修改范围。

## 禁止事项

- 不修改后端代码。
- 不修改接口调用逻辑。
- 不改变查询条件字段、筛选逻辑、分页逻辑或表格列结构。
- 不做无关视觉重构。
- 不新增依赖。
- 不修改 `.ai/`、`CLAUDE.md`、`AGENTS.md`。
- 不批量重写页面内容，尤其要保留现有中文文案和业务逻辑。

## 实现要求

### 1. 查询 label 必须补齐中文冒号

目标页面查询区内所有 `el-form-item` 的查询条件 label 需要使用中文冒号 `：` 结尾。

示例：

```vue
<el-form-item label="严重程度：" class="filter-item">
```

需要覆盖但不限于：

- 缺陷中心：严重程度、优先级、状态、关键词。
- Prompt 模板：模板类型、关键词。
- 角色管理：状态、关键词。
- 组织管理：关键词、状态。
- 菜单管理：状态、关键词。
- 日志管理：关键词、模块、操作、日期范围。
- 字典管理：左右两侧查询输入如有独立查询条件展示，也需要保持 `字段名：输入框` 的格式；如果当前只是无 label 的工具栏搜索框，需要按页面结构谨慎处理，避免破坏布局。

### 2. 查询 label 与控件需要对齐

每个目标页面的查询栏需要保证：

- label 与输入框/下拉框在同一行垂直居中。
- label 宽度稳定，避免文字挤压控件。
- 控件之间间距一致。
- 查询、重置按钮与输入控件同一基线对齐。
- 宽屏下保持横向排列；窄屏下允许自然换行，但不应出现 label 与输入框错位。

优先复用这些页面的已有模式：

- `ReportList.vue`
- `ScenarioList.vue`
- `ExecutionHistory.vue`
- `QualityGate.vue`

### 3. 缺陷中心背景色与同类页面一致

重点检查 `DefectList.vue` 的页面容器、查询栏、表格区域背景样式。

要求：

- 缺陷中心背景不应出现与其他同类页面明显不一致的浅蓝色块或突兀色带。
- 与报告中心、质量门禁、执行历史等页面的背景观感保持一致。
- 不删除必要的玻璃拟态/网格纹理效果，除非它正是导致不一致的原因。

### 4. 保持代码局部、清晰

- 优先做小范围模板 label 和 scoped CSS 调整。
- 不引入新的全局样式污染。
- 如果多个页面样式高度重复，可以小幅整理每个页面内的查询栏 CSS，但不要做跨文件大重构。
- 保持 Vue 文件结构不变。

## 验收标准

### 功能与视觉

- 缺陷中心查询栏展示为 `严重程度：输入框/下拉框`、`优先级：输入框/下拉框`、`状态：输入框/下拉框`、`关键词：输入框`。
- Prompt 模板、角色管理、组织管理、菜单管理、日志管理的查询条件 label 均补齐中文冒号。
- 字典管理中查询条件展示如存在字段 label，也需要补齐中文冒号；如果是纯搜索工具栏，应保持页面一致性和对齐，不强行制造不合理 label。
- 所有目标页面查询栏 label、输入框、按钮横向对齐，无上下错位。
- 缺陷中心页面背景与其他同类页面视觉一致，不再出现明显不一致的背景色。

### 回归

- 查询按钮、重置按钮仍可点击。
- 输入框回车查询逻辑不变。
- 下拉筛选逻辑不变。
- 表格、分页、弹窗等既有功能不受影响。

## 建议验证

优先运行：

```text
cd frontend
npm run build
```

如果项目支持本地运行，请启动前端并人工检查这些页面：

- `/report/defects` 或缺陷中心路由。
- Prompt 模板页面。
- 角色管理页面。
- 组织管理页面。
- 菜单管理页面。
- 字典管理页面。
- 日志管理页面。

如路由名称不确定，请从 `frontend/src/router` 或侧边栏菜单配置中确认，不要凭空猜测。

## Claude 输出要求

结束时必须用中文汇报：

- 实际修改了哪些文件。
- 每个页面具体修复了哪些查询 label 和样式问题。
- 是否调整了缺陷中心背景。
- 已运行的验证命令及结果。
- 无法验证的页面或剩余风险。
