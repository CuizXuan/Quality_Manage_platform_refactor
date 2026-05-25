# Codex 实现任务包

## 任务目标

统一“文档中心”页面的视觉与交互，让它与用例管理、缺陷管理、报告列表、AI 中心等页面保持同一套后台管理页风格。

重点修复用户反馈的明显问题：

- 页面背景与其他页面差异大，当前文档中心缺少统一的科技网格/玻璃面板容器。
- 列表字段左右宽度分布不均匀，表格列宽、对齐、操作列宽度需要重新梳理。
- 新增/上传按钮位置不符合其他页面习惯，应放在页头右侧或查询区右侧，不能孤立漂在内容左侧。
- 查询条件缺失，任务、规则、模板列表都应有清晰查询区。
- 表单字段与输入框未对齐，生成页与编辑弹窗的 label、控件宽度、按钮行需要统一。
- 规则编辑弹窗大小、字体、表单密度与其他页面不一致。

## 背景说明

当前文档中心由以下页面组成：

- `/docgen/tasks`：任务中心
- `/docgen/rules`：规则管理
- `/docgen/templates`：模板管理
- `/docgen/generate`：生成文档

这些页面目前大多只是 `padding: 24px` + 简单 `toolbar` + `el-table`，没有采用项目其他管理页常见的：

- 全屏 `height: 100%` 页面容器
- 12px 页面内边距、10px 区块间距
- 页头、查询区、表格区分块
- 右上角主操作按钮
- 查询 / 重置按钮
- 表格高度填满剩余区域
- 分页固定在表格区底部
- 弹窗内表单 label、输入框宽度和 footer 对齐

请先阅读现有页面风格，再实施，不要只针对文档中心单点堆样式。

## 已知现状分析

Codex 已初步定位：

1. `frontend/src/views/docgen/DocGenTasks.vue`
   - 已有任务类型、状态筛选和刷新按钮，但缺少“查询 / 重置”模式。
   - `loadTasks()` 已支持 `task_type/status`，但分页切换未完整带上 page/page_size 模型。
   - 表格列宽偏粗糙，操作列内容可能挤压。

2. `frontend/src/views/docgen/DocGenRules.vue`
   - 只有新增按钮，没有查询区。
   - store 和后端已支持 `doc_type`、`enabled` 过滤，可直接补齐查询条件。
   - 编辑弹窗 `width="600px"`，表单 label 和大文本域观感不统一，需要优化弹窗宽度、高度、label 对齐和 footer。

3. `frontend/src/views/docgen/DocGenTemplates.vue`
   - 上传按钮与确认上传按钮在内容左侧工具栏，不符合其他页面主操作位置。
   - 后端 `GET /api/docgen/templates` 目前仅支持 `page/page_size`，没有 keyword 参数。
   - 如需模板关键字查询，可以在前端对当前页做轻量过滤；若决定补后端 keyword，改动必须很小，并补齐 store/API 传参。

4. `frontend/src/views/docgen/DocGenGenerate.vue`
   - 生成页表单控件宽度、上传按钮、预览区和 tabs 容器未与管理页风格统一。
   - 三个生成表单存在重复布局，应在不做大重构的前提下统一 class、label-width、控件宽度、按钮行位置。

5. `frontend/src/stores/docgenStore.js`
   - `fetchTasks` 支持 `task_type/status`。
   - `fetchRules` 支持 `doc_type/enabled`。
   - `fetchTemplates` 目前只传 `page/page_size`。

6. `backend/app/routers/docgen.py`
   - `list_tasks` 支持 `task_type/status`。
   - `list_rules` 支持 `doc_type/enabled`。
   - `list_templates` 只支持分页。

## 必读文件

