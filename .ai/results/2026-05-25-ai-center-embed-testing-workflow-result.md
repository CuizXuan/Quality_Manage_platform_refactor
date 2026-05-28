# AI Center Embed Testing Workflow - 实现结果

## 任务概述
将 AI 能力嵌入用例、场景、执行、报告和缺陷流程，支持采纳回写。

## 变更文件

### 前端 Vue 组件

| 文件 | 变更内容 |
|------|---------|
| `frontend/src/views/case/ApiCaseForm.vue` | AI 生成断言（识别 + 采纳回写） |
| `frontend/src/views/scenario/ScenarioDetail.vue` | AI 生成步骤建议 |
| `frontend/src/views/scenario/ExecutionDetail.vue` | AI 失败分析（根因 + 修复建议） |
| `frontend/src/views/report/ReportDetail.vue` | AI 总结报告（关键发现 + 改进建议） |
| `frontend/src/views/report/DefectForm.vue` | AI 生成标题/描述/推荐严重程度和优先级 |

### 后端修复

| 文件 | 变更内容 |
|------|---------|
| `backend/app/services/api_asset_service.py` | 修复 `generate_case_from_api` 中 `group_id` 字段不存在的问题（TestCase 使用 `folder_id`） |

## 实现详情

### 1. 用例断言 AI 生成 (`ApiCaseForm.vue`)
- `generateAssertions()` 调用 `aiStore.generateAssertions({ case_data })`
- 结果显示在 `ai-suggestions` 区域，每条可单独采纳或一键采纳全部
- 采纳后写入 `modelValue.assertions[]`，支持后续保存

### 2. 场景步骤 AI 生成 (`ScenarioDetail.vue`)
- 头部「AI 生成步骤」按钮
- 调用 `aiStore.analyzeFailure({ case_data: { name, description, steps } })`
- 将 `suggestions` 展示为步骤建议供用户参考

### 3. 执行失败 AI 分析 (`ExecutionDetail.vue`)
- 仅在 `execution.status === 'failed'` 时显示「AI 分析失败」按钮
- 调用 `aiStore.analyzeFailure({ case_data: { scenario_name, step_results } })`
- 弹窗展示 `root_cause`、`suggestions`、`severity`

### 4. 报告 AI 总结 (`ReportDetail.vue`)
- 头部「AI 总结报告」按钮
- 调用 `aiStore.summarizeReport({ report_id })`
- 弹窗展示 `summary`、`key_findings`、`recommendations`

### 5. 缺陷 AI 辅助 (`DefectForm.vue`)
- 「AI 生成标题」- 根据描述生成缺陷标题
- 「AI 生成描述」- 根据标题生成缺陷描述（多行建议）
- 「AI 推荐严重程度/优先级」- 根据标题/描述推断并回填 `severity` 和 `priority`

## 验证结果
- **前端构建**: `npm run build` 通过（1.59s）
- 所有新增 AI 功能使用现有 `useAiStore` 和已有 AI API 端点

## 遗留风险
- 缺陷 AI 辅助的 prompt 设计可进一步优化以获得更精准的结果