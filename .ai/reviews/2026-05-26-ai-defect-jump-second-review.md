# AI 与缺陷跳转问题二次审查修复包

## 审查目标

审查 `.ai/results/2026-05-26-ai-defect-jump-review-fix-result.md` 对上一轮问题的修复结果，重点确认：

- AI 路由 helper 去重是否完成。
- 缺陷 query 新建预填是否区分编辑对象和 initialData。
- `fetchVersions` 调用是否全部符合 `qualityFoundationStore.fetchVersions(params = {})` 的对象参数契约。
- 验证结果是否如实反映。

## 已确认修复

以下上一轮问题已修复到位：

- `backend/app/routers/ai.py` 中重复的 `_safe_json_loads` 已删除，仅保留一处定义。
- `DefectList.vue` 的 query 自动新建路径已拆分 `currentDefect` 与 `initialDefectData`，不再把同一个对象同时传给 `defect` 和 `initialData`。
- `DefectList.vue` query 预加载版本时已改为 `foundationStore.fetchVersions({ project_id: initialDefect.project_id })`。
- `DefectForm.vue` 编辑分支与 `initialData` 分支中的 `fetchVersions` 已改为对象参数。

## 仍需修复的问题

1. `frontend/src/views/report/DefectForm.vue`: `onProjectChange(projectId)` 仍调用 `foundationStore.fetchVersions(projectId)`。当前 store 实现读取的是 `params.project_id`，裸数字会导致手动切换项目后版本列表按空参数加载或加载错误范围。请改为：

```javascript
foundationStore.fetchVersions({ project_id: projectId })
```

2. 验证结果需要更新为真实输出。当前我本地执行：

```bash
cd backend
python -m pytest tests -q
```

结果为 `84 passed, 2 errors in 53.35s`，两个错误均在 `tests/routers/test_test_plan_routes.py`，报错为登录时写 `platform_users.last_login_at` 触发 `sqlite3.OperationalError: database is locked`。请不要沿用结果文件中的 `83 passed, 1 failed, 2 errors`，修复后写入新的真实结果。

## 修复范围

只允许修改以下文件中解决上述问题所必需的部分：

- `frontend/src/views/report/DefectForm.vue`
- 如需同步结果，请新增或更新 `.ai/results/2026-05-26-ai-defect-jump-second-review-fix-result.md`

不要扩大到缺陷页面布局重构、AI 中枢无关页面或测试计划路由修复。测试计划路由的 SQLite 锁问题可在结果中明确标记为遗留问题；若要修复它，应走测试计划模块自己的审查包。

## 验证方式

修复后至少运行：

```bash
cd frontend
npm run build
```

建议额外运行：

```bash
cd backend
python -m pytest tests -q
```

手工核对：

1. 打开缺陷新建表单。
2. 手动选择项目。
3. 版本下拉列表按所选项目加载。
4. 清空项目后版本、迭代、需求级联数据被清空。

## Claude 输出要求

结束时请用中文汇报：

- 修复了哪个漏点。
- 变更文件。
- 前端构建真实结果。
- 后端测试真实结果，如仍有测试计划路由错误，请保留原始错误摘要。
- 剩余风险。

请同步写入：

- `.ai/results/2026-05-26-ai-defect-jump-second-review-fix-result.md`
