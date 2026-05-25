# Codex 实现任务包

## 任务目标

重写文档中心的弹窗交互，使其复用并对齐“场景管理”的弹窗行为和视觉表现。

本次重点不是继续调整列表样式，而是修复规则管理编辑弹窗的遮罩、挂载、大小、表单密度、footer 等问题。

## 背景说明

用户反馈：文档中心 / 规则管理中打开“编辑规则”弹窗后，列表区域出现一层灰色背景，观感与场景管理不一致。需要注意：场景管理本身是有遮罩的，不能用关闭遮罩来解决问题。

请以场景管理弹窗为准：

- `frontend/src/views/scenario/ScenarioList.vue` 中的新建场景弹窗
- `frontend/src/views/scenario/ScenarioDetailDialog.vue` 中的详情/编辑弹窗
- `frontend/src/views/scenario/ScenarioStepDialog.vue` 中的步骤弹窗

当前文档中心真正的 `el-dialog` 主要在：

- `frontend/src/views/docgen/DocGenRules.vue`

另外，删除确认使用 `ElMessageBox.confirm`，这个不属于本次“编辑弹窗重写”的主要目标，但要检查确认框没有被新样式破坏。

## 必读文件

- `AGENTS.md`
- `frontend/src/views/docgen/DocGenRules.vue`
- `frontend/src/views/docgen/DocGenTemplates.vue`
- `frontend/src/views/docgen/DocGenTasks.vue`
- `frontend/src/views/docgen/DocGenGenerate.vue`
- `frontend/src/views/scenario/ScenarioList.vue`
- `frontend/src/views/scenario/ScenarioDetailDialog.vue`
- `frontend/src/views/scenario/ScenarioStepDialog.vue`
- `frontend/src/styles/element-override.css`
- `frontend/src/styles/page-framework.css`

## 允许修改范围

优先修改：

- `frontend/src/views/docgen/DocGenRules.vue`

如确实需要抽出复用样式，可新增或修改：

- `frontend/src/views/docgen/docgenShared.css`
- `frontend/src/styles/element-override.css`
- `frontend/src/styles/page-framework.css`

但不要为了一个弹窗做大范围重构。

## 禁止事项

- 不关闭遮罩来规避问题。不要保留或新增 `:modal="false"`。
- 不改变规则管理的新增、编辑、保存、启用、删除业务逻辑。
- 不改变后端接口或 store 行为。
- 不重做文档中心整页布局，本任务只聚焦弹窗。
- 不引入新依赖。
- 不修复无关乱码，除非触碰处已经必须改文案。

## 当前必须修正的问题

请重点检查 `DocGenRules.vue` 规则弹窗，当前可能存在这些问题：

- 弹窗配置包含 `:modal="false"`，这与“场景管理有遮罩”的目标相反，必须移除。
- 弹窗遮罩应由 Element Plus 正常生成，并覆盖整屏，而不是只让列表区域出现割裂的灰色罩层。
- 弹窗行为应和场景管理接近：
  - `top="4vh"`
  - `destroy-on-close`
  - `:close-on-click-modal="false"` 可保留
  - 是否 `append-to-body` 请以场景管理对应场景判断；如果使用，必须确保遮罩层级、弹窗层级正常。
- 弹窗内容应使用和场景管理相近的表单结构：
  - `el-form` 直接作为弹窗主体或使用简单 body wrapper
  - label 宽度与场景管理协调，建议 90px 或 100px
  - input/select 宽度 100%
  - JSON textarea 高度适中，不能撑爆视口
  - footer 按钮右对齐
- 弹窗宽度不要过大，规则编辑建议 `min(720px, 92vw)` 或参考步骤弹窗 `min(640px, 92vw)`，以实际内容不拥挤为准。

## 实现要求

1. 对比场景管理弹窗实现
   - 先阅读 `ScenarioList.vue` 的新建场景弹窗。
   - 再阅读 `ScenarioStepDialog.vue` 的步骤弹窗。
   - 总结它们的共同配置和视觉特点，然后用于规则管理弹窗。

2. 重写规则管理弹窗
   - 保留 `ruleDialogVisible`、`ruleDialogTitle`、`ruleForm`、`handleSaveRule` 等现有逻辑。
   - 移除 `:modal="false"`。
   - 使用正常遮罩，确保打开弹窗时整页被一致遮罩，效果与场景管理相同。
   - 弹窗内表单、按钮、textarea 与场景管理风格一致。

3. 检查所有文档中心弹窗/确认框
   - 使用 `rg -n "<el-dialog|ElMessageBox|confirm\\(" frontend/src/views/docgen` 检查。
   - 如果发现其他 `el-dialog`，也按场景管理风格统一。
   - `ElMessageBox.confirm` 只需确认没有被破坏，不需要重写成自定义弹窗。

4. 视觉验证
   - 打开 `/docgen/rules`，点击“新增规则”和列表中的“编辑”。
   - 确认遮罩效果与 `/scenario` 中“新建场景”一致。
   - 确认弹窗显示在页面中心附近，遮罩覆盖整页，不只覆盖表格。
   - 确认关闭、取消、保存 loading、表单输入都正常。

## 验收标准

- 规则管理新增/编辑弹窗与场景管理弹窗的遮罩、位置、大小和表单密度保持一致。
- 打开规则弹窗时不再出现“只有列表被灰色罩住”的割裂效果。
- 不存在 `DocGenRules.vue` 规则编辑弹窗使用 `:modal="false"` 的情况。
- 规则新增、编辑、保存、启用、删除功能不回归。
- 删除确认框仍正常显示。
- 前端构建通过。

## 验证方式

至少运行：

```text
cd frontend
npm run build
```

建议本地手工验证：

```text
cd frontend
npm run dev
```

检查路径：

```text
http://localhost:5173/docgen/rules
http://localhost:5173/scenario
```

## Claude 输出要求

结束时必须用中文汇报：

- 修改了哪些文件。
- 对比场景管理后采用了哪些弹窗配置。
- 是否移除了 `:modal="false"`。
- 文档中心是否还有其他 `el-dialog`。
- 已运行的验证命令和结果。
- 剩余风险。
