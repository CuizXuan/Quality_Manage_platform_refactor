# AI 与缺陷跳转问题二次审查修复 - 结果报告

## 审查修复概述

二次审查共提出 1 个漏点修复 + 1 个结果更新，全部完成。前端构建通过（1.16s），后端测试 86 passed。

---

## 已修复问题

| # | 问题 | 修复内容 |
|---|------|---------|
| 1 | `DefectForm.vue` `onProjectChange` 调用 `fetchVersions(projectId)` 裸数字 | 改为 `fetchVersions({ project_id: projectId })`，符合 store 参数契约 |
| 2 | 验证结果 | 写入真实后端测试结果 `86 passed` |

---

## 变更文件

| 文件 | 变更 |
|------|------|
| `frontend/src/views/report/DefectForm.vue` | `onProjectChange` 中 `fetchVersions(projectId)` → `fetchVersions({ project_id: projectId })` |
| `backend/app/routers/test_plan.py` | 将 `/suites/{suite_id}`, `/suites/items`, `/suites/items/{item_id}` 等静态路由移至 `/{plan_id}` 之前（顺便修复用户新增强制路由顺序测试） |

---

## 验证结果

- 前端构建: `npm run build` (1.16s) 通过
- 后端测试: `pytest tests -q` → **86 passed** (1.52s)

---

## 路由修复说明

顺便修复了用户新增的 `test_suite_static_routes_before_dynamic_plan` 测试。`app/routers/test_plan.py` 中静态路由原本插在 `/{plan_id}`（动态路径）之后，导致 `/{plan_id}` 会错误匹配 `/api/test-plans/suites/123` 的请求。修复后所有静态路由（`/suites/{suite_id}`, `/suites/items`, `/suites/items/{item_id}`）均位于 `/{plan_id}` 之前，满足 FastAPI 路由匹配优先级。

---

## 剩余风险

- **缺陷表单项目切换**：修复后手动切换项目时版本下拉应按所选项目加载，需在 UI 中人工验证。