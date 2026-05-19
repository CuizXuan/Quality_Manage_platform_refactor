# 前端弹窗重构开发方案

> 适用目录：`frontend`
> 目标：统一项目内新增、编辑、详情、确认、导入、发布等弹窗体验，同时适配深色/浅色主题，保留 AI 科技感，并提升表单可用性和维护效率。

## 1. 背景与问题

当前前端是 Vue 3 + Vite + Element Plus，已存在全局 `CyberConfirm`、主题变量和多套手写弹窗样式。实际代码中弹窗实现混杂：

- 手写 `modal-overlay` / `dialog-overlay` / `case-modal-overlay`
- Element Plus `el-dialog`
- 全局 `CyberConfirm`
- 浏览器原生 `confirm()` / `alert()`
- 局部页面自定义关闭按钮、表单间距、宽度和滚动规则

截图中的问题也来自这些差异：弹窗比例偏窄、关闭按钮位置异常、表单控件宽度不统一、JSON 字段被错误渲染为 `[object Object]`、浅色主题缺少同等设计质量。

本次重构不建议直接引入 React 生态的 Ant Design。建议参考 Ant Design 的设计原则和组件交互模型，在现有 Vue + Element Plus 项目上封装统一的 Cyber 弹窗体系。

参考资料：

- Ant Design 组件总览：https://ant.design/components/overview-cn
- Ant Design Modal：https://ant.design/components/modal-cn
- Ant Design Drawer：https://ant.design/components/drawer-cn
- Ant Design 设计价值观：https://ant.design/docs/spec/values-cn

## 2. 当前弹窗盘点

### 2.1 通用组件

| 文件 | 类型 | 现状 | 重构建议 |
| --- | --- | --- | --- |
| `src/components/common/CyberConfirm.vue` | 轻量确认 | 已接近 Popconfirm 模式，但中文存在乱码，样式变量和全局主题不完全统一 | 修复文案编码，纳入统一 Token，补充尺寸、焦点和加载态 |
| `src/components/CaseFolderDialog.vue` | Element Plus 弹窗 | 使用 `el-dialog`，但依赖全局覆盖，尺寸固定 400px | 迁移到 `CyberModal` 或给 `el-dialog` 套统一 class |
| `src/components/common/AppHeader.vue` | 退出确认、主题面板 | 内部私有 modal 样式 | 退出确认改 `CyberConfirmModal`，主题面板保留 popover/drawer 形态 |
| `src/components/common/VariableEditor.vue` | 导入弹窗 | 手写 modal | 迁移到 `CyberModal` |
| `src/components/request/AssertionConfig.vue` | 添加断言 | 手写 modal | 迁移到 `CyberModal` |
| `src/components/request/RequestBar.vue` | 保存请求 | 手写保存弹窗 | 迁移到 `CyberModal` |

### 2.2 页面弹窗

