# Codex 实现任务包：调整缺陷中心与 Prompt 模板表格透明度

## 任务目标

修复两个页面表格区域背景透明度与其他模块不一致的问题：

- 缺陷中心：`frontend/src/views/report/DefectList.vue`
- Prompt 模板：`frontend/src/views/ai/AIPromptTemplates.vue`

用户反馈：这两个模块的表格透明度与其他模块不一样，当前视觉上像灰色背景。需要参考用例管理模块调整表格透明度，让背景不再是现在的灰色。

## 背景说明

当前 `DefectList.vue` 和 `AIPromptTemplates.vue` 的表格样式中，表格容器和内部 `el-table` 同时叠加了多层半透明网格背景：

- 表格容器 `__table` 使用了多层 `linear-gradient` 和较低透明度底色。
- 内部 `:deep(.el-table)` 又设置了 `background`、`--el-table-tr-bg-color`、`--el-table-header-bg-color` 等变量。
- 在浅色模式下，内部表格背景 `rgba(255, 255, 255, 0.44)` 和行背景 `rgba(255, 255, 255, 0.54)` 容易叠加成灰色块。

用例管理页面 `frontend/src/views/case/CaseList.vue` 的表格视觉更干净：

- 表格容器浅色模式背景为 `rgba(255, 255, 255, 0.86)`。
- 内部 `el-table` 没有额外叠加灰色网格背景。
- 表头使用 `var(--bg-container-soft)`。
- hover 使用 `var(--color-primary-soft)`。

本任务要求将缺陷中心和 Prompt 模板的表格透明度调整到接近用例管理模块的观感。

## 必读文件

- `AGENTS.md`
- `CLAUDE.md`
- `.ai/INDEX.md`
- `frontend/src/views/report/DefectList.vue`
- `frontend/src/views/ai/AIPromptTemplates.vue`
- `frontend/src/views/case/CaseList.vue`

## 允许修改范围

只允许修改：

- `frontend/src/views/report/DefectList.vue`
- `frontend/src/views/ai/AIPromptTemplates.vue`

## 禁止事项

- 不修改后端代码。
- 不修改接口调用、查询逻辑、分页逻辑、表格列、弹窗逻辑。
- 不修改用例管理模块。
- 不引入新依赖。
- 不做页面整体重构。
- 不修改 `.ai/`、`AGENTS.md`、`CLAUDE.md`。

## 实现要求

### 1. 参考用例管理表格样式

以 `frontend/src/views/case/CaseList.vue` 的 `.case-list-page__table` 表格区域为主要参考。

重点参考：

```css
.case-list-page__table {
  background: rgba(20, 22, 27, 0.7);
  box-shadow: var(--box-shadow-light);
  backdrop-filter: blur(10px);
}

html:not(.dark) .case-list-page__table {
  background: rgba(255, 255, 255, 0.86);
}

.case-list-page__table :deep(.el-table) {
  flex: 1;
}

.case-list-page__table :deep(.el-table__header th) {
  background: var(--bg-container-soft) !important;
}

.case-list-page__table :deep(.el-table__row:hover > td) {
  background: var(--color-primary-soft) !important;
}
```

不要求完全复制所有属性，但应让缺陷中心和 Prompt 模板表格视觉接近用例管理，尤其要消除当前灰色表格背景。

### 2. 减少表格内部灰色背景叠加

优先处理以下样式：

- `DefectList.vue` 中 `.defect-list-page__table :deep(.el-table)` 的背景叠加。
- `AIPromptTemplates.vue` 中 `.ai-prompt-templates-page__table :deep(.el-table)` 的背景叠加。
- 浅色模式下内部表格背景和行背景变量。

建议方向：

- 保留表格容器外层的基础玻璃背景即可。
- 内部 `el-table` 不要再叠加明显灰色背景。
- 浅色模式下不要使用会造成灰色观感的 `rgba(255, 255, 255, 0.44)` 作为内部表格背景。
- hover 背景建议统一使用 `var(--color-primary-soft)`。

### 3. 保持页面整体风格

- 不需要删除所有视觉效果。
- 如果保留网格纹理，必须确保表格内容区域不再呈现明显灰底。
- 表头、行 hover、固定列 hover 的观感应与用例管理保持一致。
- 深色模式也需要保持可读性，不能变成完全透明导致文字难读。

### 4. 控制修改范围

- 只调整 scoped CSS 中表格区域相关样式。
- 不修改 `<template>` 中表格列结构。
- 不修改 `<script setup>` 业务逻辑。

## 验收标准

- 缺陷中心表格背景不再呈现当前灰色块效果。
- Prompt 模板表格背景不再呈现当前灰色块效果。
- 两个页面的表格透明度、表头背景、hover 背景与用例管理模块视觉接近。
- 表格文字、标签、操作按钮仍清晰可读。
- 深色模式和浅色模式下都没有明显视觉回退。
- 表格高度、分页区域、滚动行为不变。
- 查询、分页、编辑、新建等功能不受影响。

## 建议验证

优先运行：

```text
cd frontend
npm run build
```

如本地环境可运行，请人工检查：

- 缺陷中心页面。
- Prompt 模板页面。
- 用例管理页面，作为视觉参照。

重点检查：

- 浅色模式下表格是否不再灰。
- 深色模式下表格是否仍可读。
- 表头和 hover 效果是否自然。
- 分页区域是否仍贴合表格底部。

## Claude 输出要求

结束时必须用中文汇报：

- 实际修改了哪些文件。
- 分别调整了哪些表格背景或透明度样式。
- 是否参考并对齐了用例管理模块。
- 已运行的验证命令及结果。
- 未验证项或剩余风险。
