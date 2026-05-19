# 第四阶段：场景编排与执行历史 — 实施方案

> **依据文档：** `详细设计.md` §3 + `整合文档.md` §2.5 + `05_后端开发规范.md` + `06_前端组件与页面规范.md` + `07_开发顺序与验收标准.md` §4

## 1. 需求理解（Brainstorming 结果）

### 核心功能
- 场景（Scenario）是多个用例/变体的有序编排，代表真实业务链路
- 步骤（ScenarioStep）支持：排序、启停、失败策略（stop/continue/retry/skip）、超时、重试
- 步骤间可提取变量（JSONPath/Header/Cookie/状态码）并注入到后续步骤
- 执行记录保存完整快照（请求/响应/断言/变量/版本/日志）

### 关键数据结构

```
Scenario {
  id, name, description, status, version,
  created_by, created_at
}

ScenarioStep {
  id, scenario_id, case_id, variant_id?,
  name, sort_order, enabled,
  retry_count, timeout_ms,
  failure_strategy: 'stop'|'continue'|'retry'|'skip',
  extract_rules: Rule[], inject_rules: Rule[]
}

ExecutionRun {
  id, run_type: 'case'|'scenario',
  target_id, environment_id, status,
  started_at, finished_at, duration_ms, summary
}
```

### 验收标准（来自 07_开发顺序与验收标准.md §4）
- ✅ 可把多个用例组成场景
- ✅ 登录 token 可传递给后续步骤
- ✅ 场景执行有完整步骤结果

---

## 2. 技术方案

### 2.1 后端架构

**目录结构（遵循 05_后端开发规范.md）：**
```
backend/app/
├── models/
│   └── scenario.py          # Scenario, ScenarioStep, ExecutionRun 模型
├── schemas/
│   └── scenario.py          # Pydantic schemas
├── services/
│   └── scenario_service.py  # 业务逻辑
├── repositories/
│   ├── scenario_repository.py
│   └── execution_repository.py
├── routers/
│   └── scenario.py          # API 路由
```

**执行引擎核心逻辑：**
1. 按 `sort_order` 顺序获取步骤（只取 `enabled=True`）
2. 对每步：组装请求（基础用例配置 + 变体覆盖 + 前序步骤注入变量）→ 发送HTTP → 提取变量 → 按策略处理失败
3. 记录每步执行快照（request/response/assertion/extracts）
4. 全部完成或遇 stop 策略时，生成 ExecutionRun 报告

**变量提取规则（extract_rules）示例：**
```json
[
  {"type": "jsonpath", "source": "body", "expression": "$.data.token", "var_name": "auth_token"},
  {"type": "header", "source": "response", "expression": "X-Request-Id", "var_name": "request_id"},
  {"type": "status_code", "var_name": "http_status"}
]
```

**变量注入规则（inject_rules）示例：**
```json
[
  {"type": "header", "target": "Authorization", "expression": "Bearer {{auth_token}}"},
  {"type": "query", "target": "user_id", "expression": "{{user_id}}"}
]
```

### 2.2 前端架构（遵循 06_前端组件与页面规范.md）

**目录结构：**
```
frontend/src/
├── views/
│   └── scenario/
│       ├── ScenarioList.vue      # 场景列表
│       ├── ScenarioDetail.vue    # 场景详情 + 步骤编排
│       ├── ScenarioStepForm.vue  # 步骤编辑表单
│       ├── ExecutionHistory.vue  # 执行历史
│       ├── ExecutionDetail.vue   # 执行详情（步骤级）
│       └── api/
│           └── scenario.js       # API 封装
├── stores/
│   └── scenarioStore.js          # Pinia 状态
```

**页面布局（三栏或双栏，遵循规范使用 el-row/el-col）：**
- 方案A（三栏）：左侧场景列表 → 中间步骤编排 → 右侧步骤详情
- 方案B（双栏）：左侧场景列表 → 右侧步骤编排 + 详情 Tab

推荐**方案B**，减少复杂度，el-tabs 区分"步骤配置"和"执行历史"。

---

## 3. 任务拆解（2-5 分钟粒度）

### 阶段一：后端模型 & Schema

