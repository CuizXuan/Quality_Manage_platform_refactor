# AI 中枢嵌入测试流程二次审查修复包

## 审查目标

审查 `.ai/results/2026-05-26-ai-center-embed-testing-workflow-review-fix-result.md` 对应返工结果，确认 `.ai/reviews/2026-05-26-ai-center-embed-testing-workflow-review.md` 中的问题是否真正闭环。

当前后端测试和前端构建可以通过，但仍有几个运行时问题会导致用户点击后报错或验收项不成立。请按本修复包做最小必要修复。

## 需要修复的问题

1. `frontend/src/views/case/ApiCaseForm.vue`: AI 断言建议模板中 `v-for` 变量是 `suggestion`，但插值里写成了 `sugg.field`、`sugg.assertion_type`、`sugg.expected_value`。构建不会拦住这个问题，但页面渲染 AI 建议时会访问未定义变量并报错。请改为使用 `suggestion`。

2. `frontend/src/views/case/CaseVariantList.vue`: 审查要求“AI 生成变体，采纳后创建 `CaseVariant` 并刷新列表”。当前 `acceptVariant` 只是把建议填到新建表单并要求用户再点“创建”；`acceptAllVariants` 只是反复填表，最后只会保留最后一个建议，实际没有创建多条变体。请让“采纳”真正调用现有 `caseStore.createVariant(props.caseId, data)` 创建记录并刷新列表；“采纳全部”应逐条创建所有建议。仍可保留“填充表单预览”按钮，但“采纳”文案必须对应真实创建。

3. `frontend/src/views/scenario/ExecutionDetail.vue`: 已导入 `useReportStore`，但没有执行 `const reportStore = useReportStore()`。`handleCreateDefectFromAnalysis()` 调用 `reportStore.createDefect` 时会触发 `ReferenceError`，导致“创建缺陷草稿”不可用。请补齐 store 实例。

4. `frontend/src/views/scenario/ExecutionDetail.vue`: 存在 `const emit = defineEmits(['create-defect'])` 但没有使用，且当前页面是路由页不是被父组件监听的弹窗。请删除无用 emit，避免误导。

5. `backend/app/routers/ai.py`: `generate_variants` 里仍然直接 `json.loads(case_model.headers or "{}")` 和 `json.loads(case_model.body or "{}")`。如果 `body` 是普通字符串或历史脏数据，会 500。请复用已新增的 `_safe_json_loads`。这与上一轮第 12 条同类，不能只修 `generate_assertions`。

6. `frontend/src/views/scenario/ScenarioDetail.vue`: `handleAcceptAiSteps` 直接 `scenarioStore.currentSteps.push(...)`，只是前端内存追加，刷新后消失，也没有后端 ID。审查要求“至少能追加建议步骤草稿或提示无法自动采纳原因”。请改成明确的“追加草稿”行为：要么打开现有步骤弹窗并预填当前建议，让用户保存到后端；要么将按钮文案和提示改为“暂不支持自动采纳”，不要伪装成已保存步骤。若选择自动保存，必须调用现有创建步骤接口。

7. `frontend/src/views/report/ReportDetail.vue`: `handleAiSummarize` catch 仍只读 `e.message`，没有按审查要求优先读取 `e.response?.data?.detail`。请补齐友好错误提示。

## 修复范围

只允许修改以下文件中解决上述问题所必需的部分：

- `backend/app/routers/ai.py`
- `frontend/src/views/case/ApiCaseForm.vue`
- `frontend/src/views/case/CaseVariantList.vue`
- `frontend/src/views/scenario/ExecutionDetail.vue`
- `frontend/src/views/scenario/ScenarioDetail.vue`
- `frontend/src/views/report/ReportDetail.vue`
- 如需要写结果，请新增 `.ai/results/2026-05-26-ai-center-embed-testing-workflow-second-review-fix-result.md`

## 禁止事项

- 不重写 AI 中枢页面。
- 不扩大到无关模块样式调整。
- 不修改本审查修复包。
- 不用“已采纳”描述只在内存中临时展示、刷新即消失的行为。

## 验证方式

修复后至少运行：

```bash
cd frontend
npm run build
```

```bash
cd backend
python -m pytest tests -q
```

并手工核对：

1. API 用例页 AI 断言建议能正常渲染，不报 `sugg is not defined`。
2. AI 变体单条采纳会创建一条 `CaseVariant` 并刷新列表。
3. AI 变体采纳全部会创建多条 `CaseVariant`。
4. 失败执行详情点击“创建缺陷草稿”不会 `ReferenceError`，能调用缺陷创建接口。
5. 场景步骤 AI 建议的采纳行为不会假保存；要么真实保存，要么明确提示需要手动保存。
6. `generate_variants` 遇到普通字符串 body 不会 500。
7. 报告 AI 总结未配置或失败时展示中文友好错误。

## Claude 输出要求

结束时必须用中文汇报：

- 已修复哪些问题。
- 哪些按钮现在会真实写入后端。
- 变更文件。
- 已运行的测试、构建和手工验证。
- 剩余风险。

请同步写入：

- `.ai/results/2026-05-26-ai-center-embed-testing-workflow-second-review-fix-result.md`
