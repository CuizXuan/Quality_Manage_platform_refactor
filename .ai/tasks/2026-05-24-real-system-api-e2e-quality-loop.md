# 真实系统接口 E2E 验证：平台测试平台自己的质量闭环

## 任务目标

请用当前系统自己的真实后端接口，验证完整质量链路：

```text
启动后端服务
登录系统
创建真实 API 用例，目标 URL 指向本系统接口
创建场景
添加场景步骤
执行场景
等待执行完成
确认自动生成报告
基于报告一键评估质量门禁
输出真实接口请求、响应和结论
```

本任务重点不是 mock，也不是只看代码，而是让平台把“本系统自己的接口”当作被测系统，跑出一条真实闭环。

## 前置说明

当前质量闭环第一阶段实现仍有待修复的问题，详见：

- `.ai/reviews/2026-05-23-quality-loop-foundation-review.md`

开始真实 E2E 前，必须先确认这些问题已修复：

- 自动报告不能读取不存在的 `ExecutionRun.triggered_by`。
- 自动报告必须把 `summary.total_steps` 映射为报告 `summary.total`。
- 场景执行必须把每一步 `step_result` 写入 `summary["steps"]`。
- 根目录执行 `python -m pytest backend/tests --collect-only` 必须通过。

如果这些问题尚未修复，请先按 review 包完成修复，再继续真实接口验证。

## 必读文件

- `AGENTS.md`
- `CLAUDE.md`
- `.ai/INDEX.md`
- `.ai/tasks/2026-05-23-quality-loop-foundation.md`
- `.ai/reviews/2026-05-23-quality-loop-foundation-review.md`
- `backend/app/main.py`
- `backend/app/database.py`
- `backend/app/routers/platform_auth.py`
- `backend/app/routers/testcase.py`
- `backend/app/routers/scenario.py`
- `backend/app/routers/report.py`
- `backend/app/routers/terminal.py`
- `backend/app/services/scenario_service.py`
- `backend/app/services/terminal_service.py`
- `backend/app/services/test_case_service.py`
- `backend/app/services/platform_seed.py`
- `backend/app/schemas/test_case.py`
- `backend/app/schemas/scenario.py`
- `backend/app/schemas/report.py`

## 允许修改范围

如果前置 review 尚未修复，允许修改：

- `backend/app/services/scenario_service.py`
- `backend/tests/services/test_report_service.py`
- `backend/tests/conftest.py`
- `backend/pytest.ini`
- `backend/requirements.txt`

为完成真实 E2E 验证，允许新增：

- `backend/tests/e2e/real_quality_loop_e2e.py`
- 或 `.ai/results/real_quality_loop_e2e.py`
- `.ai/results/2026-05-24-real-system-api-e2e-quality-loop-result.md`

如果需要添加一个轻量脚本，请优先放在 `.ai/results/`，避免把一次性验证脚本误认为长期测试套件。

## 禁止事项

- 不使用 mock 替代真实 HTTP 调用。
- 不只调用 service 层。
- 不直接写数据库绕过 API。
- 不删除现有数据库、用户数据、报告、缺陷或日志。
- 不引入大型依赖。
- 不依赖外网服务。
- 不把“服务启动失败”包装成验证通过。
- 不把“接口存在”当作“链路跑通”。

## 真实被测接口选择

用例里的被测 URL 应指向本系统自己的接口，优先使用：

```text
GET http://localhost:8000/api/health
```

这是最稳定的真实接口，不需要额外认证，适合验证场景执行器、终端内部执行、报告生成、门禁评估的基础闭环。

如果要增加认证链路，可再创建第二个用例：

```text
POST http://localhost:8000/api/auth/login
Body: {"username":"admin","password":"admin123"}
```

但第一条闭环必须先用 `/api/health` 跑通，避免认证变量传递影响主验证。

## 真实 E2E 操作步骤

### 1. 启动后端

从 `backend` 目录启动：

```text
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

要求：

- 如果 8000 端口被占用，先确认是否已有当前项目后端在运行。
- 不要强行杀进程。
- 如果必须换端口，要注意场景执行器当前写死调用 `http://localhost:8000/api/terminal/internal/run`，换端口可能导致场景执行失败。优先使用 8000。

### 2. 健康检查

请求：

```text
GET http://localhost:8000/api/health
```

期望：

- HTTP 200
- 返回健康状态 JSON

### 3. 登录获取 token

请求：

```text
POST http://localhost:8000/api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

期望：

- HTTP 200
- 返回 `access_token`

后续需要认证的接口使用：

```text
Authorization: Bearer <access_token>
```

### 4. 创建真实 API 用例

请求：

```text
POST http://localhost:8000/api/case
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "E2E-真实接口健康检查-<timestamp>",
  "description": "使用本系统 /api/health 验证真实质量闭环",
  "priority": "P1",
  "tags": ["e2e", "real-api", "quality-loop"],
  "case_type": "api",
  "is_automated": true,
  "api_case": {
    "method": "GET",
    "url": "http://localhost:8000/api/health",
    "headers": {},
    "params": {},
    "body_type": "none",
    "body": "",
    "auth_config": {},
    "expected_status": 200,
    "assertions": [
      {
        "type": "status_code",
        "operator": "equals",
        "expected": 200
      }
    ]
  }
}
```

记录返回的 `case_id`。

### 5. 创建场景

请求：

```text
POST http://localhost:8000/api/scenario
Content-Type: application/json

