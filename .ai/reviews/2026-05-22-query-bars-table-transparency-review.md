# Codex 审查修复包：查询栏与表格透明度任务返工

## 审查目标

审查 Claude 对以下两个任务包的实现结果：

- `.ai/tasks/2026-05-22-align-query-bars.md`
- `.ai/tasks/2026-05-22-table-transparency-defect-prompt.md`

涉及当前 diff 中的主要文件：

- `frontend/src/views/report/DefectList.vue`
- `frontend/src/views/ai/AIPromptTemplates.vue`
- `frontend/src/views/platform/RoleManagement.vue`
- `frontend/src/views/platform/OrganizationManagement.vue`
- `frontend/src/views/platform/MenuManagement.vue`
- `frontend/src/views/platform/LogManagement.vue`

构建验证已通过：

```text
cd frontend
npm run build
```

## 审查结论

整体方向正确：

- 缺陷中心、Prompt 模板、角色管理、组织管理、菜单管理、日志管理查询栏已补齐中文冒号。
- 查询栏结构已调整为统一 row 布局。
- 缺陷中心和 Prompt 模板表格内部灰色背景叠加已明显减少。
- 字典管理当前是左右工具栏纯搜索框，没有独立 label，不强行新增 label 可以接受。

但仍有以下问题需要修复。

## 需要修复的问题

### 1. `AIPromptTemplates.vue` 浅色模式整页背景被无关修改

文件：

- `frontend/src/views/ai/AIPromptTemplates.vue`

问题：

当前 diff 修改了：

```css
html:not(.dark) .ai-prompt-templates-page {
  background:
    linear-gradient(rgba(22, 119, 255, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.04) 1px, transparent 1px),
    linear-gradient(145deg, rgba(255, 255, 255, 0.76), rgba(245, 250, 255, 0.68)),
    rgba(255, 255, 255, 0.72);
}
```

这属于页面整体背景修改，不属于第二个任务的“只调整表格区域透明度”范围；第一个任务也只要求缺陷中心背景与同类页面一致，没有要求修改 Prompt 模板整页背景。

要求：

- 还原 `html:not(.dark) .ai-prompt-templates-page` 的无关背景改动。
- Prompt 模板只保留查询栏 label/对齐和表格透明度相关改动。
- 不要改动 `DefectList.vue` 的页面背景，因为第一个任务允许调整缺陷中心背景。

### 2. 缺陷中心与 Prompt 模板固定操作列 hover 背景未覆盖

文件：

- `frontend/src/views/report/DefectList.vue`
- `frontend/src/views/ai/AIPromptTemplates.vue`

问题：

这两个表格都存在 `fixed="right"` 的操作列。当前只设置了：

```css
.xxx__table :deep(.el-table__row:hover > td) {
  background: var(--color-primary-soft) !important;
}
```

但没有像用例管理 `CaseList.vue` 一样覆盖固定列：

```css
.case-list-page__table :deep(.el-table__row:hover > td.el-table-fixed-column--left),
.case-list-page__table :deep(.el-table__row:hover > td.el-table-fixed-column--right) {
  background: var(--color-primary-soft) !important;
}
```

固定操作列 hover 时可能仍保持不同背景，造成行 hover 断层。

要求：

- 在 `DefectList.vue` 表格样式中补齐固定列 hover 背景规则。
- 在 `AIPromptTemplates.vue` 表格样式中补齐固定列 hover 背景规则。
- 背景值统一使用 `var(--color-primary-soft) !important`。

## 修复范围

只允许修改：

- `frontend/src/views/report/DefectList.vue`
- `frontend/src/views/ai/AIPromptTemplates.vue`

## 禁止事项

- 不修改平台管理页面。
- 不修改字典管理页面。
- 不修改后端代码。
- 不修改接口、查询、分页、表格列、弹窗逻辑。
- 不新增依赖。
- 不继续扩大视觉重构范围。
- 不修改 `.ai/`、`AGENTS.md`、`CLAUDE.md`。

## 验证方式

修复后运行：

```text
cd frontend
npm run build
```

如本地可访问页面，请人工检查：

- 缺陷中心表格 hover 操作列背景是否连续。
- Prompt 模板表格 hover 操作列背景是否连续。
- Prompt 模板整页背景是否没有被本次任务额外改动。

## Claude 输出要求

结束时必须用中文汇报：

- 已修复哪些审查问题。
- 实际修改了哪些文件。
- 是否运行 `npm run build` 以及结果。
- 是否仍有未验证项或剩余风险。
