# 成熟质量平台基础能力四：AI 中枢嵌入测试流程

## 任务目标

请将现有 AI 中枢从“独立工具页”升级为“嵌入测试流程的辅助能力”。

现状问题：

```text
AI 中枢已有模型配置、Prompt 模板、变体生成、断言生成、失败分析、报告总结，
但这些能力没有真正贴合到用例、场景、执行、报告、缺陷流程里。
```

本任务要求保留 AI 中枢现有页面，同时在核心测试流程中增加 AI 动作入口和采纳回写。

## 必读文件

- `backend/app/routers/ai.py`
- `backend/app/services/ai_service.py`
- `backend/app/repositories/ai_repository.py`
- `backend/app/models/ai.py`
- `backend/app/routers/testcase.py`
- `backend/app/services/test_case_service.py`
- `backend/app/routers/scenario.py`
- `backend/app/services/scenario_service.py`
- `backend/app/routers/report.py`
- `frontend/src/views/ai/**`
- `frontend/src/views/case/**`
- `frontend/src/views/scenario/**`
- `frontend/src/views/report/**`

## 允许修改范围

- `backend/app/routers/ai.py`
- `backend/app/services/ai_service.py`
- `backend/app/repositories/ai_repository.py`
- `backend/app/services/test_case_service.py`
- `backend/app/services/scenario_service.py`
- `backend/app/services/report_service.py`
- `backend/app/services/defect_service.py`
- `frontend/src/api/ai.js`
- `frontend/src/stores/aiStore.js`
- `frontend/src/views/ai/**`
- `frontend/src/views/case/**`
- `frontend/src/views/scenario/**`
- `frontend/src/views/report/**`

## 禁止事项

- 不删除 AI 中枢现有页面。
- 不把 AI 结果只停留在弹窗文本。
- 不强制用户必须使用 AI 才能完成原流程。
- 不暴露 API Key。
- 不在无配置 AI 模型时让页面崩溃。

## 实现要求

### 一、用例流程嵌入 AI

在用例详情/编辑中加入：

- AI 生成断言。
- AI 生成变体。
- AI 优化用例描述。

采纳要求：

- 生成断言后可一键写入当前 API 用例 `assertions`。
- 生成变体后可一键创建 `CaseVariant`。
- 采纳记录仍写入 `AISuggestion`。

### 二、场景流程嵌入 AI

在场景详情中加入：

- AI 推荐场景步骤。
- AI 检查场景覆盖风险。

第一阶段可以先输出建议，不强制自动创建步骤；但如果用户点击采纳，至少能追加建议步骤草稿或提示无法自动采纳原因。

### 三、执行失败嵌入 AI

在执行详情中加入：

- 对失败执行一键失败分析。
- 自动读取执行 summary / step_results。
- 展示根因、影响范围、修复建议。
- 可一键创建缺陷草稿或正式缺陷。

### 四、报告嵌入 AI

在报告详情中加入：

- AI 总结报告。
- AI 提炼风险。
- AI 生成发布建议。

采纳后：

- 可保存到报告 metrics 或 AIAnalysis。
- 页面可查看历史总结。

### 五、缺陷嵌入 AI

在缺陷详情/编辑中加入：

- AI 生成复现步骤。
- AI 推荐严重程度/优先级。
- AI 生成修复建议。

第一阶段可先做按钮和结果展示，采纳写回缺陷描述或评论字段；如果缺陷还没有评论字段，先写回描述并注明。

## 前端样式要求

- 保持现有页面风格。
- AI 按钮不要做成突兀大块。
- 建议使用小按钮、抽屉或弹窗。
- 中文文案。
- 加载、失败、未配置 AI 状态必须友好。

## 验收标准

- 用例页能 AI 生成断言并写回。
- 用例页能 AI 生成变体并创建变体。
- 执行详情能 AI 分析失败。
- 报告详情能 AI 总结报告。
- 缺陷页至少有 AI 辅助入口。
- AI 未配置时不崩溃。
- 现有 AI 中枢页面仍可访问。
- 前端 build 通过。

## Claude 输出要求

中文汇报：

- AI 嵌入了哪些流程。
- 哪些 AI 结果可以采纳回写。
- 哪些仍只是建议展示。
- 测试和构建结果。
- 剩余风险。

请同步写入：

- `.ai/results/2026-05-25-ai-center-embed-testing-workflow-result.md`
