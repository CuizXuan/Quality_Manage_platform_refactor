# 质量分析看板与发布门禁审查修复包

## 审查目标

审查 `.ai/results/2026-05-25-quality-analytics-release-gate-result.md` 对任务包 `.ai/tasks/2026-05-25-quality-analytics-release-gate.md` 的实现结果，重点确认：

- 质量看板指标是否来自真实报告、缺陷、门禁、需求数据。
- 发布门禁是否能正确识别启用规则和阻塞条件。
- 项目/版本/迭代筛选是否真实影响统计。
- 前端展示是否会随筛选刷新。
- 验证结果是否覆盖新增核心逻辑。

## 当前验证结果

Codex 本地复跑：

```bash
cd backend
python -m pytest tests -q
```

结果：

```text
86 passed, 10 warnings in 2.14s
```

```bash
cd frontend
npm run build
```

结果：构建通过，`built in 1.76s`。

注意：当前通过的测试没有覆盖 `QualityAnalyticsService` 的核心统计语义，因此不能仅凭全量测试通过判断该功能可发布。

## 需要修复的问题

1. `backend/app/services/quality_analytics_service.py`: `_safe_json_loads` 不兼容 SQLAlchemy `JSON` 列已经反序列化后的 `dict/list`。`Report.summary`、`QualityGate.conditions`、`QualityGate.scope_filter` 在当前模型中都是 `Column(JSON, ...)`，读取出来通常已经是 Python 对象。当前 helper 对 dict/list 调用 `json.loads` 会抛异常并返回 fallback，导致：
   - 报告 summary 被当成 `{}`，通过率、执行数、用例总数可能全部归零。
   - 门禁 conditions 被当成 `[]`，发布门禁条件不再真实评估。
   - 门禁 scope_filter 被当成 `{}`，范围匹配失效。

   请让 helper 显式兼容已解析对象，例如对 `dict/list` 直接返回原值，只对字符串执行 `json.loads`。

2. `backend/app/services/quality_analytics_service.py`: `get_release_gate` 在传入 `project_id` 时先用 SQL 过滤：

```python
or_(QualityGate.scope_filter == None, QualityGate.scope_filter == "")
```

这会把真正配置了 `{"project_id": 当前项目}` 的门禁规则提前排除，后面的 Python scope 匹配根本没有机会执行。请改为先获取 enabled gates，再用解析后的 `scope_filter` 在 Python 中判断：

- 空 scope 表示全局规则，适用于当前范围。
- scope 中的 `project_id/version_id/iteration_id` 与当前筛选一致时适用。
- scope 不匹配时跳过。

不要因为传入 `project_id` 就只保留空 scope 规则。

3. `backend/app/services/quality_analytics_service.py`: `get_overview` 的 `requirement_covered` 计算不可信。当前逻辑把 `RequirementItem.id` 与 `Report.target_id` 直接 join，但 `Report.target_id` 注释和现有创建逻辑表示它是执行记录 ID 或场景 ID，不是需求 ID。这会产生 ID 偶然相等的误计数，也会漏掉真实需求覆盖。

   请与 `get_requirement_coverage` 保持一致，基于 `FunctionalTestCase.requirement_id` 统计覆盖需求数；如果要统计“已执行覆盖”，需要明确 join 到用例和报告的真实关联链路，不能直接用 `Report.target_id == RequirementItem.id`。

4. `backend/app/services/quality_analytics_service.py`: 质量评分公式与结果报告描述不一致。报告中写“无缺陷时 closure_rate 为 1.0”，但代码在 `defect_total == 0` 时 `closure_score = 0.0`，导致无缺陷场景天然少 25 分。请修正为无缺陷时闭环得分满分，或更新公式说明并给出产品合理性；本任务期望成熟质量平台视角，建议无缺陷不扣分。

5. `frontend/src/views/qualityAnalytics/QualityAnalytics.vue`: `coverageRate` 是 computed，却在 `onMounted` 中执行 `coverageRate.value = ...`。这是只读 computed 的错误写法，开发环境会警告，且赋值没有意义。请删除该赋值。

6. `frontend/src/views/qualityAnalytics/QualityAnalytics.vue`: `gatesChecked` 和 `scopeNote` 是本地 ref，只在 `onMounted` 后拷贝一次。用户点击“查询”或“重置”后，store 中的新值不会同步到页面，门禁检查数量和范围提示可能显示旧数据。请改为 computed：

```javascript
const gatesChecked = computed(() => analyticsStore.gatesChecked ?? 0)
const scopeNote = computed(() => analyticsStore.scopeNote || '')
```

7. 需要补充后端测试。请新增聚焦 `QualityAnalyticsService` 的测试，至少覆盖：
   - `Report.summary` 为 dict 时能正确计算 `average_pass_rate/execution_count/total_cases`。
   - `QualityGate.conditions` 为 list 时 release gate 会真实评估失败条件。
   - 带 `scope_filter={"project_id": x}` 的门禁在传入同一 project_id 时会被检查。
   - 无缺陷时质量评分不因为闭环率被扣 25 分。
   - overview 的需求覆盖与 `get_requirement_coverage` 一致，不依赖 `Report.target_id == RequirementItem.id`。

## 修复范围

允许修改：

- `backend/app/services/quality_analytics_service.py`
- `backend/tests/services/test_quality_analytics_service.py`
- `frontend/src/views/qualityAnalytics/QualityAnalytics.vue`
- 如需同步结果，新增 `.ai/results/2026-05-26-quality-analytics-release-gate-review-fix-result.md`

如确需调整 schema 或 store，必须保持现有 API 响应兼容，并在结果中说明原因。

不要修改无关业务模块，不要重构报告中心、缺陷中心或质量门禁管理页。

## 验证方式

修复后至少运行：

```bash
cd backend
python -m pytest tests/services/test_quality_analytics_service.py -q
python -m pytest tests -q
```

```bash
cd frontend
npm run build
```

建议手工核对：

1. 准备一个 summary 含 `total/passed/failed` 的报告后，看板平均通过率不是 0。
2. 准备一个 blocking 门禁，条件如 `pass_rate >= 90`，当当前通过率低于阈值时 `/release-gate` 返回 `overall_pass=false` 且 blockers 有内容。
3. 配置 project scope 的门禁后，用相同 project_id 查询能够检查到该门禁。
4. 切换筛选条件后，范围提示和门禁检查数量同步刷新。

## Claude 输出要求

结束时请用中文汇报：

- 修复了哪些统计/门禁语义问题。
- 新增了哪些测试。
- 后端测试与前端构建真实结果。
- 剩余风险。

请同步写入：

- `.ai/results/2026-05-26-quality-analytics-release-gate-review-fix-result.md`
