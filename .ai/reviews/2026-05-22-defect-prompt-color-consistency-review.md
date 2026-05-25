# Codex 审查修复包：缺陷中心与 Prompt 模板颜色体系继续统一

## 审查目标

基于用户最新截图与反馈，继续修复：

- `frontend/src/views/report/DefectList.vue`
- `frontend/src/views/ai/AIPromptTemplates.vue`

用户反馈：这两个模块颜色仍不一致，需要继续修复。

## 当前问题

上一轮修复把两个页面的 header、filter、table 收口成了类似 `CaseList.vue` 的白色卡片：

```css
html:not(.dark) .xxx__header,
html:not(.dark) .xxx__filters,
html:not(.dark) .xxx__table {
  background: rgba(255, 255, 255, 0.86);
}
```

但用户截图中的参考页面并不是这种纯白卡片风格，而是偏蓝的玻璃/网格背景体系。现在 Prompt 模板看起来像一块明显偏白的浮层压在场景管理页面上，和场景管理、报告类页面颜色不一致。

本次目标不是改结构，而是修复颜色体系：

- 缺陷中心和 Prompt 模板不能是纯白卡片观感。
- 应与场景管理、测试报告等页面的浅蓝玻璃背景一致。
- 页面基础背景、标题区、查询区、表格区需要使用同一套浅蓝透明背景，而不是白色浮层。

## 参考文件

必须参考：

- `frontend/src/views/scenario/ScenarioList.vue`
- `frontend/src/views/report/ReportList.vue`
- `frontend/src/views/case/CaseModulePage.vue`

重点参考这些浅色模式颜色：

```css
html:not(.dark) .scenario-list-page__header {
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.86), rgba(245, 250, 255, 0.68)),
    rgba(255, 255, 255, 0.72);
  box-shadow: 0 18px 46px rgba(20, 42, 76, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.82);
  border-color: rgba(22, 119, 255, 0.18);
}

html:not(.dark) .scenario-list-page__filters {
  background:
    linear-gradient(rgba(22, 119, 255, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.04) 1px, transparent 1px),
    linear-gradient(145deg, rgba(255, 255, 255, 0.76), rgba(245, 250, 255, 0.58)),
    rgba(255, 255, 255, 0.62);
  background-size: 26px 26px, 26px 26px, auto, auto;
  border-color: rgba(22, 119, 255, 0.14);
}

html:not(.dark) .scenario-list-page__table {
  background:
    linear-gradient(rgba(22, 119, 255, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.04) 1px, transparent 1px),
    linear-gradient(145deg, rgba(255, 255, 255, 0.76), rgba(245, 250, 255, 0.58)),
    rgba(255, 255, 255, 0.62);
  background-size: 32px 32px, 32px 32px, auto, auto;
  border-color: rgba(22, 119, 255, 0.14);
}
```

## 需要修复的问题

### 1. Prompt 模板颜色偏白，与参考页面不一致

文件：

- `frontend/src/views/ai/AIPromptTemplates.vue`

要求：

- `.ai-prompt-templates-page__header`、`.ai-prompt-templates-page__filters`、`.ai-prompt-templates-page__table` 的浅色模式背景改为参考页面的浅蓝玻璃背景。
- 不要继续使用单层 `rgba(255, 255, 255, 0.86)` 作为这些区域的浅色背景。
- 边框颜色、阴影、透明度也要与参考页面接近。
- 表格仍不能回到灰色块，内部 `el-table` 不要重新叠加灰色背景。

### 2. 缺陷中心颜色需要与 Prompt 模板和参考页面一致

文件：

- `frontend/src/views/report/DefectList.vue`

要求：

- `.defect-list-page__header`、`.defect-list-page__filters`、`.defect-list-page__table` 的浅色模式背景使用与 Prompt 模板相同的浅蓝玻璃背景体系。
- `.stat-card` 也要使用同一套浅蓝玻璃卡片颜色，不能是明显纯白卡片。
- 缺陷中心与 Prompt 模板之间颜色处理必须一致。

### 3. 页面背景也需要一致

文件：

- `frontend/src/views/report/DefectList.vue`
- `frontend/src/views/ai/AIPromptTemplates.vue`

要求：

- 页面容器背景要与场景管理/报告类页面颜色协调。
- 如果保留当前简化背景，必须确保视觉上不出现“白色页面浮层”。
- 如恢复页面级浅蓝网格背景，应控制层级，不要遮挡内容，不要造成此前的表格灰底问题。

## 修复范围

只允许修改：

- `frontend/src/views/report/DefectList.vue`
- `frontend/src/views/ai/AIPromptTemplates.vue`

## 禁止事项

- 不修改模板结构。
- 不修改接口、查询、分页、表格列、弹窗逻辑。
- 不修改其他页面。
- 不新增依赖。
- 不修改 `.ai/`、`AGENTS.md`、`CLAUDE.md`。
- 不重新引入会让表格内容区域变灰的内部 `el-table` 背景叠加。

## 验收标准

- 缺陷中心和 Prompt 模板不再呈现纯白浮层观感。
- 两个模块的 header、filter、table、缺陷统计卡片颜色体系一致。
- 两个模块与场景管理/测试报告页面的浅蓝玻璃背景观感一致。
- 表格内容区域不再灰。
- 查询栏冒号、控件对齐、固定列 hover 修复都保留。
- 深色模式仍可读。
- 业务逻辑不变。

## 验证方式

修复后运行：

```text
cd frontend
npm run build
```

如可本地访问，请人工对比：

- 场景管理页面。
- 测试报告页面。
- 缺陷中心页面。
- Prompt 模板页面。

重点看：

- 颜色是否同一套浅蓝玻璃体系。
- Prompt 模板是否不再像白色浮层。
- 缺陷中心和 Prompt 模板是否一致。
- 表格区域是否没有灰底。

## Claude 输出要求

结束时必须用中文汇报：

- 哪些颜色样式已统一。
- 实际修改了哪些文件。
- 是否保留了之前的查询栏和表格修复。
- 是否运行 `npm run build` 以及结果。
- 仍未人工验证的风险。
