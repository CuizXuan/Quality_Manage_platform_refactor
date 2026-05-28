# AI 中枢嵌入测试流程审查修复包

## 审查目标

审查 `.ai/tasks/2026-05-25-ai-center-embed-testing-workflow.md` 对应实现，以及结果文件：

- `.ai/results/2026-05-25-ai-center-embed-testing-workflow-result.md`

当前实现只在若干页面加了 AI 按钮，但多处前后端接口契约不匹配，且多个验收项没有真正实现采纳回写。请按本修复包做最小必要返工。

## 需要修复的问题

1. `frontend/src/views/case/ApiCaseForm.vue` + `backend/app/schemas/ai.py` + `backend/app/routers/ai.py`: 前端 `generateAssertions()` 调用 `aiStore.generateAssertions({ case_data })`，但后端 `GenerateAssertionsRequest` 不接收 `case_data`，并且 `/api/ai/generate-assertions` 要求 `response_body` 或 `execution_step_id`。当前点击“AI 生成断言”会直接 400，无法满足“用例页能 AI 生成断言并写回”。请统一契约：要么前端传可用的 `response_body`，要么后端明确支持基于 `case_data` 生成断言建议。修复后断言字段也要和 schema 对齐，后端返回的是 `expected_value`，当前前端读取 `expected`。

2. `frontend/src/views/case/**`: 任务要求“用例页能 AI 生成变体并创建变体”，但当前只改了 `CaseVariantList.vue` 的表格高度，没有任何 AI 生成变体入口，也没有一键创建 `CaseVariant`。请在用例详情或变体列表中接入 `aiStore.generateVariants`，展示 AI 变体建议，并支持采纳后调用现有变体创建接口。采纳后应刷新变体列表。

3. `frontend/src/views/scenario/ScenarioDetail.vue` + `backend/app/routers/ai.py`: “AI 生成步骤”当前复用 `analyzeFailure({ execution_step_id: null, case_data })`，但 `AnalyzeFailureRequest.execution_step_id` 是必填整数，后端也会按该 id 查询执行记录；点击会 422/404。请不要用失败分析接口冒充步骤生成。可以新增或复用合适的 AI 接口，但必须让按钮真实可用。第一阶段可以展示建议；如果用户点击采纳，至少能追加步骤草稿或明确提示无法自动采纳原因。

4. `frontend/src/views/scenario/ScenarioDetail.vue`: `aiSuggestedSteps` 只赋值，没有任何模板展示，也没有采纳按钮。即使接口修好，用户也看不到建议。请增加轻量弹窗/抽屉/页面内区域展示步骤建议，并提供“采纳/关闭”动作。

5. `frontend/src/views/scenario/ExecutionDetail.vue` + `backend/app/routers/ai.py`: “AI 分析失败”同样传 `execution_step_id: null`，而后端要求查询执行记录 id。当前按钮不可用。请改为传当前执行记录 id，或调整后端支持基于当前执行 summary / step_results 分析。验收要求是自动读取执行 summary / step_results 并展示根因、影响范围、修复建议。

6. `frontend/src/views/scenario/ExecutionDetail.vue`: 任务要求失败分析后“可一键创建缺陷草稿或正式缺陷”。当前只展示弹窗，没有任何创建缺陷入口。请接入现有缺陷创建流程，至少提供“创建缺陷草稿”按钮，能把根因/建议带入缺陷标题或描述。

7. `frontend/src/views/report/ReportDetail.vue`: 后端 `SummarizeReportResponse` 返回 `summary_md`、`risk_score`、`risk_factors`，但前端读取 `summary`、`key_findings`、`recommendations`。当前弹窗会显示空内容，无法满足“报告详情能 AI 总结报告”。请按后端响应字段展示总结、风险评分和风险因素，或同步调整后端响应和前端。

