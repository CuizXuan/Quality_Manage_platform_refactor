# 用例模块重新设计方案

**日期**：2026-05-19
**状态**：草稿
**作者**：Claude

---

## 1. 概述

### 1.1 背景

现有用例模块存在以下问题：
- 初始页面布局拥挤在右上角
- 用例没有分类，只能按单一列表展示
- 功能测试用例和接口测试用例混在一起，区分不清晰
- 与终端调试台没有打通，无法直接将调试结果转为用例

### 1.2 目标

重新设计用例模块，实现：
- 用例按测试类型（功能测试/接口测试）和业务模块双维度分类
- 采用左侧分类+三栏布局（分类树 / 用例列表 / 用例详情）
- 与终端调试台深度打通，支持将调试结果直接保存为接口测试用例

---

## 2. 架构设计

### 2.1 模块拆分

用例模块拆分为两个独立子模块：

| 模块 | 路由 | 说明 |
|------|------|------|
| 功能测试用例 | `/case/functional` | 功能测试用例管理 |
| 接口测试用例 | `/case/api` | 接口测试用例管理 |

两个模块各自拥有独立的：
- 左侧分类树（业务模块分类）
- 中间用例列表
- 右侧用例详情+变体管理

### 2.2 菜单结构

```
工具
├── 终端调试台 (/terminal)
├── 功能测试 (/case/functional)
└── 接口测试 (/case/api)
```

---

## 3. 页面布局设计

### 3.1 整体布局（三栏结构）

```
+------------------+------------------------+------------------------+
|  左侧分类树      |  中间用例列表           |  右侧用例详情           |
|  (240px)         |  (flex: 1, min: 400px) |  (400px)               |
|                  |                        |                        |
|  文件夹/标签     |  用例卡片列表           |  用例配置               |
|  树形结构        |  搜索/筛选              |  断言配置               |
|                  |  批量操作              |  变体管理               |
+------------------+------------------------+------------------------+
```

### 3.2 左侧分类树（CaseSidebar）

**结构**：
- 顶部：模块切换 Tab（功能测试 / 接口测试）
- 搜索框：搜索分类名称
- 树形列表：文件夹 + 标签分类
  - 文件夹（可展开，显示子分类）
  - 标签（扁平展示）
- 底部：新建文件夹 / 新建标签按钮

**交互**：
- 点击文件夹 → 筛选该分类下的用例
- 右键菜单 → 重命名 / 删除 / 新建子分类
- 拖拽 → 用例在分类间移动

### 3.3 中间用例列表（CaseList）

**结构**：
- 顶部工具栏：搜索框、筛选器（类型/状态/创建人）、批量操作按钮、新建用例按钮
- 列表：用例卡片或表格视图
- 底部：分页器

**列表项内容**：
- 用例名称
- 请求方法 Badge（GET/POST/PUT/DELETE）
- 所属分类
- 创建时间
- 执行状态（可选）

### 3.4 右侧用例详情（CaseDetail）

**结构**：
- 顶部：用例名称（可编辑）、操作按钮（保存/复制/删除）
- Tab 页：请求配置 / 断言 / 变量 / 前置脚本 / 后置脚本
- 底部：变体列表快捷入口

**请求配置 Tab**：
- Method、URL、Params、Headers、Body、Auth、Cookie

---

## 4. 功能详解

### 4.1 用例分类管理

**分类类型**：
1. **文件夹分类**：树形层级结构，支持多级
2. **标签分类**：扁平标签，一个用例可多个标签

**分类操作**：
- 新建 / 重命名 / 删除文件夹
- 新建 / 删除标签
- 用例在分类间移动（拖拽或右键移动）

### 4.2 用例 CRUD

**创建用例**：
- 手动创建：填写用例名称、选择分类、配置请求信息
- 从终端调试台导入：调试完成后点击"保存为用例"

**编辑用例**：
- 页面内直接编辑
- 支持版本历史回溯

**删除用例**：
- 软删除（可恢复）
- 级联删除关联变体

### 4.3 与终端调试台打通

**核心流程**：
1. 在终端调试台完成接口调试
2. 点击"保存为用例"按钮
3. 弹出用例创建弹窗，预填充调试请求信息
4. 选择保存到哪个分类（功能测试/接口测试）
5. 确认保存，自动跳转到用例详情页

**数据传递**：
- 请求方法、URL、Headers、Body、Params、Auth、Cookie
- 调试结果（响应信息）可选择性保留

### 4.4 用例类型区分

**功能测试用例**：
- 无需配置 HTTP 请求
- 配置测试步骤（操作描述、预期结果）
- 关联业务场景