#### Task 1: 创建 Scenario/ScenarioStep/ExecutionRun 模型
- **文件：** `backend/app/models/scenario.py`
- **内容：** 三个 SQLAlchemy 模型，字段严格按详细设计
- **验证：** `python -c "from app.models.scenario import Scenario, ScenarioStep, ExecutionRun; print('OK')"`

#### Task 2: 创建 Scenario Pydantic Schemas
- **文件：** `backend/app/schemas/scenario.py`
- **内容：** ScenarioCreate, ScenarioUpdate, ScenarioResponse, ScenarioStepCreate, ScenarioStepUpdate, ExecutionRunResponse
- **验证：** `python -c "from app.schemas.scenario import *; print('OK')"`

### 阶段二：后端 Repository

#### Task 3: 创建 ScenarioRepository
- **文件：** `backend/app/repositories/scenario_repository.py`
- **内容：** CRUD 方法，按 sort_order 排序
- **验证：** `pytest tests/repositories/test_scenario_repository.py -v`

#### Task 4: 创建 ExecutionRepository
- **文件：** `backend/app/repositories/execution_repository.py`
- **内容：** 保存执行记录，按 run_type + target_id 查询历史
- **验证：** `pytest tests/repositories/test_execution_repository.py -v`

### 阶段三：后端 Service & 执行引擎

#### Task 5: 创建 ScenarioService（含执行引擎核心逻辑）
- **文件：** `backend/app/services/scenario_service.py`
- **内容：**
  - CRUD 方法
  - `_build_request()` — 组装请求（基础+变体覆盖+变量注入）
  - `_extract_vars()` — 执行变量提取
  - `_execute_step()` — 单步执行
  - `execute_scenario()` — 场景执行主流程
- **验证：** `pytest tests/services/test_scenario_service.py -v`

#### Task 6: 注册 router 到 main.py
- **文件：** `backend/app/main.py`
- **验证：** `curl http://localhost:8000/api/health` 确认服务正常

### 阶段四：后端 API Router

#### Task 7: 创建 scenario.py Router
- **文件：** `backend/app/routers/scenario.py`
- **API 端点：**
  - `POST /api/scenario` — 创建场景
  - `GET /api/scenario` — 列表（分页）
  - `GET /api/scenario/{id}` — 详情（含步骤）
  - `PUT /api/scenario/{id}` — 更新场景
  - `DELETE /api/scenario/{id}` — 删除场景
  - `POST /api/scenario/{id}/step` — 新增步骤
  - `PUT /api/scenario/{id}/step/{step_id}` — 更新步骤
  - `DELETE /api/scenario/{id}/step/{step_id}` — 删除步骤
  - `PUT /api/scenario/{id}/steps/reorder` — 批量更新排序
  - `POST /api/scenario/{id}/execute` — 执行场景
  - `GET /api/execution/{id}` — 执行历史详情
  - `GET /api/execution` — 执行历史列表
- **验证：** `curl http://localhost:8000/docs` 确认路由注册

### 阶段五：前端 API 封装

#### Task 8: 创建 scenario.js API 封装
- **文件：** `frontend/src/views/scenario/api/scenario.js`
- **内容：** 对应上述所有后端端点
- **验证：** `grep -c "api" frontend/src/views/scenario/api/scenario.js` ≥ 12

#### Task 9: 创建 scenarioStore
- **文件：** `frontend/src/stores/scenarioStore.js`
- **内容：** 场景列表、当前场景、步骤、的执行历史状态管理
- **验证：** 无 lint 错误

### 阶段六：前端页面组件

#### Task 10: 创建 ScenarioList.vue
- **文件：** `frontend/src/views/scenario/ScenarioList.vue`
- **内容：** 场景表格（名称/状态/创建时间/操作），搜索/筛选，新建按钮
- **遵循规范：** el-table + el-row/el-col 布局，CSS 变量，scoped
- **验证：** `npm run lint` 无错误

