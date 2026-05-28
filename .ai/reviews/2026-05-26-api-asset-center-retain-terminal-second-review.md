# API 资产中心二次审查修复包

## 审查目标

审查 `.ai/results/2026-05-26-api-asset-center-retain-terminal-review-fix-result.md` 对应返工结果，确认 `.ai/reviews/2026-05-26-api-asset-center-retain-terminal-review.md` 中的问题是否闭环。

本次返工大部分问题已修复，后端测试和前端构建通过，但仍有一个会影响生成用例后续执行链路的残留问题。

## 需要修复的问题

1. `backend/app/services/api_asset_service.py`: `generate_case_from_api` 复用了 `get_debug_payload`，但只把提取到的 headers/query/body 写入了 `ApiTestCase`，主表 `TestCase.headers`、`TestCase.query_params`、`TestCase.body_type`、`TestCase.body` 仍然是空值。当前系统里场景执行、测试计划执行等链路会直接读取 `TestCase` 主表字段，例如 `scenario_service.py` 和 `test_plan_service.py` 都通过 `case.headers`、`case.query_params`、`case.body_type`、`case.body` 调用终端内部执行接口。因此，从 API 资产生成的用例如果被加入场景或测试计划，会丢失 OpenAPI 参数和请求体。

   请在创建 `TestCase` 时就使用 `get_debug_payload` 提取出的请求字段，保证主表和 `ApiTestCase` 明细表保持一致：

   - `TestCase.headers = json.dumps(headers_for_case, ensure_ascii=False)`
   - `TestCase.query_params = json.dumps(query_params_for_case, ensure_ascii=False)`
   - `TestCase.body_type = body_type_for_case`
   - `TestCase.body = body_for_case`
   - `TestCase.auth_config` 继续保持 `{}` 即可，除非已有明确来源。

2. `backend/app/services/api_asset_service.py`: `generate_case_from_api` 中的 `query_list` 变量已经不再使用，请删除，避免残留误导后续维护者。

3. `backend/tests/services/test_api_asset_service.py`: 当前测试只验证 `ApiTestCase` 字段包含 headers/query/body，没有验证 `TestCase` 主表字段。请补充或调整测试，明确断言生成的 `TestCase.headers`、`TestCase.query_params`、`TestCase.body_type`、`TestCase.body` 与 `ApiTestCase` 一致，且 JSON 字段可反序列化。

## 修复范围

只允许修改以下文件中解决上述问题所必需的部分：

- `backend/app/services/api_asset_service.py`
- `backend/tests/services/test_api_asset_service.py`
- 如确有必要，可小范围修改结果文件 `.ai/results/2026-05-26-api-asset-center-retain-terminal-second-review-fix-result.md`

## 禁止事项

- 不改动终端控制台、场景执行或测试计划执行链路。
- 不重写 API 资产中心前端页面。
- 不做无关样式调整或清理。
- 不修改本审查修复包。

## 验证方式

修复后至少运行：

```bash
cd backend
python -m pytest tests/services/test_api_asset_service.py -q
python -m pytest tests -q
```

建议再运行：

```bash
cd frontend
npm run build
```

手工/测试验收要点：

1. 从带 header、query 参数、JSON example 的 OpenAPI API 生成用例。
2. 生成的 `TestCase` 主表字段包含同样的 header、query 参数和 body。
3. 生成的 `ApiTestCase` 明细字段仍包含同样的 header、query 参数和 body。
4. 后续场景执行或测试计划执行读取 `TestCase` 字段时不会丢失请求参数。

## Claude 输出要求

结束时必须用中文汇报：

- 已修复哪些问题。
- 变更文件。
- 已运行的测试或检查。
- 是否写入结果文件。
- 剩余风险。

请同步写入：

- `.ai/results/2026-05-26-api-asset-center-retain-terminal-second-review-fix-result.md`
