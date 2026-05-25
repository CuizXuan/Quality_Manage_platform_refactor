# 成熟质量平台基础能力五：质量分析看板与发布门禁

## 任务目标

请在现有报告、缺陷、门禁基础上，新增质量分析看板和发布门禁视图，用于回答成熟质量平台最核心的问题：

```text
当前版本能不能发？
风险在哪里？
哪些需求没覆盖？
哪些模块质量最差？
通过率和缺陷趋势如何？
```

## 背景说明

当前系统有报告中心、缺陷中心、质量门禁，但还缺少质量趋势和发布视角。成熟平台通常要有：

- 版本质量评分。
- 通过率趋势。
- 缺陷趋势。
- 需求覆盖率。
- 门禁结果。
- 发布结论。

## 必读文件

- `backend/app/routers/report.py`
- `backend/app/services/report_service.py`
- `backend/app/services/defect_service.py`
- `backend/app/services/quality_gate_service.py`
- `backend/app/models/report.py`
- `frontend/src/views/report/ReportList.vue`
- `frontend/src/views/report/QualityGate.vue`
- `.ai/tasks/2026-05-25-quality-platform-foundation-project-version-requirement.md`

## 允许修改范围

- `backend/app/routers/quality_analytics.py`
- `backend/app/services/quality_analytics_service.py`
- `backend/app/schemas/quality_analytics.py`
- `backend/app/main.py`
- `frontend/src/api/qualityAnalytics.js`
- `frontend/src/stores/qualityAnalyticsStore.js`
- `frontend/src/views/qualityAnalytics/**`
- `frontend/src/router/index.js`
- `backend/app/services/platform_seed.py`

## 禁止事项

- 不删除现有报告中心、缺陷中心、质量门禁。
- 不造假数据。
- 没有项目/版本字段时要兼容为空，并提示统计范围有限。

## 实现要求

### 一、后端 API

前缀：

```text
/api/quality-analytics
```

接口：

```text
GET /api/quality-analytics/overview
GET /api/quality-analytics/trends
GET /api/quality-analytics/requirement-coverage
GET /api/quality-analytics/defect-distribution
GET /api/quality-analytics/release-gate
```

支持筛选：

- project_id
- version_id
- iteration_id
- start_date
- end_date

### 二、指标

至少计算：

- 报告数。
- 执行次数。
- 平均通过率。
- 失败数。
- 缺陷总数。
- P0/P1 缺陷数。
- 未关闭缺陷数。
- 需求覆盖率。
- 门禁通过/失败状态。
- 简单质量评分。

### 三、前端页面

新增路由：

```text
/quality-analytics
```

菜单：

```text
质量看板
```

页面：

- 顶部筛选栏：项目、版本、迭代、时间范围。
- 质量概览卡片。
- 趋势图。
- 缺陷分布。
- 需求覆盖。
- 发布门禁结论。

图表如当前项目没有图表库，第一阶段可用表格和轻量进度条，不强制引入 ECharts。

样式必须贴合现有模块。

## 验收标准

- 能查看质量概览。
- 能按项目/版本/迭代筛选。
- 能看到发布门禁结论。
- 数据来自报告、缺陷、门禁、需求关联，不是前端 mock。
- 前端 build 通过。

## Claude 输出要求

中文汇报：

- 新增了哪些指标。
- 质量评分如何计算。
- 发布门禁如何判断。
- 测试和构建结果。
- 剩余风险。

请同步写入：

- `.ai/results/2026-05-25-quality-analytics-release-gate-result.md`