{
  "name": "E2E-本系统接口质量闭环-<timestamp>",
  "description": "用平台自己的 /api/health 接口验证场景执行到报告门禁闭环",
  "scenario_type": "api",
  "priority": "P1",
  "version": 1,
  "status": "active"
}
```

记录返回的 `scenario_id`。

注意：当前场景接口如无认证依赖，按现有实现调用；如果后续加了认证，再补 token。

### 6. 添加场景步骤

请求：

```text
POST http://localhost:8000/api/scenario/{scenario_id}/steps
Content-Type: application/json

{
  "case_id": <case_id>,
  "name": "调用本系统健康检查接口",
  "sort_order": 1,
  "enabled": true,
  "retry_count": 0,
  "timeout_ms": 30000,
  "failure_strategy": "stop",
  "extract_rules": [],
  "inject_rules": []
}
```

期望：

- HTTP 200
- 返回步骤 ID

### 7. 执行场景

请求：

```text
POST http://localhost:8000/api/scenario/{scenario_id}/run
```

记录返回的 `run_id`。

### 8. 轮询执行详情

请求：

```text
GET http://localhost:8000/api/scenario/runs/{run_id}
```

轮询到状态进入终态：

- `passed`
- `failed`
- `stopped`

期望：

- 正常情况下应为 `passed`
- `summary.total_steps == 1`
- `summary.executed == 1`
- `summary.passed == 1`
- `summary.failed == 0`
- `summary.steps` 至少包含 1 条步骤结果

如果失败，要记录失败原因和响应。

### 9. 确认自动生成报告

请求：

```text
GET http://localhost:8000/api/reports?report_type=execution&page=1&page_size=20
```

找到满足以下条件的报告：

- `metrics.run_id == run_id`
- `metrics.scenario_id == scenario_id`
- `target_id == run_id`
- `report_type == "execution"`

期望：

- 报告存在
- `summary.total == 1`
- `summary.passed == 1`
- `summary.failed == 0`
- `summary.pass_rate == 100.0`
- `metrics.step_results` 长度为 1

记录 `report_id`。

### 10. 创建或确认质量门禁

如果没有启用的 execution 类型门禁，创建一个：

```text
POST http://localhost:8000/api/reports/quality-gates
Content-Type: application/json

{
  "name": "E2E-通过率必须100-<timestamp>",
  "description": "真实 E2E 验证用门禁",
  "gate_type": "execution",
  "enabled": true,
  "conditions": [
    {
      "metric": "pass_rate",
      "operator": ">=",
      "threshold": 100
    },
    {
      "metric": "failed",
      "operator": "<=",
      "threshold": 0
    }
  ],
  "gate_level": "blocking",
  "scope_filter": {}
}
```

记录 `gate_id`。

### 11. 基于报告一键评估门禁

请求：

```text
POST http://localhost:8000/api/reports/{report_id}/quality-gates/evaluate
```

期望：

- HTTP 200
- 返回 `aggregated_metrics.pass_rate == 100.0`
- 返回 `aggregated_metrics.failed == 0`
- 至少包含刚创建的门禁评估结果
- 对应门禁 `overall_result == "pass"`

## 建议实现一个可重复运行脚本

建议写一个脚本，例如：

```text
.ai/results/real_quality_loop_e2e.py
```

脚本职责：

- 检查后端健康。
- 登录。
- 创建唯一命名的用例、场景、步骤、门禁。
- 执行场景并轮询。
- 查询报告。
- 调用报告门禁评估。
- 输出每一步的 HTTP 状态码、关键 ID、关键断言。
- 最终输出中文结论。

脚本要求：

- 使用 Python 标准库 `urllib.request` 即可，避免额外依赖。
- 不直接访问数据库。
- 不清理数据，避免误删；使用 timestamp 命名保证可追溯。
- 每一步失败时明确报出请求、状态码、响应体。

## 验收标准

必须满足：

- 真实后端服务启动成功。
- `/api/health` 真实请求成功。
- 登录真实成功并拿到 token。
- 通过真实 API 创建用例成功。
- 通过真实 API 创建场景成功。
- 通过真实 API 添加步骤成功。
- 通过真实 API 执行场景成功。
- 执行记录进入终态，且健康检查步骤通过。
- 自动生成报告，并且报告数据正确。
- 基于报告一键评估门禁成功，门禁结果通过。

如果无法全部通过，必须准确说明卡在哪一步，附状态码、响应体和最可能的代码原因。

## 验证命令

修复前置 review 后先运行：

```text
python -m pytest backend/tests --collect-only
python -m pytest backend/tests
cd backend
python -m pytest tests --collect-only
python -m pytest tests
```

启动后端：

```text
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

另一个终端运行真实 E2E：

```text
python .ai/results/real_quality_loop_e2e.py
```

前端构建也要确认：

```text
cd frontend
npm run build
```

## 输出要求

请更新或创建：

- `.ai/results/2026-05-24-real-system-api-e2e-quality-loop-result.md`

报告必须包含：

```text
# 真实系统接口 E2E 质量闭环验证结果

## 一、执行摘要

## 二、服务与环境

## 三、真实接口链路

| 步骤 | 接口 | 方法 | 状态 | 关键结果 |
|------|------|------|------|----------|

## 四、关键业务数据

- case_id:
- scenario_id:
- step_id:
- run_id:
- report_id:
- gate_id:

## 五、报告校验

## 六、门禁校验

## 七、失败点与修复建议

## 八、剩余风险
```

最终聊天回复必须用中文说明：

- 是否真实跑通。
- 哪个接口作为被测目标。
- 关键 ID。
- 报告是否自动生成。
- 门禁是否通过。
- 如果失败，下一步该修哪里。