- `AGENTS.md`
- `.ai/CODEX_WORKFLOW.md`
- `frontend/src/views/docgen/DocGenerationCenter.vue`
- `frontend/src/views/docgen/DocGenTasks.vue`
- `frontend/src/views/docgen/DocGenRules.vue`
- `frontend/src/views/docgen/DocGenTemplates.vue`
- `frontend/src/views/docgen/DocGenGenerate.vue`
- `frontend/src/stores/docgenStore.js`
- `frontend/src/api/docgen.js`
- `frontend/src/styles/page-framework.css`
- `frontend/src/styles/global.css`
- `frontend/src/views/report/DefectList.vue`
- `frontend/src/views/report/ReportList.vue`
- `frontend/src/views/ai/AIModelConfig.vue`

按需阅读：

- `backend/app/routers/docgen.py`
- `backend/app/models/docgen.py`
- `backend/app/schemas/docgen.py`

## 允许修改范围

优先允许修改：

- `frontend/src/views/docgen/DocGenTasks.vue`
- `frontend/src/views/docgen/DocGenRules.vue`
- `frontend/src/views/docgen/DocGenTemplates.vue`
- `frontend/src/views/docgen/DocGenGenerate.vue`
- `frontend/src/stores/docgenStore.js`
- `frontend/src/api/docgen.js`

如能明显降低重复且保持简单，可以新增一个文档中心局部组件或样式文件：

- `frontend/src/views/docgen/components/*.vue`
- `frontend/src/views/docgen/docgenShared.css`

仅在确有必要且改动很小时允许修改：

- `backend/app/routers/docgen.py`
- `backend/app/schemas/docgen.py`

## 禁止事项

- 不做无关重构，不改路由层级，不改菜单权限。
- 不改变现有 API 响应结构。
- 不引入新依赖。
- 不把文档生成、预览、上传、下载、删除等业务行为改掉。
- 不把查询条件写成无法生效的假 UI；若后端不支持，必须明确采用前端当前页过滤或补齐后端小改。
- 不使用大面积单色紫色、棕色、米色或纯营销风格布局。
- 不把页面做成落地页，不增加说明型大段文案。
- 不使用嵌套卡片；页面按页头、查询区、表格区、表单区组织即可。

## 实现要求

### 1. 页面整体结构统一

四个文档中心页面统一为后台管理页结构：

- 根容器 `height: 100%`、`min-height: 0`、`display: flex`、`flex-direction: column`。
- 页面内边距建议 `12px`，区块间距建议 `10px`，参考 `DefectList.vue` / `ReportList.vue`。
- 使用统一背景，优先复用 `page-framework.css` 中的 `.page-shell--tech-grid` / `.page-surface` 思路，或在 docgen 页面局部实现一致背景。
- 页头包含标题、说明和主操作按钮。规则页主按钮为“新增规则”，模板页主按钮为“上传模板”或“确认上传”组合，任务页可放“刷新”，生成页可不强行放新增按钮。
- 页头标题字体、说明字体、区块边框、圆角、阴影与其他管理页一致。

### 2. 查询区补齐

任务中心：

- 查询条件至少包含：任务类型、状态、关键词。
- 任务类型可复用已有值：`requirement_design`、`database_design`、`api_design`。
- 状态可复用已有值：`running`、`success`、`failed`。
- 如果后端不支持 keyword，关键词可以仅对当前页 `name/source_filename/output_filename` 做前端过滤；但 UI 不能暗示全量后端搜索。
- 提供“查询”“重置”按钮，刷新按钮放在动作区。

规则管理：

- 查询条件至少包含：文档类型 `doc_type`、启用状态 `enabled`、关键词。
- `doc_type/enabled` 使用 store 已支持的后端参数。
- 关键词可当前页过滤 `name/filename/doc_type`，或补后端小改。
- 提供“查询”“重置”按钮。

模板管理：

- 查询条件至少包含：关键词。
- 上传流程需要清晰：选择文件、确认上传、取消/清空已选文件。
- 上传主动作位置应在页头右侧或查询区右侧，不要放在一个孤立左侧 toolbar。
- 若补后端 keyword，请同步改 `docgenStore.fetchTemplates` 和 `docgenApi.listTemplates` 传参。

