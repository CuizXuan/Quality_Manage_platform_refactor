# AI 与缺陷跳转问题审查修复包

## 审查目标

审查并修复 AI 中枢嵌入测试工作流中的三个遗留风险点：

1. `AIService` 对 `case_data`（尤其是场景数据）的实际处理效果需要真实 AI 配置验证。
2. 缺陷表单 query params 跳转需要确认 `/defect` 路由和初始化逻辑。
3. `AIService` 抛出的非 `HTTPException` 可能仍在前端显示英文底层异常。

本修复包面向 Claude Code 执行。执行前请先阅读 `AGENTS.md` 和本文件，保持修复范围小而明确。

## 需要修复的问题

1. `backend/app/routers/ai.py`: AI 生成类接口直接调用 `svc.generate_variants`、`svc.generate_assertions`、`svc.analyze_failure`、`svc.summarize_report`，未统一捕获 service 层非 HTTP 异常。真实模型调用失败、OpenAI SDK 报错、网络错误或解析外异常可能通过全局异常处理返回英文提示。

2. `backend/app/routers/ai.py`: `/api/ai/analyze-failure` 的 `case_data` 分支把场景数据压缩成 `{name, description, steps}` 后传给 `svc.analyze_failure(scenario_data)`，没有把场景数据作为 `case_data` 参数传入，也没有构造清晰的“基于场景生成步骤建议”输入。需要真实 AI 配置验证其输出是否能被前端 `ScenarioDetail.vue` 与 `DefectForm.vue` 正确消费。

3. `frontend/src/views/report/DefectList.vue`: 路由 `/defect` 已存在，但页面初始化只加载列表和统计，未读取 `route.query`，因此从其他页面通过 query params 跳转到缺陷表单时，无法自动打开表单或预填字段。

4. `frontend/src/views/report/DefectForm.vue`: 表单只支持 `defect` 编辑对象，不支持“新建缺陷预填值”入参；AI 辅助按钮的异常提示直接拼接 `e.response?.data?.detail || e.message`，后端或 SDK 英文错误仍会展示给用户。

5. 相关测试缺口：需要补充后端非 HTTP 异常中文化测试、前端缺陷 query 初始化测试或至少构建验证。真实 AI 配置验证必须单独记录，不能用 mock 测试替代。

## 修复范围

Claude 只能修改解决上述问题所必需的文件，优先限制在：

- `backend/app/routers/ai.py`
- `backend/app/services/ai_service.py`
- `backend/app/schemas/ai.py`
- `backend/tests/routers/` 或 `backend/tests/services/` 下与 AI 相关的测试
- `frontend/src/views/report/DefectList.vue`
- `frontend/src/views/report/DefectForm.vue`
- `frontend/src/stores/aiStore.js`
- 必要时新增一个很小的前端工具函数，例如 `frontend/src/utils/errorMessage.js`

如确实需要修改其他文件，必须在最终汇报中说明原因。

## 禁止事项

- 不做无关重构。
- 不改动 AI 配置 API、缺陷 CRUD API 的公开响应结构，除非是为了把错误提示稳定为中文。
- 不引入新的外部依赖。
- 不把真实 AI 验证替换成 mock 单测后声称完成。
- 不改动任务范围之外的页面样式、菜单、仪表盘或测试计划相关代码。
- 不暴露 `api_key`、完整 base URL token、SDK 原始错误堆栈到前端或日志输出。

## 必读文件

- `AGENTS.md`
- `.ai/CODEX_WORKFLOW.md`
- `backend/app/routers/ai.py`
- `backend/app/services/ai_service.py`
- `backend/app/schemas/ai.py`
- `backend/app/main.py`
- `frontend/src/router/index.js`
- `frontend/src/views/report/DefectList.vue`
- `frontend/src/views/report/DefectForm.vue`
- `frontend/src/stores/aiStore.js`
- `frontend/src/views/scenario/ScenarioDetail.vue`
- `frontend/src/views/scenario/ExecutionDetail.vue`
- `frontend/src/views/case/ApiCaseForm.vue`

## 实现要求

### 1. AI 后端异常中文化

- 在 `backend/app/routers/ai.py` 增加小函数处理 AI service 调用异常，例如：
  - `HTTPException` 原样抛出。
  - 其他异常统一转换为 `HTTPException(status_code=502, detail="AI 服务调用失败，请检查模型配置或稍后重试")`。
- 保留必要日志，但不要把密钥、完整请求体或 SDK 原始英文错误直接返回给前端。
- `test_ai_connection` 可以返回连接测试失败状态，但 message 也应避免直接透出冗长英文底层错误。可返回中文失败说明，并在后端日志记录简短原因。
- 保持路由函数短小；如果一个路由变长，抽出小函数。

### 2. case_data / 场景数据处理

- 梳理 `/api/ai/analyze-failure` 中 `case_data` 分支的语义：
  - 场景步骤生成应把输入明确为“场景信息”，包含 `name`、`description`、`steps`、必要上下文字段。
  - 如果继续复用 `AIService.analyze_failure`，应传入清晰的 `execution_step` 和 `case_data`，避免把场景数据伪装成执行失败步骤。
  - 更推荐在 `AIService` 中新增小函数（如 `generate_scenario_step_suggestions`），但不要大改 API；路由仍可返回现有 `AnalyzeFailureResponse` 结构。
