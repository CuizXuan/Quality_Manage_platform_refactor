# 质量管理闭环第一阶段：场景执行报告、门禁评估与测试环境

## 任务目标

请修复当前质量管理平台最核心的闭环缺口，让“场景执行 -> 自动生成报告 -> 报告一键评估质量门禁 -> 测试可回归验证”形成第一阶段可用闭环。

本任务只处理闭环地基，不做质量趋势、AI 建议回写、通知集成、测试计划等扩展能力。

## 背景说明

Codex 审查 `.ai/results/2026-05-23-full-system-e2e-quality-audit-result.md` 后确认：

1. 当前场景执行链路有 API 和前端入口，但执行完成后没有自动生成测试报告。
2. 当前质量门禁是规则引擎，可接收用户手工输入指标评估，但没有从报告或执行记录自动聚合指标的一键评估入口。
3. 后端存在测试文件，但测试环境不可复现：
   - 当前机器有 pytest，但 `python -m pytest backend\tests --collect-only` 被 `backend/pytest.ini` 编码/解析问题阻塞。
   - `backend/requirements.txt` 未声明 pytest。

本次目标是优先补齐质量闭环地基，使后续缺陷、趋势、AI 总结和门禁都能基于真实执行数据继续演进。

## 必读文件

- `AGENTS.md`
- `CLAUDE.md`
- `.ai/INDEX.md`
- `.ai/results/2026-05-23-full-system-e2e-quality-audit-result.md`
- `backend/app/routers/scenario.py`
- `backend/app/services/scenario_service.py`
- `backend/app/models/scenario.py`
- `backend/app/repositories/execution_repository.py`
- `backend/app/routers/report.py`
- `backend/app/services/report_service.py`
- `backend/app/repositories/report_repository.py`
- `backend/app/services/quality_gate_service.py`
- `backend/app/repositories/quality_gate_repository.py`
- `backend/app/models/report.py`
- `backend/app/schemas/report.py`
- `frontend/src/api/report.js`
- `frontend/src/stores/reportStore.js`
- `frontend/src/views/report/ReportList.vue`
- `frontend/src/views/report/ReportDetail.vue`
- `frontend/src/views/report/QualityGate.vue`
- `backend/requirements.txt`
- `backend/pytest.ini`
- `backend/tests/models/test_scenario.py`
- `backend/tests/services/test_ai_service.py`

如果路径与当前项目实际结构不一致，请先用 `rg --files` 查找真实文件，不要凭记忆改。

## 允许修改范围

后端：

- `backend/app/routers/scenario.py`
- `backend/app/services/scenario_service.py`
- `backend/app/repositories/execution_repository.py`
- `backend/app/routers/report.py`
- `backend/app/services/report_service.py`
- `backend/app/repositories/report_repository.py`
- `backend/app/services/quality_gate_service.py`
- `backend/app/repositories/quality_gate_repository.py`
- `backend/app/models/report.py`
- `backend/app/models/scenario.py`
- `backend/app/schemas/report.py`
- `backend/requirements.txt`
- `backend/pytest.ini`
- `backend/tests/`

前端：

- `frontend/src/api/report.js`
- `frontend/src/stores/reportStore.js`
- `frontend/src/views/report/ReportDetail.vue`
- `frontend/src/views/report/QualityGate.vue`
- 如报告详情页依赖路由或列表入口，可最小范围修改 `frontend/src/router/index.js`、`frontend/src/views/report/ReportList.vue`

文档/结果：

- 可更新 `.ai/results/2026-05-23-quality-loop-foundation-result.md`

## 禁止事项

- 不做无关 UI 重构。
- 不改动缺陷中心、AI 中枢、系统管理等无关模块。
- 不引入大型新依赖。
- 不改变已有公开 API 的响应结构，除非新增字段向后兼容。
- 不删除现有测试、数据文件或数据库文件。
- 不把用户手工输入指标当作“自动门禁闭环”。
- 不用“端点存在”替代真实验证。

## 实现要求

### 一、场景执行完成后自动生成报告

请在场景执行完成后自动创建 Report。

要求：

- 场景执行成功或失败后，都应沉淀一条报告记录。
- 报告应能关联执行记录和场景，至少包含：
  - `report_type`
  - `target_id`
  - `target_name`
  - `summary`
  - `metrics`
  - `executed_at`
  - `duration_ms`
  - `triggered_by`
- `summary` 至少包含：
  - `total`
  - `passed`
  - `failed`
  - `skipped`
  - `pass_rate`
- `metrics` 可包含：
  - `run_id`
  - `scenario_id`
  - `status`
  - `duration_ms`
  - `step_results` 或步骤摘要