| 页面 | 弹窗/浮层 | 主要用途 | 推荐形态 |
| --- | --- | --- | --- |
| `Dashboard.vue` | 新建用例 | 快速创建 | `CyberModal` medium |
| `CaseManagement.vue` | 新建/编辑用例、删除确认 | 主业务表单 | `CyberModal` large + `CyberConfirm` |
| `EnvironmentManage.vue` | 新建/编辑环境 | 表单编辑 | `CyberModal` medium |
| `ScenarioEditor.vue` | 场景详情/编辑、添加步骤、新建场景 | 大型表单、步骤配置 | 详情编辑用 `CyberDrawer` 或 xl modal；添加步骤用 medium modal |
| `AIModelConfig.vue` | 添加/编辑模型配置 | 密钥、模型参数 | `CyberModal` large，敏感字段增强 |
| `AIAnalysis.vue` | 创建基线、预测影响、创建规则 | AI 分析类操作 | `CyberModal` medium，增加 AI 状态提示 |
| `AIStudio.vue` | 历史记录 | 浏览列表 | `CyberDrawer` right |
| `AssetCenter.vue` | 使用模板 | 详情/复制信息 | `CyberModal` medium 或 `CyberDrawer` |
| `ChaosStudio.vue` | 创建实验、注入故障、韧性评估 | 风险操作 | `CyberModal` large + 风险确认 |
| `ExecutionHistory.vue` | 详情弹窗 | 查看执行结果 | `CyberDrawer` xl |
| `QualityDashboard.vue` | 创建仪表盘、添加组件 | 表单配置 | `CyberModal` medium |
| `ProjectManage.vue` | 创建项目 | 简单表单 | `CyberModal` small |
| `MenuManage.vue` | 添加分组 | 简单表单 | `CyberModal` small |
| `Marketplace.vue` | 插件详情、发布插件、我的插件、创建 CLI Key、API Key 展示 | 详情、发布、密钥展示 | 详情/我的插件用 drawer；发布和创建 key 用 modal |
| `Defect/DefectBoard.vue` | 缺陷详情 | 详情查看 | `CyberDrawer` right |
| `CodeQuality/RepositoryList.vue` | 新建/编辑仓库 | 表单编辑 | `CyberModal` medium |
| `DataDrive/DatasetList.vue` | 新建/编辑数据集 | 表单编辑 | `CyberModal` medium |
| `Integration/DefectSystemConfig.vue` | 新建/编辑集成配置 | 表单编辑 | `CyberModal` large |
| `QualityGate/GateList.vue` | 新建/编辑门禁、门禁编辑器 | 配置编辑 | 表单用 modal；编辑器用 drawer/xl modal |
| `Mock/MockRuleList.vue` | 新建/编辑 Mock 规则 | 表单编辑 | `CyberModal` large |
| `Report/ReportList.vue` | 生成报告 | 参数选择 | `CyberModal` medium |
| `Schedule/ScheduleList.vue` | 新建/编辑任务 | 表单编辑 | `CyberModal` large |
| `SelfHealConfig.vue` | 创建/编辑自愈规则 | 规则配置 | `CyberModal` large |
| `TestDataFactory.vue` | 创建模板、脱敏规则、快照 | 多种创建表单 | `CyberModal` medium |
| `TrafficLoadTest.vue` | 创建录制、回放、标签 | 流量任务配置 | `CyberModal` medium/large |

### 2.3 原生弹窗替换范围

项目内多处使用 `confirm()` / `alert()`。这些会破坏主题一致性，也无法体现 AI 风格。替换规则：

- 删除、重置、危险操作：使用 `CyberConfirm`
- 阻断式危险确认：使用 `CyberConfirmModal`
- 成功/失败提示：使用 `CyberToast` 或 `ElMessage`
- 密钥创建后展示：使用 `CyberModal`，提供复制按钮和安全提示

## 3. 设计目标

### 3.1 可用性目标

- 用户在弹窗内能清楚知道当前任务、必填项、错误项和下一步操作。
- 弹窗不挤压主要内容，表单宽度、留白和滚动符合实际工作流。
- 复杂内容不再堆在一个小弹窗里，详情类内容优先使用 Drawer。
- 键盘可用：ESC 关闭、Tab 焦点循环、Enter 提交、按钮焦点可见。

### 3.2 视觉目标

- 深色主题：低亮背景 + 克制霓虹边框 + 局部 AI 扫描线/光效。
- 浅色主题：白色或浅灰玻璃面板 + 青色/蓝色科技点缀 + 低强度阴影。
- 保留科技感，但避免过量发光影响表单阅读。
- 弹窗圆角控制在 8px，符合现有设计约束和工具类产品定位。

### 3.3 工程目标

- 统一弹窗基础组件，页面只关注业务表单。
- 清理重复 CSS，减少每个页面维护私有 `.modal` / `.dialog` 样式。
- 保留 Element Plus 表单能力，不新增重量级 UI 依赖。
- 支持分阶段迁移，优先改问题最明显、使用最高频的弹窗。

## 4. 组件架构

### 4.1 新增组件

建议新增以下组件：

```text
src/components/common/modal/
├── CyberModal.vue
├── CyberDrawer.vue
├── CyberConfirmModal.vue
├── CyberModalSection.vue
└── modalTokens.css
```

### 4.2 CyberModal

用于新增、编辑、生成、导入、发布等事务型操作。

核心 props：

