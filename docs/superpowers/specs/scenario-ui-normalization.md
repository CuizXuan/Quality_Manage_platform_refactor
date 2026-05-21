# Scenario 模块前端规范化改造 — 设计文档

## 1. 目标

对 `ScenarioList.vue`、`ScenarioDetail.vue`、`ExecutionHistory.vue`、`ExecutionDetail.vue` 四个页面按 `docs/06_前端组件与页面规范.md` 进行规范化改造，验收标准共8项。

---

## 2. 页面改造明细

### 2.1 ScenarioList.vue

**问题1：按钮换行**
- 当前：`list-header` 用 `justify-content: space-between`，搜索框和按钮各占一边，但搜索框是固定300px，viewport窄时"新建场景"会掉到第二行
- 修复：`list-header` 改为 `flex-wrap: wrap`，搜索框+按钮组用 `flex: 1` 布局，按钮组用 `gap: 8px` 不换行

**问题2：查询条件过少**
- 当前：仅有 keyword 输入框
- 修复：增加 `el-form` + `el-form-item` 布局，添加：
  - 场景名称（模糊搜索，已有keyword）
  - 状态筛选（el-select: 全部/启用/禁用）
  - 创建时间范围（el-date-picker: daterange）

**问题3：分页中文化**
- 当前：`layout="total, sizes, prev, pager, next"` 无中文字符
- 修复：引入中文 locale，或使用 `prev-text="上一页" next-text="下一页"` 等属性；每页条数默认值改为15

**保留的优点**：
- ElMessage 反馈已完善
- 查询模式已是对的（点击按钮查询）
- 所有基础控件已是 Element Plus

---

### 2.2 ScenarioDetail.vue

**问题：抽屉改弹窗**
- 当前：步骤编辑使用 `el-drawer`（`ScenarioStepForm.vue` 是 drawer 组件）
- 修复：步骤编辑是复杂表单（含多类型动态配置），改为 `el-dialog`，新建 `ScenarioStepDialog.vue`

**问题：按钮换行**
- 当前：`header-right` 用 `gap: var(--spacing-sm)` 但无 wrap，4个按钮可能溢出
- 修复：`header-right` 加 `flex-wrap: wrap`，最大宽度约束

---

### 2.3 ExecutionHistory.vue

**问题1：查询条件缺日期范围**
- 当前：有场景下拉 + 状态筛选
- 修复：增加「开始时间范围」el-date-picker（daterange）

**问题2：分页缺中文化**
- 同 ScenarioList

---

### 2.4 ExecutionDetail.vue

**问题：按钮换行**
- 当前：`header-right` 2个按钮较简单，但仍需防护viewport压缩
- 修复：同上，加 `flex-wrap: wrap`

---

## 3. 美学决策

- 风格：沿用现有 CSS 变量体系，不改变颜色/字体
- 按钮组：始终靠右对齐，使用 `gap` 控制间距，不用 margin
- 表单：统一用 `el-form` + `el-form-item`，label-width 固定 90px
- 分页：统一右下角，layout: `total, sizes, prev, pager, next, jumper`，加中文字典覆盖

---

## 4. 分页中文化方案

Element Plus 中文 locale 已在 `main.ts` 引入（`zhCn`），但需要确认全局生效。如果全局生效则无需每个页面单独配置；如果局部需要覆盖，在 `el-pagination` 上加 `prev-text="上一页" next-text="下一页" page-sizes-text="条/页"` 等属性。

---

## 5. 文件变更清单

| 文件 | 变更类型 |
|------|---------|
| `views/scenario/ScenarioList.vue` | 修改 |
| `views/scenario/ScenarioDetail.vue` | 修改 |
| `views/scenario/ScenarioStepForm.vue` | 改为 dialog，重命名 ScenarioStepDialog.vue |
| `views/scenario/ExecutionHistory.vue` | 修改 |
| `views/scenario/ExecutionDetail.vue` | 修改 |
