# 第五阶段：报告中心与缺陷中心 — 实施方案

> **依据文档：** `详细设计.md` §4 + `整合文档.md` §2.6 + `05_后端开发规范.md` + `06_前端组件与页面规范.md` + `07_开发顺序与验收标准.md` §5

## 1. 需求理解

### 核心功能
- 报告生成、列表、详情（从 ExecutionRun 数据自动生成）
- 数据统计：通过率、失败分布、耗时、变体/场景覆盖、缺陷关联
- 缺陷增删改查、状态流转、优先级、复测、修复版本
- 外部系统同步（Jira、GitLab 等）
- AI 自动归因失败、生成修复建议（第六阶段）

### 关键数据结构

```
Report {
  id, execution_id, summary, pass_rate,
  fail_distribution: Record<string, number>,
  duration_stats: {avg, max},
  variant_coverage, scenario_coverage,
  defect_ids: string[], created_at
}

Defect {
  id, name, status, severity, priority,
  linked_case_ids, linked_scenario_ids,
  created_by, created_at, updated_at,
  fix_version, retest_result
}
```

### 验收标准（来自 07_开发顺序与验收标准.md §5）
- ✅ 执行历史可生成报告
- ✅ 失败项可创建缺陷
- ✅ 门禁可根据报告和缺陷给出放行结果

---

## 2. 后端架构

### 2.1 模型

```
Report {
  id, execution_id, summary, pass_rate,
  fail_distribution(JSON), duration_stats(JSON),
  variant_coverage, scenario_coverage,
  defect_ids(JSON), created_at
}

Defect {
  id, name, status, severity, priority,
  linked_case_ids(JSON), linked_scenario_ids(JSON),
  created_by, created_at, updated_at,
  fix_version, retest_result
}

QualityGate {
  id, rule_type, threshold, status: 'pass'|'warn'|'block',
  evaluation_time
}
```

### 2.2 API 端点

**报告相关：**
- `GET /api/report` — 报告列表（分页）
- `GET /api/report/{id}` — 报告详情
- `POST /api/report/generate/{execution_id}` — 从执行历史生成报告

**缺陷相关：**
- `GET /api/defect` — 缺陷列表（分页）
- `POST /api/defect` — 创建缺陷
- `GET /api/defect/{id}` — 缺陷详情
- `PUT /api/defect/{id}` — 更新缺陷（含状态流转）
- `DELETE /api/defect/{id}` — 删除缺陷

**门禁相关：**
- `POST /api/quality-gate/evaluate` — 根据报告和缺陷计算门禁
- `GET /api/quality-gate/rules` — 门禁规则列表
- `POST /api/quality-gate/rules` — 创建门禁规则
- `PUT /api/quality-gate/rules/{id}` — 更新门禁规则
- `DELETE /api/quality-gate/rules/{id}` — 删除门禁规则

---

## 3. 任务拆解

### 阶段一：后端模型 & Schema

#### Task 1: 创建 Report / Defect / QualityGate 模型
- **文件：** `backend/app/models/report.py`
- **验证：** `python -c "from app.models.report import Report, Defect, QualityGate; print('OK')"`

#### Task 2: 创建 Report / Defect / QualityGate Pydantic Schemas
- **文件：** `backend/app/schemas/report.py`
- **验证：** `python -c "from app.schemas.report import *; print('OK')"`

### 阶段二：后端 Repository

#### Task 3: 创建 ReportRepository
- **文件：** `backend/app/repositories/report_repository.py`
- **内容：** 报告 CRUD，按 execution_id 查询，生成报告（聚合统计数据）
- **验证：** `pytest tests/repositories/test_report_repository.py -v`

#### Task 4: 创建 DefectRepository
- **文件：** `backend/app/repositories/defect_repository.py`
- **内容：** 缺陷 CRUD，状态流转验证，按 severity/priority 筛选
- **验证：** `pytest tests/repositories/test_defect_repository.py -v`

#### Task 5: 创建 QualityGateRepository
- **文件：** `backend/app/repositories/quality_gate_repository.py`
- **内容：** 门禁规则 CRUD，门禁计算逻辑
- **验证：** `pytest tests/repositories/test_quality_gate_repository.py -v`

### 阶段三：后端 Service