| Prop | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `modelValue` | boolean | false | 显示状态 |
| `title` | string | - | 主标题 |
| `subtitle` | string | - | 辅助说明，最多一行 |
| `size` | `small / medium / large / xl` | medium | 尺寸 |
| `intent` | `default / ai / danger / success` | default | 视觉语义 |
| `loading` | boolean | false | 提交加载态 |
| `destroyOnClose` | boolean | true | 关闭时销毁 |
| `closeOnEsc` | boolean | true | ESC 关闭 |
| `closeOnOverlay` | boolean | false | 默认不点遮罩关闭，避免误丢数据 |
| `showFooter` | boolean | true | 是否展示底部 |

Slots：

- `header-extra`：右侧状态、AI 标签、帮助入口
- `default`：表单主体
- `footer`：自定义底部

事件：

- `update:modelValue`
- `confirm`
- `cancel`
- `after-close`

### 4.3 CyberDrawer

用于详情、审阅、历史记录、复杂编辑器等信息密度较高的场景。

推荐场景：

- 执行历史详情
- 缺陷详情
- 插件详情
- AIStudio 历史记录
- 场景详情/编辑
- 门禁编辑器

默认从右侧滑出，不遮挡用户对列表上下文的理解。

### 4.4 CyberConfirm 与 CyberConfirmModal

- `CyberConfirm`：替代 Popconfirm，用于列表行内删除、轻量确认。
- `CyberConfirmModal`：替代浏览器 `confirm()`，用于影响范围较大的危险动作。

确认组件必须支持：

- `danger` 样式
- loading 态
- 操作对象名称
- 二次确认描述
- ESC / 点击外部关闭
- 焦点回到触发按钮

## 5. 尺寸与排版规范

### 5.1 弹窗尺寸

| Size | 宽度 | 使用场景 | 示例 |
| --- | --- | --- | --- |
| small | `min(420px, calc(100vw - 32px))` | 单字段或二字段 | 新增分类、添加分组、创建标签 |
| medium | `min(560px, calc(100vw - 32px))` | 常规表单 | 创建项目、生成报告、创建快照 |
| large | `min(720px, calc(100vw - 40px))` | 多字段表单 | 新建用例、模型配置、Mock 规则 |
| xl | `min(960px, calc(100vw - 48px))` | 复杂编辑、配置表 | 场景详情、门禁编辑器 |

高度规则：

- 默认最大高度：`min(78vh, 760px)`
- 大型弹窗最大高度：`min(84vh, 860px)`
- Header 和 Footer 固定，Body 独立滚动
- Body 顶部和底部需要滚动阴影，提示还有内容

### 5.2 内边距

| 区域 | 桌面端 | 移动端 |
| --- | --- | --- |
| Header | 20px 24px | 16px |
| Body | 24px | 16px |
| Footer | 16px 24px | 12px 16px |
| 表单项间距 | 18px | 14px |
| 分组间距 | 24px | 18px |

### 5.3 表单布局

- small/medium：单列布局。
- large/xl：可使用两列，但 URL、JSON、描述、代码编辑器必须跨两列。
- Label 使用左上布局，不建议窄弹窗内做横向 label。
- 必填星号靠近 label，错误信息紧贴控件下方。
- JSON 字段必须用文本编辑器或 JSON viewer，不允许直接渲染对象。

## 6. 主题与 AI 风格 Token

建议在 `modalTokens.css` 中新增语义变量，再映射到现有深浅色主题。

```css
:root {
  --modal-radius: 8px;
  --modal-border: rgba(0, 255, 255, 0.22);
  --modal-bg: rgba(13, 13, 20, 0.96);
  --modal-header-bg: linear-gradient(180deg, rgba(0, 255, 255, 0.08), transparent);
  --modal-footer-bg: rgba(5, 8, 14, 0.86);
  --modal-shadow: 0 24px 80px rgba(0, 0, 0, 0.48), 0 0 28px rgba(0, 255, 255, 0.18);
  --modal-ai-accent: #00f0ff;
  --modal-danger-accent: #ff4d7d;
}

.theme-light {
  --modal-border: rgba(6, 182, 212, 0.24);
  --modal-bg: rgba(255, 255, 255, 0.96);
  --modal-header-bg: linear-gradient(180deg, rgba(6, 182, 212, 0.08), transparent);
  --modal-footer-bg: rgba(248, 250, 252, 0.92);
  --modal-shadow: 0 24px 70px rgba(15, 23, 42, 0.16), 0 0 20px rgba(6, 182, 212, 0.12);
  --modal-ai-accent: #0891b2;
  --modal-danger-accent: #e11d48;
}
```

