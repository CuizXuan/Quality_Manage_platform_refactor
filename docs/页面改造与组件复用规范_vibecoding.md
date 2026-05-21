# 页面改造与组件复用规范（VibeCoding 版）

## 1. 目标

本文档用于指导质量管理平台后续模块改造，核心目标是：

- 保持页面风格统一
- 保持布局和交互一致
- 降低 vibecoding 时的返工成本
- 将用例管理中可复用的样式和组件沉淀为公共层

## 2. 适用范围

适用于：

- 列表页
- 查询页
- 配置页
- 表单页
- 弹窗页
- 调试台保存类页面

不强制包含：

- 分类树
- 统计卡片
- 侧栏
- 高级配置区

这些模块按业务需要出现，不是固定结构。

## 3. 设计来源

### 3.1 当前实现来源

- `frontend/src/views/case/CaseManagement.vue`
- `frontend/src/views/case/CaseModulePage.vue`
- `frontend/src/views/case/CaseStatCards.vue`
- `frontend/src/views/case/CaseSidebar.vue`
- `frontend/src/views/case/CaseSearchBar.vue`
- `frontend/src/views/case/CaseFilterBar.vue`
- `frontend/src/views/case/CaseTable.vue`
- `frontend/src/views/case/CaseEditDialog.vue`
- `frontend/src/components/common/OverflowText.vue`
- `frontend/src/components/common/RichTextEditor.vue`
- `frontend/src/components/common/PageSurface.vue`
- `frontend/src/styles/variables.css`
- `frontend/src/styles/global.css`
- `frontend/src/styles/element-override.css`
- `frontend/src/styles/page-framework.css`

### 3.2 规范来源

- `docs/06_前端组件与页面规范.md`
- `docs/用例管理模块页面设计方案.md`
- `docs/查询栏布局调整.md`

## 4. 页面骨架

推荐页面骨架：

1. 标题区
2. 可选统计区
3. 可选分类区
4. 查询区
5. 列表区
6. 弹窗区

没有的区块直接删除，不要硬塞。

## 5. 尺寸规范

### 5.1 页面

- 页面内边距：`12px`
- 区块间距：`12px`
- 页面高度：`100%`
- 子容器最小高度：`0`
- 面板圆角：`8px`

### 5.2 字体

- 页面正文：`14px`
- 表单标签：`14px`
- 表格正文：`14px`
- 表格表头：`13px`
- 弹窗标题：`16px`
- 区块标题：`15px`
- 辅助说明：`12px ~ 13px`

### 5.3 按钮

- 主按钮高度：`34px`
- 次按钮高度：`34px`
- 表格内操作按钮：`12px ~ 13px`
- 主按钮优先使用主色或品牌渐变

### 5.4 表格

- 表头高：`44px`
- 行高：`48px`
- 固定列：只固定关键列
- 长文本：省略 + tooltip

### 5.5 弹窗

- 简单弹窗：`760px`
- 标准弹窗：`960px`
- 复杂弹窗：`width: min(1280px, 95vw)`
- 内容区高度：`70vh ~ 80vh`
- 顶部间距：`3vh ~ 6vh`

## 6. 字体规范

- 主内容字体：`14px`
- 表格标题字体：`13px`
- 表格内容字体：`14px`
- 弹窗标题字体：`16px`
- 说明文字：`12px ~ 13px`

要求：

- 同一页面不要混用过多字号。
- 不要把正文做得过小。
- 重点字段要比辅助字段更清晰。

## 7. 背景与质感

推荐背景结构：

1. 主题底色
2. 细网格底纹
3. 轻扫描线
4. 极淡节点流线

要求：

- 背景弱于正文
- 深浅色都要适配
- 动效轻，不打扰阅读
- 优先使用 CSS / 伪元素，不依赖真实图片

当前公共实现已抽象到：

- `.page-shell`
- `.page-shell--tech-grid`
- `.page-surface`
- `.page-surface--glass`
- `.page-surface--tech`

## 8. 公共组件

### 8.1 `OverflowText`

用途：

- 单行截断
- 多行换行
- 悬停显示完整文本

适用场景：

- 编号
- 名称
- URL
- 描述
- 前置条件
- 创建人

### 8.2 `RichTextEditor`

用途：

- 富文本说明
- 前置条件
- 结果描述

### 8.3 `PageSurface`

用途：

- 页面面板外壳
- 玻璃质感容器
- 科技纹理容器

推荐使用位置：

- 左侧树
- 查询区
- 列表区
- 详情区
- 高级配置区

## 9. 查询栏规范

推荐两种形式：

### 9.1 单行紧凑型

适合 3 到 5 个筛选项。

结构：

- 左侧筛选
- 右侧操作按钮

### 9.2 多行网格型

适合 6 个以上筛选项。

结构：

- 常用筛选在前
- 日期范围单独占位
- 操作按钮固定右侧

### 9.3 推荐尺寸

- 输入框 / 选择框：`34px ~ 36px`
- 普通单选：`220px ~ 280px`
- 关键字输入：`260px ~ 320px`
- 日期区间：`320px ~ 360px`

### 9.4 交互规则

- 不自动请求
- 点击查询后请求
- 回车可查询
- 重置后清空并请求
- 分页变化可请求

## 10. 列表与表格规范

### 10.1 推荐列宽

- 编号：`140px ~ 170px`
- 名称：`180px ~ 240px`
- 方法 / 状态：`80px ~ 120px`
- 长文本：`220px ~ 320px`
- 日期：`140px ~ 160px`
- 创建人：`90px ~ 120px`
- 操作：`120px ~ 150px`

### 10.2 规则

- 编号和名称分列展示
- 长文本统一用 `OverflowText`
- 操作列固定且紧凑
- hover 高亮与主题一致
- 空状态需要统一样式

### 10.3 编号规则

- 接口用例：`APICASE-YYYYMMDD01`
- 功能用例：`FUNCCASE-YYYYMMDD01`

## 11. 弹窗规范

### 11.1 分层

- 基础信息
- 核心配置
- 高级配置

### 11.2 推荐字段分布

基础信息：

- 名称
- 说明
- 前置条件
- 优先级

核心配置：

- 接口请求配置
- 功能步骤配置
- 主业务字段

高级配置：

- 自动化
- 脚本路径
- 入口函数
- 参数
- 标签
- 失败策略
- 超时配置

### 11.3 字段数量判断

- 1 到 6 个字段：单列或双列
- 7 到 12 个字段：双列 + 分区
- 超过 12 个字段：折叠或标签页

## 12. 主题适配

必须验证：

- 输入框
- 下拉框
- 日期框
- tooltip
- table hover
- dialog
- 选中态

要求：

- 不写死颜色
- 所有颜色优先走变量
- 浮层必须兼容深浅色
- 不允许主题切换后出现高亮污染

## 13. Vibecoding 顺序

建议按以下顺序生成页面：

1. 页面骨架
2. 查询区
3. 列表区
4. 弹窗区
5. 背景与动效

没有的模块直接删，不要硬造。

## 14. 可直接复用的公共层

### 14.1 组件

- `OverflowText`
- `RichTextEditor`
- `PageSurface`

### 14.2 样式

- `page-framework.css`
- `variables.css`
- `global.css`
- `element-override.css`

## 15. 验收标准

完成改造后，页面应满足：

- 文字清晰
- 布局均匀
- 查询栏整齐
- 表格可扫读
- 弹窗分区明确
- 深浅色主题一致
- tooltip 正常
- 没有样式污染