**接口测试用例**：
- 配置完整的 HTTP 请求
- 配置断言（状态码、响应体、响应头）
- 支持变量提取和注入

---

## 5. 数据结构

### 5.1 用例基础信息

```typescript
TestCase {
  id: string
  case_type: 'functional' | 'api'          // 用例类型
  folder_id: string                         // 所属文件夹
  tags: string[]                            // 标签列表
  name: string                              // 用例名称
  description: string                       // 描述
  method?: string                            // HTTP 方法（接口测试用）
  url?: string                               // 请求 URL（接口测试用）
  query_params?: Record<string, string>     // Query 参数
  headers?: Record<string, string>           // 请求头
  cookies?: Record<string, string>          // Cookie
  body_type?: string                         // Body 类型
  body?: string                              // 请求体
  auth_config?: AuthConfig                   // 认证配置
  expected_status?: number                   // 期望状态码
  assertions?: Assertion[]                   // 断言列表
  variables?: Variable[]                      // 变量列表
  pre_script?: string                        // 前置脚本
  post_script?: string                       // 后置脚本
  source_debug_id?: string                   // 来源调试记录 ID
  created_by: string
  created_at: datetime
  updated_at: datetime
}
```

### 5.2 用例分类

```typescript
CaseFolder {
  id: string
  case_type: 'functional' | 'api'           // 所属模块
  parent_id: string | null                  // 父文件夹 ID
  name: string                              // 文件夹名称
  sort_order: number                        // 排序
  created_at: datetime
}

CaseTag {
  id: string
  case_type: 'functional' | 'api'           // 所属模块
  name: string                              // 标签名称
  color: string                             // 标签颜色
  created_at: datetime
}
```

### 5.3 变体管理

```typescript
CaseVariant {
  id: string
  case_id: string                           // 所属用例 ID
  name: string                              // 变体名称
  variant_type: VariantType                 // 变体类型
  override_params?: Record<string, string>  // 参数覆盖
  override_headers?: Record<string, string> // 请求头覆盖
  override_body?: string                    // Body 覆盖
  expected_status?: number                  // 期望状态码
  assertions?: Assertion[]                   // 断言列表
  created_by: string
  created_at: datetime
}

// 变体类型枚举
type VariantType =
  | 'normal'           // 正常值
  | 'boundary'         // 边界值
  | 'empty'            // 空值
  | 'missing_field'    // 缺失字段
  | 'type_error'       // 类型错误
  | 'enum_illegal'     // 枚举非法值
  | 'overflow'         // 超长字段
  | 'auth_fail'        // 鉴权失败
  | 'permission_denied' // 权限不足
  | 'schema_check'     // 返回结构校验
  | 'business_check'   // 返回业务值校验
  | 'performance'      // 性能阈值
```

---

## 6. API 设计

### 6.1 用例相关

| 接口 | 方法 | 说明 |
|------|------|------|
| `/case/functional` | GET | 获取功能测试用例列表 |
| `/case/functional` | POST | 创建功能测试用例 |
| `/case/functional/{id}` | GET | 获取功能测试用例详情 |
| `/case/functional/{id}` | PUT | 更新功能测试用例 |
| `/case/functional/{id}` | DELETE | 删除功能测试用例 |
| `/case/api` | GET | 获取接口测试用例列表 |
| `/case/api` | POST | 创建接口测试用例 |
| `/case/api/{id}` | GET | 获取接口测试用例详情 |
| `/case/api/{id}` | PUT | 更新接口测试用例 |
| `/case/api/{id}` | DELETE | 删除接口测试用例 |
| `/case/from-debug` | POST | 从调试记录创建用例 |

### 6.2 分类相关

| 接口 | 方法 | 说明 |
|------|------|------|
| `/case/folders` | GET | 获取分类树 |
| `/case/folders` | POST | 创建文件夹 |
| `/case/folders/{id}` | PUT | 更新文件夹 |
| `/case/folders/{id}` | DELETE | 删除文件夹 |
| `/case/tags` | GET | 获取标签列表 |
| `/case/tags` | POST | 创建标签 |
| `/case/tags/{id}` | DELETE | 删除标签 |

### 6.3 变体相关

| 接口 | 方法 | 说明 |
|------|------|------|
| `/case/{case_id}/variant` | GET | 获取变体列表 |
| `/case/{case_id}/variant` | POST | 创建变体 |
| `/case/{case_id}/variant/{id}` | PUT | 更新变体 |
| `/case/{case_id}/variant/{id}` | DELETE | 删除变体 |

