# 测试报告生成器 - 使用指南

## 📋 概述

本模块为 `Quality_Manage_platform` 项目提供美观的 pytest 测试报告功能，包含：

- **自定义 HTML 报告**：渐变色头部、统计卡片、模块分析、失败详情
- **JSON 结果文件**：完整的测试数据，便于其他系统集成
- **pytest-html 原生报告**：标准 pytest HTML 报告

---

## 📁 文件结构

```
backend/tests/report/
├── __init__.py           # TestReportGenerator 类（报告生成器）
└── README.md              # 本文档

backend/tests/conftest_report.py  # pytest hooks（自动收集数据+生成报告）
backend/pytest.ini                # pytest 配置（标记、日志、报告选项）
backend/reports/                  # 报告输出目录
│   ├── test_report.html         # 自定义美观HTML报告
│   ├── test_results.json        # JSON格式测试结果
│   └── pytest_native_report.html # pytest-html原生报告
```

---

## 🚀 快速开始

### 方式一：一键运行（推荐）

```bash
cd backend
pytest tests/
```

运行结束后会自动生成：
- `reports/test_report.html` - 自定义美观报告
- `reports/test_results.json` - JSON 结果数据
- `reports/pytest_native_report.html` - pytest-html 原生报告

### 方式二：指定测试目录

```bash
# 只测试某个模块
pytest tests/routers/test_cases.py

# 只测试项目模块
pytest tests/routers/test_projects.py

# 运行所有测试
pytest tests/
```

### 方式三：按标记运行

```bash
# 只运行 P0 测试（冒烟测试）
pytest -m p0

# 只运行 API 测试
pytest -m api

# 排除慢速测试
pytest -m "not slow"
```

---

## 📊 报告预览

### 自定义 HTML 报告包含：

1. **渐变色头部**
   - 项目名称、版本
   - 测试环境、环境地址
   - 开始时间、执行时长
   - Python/Pytest 版本

2. **通过率卡片**
   - 大字体百分比显示
   - 动态进度条动画

3. **统计卡片**（5个）
   - 📋 总用例数
   - ✅ 通过数（绿色）
   - ❌ 失败数（红色）
   - ⏭️ 跳过数（黄色）
   - ⚠️ 错误数（灰色）

4. **模块统计表格**
   - 按模块分组
   - 显示通过/失败数量
   - 状态标识（✅/⚠️）

5. **失败分析区**（如有失败）
   - 失败用例列表
   - 失败类型分类
   - 错误摘要

6. **测试结果详情**
   - 可按状态筛选（全部/通过/失败/跳过）
   - 每条结果显示：状态图标、名称、模块、耗时
   - 失败用例显示错误详情

---

## ⚙️ 配置说明

### pytest.ini 标记

| 标记 | 说明 | 用途 |
|------|------|------|
| `p0` | P0级测试用例 | 核心流程，冒烟测试 |
| `p1` | P1级测试用例 | 重要功能 |
| `p2` | P2级测试用例 | 边界/异常情况 |
| `smoke` | 冒烟测试 | 快速验证 |
| `api` | API测试 | API功能测试 |
| `slow` | 慢速测试 | 执行时间较长 |

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `TEST_ENV` | `测试环境` | 测试环境名称 |
| `TEST_ENV_URL` | `http://localhost:8000` | 测试环境地址 |
| `TEST_OPERATOR` | `自动化测试` | 操作人 |

### 使用环境变量示例

```bash
# 设置测试环境
export TEST_ENV="预发布环境"
export TEST_ENV_URL="http://pre.example.com"
export TEST_OPERATOR="张三"

# 运行测试
pytest tests/
```

---

## 🔧 高级用法

### 1. 仅生成 JSON 结果（不生成 HTML）

修改 `conftest_report.py`，注释掉 HTML 生成部分：

```python
def pytest_sessionfinish(session, exitstatus):
    collector.finalize()
    json_path = collector.save_to_json("reports/test_results.json")

    # 注释掉这行禁止生成 HTML
    # from tests.report import TestReportGenerator
    # generator.generate(collector.results, "reports/test_report.html")
```

### 2. 自定义报告生成器

```python
from tests.report import TestReportGenerator

# 创建生成器
generator = TestReportGenerator(
    project_name="我的项目",
    project_version="v2.0.0"
)

# 设置时间
from datetime import datetime
generator.start_time = datetime.now()

# 生成报告
generator.generate(results, "output/report.html")
```

### 3. 读取已有 JSON 结果生成报告

```python
import json
from tests.report import TestReportGenerator

with open("reports/test_results.json") as f:
    data = json.load(f)

results = data.get("results", [])
generator = TestReportGenerator("Quality_Manage_platform", "v1.0.0")
generator.generate(results, "reports/custom_report.html")
```

### 4. 集成到 CI/CD

```yaml
# .github/workflows/test.yml 示例
- name: Run Tests
  run: |
    cd backend
    pytest tests/ -v --tb=short

- name: Generate Report
  run: |
    # 报告已由 pytest 自动生成
    ls -la reports/
```

---

## 🎨 报告样式定制

### 修改颜色主题

编辑 `tests/report/__init__.py`，找到 `:root` 部分：

```css
:root {
    --primary: #4F46E5;      /* 主色（蓝紫色） */
    --success: #10B981;      /* 成功（绿色） */
    --warning: #F59E0B;      /* 警告（黄色） */
    --danger: #EF4444;       /* 危险（红色） */
    /* ... */
}
```

### 修改头部背景

```css
.report-header {
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
    /* 改为单色：background: var(--primary); */
}
```

---

## 📝 测试用例设计建议

为了让报告中的"描述"字段更有意义，建议在测试函数中添加 docstring：

```python
class TestCaseP0CRUD:
    """用例管理模块 - P0核心流程测试"""

    def test_case_create_full_params(self, auth_info, db_session, cleanup_case):
        """P0_TC001: 创建用例-完整参数"""
        # 测试代码...
```

运行后，报告会显示：`P0_TC001: 创建用例-完整参数`

---

## ❓ 常见问题

### Q: 报告数据为空？

**A:** 确保 `conftest.py` 中已导入 `conftest_report`：

```python
# tests/conftest.py 末尾添加
from tests.conftest_report import *
```

### Q: 如何查看本地报告？

**A:** 使用 Python 内置服务器：

```bash
cd backend/reports
python -m http.server 8080
# 访问 http://localhost:8080/test_report.html
```

### Q: 如何分享报告？

**A:** `test_report.html` 是独立的单文件报告，可以直接发送给任何人，无需网络访问。

### Q: 报告不显示中文？

**A:** 确保 HTML 文件保存为 UTF-8 编码（已默认）。

---

## 📄 依赖清单

| 依赖 | 版本 | 说明 |
|------|------|------|
| pytest | ≥8.0 | 测试框架 |
| pytest-html | 最新 | 原生HTML报告 |

---

## 🔗 相关文档

- [Pytest 文档](https://docs.pytest.org/)
- [pytest-html 插件](https://github.com/pytest-dev/pytest-html)
- [Allure Report](https://allure.qatools.ru/)（可选，用于更高级的报告）

---

*最后更新：2026-04-29*
