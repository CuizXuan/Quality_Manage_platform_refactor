# Quality_Manage_platform 项目注意事项

> 记录本项目的重要规范和常见问题，避免重复踩坑。

---

## 一、测试模块位置

### 测试文件存放路径
```
/mnt/h/workstation_hermes/Quality_Manage_platform/backend/tests/
```

### 测试模块结构
```
tests/
├── conftest.py              # 共享 fixtures（数据库、客户端、认证）
├── conftest_db.py           # 数据库相关 fixtures
├── conftest_client.py       # 客户端 fixtures
├── conftest_report.py       # 报告相关 fixtures
├── routers/                 # API 测试（按模块分离）
│   ├── test_cases.py        # 用例模块
│   ├── test_scenarios.py   # 场景模块
│   ├── test_defects.py     # 缺陷模块
│   ├── test_environments.py # 环境模块
│   ├── test_logs.py        # 日志模块
│   ├── test_datasets.py    # 数据集模块
│   ├── test_mocks.py       # MOCK 模块
│   ├── test_reports.py     # 报告模块
│   └── test_coverage.py    # 覆盖率模块
└── report/                  # 报告输出
```

### 测试报告存放路径
```
/mnt/h/workstation_hermes/Quality_Manage_platform/backend/reports/
```

### ⚠️ 注意事项
- 测试文件必须放在 `tests/routers/` 目录下
- 不要放在 `tests/report/` 目录下（那是报告输出目录）
- conftest.py 的 `override_get_db` 会导致 `PendingRollbackError`，需使用 `SessionLocal()` 绕过

---

## 二、测试报告样式

### 标准报告文件
**SRE 监控仪表盘风格**：
```
/mnt/h/workstation_hermes/Quality_Manage_platform/backend/reports/sre_dashboard_report.html
```

### 报告特点
- 深色主题 (`#0B1120` 背景)
- 玻璃态卡片设计
- 左侧边栏：环境指纹 + 质量雷达图
- 主体区域：SLO 指标、错误预算、模块统计表格
- 支持对比上次构建功能

### 更新报告的正确方式
1. 先运行测试获取最新数据
2. 更新 `sre_dashboard_report.html` 中的数据占位符
3. 不要创建新的报告文件，使用现有的 `sre_dashboard_report.html`

---

## 三、测试认证机制

### 认证 Fixture
所有 API 测试需要使用 `module scope` 的 `auth_info` fixture：

```python
@pytest.fixture(scope="module")
def auth_info():
    """获取测试用户认证信息"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "test_user").first()
        if not user:
            tenant = Tenant(name="test_tenant", code="TEST")
            db.add(tenant)
            db.flush()
            user = User(
                username="test_user",
                email="test@example.com",
                hashed_password="fake_hash",
                tenant_id=tenant.id
            )
            db.add(user)
            db.commit()
        
        # 生成 token
        access_token = create_access_token(data={"sub": user.username, "tenant_id": user.tenant_id})
        return {"user": user, "token": access_token}
    finally:
        db.close()
```

### 使用方式
```python
def test_something(auth_info):
    response = client.get(
        "/api/something",
        headers={"Authorization": f"Bearer {auth_info['token']}"}
    )
```

---

## 四、数据库隔离问题

### 问题症状
```
UNIQUE constraint failed: environments.name
PendingRollbackError: Session has a pending rollback
```

### 解决方案
1. 使用 `function` scope 而非 `module` scope
2. 每个测试后回滚事务
3. 清理测试数据

```python
@pytest.fixture(scope="function")
def db_session():
    """每个测试独立的数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()
```

---

## 五、API 路由顺序问题

### 问题
FastAPI 路由匹配按顺序进行，动态路径 `/{id}` 会在静态路径 `/batch-delete` 之前匹配。

### 错误示例
```python
@router.delete("/{log_id}")      # 先匹配，batch-delete 被当 log_id
@router.delete("/batch-delete")  # 永远不会被匹配到
```

### 正确顺序
```python
@router.delete("/batch-delete")  # 静态路径放前面
@router.delete("/{log_id}")      # 动态路径放后面
```

---

## 六、快速命令

### 运行所有测试
```bash
cd /mnt/h/workstation_hermes/Quality_Manage_platform/backend
python -m pytest tests/routers/ -v --tb=short
```

### 运行单个模块测试
```bash
python -m pytest tests/routers/test_cases.py -v
```

### 生成带时间戳的测试报告
```bash
python -m pytest tests/routers/ -v --html=reports/test_report.html --self-contained-html
```

---

## 七、常见错误排查

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| `422 Unprocessable Entity` | 请求参数格式错误 | 检查 Pydantic schema |
| `404 Not Found` | 资源不存在或路径错误 | 检查路由和 ID |
| `401 Unauthorized` | 缺少认证 | 添加 auth_info header |
| `UNIQUE constraint` | 数据重复 | 使用 function scope 或清理数据 |
| `PendingRollbackError` | 事务未提交/回滚 | 使用 `SessionLocal()` 而非 override |

---

## 八、项目结构参考

```
Quality_Manage_platform/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI 入口
│   │   ├── config.py         # 配置
│   │   ├── database.py       # 数据库连接
│   │   ├── models/           # SQLAlchemy 模型
│   │   ├── schemas/          # Pydantic 模型
│   │   ├── routers/          # API 路由
│   │   └── services/         # 业务逻辑
│   ├── tests/                 # 测试（按模块分离）
│   └── reports/               # 测试报告（SRE 仪表盘风格）
└── frontend/
    └── ...
```
