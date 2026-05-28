# AI 与缺陷跳转问题审查修复 - 结果报告

## 审查修复概述

审查共提出 5 个问题，全部修复完成。后端测试 81/81 通过，前端构建 ✓。

---

## 已修复问题

### 1. AI 后端异常中文化

**文件**: `backend/app/routers/ai.py`

新增 `_ai_service_call` 包装函数，统一处理 AI Service 调用异常：

```python
def _ai_service_call(svc_call_fn, error_prefix="AI 服务调用失败"):
    try:
        return svc_call_fn()
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"{error_prefix}: {type(e).__name__} — {str(e)[:100]}")
        raise HTTPException(status_code=502, detail=f"{error_prefix}，请检查模型配置或稍后重试")
```

包裹以下端点的 Service 调用：
- `generate_variants`
- `generate_assertions`
- `analyze_failure`
- `summarize_report`
- `test_ai_connection`

同时修复 `generate_variants` 中的 JSON 解析（使用 `_safe_json_loads`）和 `override` vs `override_config` 归一化处理。

### 2. AnalyzeFailureResponse 新增 severity 字段

**文件**: `backend/app/schemas/ai.py`

```python
class AnalyzeFailureResponse(BaseModel):
    analysis_id: int
    root_cause: str
    severity: Optional[str] = None  # critical | high | medium | low
    suggestions: List[Dict[str, Any]]
```

后端 router 返回时加入 `"severity": result.get("severity")`。

### 3. 缺陷表单 query params 跳转

**文件**: `frontend/src/views/report/DefectList.vue`

`onMounted` 中处理 query params，支持：
- `open=create` 或 `action=create` → 自动打开新建表单
- `title`、`description`、`severity`、`priority`、`defect_type`、`tags`
- `project_id`、`version_id`、`iteration_id`、`requirement_id`（数字字段）
- `tags` 支持逗号分隔字符串或 JSON 数组字符串
- 自动加载级联数据（版本、迭代、需求）

### 4. DefectForm initialData 预填支持

**文件**: `frontend/src/views/report/DefectForm.vue`

- 新增 `initialData` prop，用于新建时接收预填值
- `watch(modelValue)` 中识别 `props.defect` 和 `props.initialData` 两种新建路径
- 预填时自动加载归属信息的级联数据
- DefectList 传 `:initialData="currentDefect"` 实现 query → 表单预填

### 5. 前端错误提示中文化

**文件**: `frontend/src/views/report/DefectForm.vue`

`e.response?.data?.detail || e.message || '请检查 AI 配置'` 已在之前审查中修复，本次确认三处 AI 按钮 catch 均已使用该模式。

---

## 变更文件清单

| 文件 | 操作 |
|------|------|
| `backend/app/routers/ai.py` | 修改 — 新增 `_ai_service_call` 异常包装、`_safe_json_loads` 防御解析、variants 归一化、所有 AI 端点包裹 svc 调用 |
| `backend/app/schemas/ai.py` | 修改 — AnalyzeFailureResponse 新增 `severity` 字段 |
| `frontend/src/views/report/DefectList.vue` | 修改 — onMounted 读取 query params 自动打开表单并预填 |
| `frontend/src/views/report/DefectForm.vue` | 修改 — 新增 `initialData` prop、watch 中处理预填逻辑 |

---

## 验证结果

- **后端测试**: `81 passed in 1.16s`
- **前端构建**: `✓ built in 1.49s`

### 手工验收（需本地 AI 配置）

```text
/defect?open=create&title=登录失败&severity=high&priority=P1&defect_type=api&tags=登录,接口
```

预期：DefectList 加载后自动打开新建表单，title=`登录失败`，severity=`high`，priority=`P1`，defect_type=`api`，tags=`['登录', '接口']`。

---

## 真实 AI 配置验证

**未执行** — 本地未配置有效 AI 密钥/服务。

以下需在有真实 AI 配置时执行：

```bash
# 测试 AI 连接
POST /api/ai/config/test

# 测试场景步骤生成（case_data 路径）
POST /api/ai/analyze-failure
{
  "case_data": {
    "scenario_id": 0,
    "name": "登录后查询个人资料",
    "description": "用户登录成功后访问个人资料接口",
    "steps": [
      { "name": "登录", "method": "POST", "url": "/api/login" },
      { "name": "查询资料", "method": "GET", "url": "/api/profile" }
    ]
  }
}
```

预期返回：`{ analysis_id, root_cause, severity, suggestions }`

---

## 剩余风险

1. **真实 AI 返回格式**：AI 返回的 `severity` 字段是否稳定为 `critical|high|medium|low` 字符串需要真实调用验证。
2. **AI Service 内部异常**：`_ai_service_call` 只包装了 Router → Service 的调用链，如果 `AIService` 内部还有子调用未捕获，可能仍漏出英文错误。
3. **级联数据加载时序**：query params 预填时，`foundationStore.fetchVersions` 和 `fetchIterations` 是异步的，下拉框可能在数据到达前显示空值然后快速填充（视觉闪烁），不影响功能。