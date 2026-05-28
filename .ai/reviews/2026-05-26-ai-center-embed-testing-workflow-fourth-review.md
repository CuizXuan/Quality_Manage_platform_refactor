# AI 中枢嵌入测试流程四次审查修复包

## 审查目标

审查 `.ai/results/2026-05-26-ai-center-embed-testing-workflow-third-review-fix-result.md` 对三次审查包的修复结果。

本轮仍有两个窄范围运行时问题需要修复：一个会导致 AI 变体空结果 500，一个会导致“填入草稿”后用户保存仍然无法落库。

## 需要修复的问题

1. `backend/app/routers/ai.py`: `generate_variants` 中 `normalized_variants` 只在 `if variants:` 分支内定义，但函数最后无条件返回：

```python
return {"analysis_id": analysis.id, "variants": normalized_variants}
```

当 AI 正常返回空列表时会触发 `UnboundLocalError`，把“未生成变体建议”的正常空结果变成 500。

2. `frontend/src/views/scenario/ScenarioDetail.vue`: 三次修复把“采纳建议”改为打开 `ScenarioStepDialog` 草稿弹窗，但当前 `ScenarioStepDialog` 保存时提交的数据没有顶层 `case_id`；后端 `ScenarioStepCreate.case_id` 是必填 `int`，`ScenarioService.add_step()` 也读取 `data["case_id"]`。因此用户即使在弹窗中补充字段，保存仍会 422 或失败。这仍不满足“草稿就是草稿，保存必须可落库；不支持自动保存就明确提示”的验收标准。

## 修复范围

只允许修改以下文件中解决上述问题所必需的部分：

- `backend/app/routers/ai.py`
- `frontend/src/views/scenario/ScenarioDetail.vue`
- 如选择修正草稿保存链路，可最小修改 `frontend/src/views/scenario/ScenarioStepDialog.vue`

不要修改后端 schema、模型、场景执行引擎或测试计划相关文件。

## 禁止事项

- 不重写场景编排页面。
- 不把保存失败的行为描述成已保存或已采纳。
- 不引入新依赖。
- 不扩大到无关样式调整。

## 实现要求

### 1. 修复空变体返回

- 在 `generate_variants` 中，service 返回后立即定义：

```python
normalized_variants = []
for v in variants or []:
    ...
```

- 后续 `raw_response`、`summary`、`create_suggestions`、接口返回都使用 `normalized_variants`。
- `variants=[]` 时接口应返回 200，body 中 `variants` 为 `[]`。

### 2. 修复 AI 步骤草稿行为

任选一种最小方案：

方案 A：让草稿保存真的可落库

- 修改 `ScenarioStepDialog.vue` 的新增步骤提交逻辑，确保提交给后端的数据包含顶层 `case_id`。
- 如果当前后端只支持“关联用例步骤”，则 AI 草稿应默认打开 `step_type='case'`，并让用户选择 `config.case_id` 后保存。
- 提交 payload 至少包含：
  - `case_id: stepForm.value.config.case_id`
  - `name`
  - `sort_order`
  - `failure_strategy` 或后端实际字段
  - 其他后端 schema 支持的字段
- 不要继续提交只有 `config.case_id` 而没有顶层 `case_id` 的 payload。

方案 B：明确不支持自动草稿保存

- `ScenarioDetail.vue` 不再打开 `ScenarioStepDialog`。
- 点击“填入草稿”改为提示：`AI 已生成步骤建议，请点击添加步骤并选择用例后保存`。
- 不调用后端、不打开会保存失败的弹窗、不显示“已填入草稿”。

如果选择方案 A，请同时保证普通“添加步骤”仍能保存，不只修 AI 入口。

## 验收标准

1. `/api/ai/generate-variants` 在 `svc.generate_variants()` 返回 `[]` 时不报 500，返回 `variants: []`。
2. `/api/ai/generate-variants` 在 AI 返回 `override` 时仍返回 `override_config`。
3. 场景 AI 步骤建议不会再进入一个“看似可保存但必然 422”的草稿弹窗。
4. 如果保留草稿弹窗，用户选择用例后保存能向后端提交顶层 `case_id`。
5. 前端构建通过。

## 验证方式

```bash
cd frontend
npm run build
```

```bash
cd backend
python -m pytest tests/services/test_ai_service.py -q
```

如当前测试计划路由测试仍有导入错误，不要求本包修复，但最终汇报必须如实说明全量后端测试是否受该无关错误影响。

## Claude 输出要求

结束时必须用中文汇报：

- `generate_variants` 空列表和 `override` 兼容如何修复。
- 场景 AI 步骤建议最终采用方案 A 还是方案 B。
- 如果采用方案 A，说明普通添加步骤和 AI 草稿保存是否都会提交顶层 `case_id`。
- 已运行的构建/测试命令和结果。
- 剩余风险。

请同步写入：

- `.ai/results/2026-05-26-ai-center-embed-testing-workflow-fourth-review-fix-result.md`
