# 用例管理模块重新设计方案（v2）

**日期**：2026-05-19
**状态**：已批准
**作者**：Claude

---

## 1. 需求概述

质量管理平台需要统一的用例管理模块，支持两类用例：

- **接口用例**：针对单个 API 的测试，配置请求参数、头信息、Body、断言等。
- **功能用例**：面向业务流程的场景测试，包含前置条件、执行步骤、预期结果、用例等级等。

两类用例有公共属性（名称、描述、所属模块、标签等），也有各自特有字段。

---

## 2. 页面布局

采用**三栏布局**：

```
+----------------------------------------------------------------------------------+
|  用例管理                                                    [导入] [导出] [帮助]  |
+----------------------------------------------------------------------------------+
|         |                      |                                                |
| 左侧目录树 │   中间用例列表          |   右侧详情编辑区                             |
| (模块/项目)│  (支持筛选、搜索)       │  (动态表单，根据类型切换字段)                 |
|         |                      |                                                |
|  ▼ 项目A   │ □ ID │ 名称 │类型│等级│操作  │   [保存] [复制] [删除] [执行]            |
|    ▼ 模块1 │  1   │ 登录 │接口│ P0 │ ... │   ───────────────────────────────      |
|      - 用例1│  2   │ 下单 │功能│ P1 │ ... │   公共字段                             |
|      - 用例2│      │      │    │    │     │   用例名称: [________]                 |
|    ▼ 模块2 │      │      │    │    │     │   所属模块: [下拉]      类型: ⚫接口 ○功能|
|      - 用例3│      │      │    │    │     │   等级: [P0▼]  标签: [________]       |
|         |                      │     │   前置条件: [___________________]           |
|         |                      │     │   描述: [___________________]              |
|         |                      │     │   ───────────────────────────────          |
|         |                      │     │   [接口用例特有字段] 或 [功能用例特有字段]    |
|         |                      │     │   (根据类型动态显示)                         |
|         |                      │     │                                             |
|         |                      │     └────────────────────────────────────────────┘
+----------------------------------------------------------------------------------+
```

---

## 3. 数据模型

### 3.1 主表：TestCase（公共字段）

```python
class TestCase(Base):
    """用例主表 - 存储公共字段"""
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)                    # 用例名称
    description = Column(Text, default="")                         # 描述
    folder_id = Column(Integer, ForeignKey("case_folders.id"))      # 所属分类
    priority = Column(String(10), default="P2")                     # P0/P1/P2/P3
    tags = Column(Text, default="[]")                             # 标签 JSON 数组
    pre_condition = Column(Text, default="")                       # 前置条件
    case_type = Column(String(20), nullable=False)                 # 'api' | 'functional'
    source_debug_id = Column(Integer, nullable=True)               # 来源调试记录
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 3.2 关联表：ApiTestCase（接口用例专用）

```python
class ApiTestCase(Base):
    """接口用例专用表"""
    __tablename__ = "api_test_cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    testcase_id = Column(Integer, ForeignKey("test_cases.id"), unique=True, nullable=False)
    method = Column(String(10), default="GET")                      # GET/POST/PUT/DELETE...
    url = Column(String(2000), nullable=False)                      # 请求 URL
    headers = Column(Text, default="{}")                            # 请求头 JSON
    params = Column(Text, default="{}")                            # Query 参数 JSON
    body_type = Column(String(20), default="none")                   # none/form/json/raw
    body = Column(Text, default="")                                 # 请求体
    auth_config = Column(Text, default="{}")                       # 认证配置 JSON
    expected_status = Column(Integer, default=200)                 # 期望状态码
    assertions = Column(Text, default="[]")                       # 断言规则 JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    test_case = relationship("TestCase", backref="api_case")
