# 用例模块开发细节

## 1. 模块边界

用例模块负责管理可复用的接口测试资产，核心资源包括基础用例 `TestCase` 与用例变体 `CaseVariant`。

已明确能力：
- 基础用例增删改查
- 请求配置管理
- 从终端调试保存基础用例
- 用例变体创建与查询
- 断言配置随变体保存
- 为批量执行与覆盖率统计提供用例资产数据

设计未明确的内容不在本方案中扩展：
- 文件夹仅使用 `folder_id` 关联，不新增文件夹接口
- 标签、版本、变量、前后置脚本未给出数据结构，不新增表和接口
- 执行接口、覆盖率统计接口未定义，不新增 API

## 2. 后端目录

```
backend/app/
├── models/
│   ├── test_case.py
│   └── case_variant.py
├── schemas/
│   ├── test_case.py
│   └── case_variant.py
├── repositories/
│   ├── test_case_repository.py
│   └── case_variant_repository.py
├── services/
│   └── test_case_service.py
└── routers/
    └── testcase.py
```

## 3. 数据模型设计

### TestCase

字段：`id, folder_id, name, description, method, url, query_params, headers, cookies, auth_config, body_type, body, expected_status, source_debug_id, created_by, created_at, updated_at`

建议：
- `id`：主键
- `folder_id`：可空整数
- `name`：字符串，必填
- `description`：文本，可空
- `method`：字符串，必填
- `url`：字符串，必填
- `query_params`、`headers`、`cookies`、`auth_config`：Text，存 JSON 字符串
- `body_type`：字符串，可空
- `body`：Text，可空
- `expected_status`：整数，可空
- `source_debug_id`：整数，可空
- `created_by`：整数，可空
- `created_at`、`updated_at`：时间字段

### CaseVariant

字段：`id, case_id, name, variant_type, override_params, override_headers, override_body, expected_status, expected_schema, assertions, created_by, created_at`

建议：
- `case_id` 关联 `TestCase.id`
- `override_params`、`override_headers`、`expected_schema`、`assertions` 使用 Text 存 JSON 字符串
- `override_body` 使用 Text 存覆盖请求体
- `variant_type` 仅允许设计文档列出的类型

变体类型：
`normal, boundary, empty, missing_field, type_error, invalid_enum, overlong_field, auth_failed, permission_denied, response_schema, response_business_value, performance_threshold`

## 4. Schema 设计

### TestCaseCreate

包含：
`folder_id, name, description, method, url, query_params, headers, cookies, auth_config, body_type, body, expected_status, source_debug_id`

校验：
- `name`、`method`、`url` 必填
- `query_params`、`headers`、`cookies`、`auth_config` 必须为对象
- `expected_status` 为整数或空

### TestCaseUpdate

字段与 `TestCaseCreate` 一致，但全部可选。更新时只处理显式传入字段。

### TestCaseResponse

返回 `TestCase` 全量字段，JSON 字符串字段反序列化为对象。

### CaseVariantCreate

包含：
`name, variant_type, override_params, override_headers, override_body, expected_status, expected_schema, assertions`

校验：
- `name`、`variant_type` 必填
- `variant_type` 必须属于设计范围
- `override_params`、`override_headers` 为对象
- `expected_schema` 为对象或空
- `assertions` 为数组

### CaseVariantResponse

返回 `CaseVariant` 全量字段，JSON 字符串字段反序列化为对象。

