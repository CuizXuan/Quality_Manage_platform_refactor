# Codex 实现任务包：AI 中枢页面对齐用例管理视觉与表单样式

## 任务目标

将 AI 中枢所有页面的基础视觉、背景层、卡片层级、查询/输入表单样式对齐 `frontend/src/views/case/CaseManagement.vue`。

用户明确反馈：

- 需要继续对齐 `CaseManagement`。
- AI 中枢所有模块都要统一。
- 例如 `VariantGenerator.vue` 的查询栏/输入栏没有对齐。

本任务重点不是业务功能改造，而是统一 AI 中枢页面的基础 UI 体系。

## 背景说明

前面已处理过缺陷中心和 Prompt 模板管理的部分样式，但 AI 中枢其他页面仍存在不一致：

- 有的页面有偏绿色/蓝色流动背景，有的页面卡片层级不同。
- 有的查询/输入区仍使用 `inline` 表单，label 和控件未按统一行布局对齐。
- 多个页面 label 缺少中文冒号 `：`。
- 按钮与输入框的基线、间距、宽度不一致。
- loading、empty、result、table 等区域背景和层级处理不统一。

本次以 `CaseManagement.vue` 的页面背景和卡片风格作为参考，统一 AI 中枢页面。

## 必读文件

- `AGENTS.md`
- `CLAUDE.md`
- `.ai/INDEX.md`
- `frontend/src/views/case/CaseManagement.vue`
- `frontend/src/views/ai/AIModelConfig.vue`
- `frontend/src/views/ai/AIPromptTemplates.vue`
- `frontend/src/views/ai/VariantGenerator.vue`
- `frontend/src/views/ai/AssertionGenerator.vue`
- `frontend/src/views/ai/FailureAnalyzer.vue`
- `frontend/src/views/ai/ReportSummarizer.vue`
- `frontend/src/views/ai/SuggestionHistory.vue`

## 允许修改范围

只允许修改以下 AI 中枢页面：

- `frontend/src/views/ai/AIModelConfig.vue`
- `frontend/src/views/ai/AIPromptTemplates.vue`
- `frontend/src/views/ai/VariantGenerator.vue`
- `frontend/src/views/ai/AssertionGenerator.vue`
- `frontend/src/views/ai/FailureAnalyzer.vue`
- `frontend/src/views/ai/ReportSummarizer.vue`
- `frontend/src/views/ai/SuggestionHistory.vue`

如果发现必须抽公共样式，先不要抽；本次优先在页面 scoped CSS 内做局部统一，避免扩大影响面。

## 禁止事项

- 不修改后端代码。
- 不修改接口调用逻辑。
- 不修改 store、router、API 文件。
- 不改变表单字段、请求参数、分页逻辑、表格列结构。
- 不新增依赖。
- 不做无关重构。
- 不修改 `CaseManagement.vue`。
- 不修改 `.ai/`、`AGENTS.md`、`CLAUDE.md`。

## 实现要求

### 1. 页面背景对齐 CaseManagement

AI 中枢页面容器应参考 `CaseManagement.vue` 的 `case-center-page`：

- 页面底层保留偏绿色/蓝色的网格与流动感。
- 使用类似多层 `linear-gradient` 背景。
- 页面级 `::before` / `::after` 仅用于背景扫描线、粒子层，不应遮挡内容。
- 内容区、header、输入区、结果区必须位于背景层之上。
- 如页面已有类似背景，可保留但要统一颜色、层级、透明度。

重点参考：

```css
.case-center-page {
  position: relative;
  display: flex;
  width: 100%;
  height: 100%;
  min-height: 0;
  min-width: 0;
  flex-direction: column;
  gap: 10px;
  padding: 12px;
  background:
    linear-gradient(rgba(56, 189, 248, 0.095) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.085) 1px, transparent 1px),
    linear-gradient(145deg, rgba(34, 211, 166, 0.18), transparent 30%),
    linear-gradient(225deg, rgba(56, 189, 248, 0.22), transparent 36%),
    linear-gradient(0deg, rgba(22, 119, 255, 0.12), transparent 50%),
    var(--bg-page);
  background-size: 28px 28px, 28px 28px, auto, auto, auto, auto;
  overflow: hidden;
}
```

### 2. Header 卡片对齐 CaseManagement

每个 AI 页面 header 需要统一：

