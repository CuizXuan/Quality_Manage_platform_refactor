# Quality Analytics Release Gate 审查修复 - 结果报告

## 修复概述

共修复 6 个问题，新增 1 个测试文件覆盖核心语义。

---

## 已修复问题

### 1. `_safe_json_loads` 兼容已解析的 dict/list

**问题**：`Report.summary`、`QualityGate.conditions`、`QualityGate.scope_filter` 是 SQLAlchemy `Column(JSON)`，读取出来通常已是 Python 对象。对 `dict` 调用 `json.loads` 会抛异常，导致统计归零、门禁条件为空。

**修复**：
```python
def _safe_json_loads(self, text: Any, fallback: Any = None) -> Any:
    if text is None:
        return fallback if fallback is not None else {}
    # Already parsed by SQLAlchemy JSON column — return as-is
    if isinstance(text, (dict, list)):
        return text
    if not isinstance(text, str):
        return fallback if fallback is not None else {}
    try:
        return json.loads(text)
    except Exception:
        return fallback if fallback is not None else {}
```

### 2. `get_release_gate` SQL 过滤排除 scoped gates

**问题**：传入 `project_id` 时，SQL 过滤 `scope_filter == None OR scope_filter == ""` 会把配置了 `{"project_id": 当前项目}` 的门禁规则在 SQL 层面就排除了，Python scope 匹配根本没有机会执行。

**修复**：移除 SQL 过滤，改为先获取全部 enabled gates，再在 Python 中统一判断：
```python
gate_query = self.db.query(QualityGate).filter(QualityGate.enabled == True)
gates = gate_query.all()
# scope 匹配移到 Python 层：空 scope → 全局适用；非空 scope → 与当前筛选一致时才检查
```

### 3. `get_overview` 的 `requirement_covered` Join 链路

**问题**：原代码 `req_query.join(Report, Report.target_id == RequirementItem.id)` 依赖 ID 偶然相等，且 `FunctionalTestCase` 没有 `requirement_id` 字段。

**修复**：改为正确的 join 链路：`RequirementItem → TestCase (requirement_id) → FunctionalTestCase (testcase_id)`：
```python
covered_subq = (
    self.db.query(RequirementItem.id)
    .join(TestCase, TestCase.requirement_id == RequirementItem.id)
    .join(FunctionalTestCase, FunctionalTestCase.testcase_id == TestCase.id)
    .filter(...)
    .distinct()
)
requirement_covered = covered_subq.count()
```

同步修复 `get_requirement_coverage` 中的相同问题。

### 4. 无缺陷时质量评分得满分

**问题**：代码 `defect_total == 0` 时 `closure_score = 0.0`，导致无缺陷场景天然少 25 分。

**修复**：
```python
if defect_total > 0:
    closure_score = (defect_total - defect_open) / defect_total * 100 * 0.25
else:
    closure_score = 100.0 * 0.25  # 无缺陷 → 满分
```

### 5. 前端 `coverageRate.value` 错误赋值

**问题**：`coverageRate` 是 computed，`onMounted` 中 `coverageRate.value = ...` 报错且无意义。

**修复**：删除该赋值。

### 6. 前端 `gatesChecked` / `scopeNote` 未响应式更新

**问题**：两者是 `ref`，只在 `onMounted` 后拷贝一次，查询/重置后 store 新值不同步。

**修复**：改为 `computed`：
```javascript
const gatesChecked = computed(() => analyticsStore.gatesChecked ?? 0)
const scopeNote = computed(() => analyticsStore.scopeNote || '')
```

---

## 新增测试文件

`backend/tests/services/test_quality_analytics_service.py` — 14 个测试，覆盖：

| 测试类 | 覆盖点 |
|--------|--------|
| `TestSafeJsonLoads` | dict/list 直接返回、字符串 JSON 解析、空字符串 fallback |
| `TestOverviewReportSummary` | dict summary 正确计算通过率、字符串 JSON 兼容、空 summary 不崩溃 |
| `TestQualityScoreNoDefects` | 无缺陷时 closure_score 满分，质量评分 = 85 |
| `TestReleaseGateConditionsAsList` | conditions 为 list 时门禁正确评估失败/通过 |
| `TestReleaseGateScopeFilter` | project scope 门禁正确匹配、全局空 scope 门禁任何项目适用 |
| `TestRequirementCoverageConsistency` | 需求覆盖通过 FunctionalTestCase join 与 `get_requirement_coverage` 一致；无用例需求不计入覆盖 |

---

## 验证结果

- **后端测试**: `pytest tests -q` → **100 passed** (1.77s)
- **专项测试**: `pytest tests/services/test_quality_analytics_service.py -q` → **14 passed**
- **前端构建**: `npm run build` → ✓ (1.79s)

---

## 剩余风险

1. **scope_filter 精确匹配**：目前 Python 层只判断 `sf_project == project_id`（精确相等），若门禁配置了 `project_id IN [1, 2]` 等范围条件，当前逻辑会跳过。
2. **get_requirement_coverage 中 `scope_note` 未设置项目过滤条件**：当 `project_id` 为 None 时，`scope_note` 只写"未指定项目"，但覆盖统计仍按全部项目计算，与 overview 语义一致但可能引起用户困惑。
3. **`_safe_json_loads` 对非字符串非容器类型**：若数据库存了 `int`/`bool` 等，会 fallback 到默认值——这是防御性设计，符合预期。