8. `frontend/src/views/report/ReportDetail.vue`: 任务要求报告 AI 总结采纳后“可保存到报告 metrics 或 AIAnalysis，页面可查看历史总结”。后端已经创建 `AIAnalysis`，但前端没有展示 `analysis_id` 或历史入口，也没有采纳/保存动作。请至少显示本次 `analysis_id`，并提供查看/保留历史总结的入口或明确的“已保存到 AI 分析记录”提示。

9. `frontend/src/views/report/DefectForm.vue` + `backend/app/routers/ai.py`: 缺陷 AI 辅助三个按钮都调用 `analyzeFailure({ execution_step_id: null, case_data })`，按现有后端契约会失败。请修为真实可用的缺陷辅助路径。第一阶段可以基于标题/描述调用一个通用 AI 分析接口，但不能传后端不接受的字段。

10. `frontend/src/views/report/DefectForm.vue`: `result.suggestions` 在后端设计中是对象数组 `{ type, description, effort }`，当前 `join('\n')` 会生成 `[object Object]`；优先级推荐也用 `s.trim()`，对象会报错。请按对象结构读取 `description`，并为严重程度/优先级做稳定映射。

11. AI 未配置时的友好状态需要统一。当前有些 catch 只显示 `e.message`，axios 错误下经常是泛化文本。请优先读取 `e.response?.data?.detail`，并展示“请先配置 AI 模型”这类中文提示，确保页面不崩溃。

12. `backend/app/routers/ai.py`: `generate_assertions` 中当 `case_id` 查询用例时使用 `json.loads(case_model.body or "{}")`。`case_model.body` 可能是普通字符串或空字符串，解析失败会 500。请使用防御式 JSON 解析小函数。

## 修复范围

只允许修改以下文件中解决上述问题所必需的部分：

- `backend/app/routers/ai.py`
- `backend/app/services/ai_service.py`
- `backend/app/schemas/ai.py`
- `backend/app/repositories/ai_repository.py`
- `backend/app/services/test_case_service.py`
- `backend/app/services/scenario_service.py`
- `backend/app/services/report_service.py`
- `backend/app/services/defect_service.py`
- `frontend/src/api/ai.js`
- `frontend/src/stores/aiStore.js`
- `frontend/src/views/case/**`
- `frontend/src/views/scenario/**`
- `frontend/src/views/report/**`

## 禁止事项

- 不删除 AI 中枢现有页面。
- 不把 AI 结果只停留在不可采纳的弹窗文本，除非任务明确允许第一阶段只展示建议。
- 不强制用户必须使用 AI 才能完成原流程。
- 不暴露 API Key。
- 不引入新的大型依赖。
- 不做无关页面样式重写。
- 不修改本审查修复包。

## 验证方式

修复后至少运行：

```bash
cd frontend
npm run build
```

如修改后端 AI router/service/schema，请运行：

```bash
cd backend
python -m pytest tests -q
```

并做一轮手工验收：

1. 用例页点击 AI 生成断言，能返回建议并采纳写入当前 API 用例 `assertions`。
2. 用例页点击 AI 生成变体，能采纳并创建 `CaseVariant`。
3. 场景详情点击 AI 生成步骤，能看到建议，并能采纳或看到明确无法自动采纳原因。
4. 失败执行详情点击 AI 分析失败，能展示根因、影响范围/严重程度、修复建议，并能创建缺陷草稿。
5. 报告详情点击 AI 总结报告，能展示后端真实返回的 `summary_md`、`risk_score`、`risk_factors`，并能看到分析记录已保存。
6. 缺陷表单 AI 辅助按钮真实可用，不出现 422/404 或 `[object Object]`。
7. 未配置 AI 模型时，各页面给出中文友好提示且不崩溃。
8. 现有 AI 中枢页面仍可访问。

## Claude 输出要求

结束时必须用中文汇报：

- 已修复哪些审查问题。
- 哪些 AI 结果可以采纳回写。
- 哪些仍只是建议展示，以及原因。
- 变更文件。
- 已运行的测试、构建和手工验证。
- 剩余风险。

请同步写入：

- `.ai/results/2026-05-26-ai-center-embed-testing-workflow-review-fix-result.md`
