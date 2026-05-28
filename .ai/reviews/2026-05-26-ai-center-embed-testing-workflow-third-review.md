# AI 中枢嵌入测试流程三次审查修复包

## 审查目标

审查 `.ai/results/2026-05-26-ai-center-embed-testing-workflow-second-review-fix-result.md` 对二次审查包的修复结果。

二次审查中的多数点击路径已修复，前端构建也通过。但仍有两个会影响用户实际采纳结果的问题需要窄范围返工。

## 需要修复的问题

1. `frontend/src/views/scenario/ScenarioDetail.vue`: `handleAcceptAiSteps()` 现在调用 `scenarioStore.addStep()`，看起来是“真实保存”，但提交 payload 中 `case_id: null`。后端 `backend/app/schemas/scenario.py` 的 `ScenarioStepCreate.case_id` 是必填 `int`，模型 `ScenarioStep.case_id` 也是 `nullable=False`。因此点击“采纳建议”会请求失败，最终只提示“未能成功保存任何步骤”，不满足二次审查要求的“采纳行为不会假保存；要么真实保存，要么明确提示需要手动保存”。

2. `backend/app/routers/ai.py`: `generate_variants` 只在保存 `AIRepository.create_suggestions` 时把 `override` 归一化为 `override_config`，但接口返回仍是原始 `variants`。如果真实 AI 返回 prompt 中要求的 `override` 字段，FastAPI `response_model=GenerateVariantsResponse` 会忽略额外字段并输出默认 `override_config={}`，前端 `CaseVariantList.vue` 采纳时会丢失覆盖配置，创建出空变体。

3. 当前工作树中 `python -m pytest tests -q` 失败在 `tests/routers/test_test_plan_routes.py` 的导入错误：`from app.database import Base` 不存在。该问题属于测试计划三次返工线，不要求在本包中修复，但本包最终汇报不能继续写“后端全量测试通过”，除非当前工作树已先修复该测试收集错误。

## 修复范围

只允许修改以下文件中解决上述问题所必需的部分：

- `frontend/src/views/scenario/ScenarioDetail.vue`
- `backend/app/routers/ai.py`
- 如需要新增极小工具函数，可在同文件内新增，不要创建新模块。

不要修改测试计划相关文件；那条由测试计划三次审查包处理。

## 禁止事项

- 不重写 AI 中枢页面。
- 不改场景步骤后端 schema，除非明确同步模型、执行逻辑和现有步骤编辑表单，且有充分理由。优先前端修正交互。
- 不新增复杂的 AI 步骤自动匹配用例逻辑。
- 不把“保存失败”描述成“已采纳”。
- 不引入新依赖。

## 实现要求

### 1. 场景 AI 步骤采纳

选择下面一种最小方案：

方案 A（推荐）：改为“填充步骤草稿”

- 点击单条或批量采纳时，不直接调用 `scenarioStore.addStep()`。
- 打开现有 `ScenarioStepDialog`，把 AI 建议填入 `currentStep` 或新增一个 `initialStep` prop（如现有弹窗支持则复用），让用户选择有效 `case_id` 后保存。
- 按钮文案和成功提示必须说明是“已填入草稿，请选择用例后保存”，不能说“已保存”。

方案 B：明确不支持自动保存

- 保留 AI 建议弹窗，但“采纳建议”改为明确提示：`AI 已生成步骤建议，请点击添加步骤并选择用例后保存`。
- 不调用后端创建接口，不显示“已采纳 N 条步骤”。

不要继续发送 `case_id: null` 给后端。

### 2. 变体 override 返回归一化

- 在 `generate_variants` 中，service 返回后立即归一化 `variants`，统一字段：
  - `variant_type`
  - `description`
  - `override_config`
- `override_config` 取值优先级：已有 `override_config`，其次 `override`，否则 `{}`。
- 后续保存分析记录、保存 suggestion、接口返回都使用归一化后的列表。
- 保证如果 AI 返回：

```json
{"variant_type":"param_modify","description":"修改分页","override":{"params":{"page":"2"}}}
```

前端拿到的是：

```json
{"variant_type":"param_modify","description":"修改分页","override_config":{"params":{"page":"2"}}}
```

## 验收标准

1. 场景详情页点击 AI 生成步骤后，不会再把 `case_id: null` 发送到 `/api/scenario/{id}/steps`。
2. 场景 AI 建议的 UI 文案与真实行为一致：保存就是后端保存；草稿就是草稿；不支持自动保存就明确提示。
3. `/api/ai/generate-variants` 对 `override` 和 `override_config` 两种返回都能输出 `override_config`，前端采纳后不会丢失覆盖配置。
4. 前端构建通过。

## 验证方式

```bash
cd frontend
npm run build
```

后端如果当前测试计划路由测试尚未修复，全量测试可能因无关收集错误失败。本包至少运行或说明：

```bash
cd backend
python -m pytest tests/services/test_ai_service.py -q
```

如已修复测试计划路由测试，再运行：

```bash
cd backend
python -m pytest tests -q
```

## Claude 输出要求

结束时必须用中文汇报：

- 场景 AI 步骤采纳现在采用哪种行为：草稿、真实保存或明确不支持自动保存。
- 是否还会发送 `case_id: null`。
- `generate_variants` 的 `override` 兼容修复方式。
- 已运行的构建/测试命令和结果。
- 如果后端全量测试未运行或失败，明确说明是否受测试计划路由测试导入错误影响。

请同步写入：

- `.ai/results/2026-05-26-ai-center-embed-testing-workflow-third-review-fix-result.md`