### 3. 表格列宽与对齐

请重新梳理三个列表页列宽：

- ID 列保持窄列，建议 70。
- 名称类列使用 `min-width` 并 `show-overflow-tooltip`。
- 类型、状态、启用、大小等短字段居中，宽度固定。
- 时间列宽度保持 160-180。
- 操作列固定右侧，宽度足够容纳当前操作，不换行，不挤压。
- 表格区域应填满剩余高度，分页固定在表格区底部。
- 空状态文案保持简洁。

### 4. 新增/编辑弹窗统一

规则编辑弹窗：

- 弹窗宽度建议 `min(760px, 92vw)` 或 Element Plus 可接受的固定宽度。
- 内容高度不超过视口，必要时内部滚动。
- 表单 label 与输入框对齐，建议 `label-width="96px"` 或参考项目已有弹窗。
- JSON 内容文本域使用等宽字体或更适合 JSON 的样式，避免字体突兀。
- footer 按钮右对齐，按钮高度与其他页面一致。
- 保存前保留现有 JSON 校验行为；可在前端增加轻量校验，但后端校验不能移除。

### 5. 生成页表单统一

生成页需要与管理页风格统一：

- 左侧 tabs 区域、右侧表单区要有稳定高度和边界。
- 三个 tab 内的表单 label、输入控件、上传按钮、开关说明、预览/生成按钮行对齐。
- 文件选择与上传按钮保持同一行，不要挤压输入框。
- 预览结果使用同一面板样式，不要与页面背景混在一起。
- 保留现有预览、生成、异步模式、上传文件、跳转任务中心逻辑。

### 6. 代码质量

- Vue 组件保持可读，小函数单一职责。
- 如果重复样式太多，优先抽成局部 CSS class；不要为了抽象而引入复杂组件。
- 可见中文文案保持中文，修正明显乱码时要谨慎：如果文件整体已有编码异常，避免扩大改动。
- Element Plus icon 请从 `@element-plus/icons-vue` 显式 import，不要依赖字符串 icon。

## 验收标准

- `/docgen/tasks`、`/docgen/rules`、`/docgen/templates`、`/docgen/generate` 四个页面视觉统一，不再像独立拼出来的旧页面。
- 文档中心背景、页头、查询区、表格区、分页区与缺陷/报告/AI 中心页面风格一致。
- 新增规则、上传模板、刷新/查询/重置按钮位置符合其他页面习惯。
- 查询条件可实际影响列表展示；不能只有 UI 没行为。
- 表格列宽分布均衡，操作列不换行，名称/文件名长文本有省略和 tooltip。
- 字段 label 与输入控件对齐，生成页三个 tab 的表单宽度一致。
- 规则编辑弹窗大小、字体、footer 与其他弹窗协调，不出现内容溢出视口。
- 现有文档生成、预览、上传、下载、删除、启用开关功能不回归。
- 浅色和深色模式均没有明显文字重叠、低对比或背景突兀问题。

## 建议验证

至少运行：

```text
cd frontend
npm run build
```

建议本地启动并手工检查：

```text
cd frontend
npm run dev
```

浏览器检查路径：

```text
http://localhost:5173/docgen/tasks
http://localhost:5173/docgen/rules
http://localhost:5173/docgen/templates
http://localhost:5173/docgen/generate
```

如修改后端，额外运行：

```text
cd backend
python -m py_compile app/routers/docgen.py app/schemas/docgen.py
```

如果命令无法运行，说明阻塞原因和风险。

## Claude 输出要求

结束时必须用中文汇报：

- 变更文件列表。
- 你先分析到的文档中心差异点。
- 每个页面分别修复了什么。
- 查询条件的实现方式，特别说明 keyword 是后端查询还是当前页前端过滤。
- 已运行的验证命令和结果。
- 未覆盖或剩余风险。
