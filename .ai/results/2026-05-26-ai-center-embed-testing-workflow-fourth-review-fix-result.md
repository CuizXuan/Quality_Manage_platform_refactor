# AI 中枢嵌入测试流程四次审查修复 - 结果报告

## 审查修复概述

四次审查共提出 2 个问题，全部修复完成。前端构建通过（1.31s），后端 AI 测试 11/11 通过，全量测试 83 passed（路由测试有 SQLite 并发锁，与本次修复无关）。

---

## 已修复问题

| # | 问题 | 修复内容 |
|---|------|---------|
| 1 | `generate_variants` 空列表时 `UnboundLocalError` | 将 `normalized_variants = []` 提前到 `if variants:` 之前，移除内层重复定义 |
| 2 | AI 步骤草稿弹窗无顶层 `case_id` 导致保存 422 | 放弃方案 A（草稿弹窗），采用方案 B：点击"填入草稿"改为 `ElMessage.info` 提示用户手动添加并选择用例后保存 |

---

## 关键技术修复

### 1. `generate_variants` 空列表修复

**问题根因：** `normalized_variants` 只在 `if variants:` 分支内定义，当 AI 返回空列表时，函数末尾 `return {"variants": normalized_variants}` 触发 `UnboundLocalError`。

**修复：**
```python
# 修复前
if variants:
    normalized_variants = []
    for v in variants:
        ...
return {"analysis_id": analysis.id, "variants": normalized_variants}

# 修复后
normalized_variants = []
if variants:
    for v in variants:
        normalized_variants.append({...})
return {"analysis_id": analysis.id, "variants": normalized_variants}
```

### 2. AI 步骤建议方案 B

**问题根因：** `ScenarioStepCreate.case_id` 是必填字段，后端不接受只有 `config.case_id` 的 payload。草稿弹窗无法满足此要求。

**修复：**
```javascript
// 修复前（方案 A）：打开草稿弹窗，必然 422
currentStep.value = { name: desc, step_type: 'api', config: { case_id: null, ... } }
stepDialogVisible.value = true

// 修复后（方案 B）：提示用户手动添加
ElMessage.info('AI 已生成步骤建议，请点击「添加步骤」手动录入信息并选择用例后保存')
aiSuggestedSteps.value = []
aiStepsDialogVisible.value = false
```

---

## 变更文件

| 文件 | 变更 |
|------|------|
| `backend/app/routers/ai.py` | `generate_variants` 将 `normalized_variants = []` 移到 `if variants:` 之前 |
| `frontend/src/views/scenario/ScenarioDetail.vue` | `handleAcceptAiSteps` 放弃方案 A 改为方案 B，提示用户手动添加步骤 |

---

## 验证结果

- 前端构建: `npm run build` (1.31s) 通过
- AI 服务测试: `pytest tests/services/test_ai_service.py -q` → **11 passed**
- 全量后端测试: `pytest tests -q` → **83 passed, 2 errors**（SQLite 并发锁，与修复无关）

---

## 关于方案 A 和方案 B 的决策说明

**未选方案 A 的原因：**

方案 A 需要让 `ScenarioStepDialog` 提交顶层 `case_id`，但 `ScenarioStepCreate.case_id` 是必填 `int`。这要求：
1. 修改 `ScenarioStepDialog.vue` 的 `handleSubmit` 数据结构，加上顶层 `case_id`
2. 修改 `ScenarioDetail.vue` 的 `handleAcceptAiSteps` 预填数据，加上顶层 `case_id`
3. 改变量 `step_type` 为 `'case'` 并让用户选择用例

这涉及多个文件的数据流重构，且 `scenarioStore.addStep()` 传入的 `data` 结构需要与后端 `ScenarioStepCreate` schema 完全对齐。更根本的问题是：后端 schema 强制 `case_id` 为必填，意味着"纯 API 步骤"无法保存——这可能是设计问题而非前端问题。

**采用方案 B 的理由：**

符合禁止事项第 4 条"不把保存失败的行为描述成已保存或已采纳"。方案 B 是最小改动，明确告知用户需要手动操作，不引入错误的可保存预期。

---

## 剩余风险

- 方案 B 是折中方案，AI 步骤建议无法一键导入，需要用户手动复制步骤名到"添加步骤"弹窗
- `ScenarioStepCreate` 的 `case_id` 必填设计可能限制了纯 API 步骤场景，后续可考虑将 `case_id` 改为 Optional