AI 风格原则：

- 使用细线、角标、状态芯片、轻微扫描线表达科技感。
- 不在表单背景使用高噪声网格，避免干扰输入。
- 深色主题允许外发光，浅色主题以边框、阴影和高亮条表达。
- 标题可带 `AI`、`MODEL`、`RULE` 等小型状态 tag，但不要堆满装饰。

## 7. 与 Ant Design 的对应关系

| Ant Design 思路 | 本项目落地 |
| --- | --- |
| Modal 用于不离开当前页的事务操作 | `CyberModal` 承载新增、编辑、生成、发布 |
| Drawer 用于详情或保留上下文的复杂信息 | `CyberDrawer` 承载详情、历史、编辑器 |
| Popconfirm 用于轻量危险确认 | `CyberConfirm` 负责行内删除 |
| Form 负责输入、校验、错误提示 | 保留 Element Plus Form 或现有表单，统一样式 |
| Message/Notification 用于反馈 | `CyberToast` / `ElMessage`，禁止 `alert()` |
| Design Token 驱动主题 | `modalTokens.css` + `themes.css` 映射深浅色 |

## 8. 交互规范

### 8.1 打开与关闭

- 打开弹窗后焦点落在第一个可输入项；没有输入项则落在关闭按钮。
- ESC 关闭；有未保存变更时，弹出二次确认。
- 点击遮罩默认不关闭表单弹窗，详情 Drawer 可允许关闭。
- 关闭后焦点回到触发按钮。

### 8.2 底部按钮

- 按钮顺序：左侧可放危险/辅助动作，右侧为 `取消` + 主操作。
- 主按钮文案使用业务动作：`创建`、`保存`、`生成`、`发布`，避免一律 `确定`。
- 危险动作使用红/粉色语义，不使用普通主色。
- loading 时禁用重复提交，并保持弹窗不关闭。

### 8.3 表单校验

- 必填项即刻或失焦校验。
- 提交失败后滚动到第一个错误字段。
- 服务端错误显示在表单顶部 Alert 区，不只弹 toast。
- 密钥字段默认隐藏，提供显示/复制按钮。

### 8.4 响应式

- 小于 640px：所有 modal 宽度 `calc(100vw - 24px)`，Body 最大高度 `70vh`。
- 小于 640px：Footer 按钮可满宽双列或上下排列，保证文字不溢出。
- Drawer 在移动端占满宽度。

## 9. 实施步骤

### 阶段一：基础组件与 Token

1. 新增 `src/components/common/modal/` 组件目录。
2. 新增 `modalTokens.css` 并在 `main.ts` 中引入。
3. 实现 `CyberModal.vue`，包含 Teleport、Transition、焦点管理、尺寸、Header/Body/Footer。
4. 实现 `CyberDrawer.vue`。
5. 修复 `CyberConfirm.vue` 中文乱码和 loading 文案。
6. 增加基础用例或最少交互测试。

验收：

- 深色/浅色主题下同一 modal 视觉一致。
- ESC、Tab、Enter、loading 可用。
- Header/Footer 固定，Body 独立滚动。

### 阶段二：高频业务弹窗迁移

优先迁移：

1. `CaseManagement.vue` 新建/编辑用例。
2. `Dashboard.vue` 新建用例。
3. `CaseFolderDialog.vue` 新增/编辑分类。
4. `EnvironmentManage.vue` 新建/编辑环境。
5. `AIModelConfig.vue` 添加/编辑模型配置。

验收：

- 截图中的“新建用例”和“新增分类”问题被修复。
- 表单宽度合理，关闭按钮不再错位。
- JSON 字段不再出现 `[object Object]`。

### 阶段三：详情与复杂编辑迁移

迁移：

1. `ExecutionHistory.vue` 详情弹窗改 Drawer。
2. `Defect/DefectBoard.vue` 缺陷详情改 Drawer。
3. `Marketplace.vue` 插件详情、我的插件改 Drawer。
4. `AIStudio.vue` 历史记录改 Drawer。
5. `ScenarioEditor.vue` 场景详情/编辑评估是否拆分为 Drawer + 子 Modal。

验收：

- 详情信息有清晰分区。
- 列表上下文保留，关闭后回到原位置。

### 阶段四：全量替换原生确认和散落样式

