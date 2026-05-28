# 测试计划 / 测试套件 / 执行中心二次审查修复包

## 审查目标

审查 `.ai/results/2026-05-26-test-plan-suite-execution-center-review-fix-result.md` 对 `.ai/reviews/2026-05-26-test-plan-suite-execution-center-review.md` 的修复结果。

本轮确认前端构建和现有后端测试通过，但仍有两个核心审查点没有真正修完，并且当前测试套件没有覆盖测试计划执行中心本身。

## 需要修复的问题

1. `backend/app/services/test_plan_service.py`: 场景执行仍把未完成的 `running` 场景计入 `summary["passed"]`，并且 `final_status = "passed" if summary["failed"] == 0 else "failed"` 会让只包含 running 场景的计划执行最终显示 passed。这与上一轮审查包第 7 点“计划级 summary 不得把尚未完成或实际失败的场景记为 passed”直接冲突。请改为不把 running 场景计入 passed，建议新增 `running` 或 `pending` 计数写入 summary；计划最终状态如果存在 running/pending 且 failed 为 0，应保持 `running`、`partial` 或其他非 passed 状态，不能显示 passed。

2. `backend/app/services/test_plan_service.py`: `_load_json` 被定义了两次，其中一次带 `@staticmethod`，随后又被同名函数覆盖；更重要的是后台执行用例时仍直接使用 `json.loads(case.headers)`、`json.loads(case.query_params)`、`json.loads(case.auth_config)`。历史空字符串或脏 JSON 仍会导致用例执行进入异常失败，上一轮审查包第 9 点没有实际生效。请保留一个清晰的小函数，并在后台执行链路中使用它。

3. 缺少测试计划执行中心的回归测试。当前 `backend/tests` 下没有 `test_plan` 相关测试，`55 passed` 不能证明本模块关键路径。请新增服务级测试，至少覆盖：
   - running 场景不会增加 passed，最终计划运行状态不会误报 passed。
   - 脏 JSON 字段不会让用例项因 `json.JSONDecodeError` 直接失败，而是按空对象继续执行到终端内部接口。
   - `/api/test-plans/runs` 静态路由不会被 `/{plan_id}` 抢占（如果路由测试夹具成本过高，可在服务测试之外补一个最小 FastAPI TestClient 测试）。

## 修复范围

只允许修改以下文件中解决上述问题所必需的部分：

- `backend/app/services/test_plan_service.py`
- `backend/tests/services/test_test_plan_service.py`
- 如路由测试必须使用客户端夹具，可最小修改 `backend/tests/conftest.py`

## 禁止事项

- 不重写测试计划前端页面。
- 不改动终端控制台、场景执行引擎或其它无关模块。
- 不引入 Celery、Redis、复杂任务队列或新大型依赖。
- 不做定时执行、CI/CD 集成等新能力。
- 不把 running/pending 状态伪装成 passed。

## 验证方式

修复后至少运行：

```bash
cd backend
python -m pytest tests/services/test_test_plan_service.py -q
python -m pytest tests -q
```

如修改了路由测试，也请确保对应测试单独通过。

## Claude 输出要求

结束时必须用中文汇报：

- 已修复哪些问题。
- 变更文件清单。
- 已运行的测试。
- 场景执行未等待完成时，计划级状态和 summary 的具体规则。
- 剩余风险。

请同步写入：

- `.ai/results/2026-05-26-test-plan-suite-execution-center-second-review-fix-result.md`
