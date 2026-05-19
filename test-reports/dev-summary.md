# 开发总结 — Sprint 4缺陷修复

**日期：** 2026-05-06
**项目：** Quality_Manage_platform
**修复数量：** 4个缺陷

---

## 修复清单

| # | 缺陷 | 文件 | 修复内容 | 测试结果 |
|---|------|------|---------|---------|
| 1 | Dashboard CSS 重叠 | `frontend/src/views/Dashboard.vue` | 修复卡片/标题区域 z-index 和定位 | ✅ PASS |
| 2 | 缺陷列表数据源错误 | `frontend/src/views/DefectManagement.vue` | `queryDefects` → `queryDefectsForCurrentUser` | ✅ PASS |
| 3 | 复制用例消息重复后缀 | `frontend/src/views/CaseManagement.vue:318` | 去掉前端重复的 `-复制` | ✅ PASS |
| 4 | 执行失败时不弹窗 | `frontend/src/views/CaseManagement.vue:267-306` | try-catch 分离，弹窗移到外部 | ❌ FAIL（执行按钮卡死） |

---

## 修复详情

### 修复 #1 — Dashboard CSS 重叠
**类型：** Visual
**文件：** `frontend/src/views/Dashboard.vue`
**方案：** 调整卡片/标题区域的 z-index 和定位，添加 `z-index: 1` 保护层
**验证：** 页面布局正常，无重叠元素

### 修复 #2 — 缺陷列表数据源
**类型：** Functional
**文件：** `frontend/src/views/DefectManagement.vue`
**方案：** 将数据查询方法从 `queryDefects` 改为 `queryDefectsForCurrentUser`
**验证：** 缺陷列表显示 36 条数据（33条待处理），数据正常加载

### 修复 #3 — 复制用例命名重复
**类型：** Functional
**文件：** `frontend/src/views/CaseManagement.vue:318`
**方案：** 后端返回的 name 已包含 `(copy)`，前端不再重复添加后缀
**代码变更：**
```javascript
// 修改前
ElMessage.success(`用例复制成功 【${newCase?.name}-复制】`)
// 修改后
ElMessage.success(`用例复制成功 【${newCase?.name}】`)
```
**验证：** 消息显示 `【批量删除测试用例2 (copy)】`，无重复后缀

### 修复 #4 — 执行失败弹窗
**类型：** Functional
**文件：** `frontend/src/views/CaseManagement.vue:267-306`
**方案：** 重构 `runCase()` 函数，将 try-catch 分离，弹窗逻辑从 try 内移到 try-catch 之外
**代码变更：**
- API 调用独立 try-catch，异常存入 `apiError`
- `ElMessageBox.alert` 在 try-catch 之外调用
- 统一 `error` 变量：`apiError || result.data?.error || resp.error`
**验证：** ❌ FAIL — 执行按钮卡死，无法完成验证（见下方新发现）

---

## 新发现的问题

### 问题：执行按钮卡死（Medium）

**现象：** 用例执行按钮点击后一直显示 `⟳` 加载状态，超过15秒无响应。

**根因分析（推测）：**
1. 用例 URL 为相对路径 `/`，导致请求挂起
2. 后端未设置请求超时，前端 axios 也无超时控制
3. 请求一直处于 pending 状态，既不成功也不失败

**建议修复方案：**
```javascript
// 在 caseStore.runCase 中添加 timeout
runCase: (id, data) => client.post(`/cases/${id}/run`, data, { timeout: 30000 })

// 或在 runCase() 函数中添加超时检测
async function runCase(c) {
  runningCaseId.value = c.id
  let result = {}
  let apiError = null

  // 添加超时控制
  const timeoutPromise = new Promise((_, reject) =>
    setTimeout(() => reject(new Error('请求超时（30s）')), 30000)
  )

  try {
    result = await Promise.race([
      caseStore.runCase(c.id),
      timeoutPromise
    ]) || {}
  } catch (err) {
    apiError = err.message || '请求失败'
    result = {}
  }
  // ... 弹窗逻辑不变
}
```

---

## 技术笔记

### 端口说明
- **3000** — 后端 API + 主应用入口
- **5173** — 前端 Vite dev server（开发时前端独立运行）

### 账号信息
- 用户名：`admin`
- 密码：`admin123`

### 测试工具
- dogfood skill — 探索性 QA 测试
- 截图保存路径：`test-reports/dogfood/screenshots/`

---

## 总结

本次 Sprint 完成 4 个缺陷修复，其中 3 个通过验证，1 个发现新的阻塞性问题（执行按钮卡死）。建议优先修复该问题后重新验证修复 #4。