1. 替换所有 `confirm()`。
2. 替换所有 `alert()`。
3. 删除页面私有 `.modal-overlay` / `.dialog-overlay` 重复样式。
4. 保留仅与业务布局相关的局部 CSS。

验收：

- `rg "confirm\\(|alert\\(" src` 不再命中业务代码。
- 页面内不再重复定义基础 modal 样式。

### 阶段五：视觉回归与文档固化

1. 为深色、浅色主题各截一组关键弹窗。
2. 校验 1366px、1440px、1920px、390px 宽度。
3. 补充组件使用文档。
4. 形成迁移 checklist。

## 10. 开发 Checklist

- [ ] 是否使用 `CyberModal` / `CyberDrawer` / `CyberConfirm`，而不是新增页面私有 modal？
- [ ] 弹窗尺寸是否选择 small/medium/large/xl？
- [ ] Body 是否独立滚动？
- [ ] 是否支持深色和浅色主题？
- [ ] 表单字段是否有 label、placeholder、错误提示？
- [ ] JSON/对象字段是否显式序列化或使用编辑器？
- [ ] 危险操作是否使用 danger 样式和二次确认？
- [ ] 是否移除了 `confirm()` / `alert()`？
- [ ] ESC、Tab、Enter 是否可用？
- [ ] 移动端是否无溢出、无文字遮挡？

## 11. 关键页面落地建议

### 11.1 新建用例

推荐 `large`，宽度约 720px。布局：

- 第一行：名称
- 第二行：请求方法 + URL
- 第三行：所属分类
- 第四行：描述
- 第五行：请求头 JSON
- 第六行：请求体 JSON

请求头和请求体使用等宽字体编辑区，默认值为格式化 JSON 字符串：

```json
{}
```

不要直接绑定对象到 textarea，避免 `[object Object]`。

### 11.2 新增分类

推荐 `small`，宽度约 420px。布局：

- 分类名称
- 排序

关闭按钮使用统一 icon button，固定在 Header 右侧，不允许覆盖标题区域。

### 11.3 模型配置

推荐 `large`。密钥字段需要：

- 默认 password
- 显示/隐藏按钮
- 保存前校验 provider、model、apiKey
- 服务端失败展示在表单顶部

### 11.4 详情类弹窗

执行历史、缺陷详情、插件详情不要继续用居中 modal。右侧 Drawer 更适合：

- 宽度 `min(720px, 100vw)`
- Header 展示标题、状态、时间
- Body 分区展示元信息、日志、JSON、操作记录
- Footer 只保留必要操作

## 12. 风险与注意事项

- 项目存在中文乱码文件，迁移时需要确认文件编码，避免继续污染文案。
- Element Plus 全局样式已有覆盖，新增组件样式要避免与 `.el-dialog` 冲突。
- 当前 `themes.css`、`premium-dark.css`、`cyberpunk.css`、`cyberlight.css` 都包含 modal 样式，迁移后需要逐步收敛。
- 大型页面如 `ScenarioEditor.vue` 文件较长，迁移时应顺手拆分弹窗表单为子组件，避免继续扩大单文件。
- 不建议一次性改完全量弹窗，先完成基础组件和高频页面，再批量替换。

## 13. 建议优先级

P0：

- `CyberModal` / `CyberDrawer` / `modalTokens.css`
- `CaseManagement.vue`
- `CaseFolderDialog.vue`
- `Dashboard.vue`
- `CyberConfirm.vue` 文案修复

P1：

- `EnvironmentManage.vue`
- `AIModelConfig.vue`
- `ScenarioEditor.vue`
- `ExecutionHistory.vue`
- `Defect/DefectBoard.vue`

P2：

- Marketplace、TrafficLoadTest、TestDataFactory、SelfHealConfig、QualityGate、Mock、Schedule、Report 等页面全量统一。

## 14. 预期效果

完成后，项目弹窗将具备统一的现代化 AI 工具风格：

- 深色主题有克制霓虹、玻璃质感和高对比输入体验。
- 浅色主题保留科技感，但更干净、专业、适合长时间使用。
- 新增/编辑/详情/确认各有明确组件边界。
- 弹窗大小、排版、滚动、按钮、错误处理都可预测。
- 后续新增页面只需要组合统一组件，不再重复写私有弹窗 CSS。