```

### 3.3 关联表：FunctionalTestCase（功能用例专用）

```python
class FunctionalTestCase(Base):
    """功能用例专用表"""
    __tablename__ = "functional_test_cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    testcase_id = Column(Integer, ForeignKey("test_cases.id"), unique=True, nullable=False)
    steps = Column(Text, default="[]")                              # 执行步骤 JSON
    test_data = Column(Text, default="{}")                         # 测试数据 JSON
    post_action = Column(Text, default="")                        # 后置动作
    expected_result = Column(Text, default="")                     # 预期结果
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    test_case = relationship("TestCase", backref="functional_case")
```

### 3.4 分类表：CaseFolder

```python
class CaseFolder(Base):
    """用例分类文件夹"""
    __tablename__ = "case_folders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    parent_id = Column(Integer, nullable=True)                     # 父级 ID，null 为根
    name = Column(String(200), nullable=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

---

## 4. 页面结构

### 4.1 路由

- 统一入口：`/case` → CaseManagement.vue（三栏布局）

### 4.2 组件结构

```
frontend/src/views/case/
├── CaseManagement.vue       # 主页面（三栏布局）
├── CaseSidebar.vue           # 左侧分类树
├── CaseList.vue             # 中间用例列表
├── CaseDetail.vue            # 右侧详情表单（动态）
├── ApiCaseForm.vue           # 接口用例表单（动态加载）
├── FunctionalCaseForm.vue    # 功能用例表单（动态加载）
└── CaseFolderDialog.vue      # 分类管理弹窗
```

### 4.3 三栏宽度

- 左侧目录树：240px（可折叠）
- 中间用例列表：min 500px，flex 1
- 右侧详情表单：480px

---

## 5. API 设计

### 5.1 用例相关

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/case` | GET | 获取用例列表（分页、筛选） |
| `/api/case` | POST | 创建用例 |
| `/api/case/{id}` | GET | 获取用例详情（含关联数据） |
| `/api/case/{id}` | PUT | 更新用例 |
| `/api/case/{id}` | DELETE | 删除用例 |
| `/api/case/{id}/copy` | POST | 复制用例 |

### 5.2 分类相关

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/case/folders` | GET | 获取分类树 |
| `/api/case/folders` | POST | 创建分类 |
| `/api/case/folders/{id}` | PUT | 更新分类 |
| `/api/case/folders/{id}` | DELETE | 删除分类 |

---

## 6. 字段设计

### 6.1 公共字段（TestCase）

| 字段名 | 组件 | 说明 |
|--------|------|------|
| 用例名称 | el-input | 必填，最大 100 字符 |
| 所属分类 | tree-select | 从分类树选择 |
| 用例类型 | el-radio-group | 接口/功能，切换时重置特有字段 |
| 优先级 | el-select | P0/P1/P2/P3 |
| 标签 | el-select(tags) | 多选 |
| 前置条件 | el-input textarea | |
| 描述 | el-input textarea | |

### 6.2 接口用例特有（ApiTestCase）

| 字段名 | 组件 | 说明 |
|--------|------|------|
| 请求方法 | el-select | GET/POST/PUT/DELETE/PATCH |
| URL | el-input | 支持变量 {{}} |
| 请求头 | 键值对表格 | |
| Query 参数 | 键值对表格 | |
| Body 类型 | el-radio-group | none/form/json/raw |
| Body 内容 | code-editor | |
| 认证配置 | collapse | Basic/Bearer/APIKey |
| 期望状态码 | el-input-number | |
| 断言规则 | 表格 | 字段/操作符/期望值 |

### 6.3 功能用例特有（FunctionalTestCase）

| 字段名 | 组件 | 说明 |
|--------|------|------|
| 执行步骤 | 步骤列表（可拖拽） | 步骤描述/预期结果/测试数据 |
| 测试数据 | JSON 编辑器 | |
| 后置动作 | textarea | |
| 预期结果 | textarea | |

---

## 7. 实现范围（第一版）

### 包含
1. 三栏布局完整呈现
2. 统一入口 `/case`
3. 分类树管理（CRUD）
4. 用例 CRUD（创建/编辑/复制/删除）
5. 类型切换，动态显示字段
6. 搜索和分页筛选

### 暂不实现
- 导入导出
- 批量操作
- 拖拽排序
- 用例执行（接口调试/功能步骤）

---

## 8. 技术选型

- **前端**：Vue3 + Pinia + Element Plus
- **后端**：FastAPI + SQLAlchemy
- **数据库**：SQLite（现有）
- **样式**：CSS 变量 + scoped

---

## 9. 目录树实现

- 支持无限深度
- 超过三级时水平滚动条
- 每个节点显示用例数量
- 右键菜单（新建/重命名/删除）
- 拖拽移动（暂不实现）

---

## 10. 状态管理

```javascript
// stores/caseStore.js
export const useCaseStore = defineStore('case', () => {
  // 状态
  const folders = ref([])              // 分类树
  const cases = ref([])                // 用例列表
  const currentCase = ref(null)        // 当前编辑的用例
  const loading = ref(false)

  // Actions
  async function fetchFolders() { ... }
  async function fetchCases(params) { ... }
  async function fetchCaseDetail(id) { ... }
  async function createCase(data) { ... }
  async function updateCase(id, data) { ... }
  async function deleteCase(id) { ... }
  async function copyCase(id) { ... }

  return { ... }
})
```