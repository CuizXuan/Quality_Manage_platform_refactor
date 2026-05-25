# 全系统功能审计结果返工要求

## 审查目标

请基于 Codex 对 `.ai/results/2026-05-23-full-system-e2e-quality-audit-result.md` 的复核结论，修订并补充全系统功能串联测试结果。

本次不要直接修改业务代码，优先修正审计结论、补充真实验证证据，并把“代码存在”与“功能可用”明确区分开。

## 原始结果文件

- `.ai/results/2026-05-23-full-system-e2e-quality-audit-result.md`

## 必须复核的问题

### 1. 后端测试结论不准确

原报告写到：

- “pytest 未安装”
- “backend/tests/ 仅 models/services 目录，无测试文件”

Codex 复核发现：

- `backend/tests/services/test_ai_service.py` 存在。
- `backend/tests/models/test_scenario.py` 存在。
- 当前环境可以启动 `python -m pytest`，但在读取 `backend/pytest.ini` 时出现编码错误：

```text
UnicodeDecodeError: 'gbk' codec can't decode byte 0x80 ...
```

同时：

- `backend/requirements.txt` 未声明 `pytest`。
- 需要判断这是依赖声明缺失、配置文件编码问题，还是测试环境问题。

请修订结论：

- 不能再写“测试目录为空”。
- 不能简单写“pytest 未安装”。
- 应改为“存在测试文件，但测试收集被 pytest.ini 编码问题阻塞；pytest 也未在 requirements 中声明，测试环境可复现性不足”。

### 2. 场景详情路由问题需要重新定级

原报告把以下问题定为 P0：

```javascript
path: '/scenario/:id',
redirect: '/scenario'
```

Codex 复核发现：

- `frontend/src/views/scenario/ScenarioList.vue` 通过 `ScenarioDetailDialog` 打开详情。
- 场景详情、步骤编排、执行场景、执行历史入口都在弹窗中。
- `/scenario/:id` 不能直达详情页是事实，但不必然导致用户无法使用详情和步骤编排。

请补测：

- 从 `/scenario` 列表点击行是否能打开详情弹窗。
- 新建场景后是否自动打开详情弹窗。
- 详情弹窗里是否能添加步骤。
- 详情弹窗里是否能执行场景。
- 执行后是否能跳转到执行详情。

请重新定级：

- 如果弹窗链路可用，则该问题应从 P0 降级为 P2 或“深链路体验缺失”。
- 如果弹窗链路不可用，才可继续作为 P0/P1 阻塞。

### 3. 缺陷中心样式结论疑似过期

原报告写：

- “DefectList.vue 灰色遮罩未修复”

Codex 复核当前文件发现：

- `frontend/src/views/report/DefectList.vue` 已加入流动网格背景。
- 页面级背景、筛选区、表格区均已有 CaseManagement/ScenarioList 风格样式。

请不要继续沿用旧截图结论。必须通过当前代码或浏览器实际截图验证：

- `/defect` 当前是否仍有灰色大块遮罩。
- 如果仍存在，具体是哪一层 DOM/CSS 造成。
- 如果不存在，应删除 Q-07 或标记为已解决。

### 4. 报告生成链路需要更准确表达

Codex 复核 `backend/app/services/report_service.py` 发现：

- `ReportService.create_report()` 只在请求数据包含 `execution_data` 时计算 summary。
- 当前没有看到“场景执行完成后自动生成报告”的明确调用链。

请补充验证：

- 场景执行服务是否在执行完成后创建 Report。
- 前端报告列表是否只展示手工创建报告，还是能展示执行生成报告。
- `Report.target_id` 是否能关联 ExecutionRun、Scenario 或 Case。

如果无法自动生成报告，应把“报告-执行闭环不完整”列为 P1，而不仅是“未验证”。

### 5. 质量门禁不是自动评估闭环

Codex 复核 `backend/app/routers/report.py` 和 `backend/app/services/quality_gate_service.py` 发现：

- 质量门禁评估接口读取的是请求体 `scope_filter` 中传入的指标。
- 暂未看到从 ExecutionRun 或 Report 自动聚合指标再评估的闭环。

请补充验证：

- 前端质量门禁页面是否需要用户手工输入指标。
- 是否存在从报告/执行记录一键评估门禁的入口。
- 门禁评估结果是否回写到报告、版本或执行记录。

如果没有自动聚合，应把它描述为“规则引擎可用，但质量门禁闭环不完整”。

### 6. AI 中枢上下文读取存在模型使用疑点

Codex 复核 `backend/app/routers/ai.py` 发现：

- `generate_assertions` 使用 `execution_step_id` 时查询的是 `ExecutionRun`。
- `analyze_failure` 也查询 `ExecutionRun`，但字段名和语义像是执行步骤。
- 需要确认模型里是否真的存在步骤级执行记录；如果没有，AI 失败分析只能基于 run 级数据。

请补充验证：

- `backend/app/models/scenario.py` 中是否有执行步骤模型。
- `ExecutionRun` 是否包含 `response_body`、`error_message` 等字段。
- 前端 FailureAnalyzer.vue 传入的是 run_id 还是 step_id。
- AI 采纳建议是否只标记 accepted，还是会回写到用例/断言/变体。

## 必须补充的验证

请尽量运行或补测：

```text
cd frontend && npm run build
python -m pytest backend/tests --collect-only
```

如果 pytest 仍因编码失败，请记录失败，并说明：

- 失败文件。
- 失败原因。
- 是否影响测试覆盖判断。
- 后续修复建议。

如果可以启动服务，请优先补测以下手工链路：

```text
登录
进入 /case 创建或确认一个可执行用例
进入 /scenario 新建场景
打开场景详情弹窗
添加步骤
执行场景
进入执行详情
检查是否产生报告
检查是否可创建/关联缺陷
检查质量门禁是否能基于执行/报告自动评估
```

## 修订后的输出要求

请更新或重写：

- `.ai/results/2026-05-23-full-system-e2e-quality-audit-result.md`

必须包含：

- “已实测通过”
- “代码存在但未实测”
- “实测阻塞”
- “产品闭环缺失”
- “原审计结论修正说明”

最终聊天回复必须用中文说明：

- 哪些原结论被修正。
- 哪些链路完成了真实验证。
- 哪些仍只是代码审查。
- 下一步最应该实现的 3 个任务。
