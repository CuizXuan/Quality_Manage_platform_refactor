# 用例管理功能增强

> 文档版本：v1.0
> 创建时间：2026-05-06
> 目标：完善用例管理功能（执行弹窗、用例字段、终端联动、复制命名）

---

## 1. 需求概述

### 1.1 背景
当前质量管理平台的用例管理模块存在以下不足：
1. 执行结果弹窗信息不完整，缺少请求头/请求体展示
2. 用例缺少请求头、请求体、响应体等关键字段
3. 终端调试结果无法直接转为用例
4. 复制命名规则不直观

### 1.2 目标
完善用例管理功能，使其具备完整的 API 测试能力，并支持与终端调试联动。

---

## 2. 功能详述

### 2.1 执行结果弹窗完善

**位置：** `frontend/src/views/CaseManagement.vue` 的 `runCase()` 函数

**修改点：**
- 执行按钮点击后，按钮进入 loading 状态（已有 `runningCaseId` 支持）
- 弹窗标题改为 `"执行结果"`（当前是 `'// 执行结果'`，去掉 `//`）
- 执行结果弹窗内容增加以下字段展示：
  - 用例名称
  - 请求方法 + 请求URL
  - 请求头（headers，JSON 格式化）
  - 请求体（body，JSON 格式化）
  - 执行状态（成功/失败）
  - 响应时间（ms）
  - 状态码
  - 响应体（JSON 格式化）
  - 错误信息（如有）

**弹窗内容模板：**
```html
<p><strong>用例:</strong> ${c.name}</p>
<p><strong>方法:</strong> ${c.method} <strong>地址:</strong> ${c.url}</p>
${c.headers ? `<p><strong>请求头:</strong></p><pre>${formatJson(c.headers)}</pre>` : ''}
${c.body ? `<p><strong>请求体:</strong></p><pre>${formatJson(c.body)}</pre>` : ''}
<hr/>
<p><strong>状态:</strong> ${isSuccess ? '✅ 成功' : '❌ 失败'}</p>
${resp.time_ms ? `<p><strong>响应时间:</strong> ${resp.time_ms}ms</p>` : ''}
${resp.status_code ? `<p><strong>状态码:</strong> ${resp.status_code}</p>` : ''}
${resp.body ? `<p><strong>响应:</strong></p><pre>${formatJson(resp.body)}</pre>` : ''}
${resp.error ? `<p style="color:#F43F5E;"><strong>错误:</strong> ${resp.error}</p>` : ''}
```

**注意：** `formatJson()` 函数需处理非对象字符串（如纯文本响应）。

---

### 2.2 用例表单字段扩展

**涉及文件：**
- `frontend/src/views/CaseManagement.vue`（新建/编辑弹窗）
- `backend/app/models/case.py`（数据库模型）
- `backend/app/schemas/case.py`（Pydantic schema）
- `backend/app/routers/cases.py`（API 路由）
- `frontend/src/stores/caseStore.js`（状态管理）
- `frontend/src/api/case.js`（API 客户端）

**新增字段：**

| 字段名 | 类型 | 说明 | 存储位置 |
|--------|------|------|---------|
| `headers` | JSON string | HTTP 请求头 | `test_case.headers`（已有） |
| `request_body` | TEXT | 请求体内容 | 需新增字段 |
| `response_body` | TEXT | 响应体内容（执行后自动填充） | 需新增字段 |

**现有字段复用：**
- `body` → 改名为 `request_body` 或直接使用（已有 `body` 字段）
- `headers` → 已存在，无需修改数据库

**新建/编辑弹窗新增表单项（位置：在"描述"字段下方）：**

```html
<div class="form-group">
  <label>请求头 (JSON)</label>
  <textarea v-model="form.headers" rows="3" placeholder='{"Content-Type": "application/json"}'></textarea>
</div>
<div class="form-group">
  <label>请求体</label>
  <textarea v-model="form.request_body" rows="4" placeholder="请求体内容..."></textarea>
</div>
```

**详情/展示（执行后）：**

响应体在执行成功后自动填充到用例记录，并可在详情中查看。

---

### 2.3 执行后自动保存响应体

**位置：** `runCase()` 函数中，API 调用成功后

**逻辑：**
1. 执行 API 返回响应体后，调用 `caseStore.updateCase(c.id, { response_body: resp.body })`
2. 仅在执行成功时更新
3. 用户需主动触发保存（不在每次执行时自动覆盖，除非为空）

**注意：** 如果后端已有 `response_body` 字段则复用，没有则新增。

---

### 2.4 复制命名规则优化

