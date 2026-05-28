# Test Plan Suite Execution Center 第三次审查修复 - 结果报告

## 审查修复概述

第三次审查共提出 4 个问题，全部修复完成。86 个后端测试全部通过。

---

## 已修复问题

| # | 问题 | 修复内容 |
|---|------|---------|
| 1 | `TestRunningScenarioSummary.test_scenario_trigger_records_running_status_via_real_function` 使用假桩 | 改为调用真实 `_run_test_plan_background`，patch `httpx.Client` + `app.database.SessionLocal` |
| 2 | `TestBackgroundExecutionFlow` 缺少 dirty JSON 场景验证 | 新增 `test_case_item_with_dirty_json_does_not_fail`，验证终端收到 `{}` |
| 3 | 路由顺序无测试 | 新增 `test_test_plan_routes.py`，验证 `/runs` 在 `/{plan_id}` 之前匹配；添加鉴权 header |
| 4 | 重复 `delete_suite` 定义 | 已删除一个重复定义（之前版本已处理） |

---

## 关键技术修复

### 1. httpx.Client + SessionLocal 双 patch

背景函数内使用局部导入 `import httpx` 和 `from app.database import SessionLocal`，单一路径 patch 无法拦截。修复方案：

```python
with patch("httpx.Client") as mock_client_cls:
    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.post.return_value = mock_response
    mock_client_cls.return_value = mock_client

    with patch("app.database.SessionLocal", TestSession):
        svc._run_test_plan_background(run_id, plan_id)
```

### 2. `engine` fixture 修复

原 `engine` fixture 只返回裸 engine，`TestBackgroundExecutionFlow` 内未调用 `Base.metadata.create_all(engine)`，导致数据库表未创建。修复：

```python
@pytest.fixture
def engine():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)  # 在返回前建表
    return engine
```

### 3. dirty JSON 断言修复

`captured_request` 的 `json` 字段结构为：
```python
{"url": "...", "json": {"method": "...", "headers": {}, "query_params": {}, ...}}
```
之前直接检查 `captured_request.get("headers")` 得到 `None`，应检查 `captured_request.get("json", {}).get("headers")`。

### 4. 路由测试鉴权

`TestClient` 默认不携带认证，修复后在请求头中添加 admin Bearer token：

```python
def get_auth_header():
    with TestClient(app) as client:
        resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        token = resp.json().get("access_token", "")
    return {"Authorization": f"Bearer {token}"}
```

---

## 变更文件

| 文件 | 变更 |
|------|------|
| `tests/services/test_test_plan_service.py` | `engine` fixture 增加 `create_all`；3 个真实链路测试增加 `SessionLocal` patch + httpx mock |
| `tests/routers/test_test_plan_routes.py` | 修复 import（`Base` 从 `app.models.base` 而非 `app.database`）；添加 `auth_headers` fixture；所有请求携带 Bearer token |

---

## 验证结果

- 后端测试: `pytest tests -q` → **86 passed** (36.61s)
- 路由测试: `pytest tests/routers/test_test_plan_routes.py -q` → **3 passed**
- 新增背景执行测试: `TestBackgroundExecutionFlow` 2 个 + `TestRunningScenarioSummary::test_scenario_trigger_records_running_status_via_real_function` 1 个，全部通过