#### Task 6: 创建 ReportService（含报告生成逻辑）
- **文件：** `backend/app/services/report_service.py`
- **内容：**
  - `generate_report(execution_id)` — 从 ExecutionRun 聚合数据生成报告
  - `get_report(id)` — 报告详情
  - `list_reports()` — 分页列表
- **验证：** `pytest tests/services/test_report_service.py -v`

#### Task 7: 创建 DefectService（含状态流转逻辑）
- **文件：** `backend/app/services/defect_service.py`
- **内容：**
  - 状态机：open → confirmed → fixed → verified / wont_fix
  - 严重度/优先级更新
  - 与 case/scenario 关联
- **验证：** `pytest tests/services/test_defect_service.py -v`

#### Task 8: 创建 QualityGateService（含门禁计算逻辑）
- **文件：** `backend/app/services/quality_gate_service.py`
- **内容：**
  - `evaluate(report_id, defect_ids)` — 计算门禁通过/警告/阻断
  - 门禁规则：pass_rate < threshold → block，fail_count > threshold → warn
  - 高危缺陷存在 → block
- **验证：** `pytest tests/services/test_quality_gate_service.py -v`

### 阶段四：后端 Router

#### Task 9: 创建 report.py Router
- **文件：** `backend/app/routers/report.py`
- **内容：** 报告 + 缺陷 + 门禁 所有端点
- **验证：** `curl http://localhost:8000/docs` 确认路由

### 阶段五：前端 API 封装

#### Task 10: 创建 report.js API 封装
- **文件：** `frontend/src/views/report/api/report.js`
- **内容：** 报告列表/详情、缺陷 CRUD、门禁规则

#### Task 11: 创建 reportStore
- **文件：** `frontend/src/stores/reportStore.js`

### 阶段六：前端页面

#### Task 12: 创建 ReportList.vue
- **文件：** `frontend/src/views/report/ReportList.vue`
- **内容：** 报告列表（表格），执行时间、通过率、缺陷数

#### Task 13: 创建 ReportDetail.vue
- **文件：** `frontend/src/views/report/ReportDetail.vue`
- **内容：** 报告详情（通过率图、失败分布、步骤结果）

#### Task 14: 创建 DefectList.vue
- **文件：** `frontend/src/views/report/DefectList.vue`
- **内容：** 缺陷表格（状态/严重度/优先级），筛选，状态流转按钮

#### Task 15: 创建 DefectForm.vue（新建/编辑缺陷抽屉）
- **文件：** `frontend/src/views/report/DefectForm.vue`
- **内容：** 新建缺陷表单，关联 case/scenario

#### Task 16: 创建 QualityGate.vue
- **文件：** `frontend/src/views/report/QualityGate.vue`
- **内容：** 门禁规则列表，添加/编辑/删除规则，门禁状态展示

#### Task 17: 路由注册
- **文件：** `frontend/src/router/index.js`
- **内容：** `/report`, `/report/:id`, `/defect`, `/quality-gate`

### 阶段七：集成测试

#### Task 18: 后端核心链路测试
- **文件：** `backend/tests/routers/test_report.py`
- **覆盖：** 执行历史 → 生成报告 → 创建缺陷 → 门禁评估
- **验证：** `pytest tests/routers/test_report.py -v` 全绿

#### Task 19: 前端集成验证
- **验证清单：**
  - [ ] 执行完成 → 自动生成报告
  - [ ] 查看报告 → 显示统计数据
  - [ ] 失败用例 → 创建缺陷
  - [ ] 缺陷状态流转正确
  - [ ] 门禁评估 → 给出放行/阻断结果

---

## 4. 验收标准检查表

| 检查项 | 标准 |
|--------|------|
| 报告生成 | 从 ExecutionRun 自动聚合数据 |
| 报告列表 | 分页 + 按 execution_id 筛选 |
| 缺陷 CRUD | 状态机正确流转 |
| 缺陷关联 | 可关联 case + scenario |
| 门禁计算 | pass_rate + fail_count + 高危缺陷三重判断 |
| 门禁规则 | 可配置阈值 |
| 前端统计图 | 通过率/失败分布可视化（el-progress + 自定义图表） |
| 权限编码 | 所有操作有 permission_code |
| 测试覆盖 | 核心链路有 pytest 测试 |