- 如果当前 `ExecutionRun.summary` 已存储步骤信息，请复用；如果没有，按当前模型能提供的数据生成最小可信报告。
- 报告生成逻辑应放在 service 层，避免路由层堆业务逻辑。
- 如果报告已存在，避免重复创建；可按 `run_id` 或 `metrics.run_id` 做幂等判断。

### 二、报告详情页一键评估质量门禁

请补齐“从报告自动聚合指标 -> 调用质量门禁评估”的入口。

后端要求：

- 提供一个基于报告的门禁评估能力，建议新增接口之一：
  - `POST /api/reports/{report_id}/quality-gates/evaluate`
  - 或 `POST /api/reports/{report_id}/evaluate-gates`
- 该接口应从 Report 的 `summary` 和 `metrics` 自动聚合门禁指标，而不是要求前端手工传 `pass_rate`。
- 至少聚合：
  - `pass_rate`
  - `test_pass_rate`
  - `failed`
  - `defect_count`（如当前无法从缺陷表关联报告，可先为 0，并在注释/结果中说明）
  - `critical_defects`（如当前无法关联，可先为 0）
  - `avg_duration` 或 `duration_ms`
- 调用已有 `QualityGateService.evaluate_all_gates_for_execution()` 或合理扩展 service。
- 返回所有启用门禁的评估结果。

前端要求：

- 在 `ReportDetail.vue` 增加“评估门禁”按钮或清晰入口。
- 点击后自动使用当前报告数据发起评估。
- 展示评估结果，至少包括：
  - 门禁名称
  - 总体结果：pass/fail/skipped
  - 每条条件的实际值、阈值、结果
- 不要求用户手工输入 pass_rate 等指标。
- 加载、失败、空结果状态要有中文提示。

### 三、修复 pytest 测试环境可复现性

请修复测试收集阻塞。

要求：

- `backend/requirements.txt` 添加测试所需最小依赖：
  - `pytest`
  - 如果现有测试需要，再补 `pytest-asyncio`、`httpx` 等，但不要无脑加大型依赖。
- 修复 `backend/pytest.ini` 编码/解析问题，确保在 Windows 环境下不会因 GBK 解码失败。
- 注意 `backend/pytest.ini` 当前包含中文注释，必须保证 pytest 能正确读取。
- 如果 pytest 不支持指定 ini 编码，请将配置文件保存为当前环境可读的 UTF-8 无 BOM或 ASCII 兼容内容；必要时减少中文注释。
- 保持测试路径与执行命令一致。

### 四、补充核心回归测试

请补充最小但有价值的测试，覆盖本次闭环。

建议测试：

- `ReportService.build_summary()` 能正确计算通过率。
- 场景执行报告生成逻辑能从 ExecutionRun/场景数据生成 Report。
- 基于报告自动聚合质量门禁指标。
- `QualityGateService` 能正确评估 pass/fail/skipped。

测试要求：

- 优先使用内存 SQLite 或现有测试 fixture。
- 不依赖真实网络请求。
- 不依赖真实 AI 服务。
- 测试命名清晰，中文注释可以有，但文件必须能被 pytest 正常读取。

## 验收标准

- 执行场景后能自动产生报告记录。
- 报告详情页能一键评估质量门禁，不需要用户手工输入指标。
- 门禁评估结果能在前端清楚展示。
- `backend/requirements.txt` 声明 pytest。
- `python -m pytest backend/tests --collect-only` 能通过。
- 相关新增/修改测试能通过。
- `cd frontend && npm run build` 能通过。
- 所有用户可见文案、总结和测试结果必须使用中文。

## 验证方式

请至少运行：

```text
python -m pytest backend/tests --collect-only
python -m pytest backend/tests
cd frontend && npm run build
```

如果能启动服务，请额外手工验证：

```text
登录系统
进入 /scenario
创建或选择一个场景
执行场景
进入执行详情或报告列表
确认报告自动生成
进入报告详情
点击评估门禁
确认门禁结果展示
```

如果任何命令无法运行，必须说明：

- 执行命令。
- 失败原因。
- 是否是依赖、编码、数据库、配置或代码缺陷导致。
- 对本任务验收的影响。

## Claude 输出要求

结束时必须用中文汇报：

- 修改了哪些文件。
- 场景执行自动报告如何实现。
- 报告一键门禁评估如何实现。
- pytest 阻塞如何修复。
- 已运行的测试/构建命令及结果。
- 未完成内容和剩余风险。

建议同步写入：

- `.ai/results/2026-05-23-quality-loop-foundation-result.md`