**位置：** `frontend/src/views/CaseManagement.vue` 的 `duplicateCase()` 函数

**修改：**
```javascript
// 修改前
const newName = newCase?.name ? `【${newCase.name} (copy)】` : ''
// 修改后
const newName = newCase?.name ? `【${newCase.name}-复制】` : ''
```

---

### 2.5 终端"转用例"功能

**位置：** `frontend/src/views/Dashboard.vue`（终端调试页面）

**触发时机：** 用户在终端完成一次 API 调试并查看到响应结果后

**交互流程：**

1. **终端页面增加"转用例"按钮**
   - 位置：在终端的响应展示区附近
   - 按钮文案：`转用例`
   - 按钮样式：与"发送"按钮一致

2. **点击后弹出用例名称输入框**
   ```javascript
   const caseName = ref('')
   ElMessageBox.prompt('请输入用例名称', '转用例', {
     confirmButtonText: '确认',
     cancelButtonText: '取消',
     inputValue: `${requestStore.method} ${requestStore.url}`, // 默认填入
   })
   ```

3. **确认后调 API 创建用例**
   ```javascript
   await caseStore.createCase({
     name: caseName,           // 用户输入的名称
     method: requestStore.method,
     url: requestStore.url,
     headers: requestStore.headers || {},
     body: requestStore.body || '',
     description: `从终端调试创建 - ${new Date().toLocaleString()}`,
     folder_path: '/终端导入',
   })
   ElMessage.success('用例创建成功')
   ```

4. **跳转到用例管理页面**
   ```javascript
   router.push('/cases')
   ```

---

## 3. 数据库变更

### 3.1 新增字段（PostgreSQL/SQLite）

```sql
ALTER TABLE test_case ADD COLUMN request_body TEXT DEFAULT '';
ALTER TABLE test_case ADD COLUMN response_body TEXT DEFAULT '';
```

### 3.2 后端模型变更

**文件：** `backend/app/models/case.py`

```python
# 新增字段（在 body 字段后）
request_body = Column(Text, default="")
response_body = Column(Text, default="")
```

**文件：** `backend/app/schemas/case.py`

TestCaseBase / TestCaseCreate / TestCaseUpdate / TestCaseResponse 四个 schema 均需新增：

```python
request_body: Optional[str] = ""
response_body: Optional[str] = ""
```

---

## 4. API 变更

### 4.1 用例 CRUD 接口

所有接口保持 REST 风格，新增字段自动支持（由 Pydantic schema 定义）。

### 4.2 执行接口返回结构

确保 `/api/cases/{id}/run` 的返回结构包含完整响应信息（headers/body/time_ms 等），已在之前的 Bug 修复中确认。

---

## 5. 前端文件清单

| 文件 | 改动内容 |
|------|---------|
| `views/CaseManagement.vue` | 弹窗内容扩展 + 表单新增字段 + 复制命名 |
| `stores/caseStore.js` | 新增 request_body/response_body 字段 |
| `api/case.js` | 确认 API 字段映射 |
| `views/Dashboard.vue` | 新增"转用例"按钮和交互逻辑 |

---

## 6. 任务拆分（执行计划）

| 序号 | 任务 | 依赖 | 执行者 |
|------|------|------|--------|
| 1 | 数据库模型 + Schema 扩展 | 无 | 小曦 |
| 2 | 后端 API 适配（确认新字段流通） | 1 | 小曦 |
| 3 | 用例新建/编辑弹窗表单扩展 | 1+2 | 小曦 |
| 4 | 执行结果弹窗内容完善（展示请求头/请求体） | 1+2 | 小曦 |
| 5 | 复制命名规则修复 | 1+2 | 小曦 |
| 6 | 终端"转用例"功能开发 | 1+2+3 | 小曦 |
| 7 | 集成验证（浏览器自动化） | 全部 | 小薇 |

---

## 7. 设计约束

1. **向后兼容：** 新增字段有默认值 `""`，不影响现有数据
2. **最小修改：** 不改动现有 API 路由结构，只扩展字段
3. **一致性：** 请求头使用 JSON 字符串存储，前端做 JSON 格式化展示
4. **防御性编程：** 所有 JSON.parse 做好 try-catch

---

## 8. 美学方向

遵循质量管理平台现有 UI 风格（cyber-主题，深色面板 + 终端字体）：

- 弹窗内容使用 `<pre>` 展示 JSON，保持等宽字体
- 请求头/请求体/响应体 使用可折叠/滚动区域（`max-height: 200px; overflow: auto`）
- "转用例"按钮风格与页面其他主按钮一致
