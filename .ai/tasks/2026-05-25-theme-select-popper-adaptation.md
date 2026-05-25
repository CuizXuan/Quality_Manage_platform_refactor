# Codex 实现任务包

## 任务目标

统一修复前端下拉框及其弹层在深浅色主题切换后的样式适配问题，确保文档中心、页头环境切换、生成页多选、列表筛选区等场景在浅色和深色主题下都表现正确。

本次任务重点是 Element Plus 的：

- `el-select`
- `el-select-dropdown`
- `el-popper`
- 相关输入框、选中项、hover、selected、边框、阴影、箭头样式

## 背景说明

用户反馈：切换深浅色主题后，下拉框会出现明显不适配，尤其是在规则管理弹窗中，输入框本体与下拉弹层的背景、文字、边框、hover 状态不一致。截图显示浅色主题下，弹窗中的下拉框主体接近浅色，但展开后的选项面板仍然是深色，导致：

- 下拉面板背景过暗，和浅色弹窗割裂
- 选项文字可读性和 hover 高亮不协调
- 边框、箭头、阴影不符合当前主题

初步分析表明，这不是 `DocGenRules.vue` 单文件问题，而是全局 Element Plus 主题覆盖策略的问题。

## 已知现状分析

Codex 已定位到以下关键信息：

1. 主题切换逻辑
   - `frontend/src/app/AppShell.vue`
   - 通过 `document.documentElement.classList.toggle('dark', dark)` 控制 `html.dark`
   - 说明当前主题切换机制本身是清晰的，可以直接基于 `html.dark` / `:root` 变量修复

2. 浅色主题变量
   - `frontend/src/styles/variables.css`
   - 当前 `:root` 中存在：
     - `--bg-container`
     - `--bg-hover`
     - `--text-primary`
     - `--text-secondary`
     - `--border-color`
   - 但这里同时定义了：
     - `--el-bg-color-overlay: rgba(0, 0, 0, 0.6)`
   - 这个值对浅色主题下拉弹层非常可疑，因为它会直接把 overlay / popper 类背景拉成深色半透明

3. 深色主题变量
   - `frontend/src/styles/dark.css`
   - `html.dark` 中定义：
     - `--el-bg-color-overlay: #122136`
   - 这说明深色主题下弹层使用深色背景是合理的，但浅色主题不应复用深色 overlay 思路

4. 全局 Element Plus 覆盖
   - `frontend/src/styles/element-override.css`
   - 当前全局覆写了：
     - `.el-popper, .el-select__popper, .el-picker__popper`
     - `.el-popper.is-dark`
     - `.el-select-dropdown`
     - `.el-select-dropdown__item`
     - `.el-select-dropdown__item:hover`
     - `.el-select-dropdown__item.selected`
   - 说明真正的修复点大概率应放在全局覆盖和主题变量，而不是每个页面局部补丁

5. 受影响页面范围
   - 文档中心：
     - `frontend/src/views/docgen/DocGenRules.vue`
     - `frontend/src/views/docgen/DocGenTasks.vue`
     - `frontend/src/views/docgen/DocGenGenerate.vue`
   - 页头环境切换：
     - `frontend/src/app/AppShell.vue`
   - 其他大量筛选页也可能受影响：
     - `scenario`
     - `report`
     - `platform`
     - `ai`
     - `case`

因此这次应做“全局统一修复 + 核心页面重点验证”，而不是只改规则管理页面。

## 必读文件

- `AGENTS.md`
- `frontend/src/app/AppShell.vue`
- `frontend/src/styles/variables.css`
- `frontend/src/styles/dark.css`
- `frontend/src/styles/element-override.css`
- `frontend/src/views/docgen/DocGenRules.vue`
- `frontend/src/views/docgen/DocGenTasks.vue`
- `frontend/src/views/docgen/DocGenGenerate.vue`
- `frontend/src/views/scenario/ScenarioList.vue`
- `frontend/src/views/ai/AIPromptTemplates.vue`

按需阅读：

- `frontend/src/views/report/ReportList.vue`
- `frontend/src/views/platform/UserManagement.vue`
- 其他包含 `el-select` 的页面

## 允许修改范围

优先允许修改：

- `frontend/src/styles/variables.css`
- `frontend/src/styles/dark.css`
- `frontend/src/styles/element-override.css`

