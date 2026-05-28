# API 资产中心二次审查修复结果

## 修复执行摘要

本次修复解决 Codex 二次审查包 `2026-05-26-api-asset-center-retain-terminal-second-review.md` 中列出的全部 3 个问题。

---

## 已修复的问题

### 1. `generate_case_from_api` 创建时 `TestCase` 主表字段为空

**文件**: `backend/app/services/api_asset_service.py`

**问题**: `get_debug_payload` 提取的 headers/query/body 只写入了 `ApiTestCase`，主表 `TestCase.headers`、`TestCase.query_params`、`TestCase.body_type`、`TestCase.body` 仍是空值。场景执行和测试计划执行链路直接读取 `TestCase` 主表字段，导致从 API 资产生成的用例丢失 OpenAPI 参数和请求体。

**修复**: 将 `get_debug_payload` 调用提前到 `TestCase` 创建之前，直接用于填充所有字段：

```python
# 修复后：在创建 TestCase 前提取调试参数
debug = get_debug_payload(db, api.id) or {}
headers_for_case = debug.get("headers", {})
query_params_for_case = debug.get("query_params", {})
body_type_for_case = debug.get("body_type", "none")
body_for_case = debug.get("body", "")

case = TestCase(
    name=api.summary or api.name,
    description=api.description or "",
    case_type="api",
    method=api.method,
    url=f"{api.base_url or ''}{api.path}",
    headers=json.dumps(headers_for_case, ensure_ascii=False),      # 填充
    query_params=json.dumps(query_params_for_case, ensure_ascii=False),  # 填充
    cookies=json.dumps({}),
    auth_config=json.dumps({}),
    body_type=body_type_for_case,                                  # 填充
    body=body_for_case,                                            # 填充
    auto_case_id=auto_case_id,
)
```

`ApiTestCase` 和 `TestCase` 现在使用同一份 `get_debug_payload` 结果，保证主表和明细表一致。

---

### 2. 删除未使用的 `query_list` 变量

**文件**: `backend/app/services/api_asset_service.py`

**问题**: `query_list = [p for p in params if ...]` 变量提取后未使用，残留误导后续维护者。

**修复**: 该变量及其相关代码已随 `get_debug_payload` 提取逻辑前置一并删除。

---

### 3. 补充 `TestCase` 主表字段一致性断言

**文件**: `backend/tests/services/test_api_asset_service.py`

**问题**: 原测试只验证 `ApiTestCase` 字段，未验证 `TestCase` 主表与 `ApiTestCase` 一致。

**修复**: `test_json_fields_are_deserializable` 测试重写，新增断言：

```python
# TestCase 主表字段从 get_debug_payload 填充
tc_headers = json.loads(case.headers)
tc_params = json.loads(case.query_params)
assert tc_headers.get("X-Token") == "tok123"
assert tc_params.get("size") == "large"
assert case.body_type == "json"
body = json.loads(case.body)
assert body["a"] == 1

# ApiTestCase 明细字段与 TestCase 主表一致
assert json.loads(api_case.headers) == tc_headers
assert json.loads(api_case.params) == tc_params
assert api_case.body_type == case.body_type
assert json.loads(api_case.body) == body
```

---

## 变更文件清单

| 文件 | 操作 |
|------|------|
| `backend/app/services/api_asset_service.py` | 修改 — 主表字段填充修复、删除 query_list |
| `backend/tests/services/test_api_asset_service.py` | 修改 — 补充主表一致性断言 |

---

## 验证结果

### 后端测试（55 passed）

```bash
cd backend
python -m pytest tests -q

# 结果：55 passed in 1.08s
```

`tests/services/test_api_asset_service.py`: **14 passed**

### 前端构建

**说明**: 前端构建报错来自 `frontend/src/views/docgen/DocGenTemplates.vue`（与本次审查修复无关的预存在文件），不在本次修复范围内。后端测试全部通过，业务逻辑修复已验证。

---

## 剩余风险

1. **DocGenTemplates.vue 预存编译错误**: 该文件有 "Invalid end tag" 语法错误，与本次审查修复无关。如需完整构建需单独处理。

2. **auth_config 未填充**: `TestCase.auth_config` 继续保持空对象 `{}`，除非 API 定义中有明确的 auth 来源字段。如后续场景需要认证配置，应从 OpenAPI 的 `security` 字段或 `components/securitySchemes` 提取。