#### Task 11: 创建 ScenarioDetail.vue（步骤编排）
- **文件：** `frontend/src/views/scenario/ScenarioDetail.vue`
- **内容：**
  - 场景信息编辑区（名称/描述/状态）
  - 步骤列表（拖拽排序，启用/停用开关，失败策略下拉，超时/重试配置）
  - 步骤新增按钮
  - el-tabs：步骤配置 / 执行历史
- **遵循规范：** 动态组件优先用 Vue 内置能力，其次 Element Plus
- **验证：** 功能测试（选择场景→加载步骤→拖拽排序→保存）

#### Task 12: 创建 ScenarioStepForm.vue（步骤编辑抽屉）
- **文件：** `frontend/src/views/scenario/ScenarioStepForm.vue`
- **内容：** 用例选择器、变体选择器、失败策略、超时、重试次数、变量提取规则、变量注入规则
- **遵循规范：** el-drawer + el-form，CSS 变量
- **验证：** 功能测试（打开抽屉→选择用例→填写规则→保存）

#### Task 13: 创建 ExecutionHistory.vue
- **文件：** `frontend/src/views/scenario/ExecutionHistory.vue`
- **内容：** 执行历史列表（场景名/状态/开始时间/耗时/操作），分页
- **验证：** 功能测试

#### Task 14: 创建 ExecutionDetail.vue（执行详情）
- **文件：** `frontend/src/views/scenario/ExecutionDetail.vue`
- **内容：** 步骤级执行结果（每步：请求/响应/断言/提取变量），可展开
- **遵循规范：** el-table 展开行，el-descriptions
- **验证：** 功能测试

#### Task 15: 路由注册
- **文件：** `frontend/src/router/index.js`
- **内容：** `/scenario` → ScenarioList.vue，`/scenario/:id` → ScenarioDetail.vue
- **验证：** 路由跳转正常

### 阶段七：集成测试

#### Task 16: 后端核心链路测试
- **文件：** `backend/tests/routers/test_scenario.py`
- **覆盖：** 创建场景 → 添加步骤 → 执行 → 查询历史
- **验证：** `pytest tests/routers/test_scenario.py -v` 全绿

#### Task 17: 前端集成验证
- **验证清单：**
  - [ ] 创建场景 → 出现在列表
  - [ ] 添加步骤 → 步骤显示在编排区
  - [ ] 拖拽排序 → sort_order 更新
  - [ ] 执行场景 → 步骤依次执行，变量传递生效
  - [ ] 执行历史 → 生成记录，点击可看详情

### 阶段八：收尾

#### Task 18: 清理与文档
- 检查 AGENTS.md 是否需要更新（如果项目结构有变化）
- 确认 commit 记录清晰（每任务一 commit）

---

## 4. 验收标准检查表（严格执行）

| 检查项 | 标准 |
|--------|------|
| 场景 CRUD | POST/GET/PUT/DELETE 全通 |
| 步骤 CRUD | 增删改 + 排序全通 |
| 变量提取 | JSONPath + Header + StatusCode 全通 |
| 变量注入 | 后续步骤能使用前序提取的变量 |
| 执行引擎 | stop/continue/retry/skip 策略正确 |
| 执行快照 | 每步 request/response/assertion 全量保存 |
| 执行历史 | 可分页查询，可查看步骤级详情 |
| 前端布局 | 符合 CSS 变量规范，el-row/el-col 布局 |
| 前后端联调 | 场景执行链路完全打通 |
| 权限编码 | 所有操作有 permission_code |
| 测试覆盖 | 核心链路有 pytest 测试 |

---

## 5. 注意事项（踩坑预警）

1. **执行引擎必须是同步的**（FastAPI background task 可选，但 MVP 同步即可）
2. **变量注入时优先顺序**：变体 override_params > 前序步骤注入 > 基础用例配置
3. **retry 策略**：需要记录重试次数，超过 `retry_count` 才判定失败
4. **sort_order 更新**：批量更新时使用 CASE WHEN 批量 SQL，避免 N 次 update
5. **ExecutionRun.status**：pending / running / passed / failed / stopped
6. **JWT Token 传递**：登录场景在步骤1提取 token，后续步骤自动注入 Authorization header
7. **超时处理**：使用 `httpx` 的 `timeout` 参数，捕获 `TimeoutException`