分页响应统一为：

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20
}
```

## 5. API 接口设计

### 创建基础用例

`POST /testcase`

请求体使用 `TestCaseCreate`。

处理流程：
1. 校验必填字段。
2. 校验 JSON 字段类型。
3. 序列化 JSON 字段。
4. 写入 `TestCase`。
5. 返回 `TestCaseResponse`。

### 查询基础用例列表

`GET /testcase`

查询参数：
- `page`
- `page_size`
- `folder_id`
- `keyword`

处理规则：
- 默认 `page = 1`
- 默认 `page_size = 20`
- `folder_id` 按所属文件夹过滤
- `keyword` 按 `name` 模糊查询

### 查询基础用例详情

`GET /testcase/{id}`

处理规则：
- 用例不存在返回 `404`
- 只返回基础用例，不内嵌变体列表

### 更新基础用例

`PUT /testcase/{id}`

请求体使用 `TestCaseUpdate`。

处理规则：
- 用例不存在返回 `404`
- 只更新显式传入字段
- JSON 字段整体替换
- 更新 `updated_at`

### 删除基础用例

`DELETE /testcase/{id}`

响应：

```json
{
  "id": 1
}
```

处理规则：
- 用例不存在返回 `404`
- 删除基础用例时同步删除关联变体，避免无效 `case_id`

### 创建用例变体

`POST /testcase/{id}/variant`

请求体使用 `CaseVariantCreate`。

处理规则：
- 先校验基础用例存在
- 校验 `variant_type`
- 序列化 JSON 字段
- 写入 `CaseVariant`
- 返回 `CaseVariantResponse`

### 查询用例变体列表

`GET /testcase/{id}/variant`

查询参数：
- `page`
- `page_size`
- `variant_type`

处理规则：
- 先校验基础用例存在
- 按 `case_id` 查询
- `variant_type` 存在时按类型过滤
- 返回分页结构

## 6. Repository 设计

### TestCaseRepository

方法：
- `create(db, data)`
- `list(db, page, page_size, folder_id, keyword)`
- `get_by_id(db, case_id)`
- `update(db, case_obj, data)`
- `delete(db, case_obj)`

要求：
- 只负责数据库访问
- 不抛出 HTTP 异常
- 列表查询同时返回 `items` 和 `total`

### CaseVariantRepository

方法：
- `create(db, case_id, data)`
- `list_by_case(db, case_id, page, page_size, variant_type)`
- `delete_by_case(db, case_id)`

要求：
- 查询必须带 `case_id`
- 删除基础用例时删除其关联变体

## 7. Service 业务流程

### 创建基础用例

1. 接收 `TestCaseCreate`
2. 校验字段
3. 序列化 JSON 字段
4. 调用 Repository 创建
5. 反序列化后返回

### 查询基础用例

1. 规范化分页参数
2. 调用 Repository 查询
3. 反序列化 JSON 字段
4. 返回分页结构

### 更新基础用例

1. 查询基础用例
2. 不存在则抛出业务异常
3. 提取显式传入字段
4. 序列化 JSON 字段
5. 更新并返回

### 删除基础用例

1. 查询基础用例
2. 不存在则抛出业务异常
3. 删除关联变体
4. 删除基础用例
5. 返回删除 ID

### 创建变体

1. 查询基础用例
2. 校验 `variant_type`
3. 序列化 JSON 字段
4. 创建变体
5. 返回变体详情

## 8. 错误处理

| 场景 | 状态码 | detail |
|---|---:|---|
| 基础用例不存在 | 404 | `Test case not found` |
| 变体类型非法 | 400 | `Invalid variant type` |
| JSON 字段非法 | 400 | `Invalid JSON field` |
| Pydantic 校验失败 | 422 | FastAPI 默认响应 |

规则：
- Repository 不处理 HTTP 异常
- Service 抛业务异常
- Router 转换为 `HTTPException`

## 9. 前端设计

### API 模块

文件：`frontend/src/api/case.js`

方法：
- `list(params)`
- `get(id)`
- `create(data)`
- `update(id, data)`
- `delete(id)`
- `listVariants(id, params)`
- `createVariant(id, data)`

### Store

文件：`frontend/src/stores/caseStore.js`

Store：`useCaseStore`

状态：
- `cases`
- `total`
- `page`
- `pageSize`
- `currentCase`
- `variants`
- `variantTotal`
- `loading`

Actions：
- `fetchCases(params)`
- `fetchCase(id)`
- `createCase(data)`
- `updateCase(id, data)`
- `deleteCase(id)`
- `fetchVariants(id, params)`
- `createVariant(id, data)`

## 10. 前端组件

### CaseTree

职责：
- 展示文件夹维度入口
- 选择文件夹后触发刷新

约束：
- 文件夹接口未定义，只消费外部传入数据

事件：
- `folder-selected`

### CaseList

职责：
- 展示基础用例列表
- 支持关键字查询
- 支持选择、创建、删除入口

事件：
- `case-selected`
- `create-case`
- `delete-case`

### CaseDetail

职责：
- 展示和编辑基础用例详情
- 管理请求配置字段
- 保存基础用例

字段：
`folder_id, name, description, method, url, query_params, headers, cookies, auth_config, body_type, body, expected_status, source_debug_id`

### CaseVariantList

职责：
- 展示当前用例变体
- 按 `variant_type` 过滤
- 创建新变体

### CaseAssertionEditor

职责：
- 编辑变体 `assertions`

约束：
- 断言结构未定义，只保证输出数组对象

### CaseRunPanel

职责：
- 展示运行入口和状态区域

约束：
- 执行接口未定义，不新增 API

## 11. 页面流程

基础用例流程：
1. 页面加载调用 `fetchCases`
2. 选择文件夹后按 `folder_id` 重新查询
3. 选择用例后调用 `fetchCase` 与 `fetchVariants`
4. 编辑后调用 `updateCase`
5. 创建后刷新列表并选中新用例
6. 删除后刷新列表并清空详情

变体流程：
1. 选中基础用例
2. 查询该用例变体
3. 填写变体类型和覆盖配置
4. 调用 `createVariant`
5. 创建成功后刷新列表

从终端调试保存基础用例：
1. 调试模块提供 `source_debug_id` 与请求配置
2. 用例模块按 `TestCaseCreate` 接收
3. 创建基础用例并保存 `source_debug_id`
4. 返回基础用例详情

## 12. 测试范围

后端：
- 创建基础用例成功
- 查询基础用例列表成功
- 查询基础用例详情成功
- 不存在用例返回 `404`
- 更新基础用例成功
- 删除基础用例成功
- 创建变体成功
- 不存在用例创建变体返回 `404`
- 非法 `variant_type` 返回 `400`
- 查询变体列表成功

前端：
- `fetchCases` 写入列表和分页状态
- `fetchCase` 写入当前用例
- `fetchVariants` 写入变体列表
- `CaseDetail` 提交基础用例字段
- `CaseVariantList` 创建变体后刷新列表

## 13. 开发顺序

1. 创建 SQLAlchemy 模型
2. 创建 Pydantic schema
3. 创建 Repository
4. 创建 Service
5. 创建 Router 并注册到 FastAPI
6. 编写后端接口测试
7. 创建前端 API 模块
8. 创建 `useCaseStore`
9. 创建 `CaseList`、`CaseDetail`、`CaseVariantList`
10. 接入 `CaseTree`、`CaseAssertionEditor`、`CaseRunPanel`
11. 完成页面联调