- 修正前后端字段不匹配风险：
  - 后端 `AnalyzeFailureResponse` 当前只返回 `analysis_id`、`root_cause`、`suggestions`，前端 `DefectForm.vue` 却读取 `result.severity`。要么后端响应 schema 明确包含 `severity`，要么前端不再依赖该字段。
  - 保持向后兼容，优先让后端返回 `severity` 字段并更新 schema。
- 对 `GenerateVariantsResponse.VariantItem` 注意字段兼容：AI prompt 要求 `override`，schema 是 `override_config`。如本次验证发现真实 AI 返回 `override` 导致响应校验失败，需要在 parser 或 router 层归一化为 `override_config`，同时兼容已有 `override_config`。

### 3. 缺陷表单 query params 跳转

- 确认路由为 `frontend/src/router/index.js` 中的 `/defect` / `DefectList`，不要新增重复路由。
- 在 `DefectList.vue` 使用 `useRoute` 读取 query，支持至少这些字段：
  - `open=create` 或 `action=create` 时自动打开新建缺陷表单。
  - `title`
  - `description`
  - `severity`
  - `priority`
  - `defect_type`
  - `project_id`
  - `version_id`
  - `iteration_id`
  - `requirement_id`
  - `tags`（支持逗号分隔字符串或 JSON 数组字符串）
- 新增小函数把 query 归一化为缺陷草稿对象，数字字段转为 `Number`，非法值忽略或回退默认值。
- `DefectForm.vue` 增加 `initialData` 或等价 prop，用于新建时预填。编辑模式仍以 `defect` 为准。
- 打开新建表单时加载项目/版本/迭代/需求级联数据，确保 query 中的归属字段能在下拉框显示。
- 不要在表单保存后把用户带到其他页面；保持现有保存后刷新列表行为。

### 4. 前端错误提示中文化

- 在 `DefectForm.vue` 的 AI 辅助 catch 分支中，不要直接展示 `e.message`。
- 可抽取小函数，例如 `getAiErrorMessage(err, fallback)`：
  - 优先使用后端中文 `detail`。
  - 如果 `detail` 或 `message` 是明显英文 SDK/网络错误，显示中文兜底：`AI 服务调用失败，请检查模型配置或稍后重试`。
  - 保留不同操作的前缀，如 `AI 生成失败：...`、`AI 推荐失败：...`。
- 如 `aiStore.js` 中也保存英文 `error`，请一并收敛，避免 AI 页面直接展示英文底层错误。

## 验收标准

1. 访问 `/defect?open=create&title=登录失败&severity=high&priority=P1&defect_type=api&tags=登录,接口` 后，`DefectList` 自动打开新建缺陷表单，字段按 query 预填。
2. 访问 `/defect?action=create&project_id=1&version_id=2&iteration_id=3&requirement_id=4` 时，表单自动打开并尝试加载对应级联数据；不存在的数据不导致页面报错。
3. AI service 抛出普通 `Exception("Connection timed out")` 时，API 返回 502，`detail` 为中文兜底文案，前端不会显示英文 SDK/网络错误。
4. `/api/ai/analyze-failure` 的 `case_data` 分支返回结构仍兼容现有前端，包含 `analysis_id`、`root_cause`、`suggestions`，如实现了 severity，也包含合法的 `severity`。
5. 如果真实 AI 返回变体字段 `override`，`/api/ai/generate-variants` 不应因为响应模型校验失败而 500。
6. 不改变缺陷列表既有查询、分页、状态流转和编辑行为。

## 真实 AI 配置验证

这项不能用 mock 替代。请在本地已有真实 AI 配置时执行：

1. 进入 AI 配置页或调用 `/api/ai/config/test`，确认连接测试可用。
2. 使用一个场景 `case_data` 调用 `/api/ai/analyze-failure`，示例：

```json
{
  "case_data": {
    "scenario_id": 0,
    "name": "登录后查询个人资料",
    "description": "用户登录成功后访问个人资料接口，校验昵称和用户ID存在",
    "steps": [
      { "name": "登录", "method": "POST", "url": "/api/login" },
      { "name": "查询资料", "method": "GET", "url": "/api/profile" }
    ]
  }
}
```

3. 记录返回结果是否：
   - 为中文。
   - 能被前端展示。
   - `suggestions` 结构稳定。
   - 不含英文底层错误。
4. 如果当前环境没有真实 AI 配置或密钥，请在最终汇报中明确写：`真实 AI 配置验证未执行，原因：本地未配置有效 AI 密钥/服务`。

## 建议验证

后端：

```text
cd backend
pytest tests/services/test_ai_service.py
pytest tests/routers/test_ai*.py
```

如没有现成 router 测试文件，可新增最小覆盖后运行对应测试。

前端：

```text
cd frontend
npm run build
```

手工验证：

```text
/defect?open=create&title=登录失败&severity=high&priority=P1&defect_type=api&tags=登录,接口
```

## Claude 输出要求

结束时必须用中文汇报：

- 修复了哪些问题。
- 变更文件列表。
- 已运行的测试或构建命令及结果。
- 真实 AI 配置验证是否执行；若执行，给出简要结果；若未执行，说明原因。
- 剩余风险。
