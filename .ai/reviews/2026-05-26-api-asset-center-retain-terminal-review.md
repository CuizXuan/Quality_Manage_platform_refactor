# API 资产中心实现审查修复包

## 审查目标

审查 `.ai/results/2026-05-25-api-asset-center-retain-terminal-result.md` 对应的 API 资产中心实现，重点核对：

- API 资产导入、列表、调试跳转、生成用例是否满足 `.ai/tasks/2026-05-25-api-asset-center-retain-terminal.md`。
- 终端调试台 `/terminal` 是否保持独立可用，并能接收 API 资产带入的调试参数。
- 前后端关键路径是否有真实可执行验证。

## 需要修复的问题

1. `backend/app/services/api_asset_service.py`: `generate_case_from_api` 创建 `ApiTestCase` 时使用了不存在的字段 `case_id=case.id`。当前模型字段是 `testcase_id`，该问题会导致 `POST /api/assets/apis/{id}/generate-case` 运行时报 `TypeError: 'case_id' is an invalid keyword argument for ApiTestCase`，任务验收项“能从 API 生成测试用例”实际不成立。

2. `backend/app/services/api_asset_service.py`: `generate_case_from_api` 写入 `ApiTestCase.headers`、`params`、`assertions` 时传入了 list/dict 原始对象，但模型字段是 `Text`，现有 `TestCaseService` 的模式是显式 `json.dumps`。请统一为 JSON 字符串，并尽量复用 `get_debug_payload` 的 header/query/body 提取逻辑，避免生成出来的用例丢失 OpenAPI 参数和请求体。

3. `frontend/src/views/apiAsset/ApiAssetCenter.vue`: `debugApi` 跳转 `/terminal` 时没有传递 `payload.query_params`。`Terminal.vue` 已经尝试读取 `route.query.query_params`，但前端没有带过去，导致从 API 资产跳转调试时 query 参数丢失。

4. `frontend/src/views/apiAsset/ApiAssetCenter.vue`: `deleteApi` 的 `catch` 块引用了未定义变量 `e`，删除确认取消或删除失败时会触发新的 `ReferenceError`，掩盖真实状态。请改为 `catch (e)` 并保持取消时静默、失败时提示。

5. `frontend/src/views/apiAsset/ApiAssetCenter.vue`: 页面声称支持“编辑 API”，并且已有 `editingApi`、`updateApi`、弹窗标题分支，但表格操作没有编辑入口，也没有把当前行数据填充到 `apiForm` 的函数。请补齐最小编辑入口，避免“新建/编辑 API”验收只完成一半。

6. 缺少 API 资产中心关键路径测试。请至少新增后端服务级测试覆盖：
   - OpenAPI JSON 内容导入后生成分组和 API 定义。
   - `get_debug_payload` 能返回 method/url/headers/query_params/body_type/body。
   - `generate_case_from_api` 能创建 `TestCase` 和关联 `ApiTestCase`，且 JSON 字段可反序列化。

## 修复范围

Claude 只能修改解决上述问题所必需的文件，建议范围：

- `backend/app/services/api_asset_service.py`
- `backend/tests/services/test_api_asset_service.py`
- `frontend/src/views/apiAsset/ApiAssetCenter.vue`
- 如测试夹具确实需要，可最小修改 `backend/tests/conftest.py`

## 禁止事项

- 不删除、替换或弱化 `frontend/src/views/terminal/Terminal.vue` 的现有功能。
- 不改动 `/terminal` 路由定位，不把终端控制台嵌入 API 资产中心。
- 不重写 API 资产中心页面整体样式。
- 不扩大到文档中心、质量基础、AI 中心等无关模块。
- 不为了通过测试而跳过真实数据库写入或绕开服务逻辑。

## 验证方式

修复后至少运行：

```bash
cd backend
python -m pytest tests/services/test_api_asset_service.py -q
python -m pytest tests -q

cd ../frontend
npm run build
```

建议手工验证：

1. 导入一个最小 OpenAPI JSON。
2. 在 API 资产中心点击“调试”，确认 `/terminal` 中 method、url、headers、query params、body 被正确带入。
3. 点击“生成用例”，确认用例管理页能看到生成的接口用例。
4. 点击“编辑”，修改 API 名称或状态后保存，列表更新。

## Claude 输出要求

结束时必须用中文汇报：

- 已修复哪些问题。
- 变更文件。
- 已运行的测试或检查。
- 剩余风险。

请同步写入：

- `.ai/results/2026-05-26-api-asset-center-retain-terminal-review-fix-result.md`
