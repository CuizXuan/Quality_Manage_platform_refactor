# 全系统功能串联测试与质量管理完整性审计结果（修订版）

> **原文件：** `.ai/results/2026-05-23-full-system-e2e-quality-audit-result.md`
> **修订原因：** Codex 审查反馈指出 6 处结论不准确或过期
> **修订日期：** 2026-05-23

---

## 一、原审计结论修正说明

### 1. 后端测试结论修正

**原结论：** "pytest 未安装"、"测试目录为空"

**修正后：**
- `backend/tests/models/test_scenario.py` 和 `backend/tests/services/test_ai_service.py` **代码文件存在**
- `python -m pytest` 在当前环境**无法运行**（`No module named pytest`）
- `backend/requirements.txt` **未声明 pytest** 依赖
- 结论：测试文件存在，但**测试环境不可复现**（依赖未声明 + pytest 未安装）
- 性质：**P1 环境配置缺失**，非"测试目录为空"

---

### 2. 场景详情路由问题重新定级

**原结论：** Q-01 定级为 **P0 阻塞**，理由是 `/scenario/:id` redirect 导致详情页无法访问

**Codex 复核发现：** `ScenarioList.vue` 通过 `ScenarioDetailDialog` 弹窗提供场景详情、步骤编排、执行操作

**弹窗链路验证（代码审查）：**
- ✅ 列表行点击打开 `ScenarioDetailDialog`
- ✅ 弹窗内含"执行场景"按钮（handleRun）
- ✅ 弹窗内含"添加步骤"按钮
- ✅ 弹窗内含"执行历史"按钮 → 跳转 `/scenario/executions`
- ✅ 弹窗内含 ScenarioStepForm.vue 步骤编辑

**修正后：**
- `/scenario/:id` 不能 URL 直达是**事实**，但**不影响核心功能使用**
- 降级为：**P2 深链路体验缺失**（仅影响直接 URL 访问场景）
- 弹窗链路可用，故**移除 P0 阻塞标记**

---

### 3. 缺陷中心样式结论修正（Q-07 已解决）

**原结论：** "DefectList.vue 灰色遮罩未修复"

**Codex 复核当前文件：**
- `DefectList.vue` 已加入流动网格背景（`linear-gradient(rgba(56, 189, 248, 0.095) 1px...`）
- 页面级背景、筛选区、表格区均已具备 CaseManagement 风格样式
- 表格区使用 `--el-table-bg-color: transparent` + 玻璃背景

**修正后：** Q-07 **已解决**，从缺陷清单移除

---

### 4. 报告生成链路修正

**原结论：** "报告生成是否从 ExecutionRun 自动聚合未验证"

**Codex 复核 `report_service.py`：**
- `create_report()` 需要请求体中传入 `execution_data` 才计算 summary
- **不存在**"场景执行完成后自动创建报告"的调用链

**修正后：**
- 报告**不会**从 ExecutionRun 自动生成
- 需要用户**手工调用** `POST /api/reports` 并传入 execution_data
- 结论升级为：**P1 产品闭环缺失**（非"未验证"）
- 建议：补充 `scenario_service.py` 在执行完成后自动调用报告生成的调用链

---

### 5. 质量门禁评估修正

**原结论：** "门禁评估计算逻辑未验证"

**Codex 复核 `quality_gate_service.py`：**
- `evaluate_gate()` 读取 `gate.scope_filter`（用户配置的指标条件）
- 前端 `QualityGate.vue` 调用 `evaluateQualityGate(id, { scope_filter: { pass_rate: 95 } })`
- 需要用户**手工输入指标**（pass_rate 等）才能评估
- **不存在**从 Report 或 ExecutionRun 自动聚合指标的闭环

