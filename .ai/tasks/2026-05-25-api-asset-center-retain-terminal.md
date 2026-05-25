# 成熟质量平台基础能力二：API 资产中心，并保留终端控制台

## 任务目标

请新增“API 资产中心”，对齐 Apifox/Postman 类产品的接口资产管理能力。

同时必须保留现有“终端控制台/终端调试台”，不要删除、弱化或替换。终端控制台的定位是：

```text
临时请求调试 / 排查问题 / 保存为用例 / 验证接口
```

API 资产中心的定位是：

```text
接口定义资产 / OpenAPI 导入 / 接口文档 / 接口版本 / 从接口生成用例 / 跳转终端调试
```

## 背景说明

当前系统有终端调试和用例管理，但没有“接口定义是单一事实源”的 API 资产层。成熟平台通常有：

- API 分组。
- API 定义。
- 请求参数。
- 响应结构。
- 示例。
- OpenAPI 导入。
- API 文档。
- 从 API 生成测试用例。
- API 跳转调试台。

## 必读文件

- `backend/app/routers/terminal.py`
- `backend/app/services/terminal_service.py`
- `backend/app/routers/testcase.py`
- `backend/app/services/test_case_service.py`
- `backend/app/models/test_case.py`
- `frontend/src/views/terminal/Terminal.vue`
- `frontend/src/views/case/CaseManagement.vue`
- `frontend/src/router/index.js`
- `H:\workstation_hermes\doc-generator\converters\api\openapi.py`

## 允许修改范围

- `backend/app/models/api_asset.py`
- `backend/app/schemas/api_asset.py`
- `backend/app/routers/api_asset.py`
- `backend/app/services/api_asset_service.py`
- `backend/app/main.py`
- `backend/app/database.py`
- `backend/app/services/platform_seed.py`
- `frontend/src/api/apiAsset.js`
- `frontend/src/stores/apiAssetStore.js`
- `frontend/src/views/apiAsset/**`
- `frontend/src/router/index.js`
- 可最小范围修改 `frontend/src/views/terminal/Terminal.vue`，只用于接收 API 资产带入的调试参数

## 禁止事项

- 禁止删除终端控制台。
- 禁止把终端控制台改成只读。
- 禁止通过 iframe 嵌入其它项目页面。
- 禁止直接复制 doc-generator 前端。
- 不做 Mock 服务，Mock 放后续任务。

## 实现要求

### 一、后端模型

新增：

- `ApiGroup`
  - `id`, `project_id`, `name`, `parent_id`, `sort_order`

- `ApiDefinition`
  - `id`
  - `project_id`
  - `group_id`
  - `name`
  - `method`
  - `path`
  - `base_url`
  - `summary`
  - `description`
  - `tags`
  - `parameters`
  - `request_body`
  - `responses`
  - `version`
  - `status`
  - `created_at`
  - `updated_at`

- `ApiImportRecord`
  - `id`
  - `project_id`
  - `source_type`
  - `source_url`
  - `status`
  - `imported_count`
  - `message`
  - `created_at`

### 二、后端 API

前缀：

```text
/api/assets
```

接口：

```text
GET/POST/PUT/DELETE /api/assets/groups
GET/POST/PUT/DELETE /api/assets/apis
POST /api/assets/import/openapi
POST /api/assets/apis/{id}/generate-case
GET /api/assets/apis/{id}/debug-payload
GET /api/assets/export/openapi
```

要求：

- OpenAPI 导入可输入 URL 或上传 JSON。
- 导入后按 tags 生成分组。
- 可从 API 定义生成 API 测试用例。
- `debug-payload` 返回终端控制台可识别的 method/url/headers/body/body_type 等数据。

### 三、前端页面

新增路由：

```text
/api-assets
```

菜单建议：

```text
接口中心
```

页面能力：

- 左侧 API 分组树。
- 右侧 API 表格。
- 查询栏：项目、关键词、方法、状态。
- 导入 OpenAPI 按钮。
- 新建/编辑 API。
- 从 API 生成用例。
- 跳转终端调试。

跳转终端调试要求：

- 不替代终端控制台。
- 点击“调试”后进入现有 `/terminal`。
- 尽量通过 query 或 store 把 method/url/body 带过去。
- 如果无法带入，也至少打开终端并记录待完善点。

### 四、样式要求

完全贴合当前平台：

- 背景参考 CaseManagement/ScenarioList。
- 查询栏 label 带中文冒号。
- 表格透明度与当前模块一致。
- 不能使用 doc-generator 原界面。

## 验收标准

- 能导入当前系统 `http://localhost:8000/openapi.json`。
- 能生成 API 列表。
- 能从 API 生成测试用例。
- 能从 API 跳转终端控制台调试。
- 终端控制台仍可独立使用。
- 前端 build 通过。

## Claude 输出要求

中文汇报：

- API 资产中心新增能力。
- 终端控制台如何保留并联动。
- OpenAPI 导入验证结果。
- 从 API 生成用例验证结果。
- 构建和测试结果。

请同步写入：

- `.ai/results/2026-05-25-api-asset-center-retain-terminal-result.md`