---

## 7. 组件设计

### 7.1 组件结构

```
views/case/
├── functional/
│   └── FunctionalCase.vue      # 功能测试用例主页面
└── api/
    └── ApiCase.vue              # 接口测试用例主页面

components/case/
├── CaseSidebar.vue              # 左侧分类树
├── CaseList.vue                 # 用例列表
├── CaseDetail.vue               # 用例详情
├── CaseVariantList.vue          # 变体列表
├── CaseFolderTree.vue           # 文件夹树组件
├── CaseTagList.vue              # 标签列表组件
├── FunctionalCaseForm.vue       # 功能用例表单
└── ApiCaseForm.vue              # 接口用例表单
```

### 7.2 组件职责

| 组件 | 职责 |
|------|------|
| `CaseSidebar` | 分类树展示、搜索、分类CRUD |
| `CaseList` | 用例列表展示、搜索、筛选、分页 |
| `CaseDetail` | 用例详情展示、编辑、保存 |
| `CaseVariantList` | 变体列表管理、创建变体 |
| `CaseFolderTree` | 树形结构渲染，支持拖拽 |
| `CaseTagList` | 标签展示，关联用例计数 |

---

## 8. 状态管理

### 8.1 Pinia Store 设计

```typescript
// stores/caseStore.js
export const useCaseStore = defineStore('case', () => {
  // 状态
  const caseType = ref('api')  // 'functional' | 'api'
  const folders = ref([])
  const tags = ref([])
  const currentCase = ref(null)
  const caseList = ref([])
  const variants = ref([])

  // Actions
  async function fetchFolders() { ... }
  async function fetchTags() { ... }
  async function fetchCaseList() { ... }
  async function fetchCaseDetail(id) { ... }
  async function createCase(data) { ... }
  async function updateCase(id, data) { ... }
  async function deleteCase(id) { ... }
  async function createVariant(caseId, data) { ... }

  return { ... }
})
```

---

## 9. 与终端调试台的打通

### 9.1 打通流程

1. 用户在终端调试台完成接口调试
2. 点击"保存为用例"按钮（或快捷键 Ctrl+S）
3. 弹出用例创建弹窗，字段预填充：
   - 请求方法、URL、Headers、Body 等
   - 期望状态码（从响应获取）
   - 断言建议（从 AI 分析结果获取）
4. 用户选择用例类型（功能测试/接口测试）和分类
5. 确认保存，自动跳转到用例详情页

### 9.2 数据流

```
终端调试台                    用例模块
    │                           │
    ├── 保存为用例 ──────────►  创建用例（预填充数据）
    │                           │
    ├── 查看历史 ────────────►  用例详情页显示调试历史
    │                           │
    └── 重新编辑 ────────────►  加载到调试台继续编辑
```

---

## 10. 样式规范

### 10.1 CSS 变量使用

遵循 `docs/06_前端组件与页面规范.md` 的规定：
- 所有颜色通过 CSS 变量定义
- 布局使用 `flex` 或 `el-row/el-col`
- 组件样式使用 `scoped`

### 10.2 布局关键样式

```css
.case-page {
  display: flex;
  height: 100%;
  overflow: hidden;
}

.case-sidebar {
  width: var(--sidebar-width);  /* 240px */
  border-right: 1px solid var(--border-color);
  overflow-y: auto;
}

.case-list {
  flex: 1;
  min-width: 400px;
  overflow-y: auto;
}

.case-detail {
  width: 400px;
  border-left: 1px solid var(--border-color);
  overflow-y: auto;
}
```

---

## 11. 路由设计

### 11.1 路由配置

```javascript
{
  path: '/case',
  component: () => import('../app/AppShell.vue'),
  meta: { requiresAuth: true },
  children: [
    {
      path: 'functional',
      name: 'FunctionalCases',
      component: () => import('../views/case/functional/FunctionalCase.vue'),
    },
    {
      path: 'api',
      name: 'ApiCases',
      component: () => import('../views/case/api/ApiCase.vue'),
    },
  ]
}
```

---

## 12. 待确认事项

1. 功能测试用例的具体字段结构（是否需要步骤配置）
2. 用例版本管理的具体策略
3. 变体生成的 AI 辅助功能

---

## 13. 实施计划

分阶段实施：
1. 第一阶段：基础框架（路由、页面布局）
2. 第二阶段：功能测试用例完整功能
3. 第三阶段：接口测试用例完整功能
4. 第四阶段：与终端调试台打通
5. 第五阶段：变体管理和 AI 辅助功能