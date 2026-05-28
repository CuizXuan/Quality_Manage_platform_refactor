# AI 中枢嵌入测试流程三次审查修复 - 结果报告

## 审查修复概述

本次审查提出 2 个问题，全部修复完成。前端构建通过，后端 AI 服务测试 11/11 通过。

---

## 已修复问题

### 1. 场景 AI 步骤采纳改为填充草稿弹窗（方案 A）

**文件**: `frontend/src/views/scenario/ScenarioDetail.vue`

原实现 `handleAcceptAiSteps()` 直接调用 `scenarioStore.addStep()` 批量添加步骤，`case_id: null` 会导致后端必填校验失败。

修复后采用**方案 A（推荐）：填充步骤草稿弹窗**：

- 点击「填入草稿」后，不再直接保存
- 将 AI 建议的第一条步骤（name/description）填入 `currentStep`，打开 `ScenarioStepDialog`
- 用户在弹窗中选择有效 `case_id` 后保存
- AI 建议弹窗的按钮文案从「采纳建议」改为「填入草稿」，提示语同步更新为「采纳后将填入步骤草稿，请选择用例后保存」

**行为对比**：

| 维度 | 修复前 | 修复后 |
|------|--------|--------|
| case_id | `null` | 用户在弹窗中选择 |
| 保存方式 | 直接批量 addStep | 打开弹窗，用户确认后保存 |
| UI 文案 | 「采纳建议」+「已采纳 N 条」 | 「填入草稿」+ 弹窗草稿交互 |
| 是否假保存 | 有（case_id=null 必失败） | 无 |

### 2. generate_variants 返回归一化 override_config

**文件**: `backend/app/routers/ai.py`

原实现：service 返回的 `variants` 列表中 AI 可能返回 `override` 字段，但在保存建议时归一化为 `override_config`，而接口 response 直接返回原始 `variants`，FastAPI Pydantic 模型忽略额外字段导致前端拿到的 `override_config={}`。

修复：接口返回前将 `variants` 归一化为 `normalized_variants` 后再返回，保证字段名为 `override_config`。

```python
# 修复前
return {"analysis_id": analysis.id, "variants": variants}

# 修复后
return {"analysis_id": analysis.id, "variants": normalized_variants}
```

**归一化逻辑**（已存在于保存建议分支，本次移至返回前复用）：

```python
normalized_variants = []
for v in variants:
    normalized_variants.append({
        "variant_type": v.get("variant_type", "normal"),
        "description": v.get("description", ""),
        "override_config": v.get("override_config") or v.get("override") or {},
    })
```

---

## 变更文件清单

| 文件 | 操作 |
|------|------|
| `frontend/src/views/scenario/ScenarioDetail.vue` | 修改 — `handleAcceptAiSteps` 改为填充草稿弹窗；AI 步骤弹窗按钮文案更新 |
| `backend/app/routers/ai.py` | 修改 — `generate_variants` 返回 `normalized_variants` 而非原始 `variants` |

---

## 验证结果

- **前端构建**: `✓ built in 1.34s`
- **后端 AI 服务测试**: `11 passed in 0.31s`

---

## 场景 AI 步骤采纳行为说明

采用**方案 A（填充步骤草稿弹窗）**：

- 点击「填入草稿」后，AI 建议不直接落库
- 弹出 `ScenarioStepDialog`，name/description 已预填，用户选择 `case_id` 后保存
- **不会**发送 `case_id: null` 到后端
- UI 文案与真实行为一致：「填入草稿」即填入草稿，不是"已保存"

---

## generate_variants override 兼容修复方式

归一化在接口返回前执行，保证 FastAPI response_model 输出正确的 `override_config` 字段：

- AI 返回 `override` → 前端收到 `override_config`
- AI 返回 `override_config` → 前端收到 `override_config`
- AI 两者都无 → 前端收到 `override_config: {}`

前端 `CaseVariantList.vue` 采纳变体时不会再丢失覆盖配置。

---

## 剩余风险

1. **批量采纳**：当前实现只填入第一条 AI 建议作为草稿（`aiSuggestedSteps[0]`），多条建议时其余步骤需要用户重复操作。这是方案 A 的已知限制，如需真正的批量草稿需要扩展弹窗支持多步草稿列表。
2. **测试计划路由测试**：`tests/routers/test_test_plan_routes.py` 有导入错误（`from app.database import Base` 不存在），属于测试计划三次审查范围，本次未修改。