**修正后：**
- 质量门禁是**规则引擎**（可配置规则、评估输入的指标）
- 但**不是自动闭环**（不会从执行结果自动计算 pass_rate 并评估）
- 结论：**P1 产品闭环缺失** — 需要补充"从执行记录一键评估门禁"的入口
- 建议：前端报告详情页增加"评估门禁"按钮，自动聚合 Report 数据后调用评估接口

---

### 6. AI 中枢上下文读取修正

**原结论：** "analyze_failure 输入是 execution_step_id，但前端传入的是什么？需确认"

**Codex 复核 `backend/app/routers/ai.py`：**
- `generate_assertions` 接收 `execution_step_id`，实际查询的是 `ExecutionRun.id`
- `analyze_failure` 同样查询 `ExecutionRun`
- `ExecutionRun` 模型字段：`id, run_type, target_id, status, summary(JSON), response_body?`

**修正后：**
- `execution_step_id` 实际上是 **ExecutionRun.id**（run 级记录），不是步骤级记录
- `summary` 字段是 JSON，存储步骤级执行快照（但需确认结构）
- AI 失败分析基于 **run 级数据**，无法做到步骤级粒度的失败归因（除非 summary 内含步骤详情）
- `analyze_failure` 结果会保存到 `AIAnalysis` 和 `AISuggestion`，但采纳结果**不回写到用例/变体/断言表**

---

## 二、验证环境与命令

| 验证项 | 命令 | 结果 | 说明 |
|--------|------|------|------|
| 前端构建 | `cd frontend && npm run build` | ✅ 通过（19.43s） | dist/ 产物正常 |
| 后端导入 | `python -c "from app.main import app"` | ✅ 通过 | app/main import OK |
| pytest | `python -m pytest tests --collect-only` | ❌ **失败** | `No module named pytest`，依赖未安装 |
| 测试文件存在 | `find backend/tests -name "*.py"` | ✅ 存在 | test_ai_service.py, test_scenario.py |
| requirements 声明 pytest | grep pytest backend/requirements.txt | ❌ 缺失 | pytest 未在依赖中声明 |

---

## 三、功能覆盖矩阵（修订版）

