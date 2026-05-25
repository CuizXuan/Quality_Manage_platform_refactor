# Codex 审查修复包：统一基础页面表单与表格样式体系

## 审查目标

基于用户最新反馈，重新审查前两轮任务的实现：

- `.ai/tasks/2026-05-22-align-query-bars.md`
- `.ai/tasks/2026-05-22-table-transparency-defect-prompt.md`
- `.ai/reviews/2026-05-22-query-bars-table-transparency-review.md`

用户指出：当前不是统一的处理方式，基础页面样式需要按照用例管理模块统一，包括背景、表格透明度、层级控制等。

## 核心问题

当前 `DefectList.vue` 和 `AIPromptTemplates.vue` 虽然局部修复了查询栏冒号和表格灰底，但页面仍然混用了两套样式体系：

1. 页面容器仍保留多层 `linear-gradient` 网格背景、`::before` 扫描层、`::after` 粒子层。
2. 标题区和查询区仍保留复杂背景、伪元素、较重的 `box-shadow`、高强度 `backdrop-filter`。
3. 表格区已经部分参考用例管理，但 header/filter/page/stat 区域没有同步收口。
4. 视觉层级上，多个伪元素叠在内容层上方或同级，导致页面整体背景、查询栏、表格区域不像同一套基础表单样式。

用户要的不是单独调透明度，而是让这些基础页面区域与用例管理模块保持一致。

## 目标基准

以 `frontend/src/views/case/CaseList.vue` 为基础样式基准。

重点参考：

```css
.case-list-page {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-height: 0;
  min-width: 0;
  gap: 10px;
  padding: 12px;
  background:
    radial-gradient(circle at top right, rgba(56, 189, 248, 0.13), transparent 30%),
    var(--bg-page);
  overflow: hidden;
}

.case-list-page__header,
.case-list-page__filters,
.case-list-page__table {
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: rgba(20, 22, 27, 0.7);
  box-shadow: var(--box-shadow-light);
  backdrop-filter: blur(10px);
}

html:not(.dark) .case-list-page__header,
html:not(.dark) .case-list-page__filters,
html:not(.dark) .case-list-page__table {
  background: rgba(255, 255, 255, 0.86);
}
```

## 需要修复的问题

### 1. 缺陷中心页面基础容器未按用例管理收口

文件：

- `frontend/src/views/report/DefectList.vue`

要求：

- `.defect-list-page` 按 `CaseList.vue` 的基础页面容器方式处理。
- 移除或停用页面级 `::before`、`::after` 扫描/粒子层。
- 页面背景使用用例管理同类处理，不再使用多层网格、扫描线和多重渐变。
- 不要让页面背景层侵入标题区、统计区、查询区和表格区。

### 2. 缺陷中心标题区、查询区、表格区样式体系不统一

文件：

- `frontend/src/views/report/DefectList.vue`

要求：

- `.defect-list-page__header` 参考 `.case-list-page__header`，使用简单背景、统一边框、统一阴影、统一 blur。
- `.defect-list-page__filters` 参考 `.case-list-page__filters`，移除查询区伪元素扫描层和网格叠加。
- `.defect-list-page__table` 保持已接近用例管理的方向，但边框、阴影、背景、backdrop-filter 应与用例管理一致。
- 如保留 `.defect-list-page__stats`，统计卡片也要使用同一基础卡片处理，不要使用扫描伪元素和网格叠加；保持与页面其他卡片统一。
- 保留查询 label 中文冒号和对齐修复。
- 保留固定列 hover 背景修复。

### 3. Prompt 模板页面基础容器未按用例管理收口

文件：

- `frontend/src/views/ai/AIPromptTemplates.vue`

要求：

- `.ai-prompt-templates-page` 按 `CaseList.vue` 的基础页面容器方式处理。
- 移除或停用页面级 `::before`、`::after` 扫描/粒子层。
- 页面背景使用用例管理同类处理，不再使用多层网格、扫描线和多重渐变。

### 4. Prompt 模板标题区、查询区、表格区样式体系不统一

文件：

- `frontend/src/views/ai/AIPromptTemplates.vue`

要求：

- `.ai-prompt-templates-page__header` 参考 `.case-list-page__header`。
- `.ai-prompt-templates-page__filters` 参考 `.case-list-page__filters`，移除查询区伪元素扫描层和网格叠加。
- `.ai-prompt-templates-page__table` 参考 `.case-list-page__table`，统一边框、背景、阴影、blur。
- 保留查询 label 中文冒号和对齐修复。
- 保留固定列 hover 背景修复。

## 修复范围

只允许修改：

- `frontend/src/views/report/DefectList.vue`
- `frontend/src/views/ai/AIPromptTemplates.vue`

本次不要修改：

- `frontend/src/views/report/ReportList.vue`
- `frontend/src/views/case/CaseList.vue`
- 平台管理页面
- 字典管理页面
- 后端代码

## 禁止事项

- 不修改接口、查询、分页、表格列、弹窗逻辑。
- 不删除业务功能。
- 不改变页面结构，除非只是为了移除无用伪元素相关样式。
- 不新增依赖。
- 不继续扩大到其他页面。
- 不修改 `.ai/`、`AGENTS.md`、`CLAUDE.md`。

## 验收标准

- 缺陷中心和 Prompt 模板的页面背景、标题区、查询区、表格区基础视觉与用例管理模块一致。
- 不再出现复杂网格背景、扫描线、粒子层穿透到表格或查询栏的情况。
- 查询栏 label 仍保留中文冒号。
- 查询栏控件和按钮仍然对齐。
- 表格背景不再呈现灰色块。
- 表格 hover 包含固定操作列，hover 背景连续。
- 深色模式和浅色模式下文字、表格、按钮仍清晰可读。
- 缺陷中心统计卡片与页面基础卡片风格一致。
- 查询、重置、分页、新建、编辑等交互逻辑不变。

## 验证方式

修复后运行：

```text
cd frontend
npm run build
```

如可本地访问，请人工对比：

- 用例管理页面。
- 缺陷中心页面。
- Prompt 模板页面。

重点看：

- 页面背景是否同一套。
- 标题区、查询区、表格区是否同一套边框/背景/阴影/层级。
- 表格区域是否不再灰。
- 查询栏是否仍有 `字段名：输入框` 的格式。

## Claude 输出要求

结束时必须用中文汇报：

- 已修复哪些基础样式不一致问题。
- 实际修改了哪些文件。
- 哪些样式按用例管理完成了统一。
- 是否运行 `npm run build` 以及结果。
- 是否仍有未验证项或剩余风险。
