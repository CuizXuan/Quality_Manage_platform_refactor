# 样式统一修复任务包

## 任务目标

全面排查并修复 Quality Manage Platform 前端页面的样式不统一问题，以用例管理（CaseManagement）为设计规范基准，将所有模块的样式统一化。

## 背景说明

当前项目存在大量页面样式细节不一致的问题，虽然整体可看，但背景色、字体、查询栏布局、按钮样式、分页组件、弹窗大小等细节均存在差异，影响整体视觉体验和用户体验。

## 视觉/交互基准页

本次统一修复以**用例管理**为设计规范基准：

| 参考文件 | 用途 |
|----------|------|
| `frontend/src/views/case/CaseManagement.vue` | 整体布局、背景、header、主题适配 |
| `frontend/src/views/case/CaseFilterBar.vue` | Filter 栏布局（el-row :gutter=12） |
| `frontend/src/views/case/CaseSearchBar.vue` | 搜索栏布局、按钮样式 |
| `frontend/src/views/case/CaseModulePage.vue` | 卡片背景、边框、圆角 |
| `frontend/src/views/case/CaseStatCards.vue` | 统计卡片样式 |
| `frontend/src/views/case/CasePagination.vue` | 分页组件布局 |
| `frontend/src/views/scenario/ScenarioList.vue` | 标准列表页结构（Header + Filter + Table + Pagination） |

## 必读文件

- `frontend/src/styles/variables.css` — 全局 CSS 变量
- `frontend/src/app/AppShell.vue` — 侧边栏和整体布局
- `frontend/src/views/scenario/ScenarioList.vue` — 标准列表页模板
- `frontend/src/views/case/CaseFilterBar.vue` — Filter 栏规范
- `frontend/src/views/case/CaseSearchBar.vue` — 搜索栏规范
- `frontend/src/views/case/CasePagination.vue` — 分页规范

## 允许修改范围

- `frontend/src/views/` 下的所有 .vue 页面文件
- `frontend/src/styles/variables.css`（如需新增全局变量）

## 禁止事项

- ❌ 不允许修改业务逻辑，只修复样式
- ❌ 不允许改变公开 API 或数据结构
- ❌ 不允许引入新依赖
- ❌ 不允许改动后端代码
- ❌ 不允许改变页面功能结构，只修复视觉细节
- ❌ 不允许自创新的样式类名，必须复用现有规范

## 实现要求

### 一、Header 区域统一规范

所有列表页 header 必须遵循：

```vue
<header class="xxx-list-page__header">
  <div>
    <h1>页面标题</h1>
    <p>页面描述</p>
  </div>
  <el-button type="primary" class="btn-primary-add" :icon="Plus">
    新建
  </el-button>
</header>
```

样式规范：
- h1: `font-size: 24px; color: var(--text-strong)`
- p: `font-size: 13px; color: var(--text-secondary)`
- 按钮使用 `class="btn-primary-add"`
- 布局: `display: flex; justify-content: space-between; align-items: center`

需修复的页面（Header 不统一）：
- `report/DefectList.vue`
- `report/ReportList.vue`
- `docgen/DocGenTasks.vue`
- `docgen/DocGenRules.vue`
- `docgen/DocGenTemplates.vue`
- `platform/UserManagement.vue`
- `platform/RoleManagement.vue`
- `platform/OrganizationManagement.vue`
- `ai/AIModelConfig.vue`
- `ai/AIPromptTemplates.vue`
- 等其他所有有 header 的页面

### 二、Filter 栏统一规范

Filter 栏必须使用：
- `el-form :inline="false" class="filter-form"`
- `el-row :gutter="12"`
- `el-col` 响应式布局
- `el-form-item label="..." class="filter-item"`
- `el-select class="filter-control"`（必须）

禁止：
- ❌ `class="keyword-input"`（应该是 `class="search-bar__input"`）
- ❌ 混用 `el-form :inline="true"`

需修复的页面：
- `docgen/DocGenTasks.vue` — keyword-input 问题
- `docgen/DocGenRules.vue`
- `docgen/DocGenTemplates.vue`
- 所有使用不一致 filter 布局的页面

### 三、Search 栏统一规范

Search 栏必须使用：
- `el-form-item label="关键词：" class="search-item"`
- `el-input class="search-bar__input"`
- `div class="xxx-search-bar__actions"`（按钮容器）
- 新增按钮使用 `class="xxx-search-bar__primary" background: var(--brand-gradient)`

### 四、Table 统一规范

所有 el-table 必须包含：
```vue
<el-table height="100%" highlight-current-row>
```

禁止：
- ❌ `stripe` 属性
- ❌ 缺少 `highlight-current-row`
- ❌ 缺少 `height="100%"`

需检查修复的页面：
- `docgen/DocGenTasks.vue` — 有 stripe 问题
- `report/DefectList.vue` — 检查属性
- 其他所有表格页面

### 五、Pagination 统一规范

分页组件必须使用：
```vue
<footer class="xxx-list-page__pagination">
  <el-pagination
    layout="total, sizes, prev, pager, next, jumper"
    prev-text="上一页"
    next-text="下一页"
  />
</footer>
```

样式：
```css
.xxx-list-page__pagination {
  display: flex;
  justify-content: flex-end;
  padding: 10px 16px;
  border-top: 1px solid var(--border-color-lighter);
}
```

### 六、主题适配规范

所有页面必须同时包含深色和浅色主题适配：

```css
/* 深色模式（默认） */
.page-class {
  background: linear-gradient(...);
  border: 1px solid rgba(56, 189, 248, 0.18);
}

/* 浅色模式 - 必须有 */
html:not(.dark) .page-class {
  background: linear-gradient(...);
  border: 1px solid rgba(22, 119, 255, 0.14);
}
```

需检查修复的页面（缺少 html:not(.dark)）：
- `report/DefectList.vue`
- `report/ReportList.vue`
- `docgen/DocGenTasks.vue`
- `platform/UserManagement.vue`
- 等所有非 CaseManagement 的页面

## 验收标准

1. **Header 验收**：所有页面 header 布局与 ScenarioList.vue 一致
2. **Filter 验收**：所有 filter-item 使用 `class="filter-item"`，select 使用 `class="filter-control"`
3. **Table 验收**：所有 el-table 包含 `height="100%" highlight-current-row`，无 stripe
4. **Pagination 验收**：所有分页右对齐，内边距 10px 16px
5. **主题适配验收**：所有页面同时支持深色/浅色主题
6. **整体验收**：视觉风格一致，无明显差异

## 验证方式

```bash
cd frontend
npm run build
```

构建成功即样式修复通过。

## Claude 输出要求

完成后必须用中文汇报：
- 变更文件列表
- 每个模块修复的具体内容
- 仍存在的差异（如有）
- 验证结果