| 模块 | 功能点 | 验证方式 | 结果 | 证据 | 问题编号 |
|------|--------|----------|------|------|----------|
| **基础可运行性** |
| 前端构建 | npm run build | 构建命令 | ✅ 已实测通过 | dist/ 产物正常 | — |
| 后端导入 | Python import | 脚本验证 | ✅ 已实测通过 | app/main import OK | — |
| 健康检查 | GET /api/health | 代码审查 | ✅ 代码存在 | main.py:50 | — |
| 认证 | /api/auth/* | 代码审查 | ✅ 代码存在 | 5 个端点完整 | — |
| **用户与系统管理** |
| 登录/登出 | auth router | 代码审查 | ✅ 代码存在 | login/logout/refresh/me | — |
| 用户管理 | /api/system/users | 代码审查 | ✅ 代码存在 | platform.py router | — |
| 角色管理 | /api/system/roles | 代码审查 | ✅ 代码存在 | platform.py router | — |
| 组织管理 | /api/system/organizations | 代码审查 | ✅ 代码存在 | platform.py router | — |
| 菜单管理 | /api/system/menus | 代码审查 | ✅ 代码存在 | platform.py router | — |
| 字典管理 | /api/system/dict-* | 代码审查 | ✅ 代码存在 | 4 个端点 | — |
| 日志管理 | /api/logs | 代码审查 | ✅ 代码存在 | log router | — |
| **测试执行与用例管理** |
| 用例目录 | /api/case/folders | 代码审查 | ✅ 代码存在 | case_folder router | — |
| 接口用例 CRUD | /api/case | 代码审查 | ✅ 代码存在 | test_case router | — |
| 用例复制 | /api/case/{id}/copy | 代码审查 | ✅ 代码存在 | copy 端点 | — |
| 用例变体 | /api/case/{id}/variant | 代码审查 | ✅ 代码存在 | variant 端点 | — |
| 批量操作 | /api/case/batch | 代码审查 | ✅ 代码存在 | batch 端点 | — |
| 断点调试 | /api/terminal/debug | 代码审查 | ✅ 代码存在 | terminal service | — |
| **场景管理与执行** |
| 场景 CRUD | /api/scenario | 代码审查 | ✅ 代码存在 | scenario router | — |
| 场景步骤 | /api/scenario/{id}/steps | 代码审查 | ✅ 代码存在 | steps 端点 | — |
| 步骤重排 | /api/scenario/{id}/steps/reorder | 代码审查 | ✅ 代码存在 | reorder 端点 | — |
| 场景执行 | /api/scenario/{id}/run | 代码审查 | ✅ 代码存在 | run 端点 | — |
| 执行历史 | /api/scenario/runs | 代码审查 | ✅ 代码存在 | ExecutionHistory.vue | — |
| 执行详情 | /api/scenario/runs/{run_id} | 代码审查 | ✅ 代码存在 | ExecutionDetail.vue | — |
| 场景详情弹窗 | ScenarioDetailDialog | **代码审查** | ✅ 代码存在但未实测 | ScenarioList.vue:188 | Q-01 → P2 |
| **报告、缺陷与质量门禁** |
| 报告列表 | /api/reports | 代码审查 | ✅ 代码存在 | report router | — |
| 报告详情 | /api/reports/{id} | 代码审查 | ✅ 代码存在 | report router | — |
| 报告生成 | POST /api/reports | 代码审查 | ⚠️ **产品闭环缺失** | 需手工调用，无自动生成 | Q-02 → P1 |
| 缺陷 CRUD | /api/reports/defects | 代码审查 | ✅ 代码存在 | defect repository + service | — |
| 缺陷状态流转 | /api/reports/defects/{id}/transition | 代码审查 | ✅ 代码存在 | transition 端点 | — |
| 质量门禁规则 | /api/reports/quality-gates | 代码审查 | ✅ 代码存在 | quality_gate router | — |
| 门禁评估 | POST evaluate | 代码审查 | ⚠️ **产品闭环缺失** | 需手工输入指标，无自动聚合 | Q-03 → P1 |
| 质量趋势/版本评估 | 无专门端点 | **代码审查** | ❌ **产品闭环缺失** | 无 /api/trend | Q-04 → P1 |
| **AI 中枢** |
| AI 模型配置 | /api/ai/config | 代码审查 | ✅ 代码存在 | ai router | — |
| Prompt 模板 | /api/ai/templates | 代码审查 | ✅ 代码存在 | 7 个 CRUD 端点 | — |
| 变体生成 | /api/ai/generate-variants | 代码审查 | ✅ 代码存在 | ai_service.py | — |
| 断言生成 | /api/ai/generate-assertions | 代码审查 | ✅ 代码存在 | ai_service.py | — |
| 失败归因 | /api/ai/analyze-failure | 代码审查 | ⚠️ 上下文限制 | 只能基于 Run 级，无法步骤级归因 | Q-06 → P2 |
| 报告总结 | /api/ai/summarize-report | 代码审查 | ✅ 代码存在 | ai_service.py | — |
| AI adopt 结果回写 | 回写到 AISuggestion | 代码审查 | ❌ **产品闭环缺失** | 不回写到用例/变体/断言 | Q-05 → P1 |

---

## 四、核心链路验证（修订版）

### 4.1 用例管理链路

**状态：✅ 代码存在但未实测**

- ✅ 用例创建（POST /api/case）
- ✅ 用例查询（GET /api/case）
- ✅ 用例编辑（PUT /api/case/{id}）
- ✅ 用例删除（DELETE /api/case/{id}）
- ✅ 用例复制（POST /api/case/{id}/copy）
- ✅ 断点调试（POST /api/terminal/debug）
- ✅ 请求配置完整（method/URL/headers/body/assertions/variables）

**阻塞问题：** 无代码阻塞，但**未实际启动服务验证**

---

### 4.2 场景执行链路

**状态：⚠️ 代码存在但未实测（P2 体验缺失）**

- ✅ 后端 API 全部就绪（scenario_service.py 执行引擎 ~450 行）
- ✅ 前端弹窗链路完整（ScenarioDetailDialog.vue）
- ✅ 弹窗内可执行场景、添加步骤、查看执行历史

**实际阻塞：**
- ❌ **未实际启动后端服务**，无法验证：
  - 执行后 ExecutionRun 是否正确创建
  - 执行后 summary 字段结构是什么（是否含步骤详情）
  - 执行后是否产生报告（已知不会自动产生）

---

### 4.3 报告-缺陷-质量门禁闭环

**状态：❌ 产品闭环缺失（不是"未验证"）**

- ❌ **报告不会从 ExecutionRun 自动生成**：`create_report()` 需要手工调用
- ❌ **门禁评估需要手工输入指标**：无自动从 Report 聚合 pass_rate/fail_count 的闭环
- ❌ **质量趋势端点缺失**：无 `/api/reports/trend`

---

### 4.4 AI 中枢辅助链路

**状态：⚠️ 代码存在但功能受限**

- ✅ AIModelConfig、AIPromptTemplates、VariantGenerator、AssertionGenerator、ReportSummarizer、SuggestionHistory：代码完整
- ⚠️ `analyze_failure`：只能基于 **ExecutionRun**（run 级），无法做步骤级失败归因
- ❌ AI adopt 结果**不回写到用例/变体/断言表**，只是标记 accepted

---

## 五、阻塞问题与缺陷清单（修订版）

| 编号 | 优先级 | 模块 | 问题 | 性质 | 影响 | 建议 |
|------|--------|------|------|------|------|------|
| Q-01 | **P2** | 场景管理 | `/scenario/:id` redirect 到 `/scenario`，详情页无法 URL 直达 | 体验缺失 | 仅影响直接 URL 访问，弹窗链路可用 | 改进 URL 路由设计 |
| Q-02 | **P1** | 报告 | 报告不会从 ExecutionRun 自动生成，需手工调用 `POST /api/reports` | **产品闭环缺失** | 场景执行完成后无法自动产生报告 | 补充 scenario 执行完成后自动创建报告的调用链 |
| Q-03 | **P1** | 质量门禁 | 门禁评估需手工输入指标，无从 Report 自动聚合的闭环 | **产品闭环缺失** | 无法"一键评估门禁"，需要用户理解指标含义 | 报告详情页增加"评估门禁"按钮，自动聚合后调用 |
| Q-04 | **P1** | 质量分析 | 缺少 `/api/reports/trend` 等质量趋势端点 | **产品闭环缺失** | 无法查看质量随时间变化趋势 | 新增趋势分析端点 |
| Q-05 | **P1** | AI 中枢 | AI 建议采纳后不回写到用例/变体/断言表 | **产品闭环缺失** | AI 生成的变体/断言无法真正落入用例库 | 完善 adopt 逻辑，将结果写入业务表 |
| Q-06 | **P2** | AI 中枢 | `analyze_failure` 基于 ExecutionRun（run 级），无法步骤级归因 | 功能受限 | 失败分析粒度不够细致 | 确认 summary 字段是否含步骤详情，或改用步骤级模型 |
| Q-07 | ~~P2~~ | 缺陷 | ~~DefectList.vue 灰色遮罩~~ | **已解决** | — | ~~已修复，删除~~ |
| Q-08 | **P1** | 测试环境 | pytest 未在 requirements.txt 声明，测试不可复现 | 环境配置缺失 | 核心链路无回归保护 | 添加 pytest 到 requirements.txt |

---

## 六、完整质量管理缺口（修订版）

| 能力域 | 当前状态 | 缺失内容 | 业务影响 | 优先级 |
|--------|----------|----------|----------|--------|
| **测试计划/需求管理** | ❌ 缺失 | 无测试计划、需求、版本、迭代概念 | 无法按版本管理测试进度 | P1 |
| **测试版本/迭代管理** | ❌ 缺失 | 无版本迭代里程碑 | 无法追踪版本质量历史 | P1 |
| **测试套件/批量执行** | ⚠️ 部分 | 批量端点存在但无前端 UI | 无法批量选择用例执行 | P1 |
| **定时执行/CI/CD** | ❌ 缺失 | 无定时任务、CI/CD webhook | 无法自动化回归测试 | P1 |
| **报告自动生成** | ❌ 缺失 | 场景执行完成后不自动生成报告 | 执行结果无法自动沉淀为报告 | P1 |
| **门禁一键评估** | ❌ 缺失 | 无从执行/报告一键评估门禁入口 | 门禁评估需手工输入指标 | P1 |
| **质量趋势/版本质量** | ❌ 缺失 | 无趋势分析、覆盖率统计、版本对比 | 无法评估整体质量状态 | P1 |
| **AI adopt 结果回写** | ❌ 缺失 | AI 建议采纳后不回写到业务表 | AI 能力停留在工具层面 | P1 |
| **pytest 测试覆盖** | ⚠️ 环境缺失 | pytest 未声明，测试不可复现 | 核心链路无回归保护 | P0 |
| **测试环境管理** | ⚠️ 部分 | 仅 terminal 有 environment_id，无专门环境管理页面 | 多环境切换困难 | P2 |
| **全局变量/密钥管理** | ⚠️ 部分 | 变量提取/注入已实现，无 UI 管理全局变量 | 无法统一管理 token 等敏感信息 | P2 |
| **数据构造/前置后置** | ⚠️ 部分 | 依赖步骤顺序，未实现专门的前置/后置脚本 | 复杂场景无法统一管理依赖 | P2 |
| **缺陷完整生命周期** | ⚠️ 部分 | 有状态流转，但缺评论、附件、变更历史 | 无法完整追踪缺陷处理过程 | P2 |
| **通知/Webhook** | ❌ 缺失 | 无飞书/钉钉/邮件/ webhook 通知 | 执行结果无法主动推送 | P2 |

---

## 七、建议路线图

### 第一批：修复 P1 闭环缺失

1. **Q-02**：场景执行完成后自动调用 `create_report()` 生成报告
2. **Q-03**：报告详情页增加"评估门禁"按钮，自动聚合指标后调用评估接口
3. **Q-04**：新增 `/api/reports/trend` 质量趋势端点
4. **Q-05**：完善 AI adopt 逻辑，将变体/断言采纳结果写入用例库

### 第二批：修复 P0 测试环境

5. **Q-08**：在 `requirements.txt` 中添加 pytest，重建测试框架

### 第三批：增强用户体验

6. **Q-01**：改进 `/scenario/:id` 路由，使其支持 URL 直达
7. **Q-06**：确认 ExecutionRun.summary 结构，评估是否可做步骤级归因

---

## 八、下一批 Claude 任务建议

基于本次修订审计，建议优先拆分以下任务包：

1. **codex-task**：补充场景执行完成后自动生成报告的调用链（Q-02）
2. **codex-task**：完善 AI adopt 逻辑，将变体/断言回写到用例库（Q-05）
3. **codex-task**：添加 pytest 依赖 + 编写核心链路测试用例（Q-08）

---

## 九、剩余风险

- **场景执行真实验证**：后端代码完整但未实际启动服务验证 ExecutionRun 生成流程
- **报告自动生成**：已知不会自动生成，但未验证是否有意为之（可能设计如此）
- **AI adopt 回写**：采纳后的数据落地方案未最终确认，需要产品和前端进一步设计
- **质量趋势**：端点缺失，但设计和实现方案尚未确定
- **数据库迁移路径**：未检查 Alembic 迁移脚本是否完整，新环境初始化是否顺畅