如确有必要允许少量修改：

- `frontend/src/app/AppShell.vue`
- `frontend/src/views/docgen/DocGenRules.vue`
- `frontend/src/views/docgen/DocGenTasks.vue`
- `frontend/src/views/docgen/DocGenGenerate.vue`

除非必须，不要去逐页补丁式修几十个页面。

## 禁止事项

- 不做逐页堆样式式修复，优先在全局主题变量和 Element Plus 覆盖层处理。
- 不引入新依赖。
- 不更改业务逻辑、接口、store。
- 不为了浅色主题修复而破坏深色主题现有观感。
- 不只修规则管理弹窗而忽略页头环境切换、生成页多选、筛选下拉等代表场景。
- 不把问题简单粗暴处理成固定白底固定黑字，必须真正满足深浅色主题切换。

## 实现要求

1. 先分析全局原因，再修改
   - 先确认 `--el-bg-color-overlay` 在浅色主题中是否被错误用于 select/dropdown/popper 背景。
   - 分清“遮罩背景变量”和“下拉弹层背景变量”是否被混用。
   - 如果是混用，应拆分或改用更合适的主题变量，而不是继续让 popper 背景依赖半透明黑色。

2. 统一修复 Element Plus 下拉弹层样式
   - 下拉框本体、展开面板、hover、selected、边框、箭头、阴影都要与当前主题一致。
   - 浅色主题：
     - 弹层背景应接近 `--bg-container` / `--bg-container-soft`
     - 文字应使用 `--text-primary`
     - hover 应使用 `--bg-hover`
     - border/shadow 不应过重发黑
   - 深色主题：
     - 保持深色面板，但文字、hover、selected、边框要与现有深色体系一致
   - 如果 `el-popper.is-dark` 的覆写会误伤普通 select dropdown，请重新梳理选择器范围

3. 检查 teleported / popper 场景
   - 页头环境切换下拉 `AppShell.vue` 使用了 `:teleported="true"`
   - 规则管理弹窗内下拉、生成页中的 filterable / multiple 下拉也会弹到 body
   - 必须确认这些 body-level popper 在深浅色主题下都能正确继承主题变量和样式

4. 验证的代表场景
   - `/docgen/rules`
     - 规则编辑弹窗中的“文档类型”下拉
     - 页面筛选区中的“文档类型”“启用状态”下拉
   - `/docgen/generate`
     - 多选规则
     - 模板选择
     - filterable 文件选择
   - 顶部页头环境切换下拉
   - 至少再抽查一个非文档中心页面的筛选下拉，例如：
     - `/scenario`
     - `/report`
     - `/system/users`

5. 代码质量要求
   - 优先用主题变量，不要在多个选择器里重复硬编码颜色。
   - 如果需要新增变量，命名要清晰，例如区分：
     - 遮罩背景
     - 弹层背景
     - 弹层 hover
     - 弹层边框
   - Vue 页面只在确实需要时改动，核心修复应尽量集中在样式层。

## 验收标准

- 深色和浅色主题下，`el-select` 本体与展开面板风格一致，没有“浅色输入框 + 深色下拉面板”错配。
- 文档中心规则管理弹窗中的下拉在两种主题下都可读、边界清晰、hover 正常。
- 页头环境切换下拉在两种主题下都正常。
- 文档生成页中的普通下拉、多选下拉、filterable 下拉都正常。
- 至少一个非文档中心页面的下拉也验证通过，说明修复是全局性的。
- 不破坏现有对话框、表格、菜单、tooltip 的主题表现。
- 前端构建通过。

## 建议验证

至少运行：

```text
cd frontend
npm run build
```

建议本地启动手工检查：

```text
cd frontend
npm run dev
```

重点检查：

```text
http://localhost:5173/docgen/rules
http://localhost:5173/docgen/generate
http://localhost:5173/scenario
```

需要分别在深色和浅色主题下检查。

## Claude 输出要求

结束时必须用中文汇报：

- 修改了哪些文件。
- 你判断的根因是什么，特别说明是否存在 `--el-bg-color-overlay` 与下拉弹层背景变量混用。
- 你最终把全局样式如何拆分或调整。
- 验证了哪些页面和哪些下拉场景。
- 已运行的命令和结果。
- 剩余风险。
