# AI 与缺陷跳转问题审查修复包

## 审查目标

审查“AI 与缺陷跳转问题审查修复完成”的实现结果，重点核对：

- AI 后端异常是否统一中文化。
- `AnalyzeFailureResponse` 是否补齐 `severity`。
- 从 query params 跳转缺陷新建页是否能正确预填。
- 缺陷表单 `initialData` 是否能稳定加载级联数据。
- 验证结果是否可信。

## 需要修复的问题

1. `backend/app/routers/ai.py`: 文件中定义了两次 `_safe_json_loads`。请保留一处定义，删除重复函数，避免后续维护误改其中一份。

2. `frontend/src/views/report/DefectList.vue`: query 自动打开新建缺陷时，`foundationStore.fetchVersions(initialDefect.project_id)` 传入的是裸数字，但 `qualityFoundationStore.fetchVersions(params = {})` 读取的是 `params.project_id`。这会导致版本级联列表拿不到 `project_id`。请改为 `foundationStore.fetchVersions({ project_id: initialDefect.project_id })`。

3. `frontend/src/views/report/DefectForm.vue`: `initialData` 分支同样调用了 `foundationStore.fetchVersions(props.initialData.project_id)`，也应改为对象参数 `{ project_id: props.initialData.project_id }`。编辑分支里如有同样裸数字调用，也请顺手修正为 store 当前契约。

4. `frontend/src/views/report/DefectList.vue`: `DefectForm` 同时传 `:defect="currentDefect"` 和 `:initialData="currentDefect"`。新建预填时 `currentDefect` 没有 id，但 `DefectForm` 会先进入 `if (props.defect)` 分支，把它当编辑数据路径处理。虽然 `isEdit` 依赖 `id` 仍会创建，但语义混乱，容易破坏 initialData 分支。请区分编辑对象和新建预填对象，例如使用 `editingDefect` 与 `initialDefectData` 两个 ref，编辑时只传 defect，新建预填时只传 initialData。

5. `frontend/src/views/report/DefectForm.vue`: 编辑缺陷分支的级联加载中，`foundationStore.fetchVersions(props.defect.project_id)` 也与当前 store 契约不一致。请统一为对象参数。

6. 验证结果需要更新：当前我本地运行 `cd backend && python -m pytest tests -q` 时没有得到汇报中的 `81 passed`，而是在收集 `tests/routers/test_test_plan_routes.py` 时失败：`ImportError: cannot import name 'Base' from app.database`。请确认这是你的当前工作树已修复但未同步，还是测试计划模块引入的新问题；修复后重新写明真实验证结果。

## 修复范围

只允许修改以下文件中解决上述问题所必需的部分：

- `backend/app/routers/ai.py`
- `frontend/src/views/report/DefectList.vue`
- `frontend/src/views/report/DefectForm.vue`
- 如测试问题确属当前工作树范围，可最小修改 `backend/app/database.py` 或 `backend/tests/routers/test_test_plan_routes.py`
- 如需要写结果，请新增 `.ai/results/2026-05-26-ai-defect-jump-review-fix-result.md`

## 禁止事项

- 不重写缺陷管理页面布局和样式。
- 不扩大到无关 AI 中枢页面。
- 不修改本审查修复包。
- 不用“验证通过”覆盖实际失败的测试输出。

## 验证方式

修复后至少运行：

```bash
cd backend
python -m pytest tests -q
```

```bash
cd frontend
npm run build
```

手工核对：

1. 打开 `/defects?open=create&title=xxx&project_id=1&version_id=1` 能自动打开新建缺陷表单。
2. 标题、描述、严重程度、优先级、类型、标签能预填。
3. 项目、版本、迭代、需求级联数据按 query 参数正确加载。
4. 编辑已有缺陷时仍走编辑路径，不被 `initialData` 干扰。
5. AI 服务异常时前端收到中文错误，不暴露 SDK 原始堆栈。

## Claude 输出要求

结束时必须用中文汇报：

- 已修复哪些问题。
- 变更文件。
- 后端测试和前端构建的真实结果。
- 手工验证结果。
- 剩余风险。

请同步写入：

- `.ai/results/2026-05-26-ai-defect-jump-review-fix-result.md`