- `position: relative`
- `z-index: 1`
- `min-height: 56px`
- `padding: 12px 16px`
- 统一边框、圆角、背景、阴影、`backdrop-filter`
- 浅色模式使用玻璃白背景，而不是死白大块。
- 如保留 `::after` 流动线条，需要保证 h1、p、按钮在上层。

### 3. 查询/输入表单统一对齐

所有 AI 页面中用于查询、输入、生成的表单区域都要统一为类似下面结构：

```vue
<el-form :model="..." label-position="left" class="filter-form">
  <div class="filter-form__row">
    <el-form-item label="字段名：" class="filter-item">
      ...
    </el-form-item>
    <div class="filter-actions">
      ...
    </div>
  </div>
</el-form>
```

要求：

- 查询/输入区 label 必须补中文冒号 `：`。
- label 与输入框/选择框/按钮同一基线对齐。
- 按钮高度与输入控件一致。
- 按钮间距统一。
- 宽屏下横向排列；窄屏可换行但不能错位。
- 不再依赖 `inline` 表单造成不可控间距。

重点页面：

- `VariantGenerator.vue`
  - `原始用例：`
  - `变体数量：`
  - `变异策略：`
  - `生成变体` 按钮与输入控件对齐。
- `AssertionGenerator.vue`
  - `用例ID：`
  - `响应JSON：`
  - `生成断言` 按钮与输入控件对齐。
- `FailureAnalyzer.vue`
  - `执行步骤ID：`
  - `分析失败` 按钮与输入控件对齐。
- `ReportSummarizer.vue`
  - `报告ID：`
  - `生成总结`、`重置` 按钮与输入控件对齐。
- `SuggestionHistory.vue`
  - `采纳状态：`
  - `建议类型：`
  - 查询/重置按钮对齐。
- `AIPromptTemplates.vue`
  - 保留已有 `模板类型：`、`关键词：` 处理，并检查与其他 AI 页面一致。
- `AIModelConfig.vue`
  - 这是配置表单，不要强行改成查询栏；但基础卡片背景、header、表单 label 间距应与 AI 页面体系协调。

### 4. 卡片/结果/表格区域统一

AI 页面中的以下区域需要使用同一套视觉层级：

- 输入区，例如 `variant-generator__input`
- loading 区，例如 `variant-generator__loading`
- empty 区，例如 `variant-generator__empty`
- result/table 区，例如 `variant-generator__result`
- config/form/status/test-result 区

要求：

- 参考 `CaseManagement.vue` 的玻璃卡片效果。
- 保持 `z-index: 1`，内容在页面背景层之上。
- 表格内部不要出现灰色大块遮罩。
- 表头、hover、固定列 hover 保持自然。
- 不要让背景伪元素覆盖文字和控件。

### 5. 保持已有修复

必须保留：

- `AIPromptTemplates.vue` 之前已修复的查询 label 中文冒号。
- `AIPromptTemplates.vue` 表格固定列 hover 修复。
- `AIPromptTemplates.vue` 表格不灰底。
- 不要破坏现有业务逻辑。

## 验收标准

- AI 中枢所有页面背景都有与 `CaseManagement.vue` 一致的偏绿色/蓝色流动感。
- AI 中枢所有页面 header、输入区、结果区、表格区视觉层级一致。
- `VariantGenerator.vue` 查询/输入栏不再错位，label 均带中文冒号。
- 其他 AI 页面表单 label 与控件也对齐。
- 生成、查询、重置等按钮与输入控件同一基线。
- 表格/结果区没有灰色大块遮罩。
- 页面文字、按钮、表格在浅色和深色模式下都清晰可读。
- 所有原有功能不变。

## 建议验证

运行：

```text
cd frontend
npm run build
```

如本地可访问，请人工检查：

- AI 模型配置
- Prompt 模板管理
- 用例变体生成
- 断言生成
- 失败分析
- 报告总结
- 建议历史
- 用例管理页面，作为视觉参考

重点看：

- 背景是否有 CaseManagement 的偏绿色流动感。
- 表单 label 是否是 `字段名：控件`。
- 控件和按钮是否横向对齐。
- 结果区/空状态/表格区是否同一套卡片层级。

## Claude 输出要求

结束时必须用中文汇报：

- 修改了哪些 AI 页面。
- 每个页面修复了哪些背景、卡片、表单对齐问题。
- 是否保留了 Prompt 模板既有修复。
- 是否运行 `npm run build` 以及结果。
- 未人工验证项或剩余风险。
