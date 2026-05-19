# 用例管理模块 v2 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用例管理模块重构为统一入口、三栏布局，数据库采用单主表+关联专用表结构

**Architecture:** 后端：TestCase主表 + ApiTestCase/FunctionalTestCase关联表；前端：CaseManagement.vue三栏布局，动态切换表单

**Tech Stack:** Vue3 + Pinia + Element Plus (前端), FastAPI + SQLAlchemy (后端)

---

## 文件结构

### 后端变更

**Models:**
- Modify: `backend/app/models/test_case.py` — 移除接口专用字段，保留公共字段
- Create: `backend/app/models/api_test_case.py` — ApiTestCase 模型
- Create: `backend/app/models/functional_test_case.py` — FunctionalTestCase 模型
- Modify: `backend/app/models/__init__.py` — 导出新模型
- Modify: `backend/app/database.py` — 添加新表迁移

**Schemas:**
- Modify: `backend/app/schemas/test_case.py` — 重构为公共字段
- Create: `backend/app/schemas/api_test_case.py` — ApiTestCase Schema
- Create: `backend/app/schemas/functional_test_case.py` — FunctionalTestCase Schema
- Modify: `backend/app/schemas/__init__.py` — 导出新Schema

**Routers:**
- Modify: `backend/app/routers/testcase.py` — 更新CRUD逻辑

**Services:**
- Modify: `backend/app/services/test_case_service.py` — 更新业务逻辑

### 前端变更

**Views:**
- Create: `frontend/src/views/case/CaseManagement.vue` — 主页面三栏布局
- Create: `frontend/src/views/case/CaseSidebar.vue` — 左侧分类树
- Create: `frontend/src/views/case/CaseList.vue` — 中间用例列表
- Create: `frontend/src/views/case/CaseDetail.vue` — 右侧详情表单（动态）
- Create: `frontend/src/views/case/ApiCaseForm.vue` — 接口用例表单
- Create: `frontend/src/views/case/FunctionalCaseForm.vue` — 功能用例表单
- Delete: `frontend/src/views/case/api/` — 旧接口测试页面
- Delete: `frontend/src/views/case/functional/` — 旧功能测试页面

**Store:**
- Modify: `frontend/src/stores/caseStore.js` — 更新状态管理

**Router:**
- Modify: `frontend/src/router/index.js` — 统一入口 `/case`

**Menu:**
- Modify: `frontend/src/app/AppShell.vue` — 更新菜单为单一入口

---

## 任务分解

### Task 1: 后端 - 重构 TestCase 主表模型

**Files:**
- Modify: `backend/app/models/test_case.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: 重构 TestCase 模型**

删除接口专用字段（method, url, query_params, headers, cookies, auth_config, body_type, body, expected_status），保留公共字段：

```python
# backend/app/models/test_case.py
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.models.base import Base


class TestCase(Base):
    """用例主表 - 存储公共字段"""
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    folder_id = Column(Integer, ForeignKey("case_folders.id"), nullable=True)
    priority = Column(String(10), default="P2")  # P0/P1/P2/P3
    tags = Column(Text, default="[]")  # JSON array
    pre_condition = Column(Text, default="")
    case_type = Column(String(20), nullable=False)  # 'api' | 'functional'
    source_debug_id = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    variants = relationship("CaseVariant", back_populates="test_case", cascade="all, delete-orphan")
```

- [ ] **Step 2: 更新 models/__init__.py**

```python
# backend/app/models/__init__.py
from .base import Base
from .platform import PlatformUser, PlatformRole, PlatformOrganization, PlatformMenu
from .terminal import DebugRequest, DebugResult
from .test_case import TestCase
from .case_folder import CaseFolder
from .api_test_case import ApiTestCase
from .functional_test_case import FunctionalTestCase

__all__ = [
    "Base",
    "PlatformUser",
    "PlatformRole",
    "PlatformOrganization",
    "PlatformMenu",
    "DebugRequest",
    "DebugResult",
    "TestCase",
    "CaseFolder",
    "ApiTestCase",
    "FunctionalTestCase",
]
```

- [ ] **Step 3: 更新数据库迁移添加新字段**

在 `backend/app/database.py` 的 `_run_migrations()` 中添加 priority 和 tags 字段迁移：

```python
def _run_migrations():
    """Run one-time migrations for schema changes that require ALTER TABLE."""
    from sqlalchemy import text

    db = Session(bind=engine)
    try:
        # Check test_cases table columns
        result = db.execute(text("PRAGMA table_info(test_cases)"))
        columns = [row[1] for row in result.fetchall()]

        if 'priority' not in columns:
            db.execute(text("ALTER TABLE test_cases ADD COLUMN priority VARCHAR(10) DEFAULT 'P2'"))

        if 'tags' not in columns:
            db.execute(text("ALTER TABLE test_cases ADD COLUMN tags TEXT DEFAULT '[]'"))

        if 'pre_condition' not in columns:
            db.execute(text("ALTER TABLE test_cases ADD COLUMN pre_condition TEXT DEFAULT ''"))

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/models/test_case.py backend/app/models/__init__.py backend/app/database.py
git commit -m "refactor(models): 重构 TestCase 主表，添加 priority/tags/pre_condition 字段"
```

---

### Task 2: 后端 - 创建 ApiTestCase 模型

**Files:**
- Create: `backend/app/models/api_test_case.py`
- Create: `backend/app/schemas/api_test_case.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/schemas/__init__.py`

- [ ] **Step 1: 创建 ApiTestCase 模型**

```python
# backend/app/models/api_test_case.py
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.models.base import Base


class ApiTestCase(Base):
    """接口用例专用表"""
    __tablename__ = "api_test_cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    testcase_id = Column(Integer, ForeignKey("test_cases.id"), unique=True, nullable=False)
    method = Column(String(10), default="GET")
    url = Column(String(2000), nullable=False)
    headers = Column(Text, default="{}")
    params = Column(Text, default="{}")
    body_type = Column(String(20), default="none")
    body = Column(Text, default="")
    auth_config = Column(Text, default="{}")
    expected_status = Column(Integer, default=200)
    assertions = Column(Text, default="[]")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    test_case = relationship("TestCase", back_populates="api_case")
```

- [ ] **Step 2: 创建 ApiTestCase Schema**

```python
# backend/app/schemas/api_test_case.py
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ApiTestCaseCreate(BaseModel):
    method: str = Field(default="GET", max_length=10)
    url: str = Field(..., max_length=2000)
    headers: Dict[str, Any] = Field(default_factory=dict)
    params: Dict[str, Any] = Field(default_factory=dict)
    body_type: str = Field(default="none", max_length=20)
    body: str = ""
    auth_config: Dict[str, Any] = Field(default_factory=dict)
    expected_status: int = Field(default=200)
    assertions: List[Dict[str, Any]] = Field(default_factory=list)


class ApiTestCaseUpdate(BaseModel):
    method: Optional[str] = Field(None, max_length=10)
    url: Optional[str] = Field(None, max_length=2000)
    headers: Optional[Dict[str, Any]] = None
    params: Optional[Dict[str, Any]] = None
    body_type: Optional[str] = Field(None, max_length=20)
    body: Optional[str] = None
    auth_config: Optional[Dict[str, Any]] = None
    expected_status: Optional[int] = None
    assertions: Optional[List[Dict[str, Any]]] = None


class ApiTestCaseResponse(BaseModel):
    id: int
    testcase_id: int
    method: str
    url: str
    headers: Dict[str, Any]
    params: Dict[str, Any]
    body_type: str
    body: str
    auth_config: Dict[str, Any]
    expected_status: int
    assertions: List[Dict[str, Any]]
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True
```

- [ ] **Step 3: 更新 __init__.py**

```python
# backend/app/models/__init__.py 添加 ApiTestCase 到 __all__
# backend/app/schemas/__init__.py 添加导入
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/models/api_test_case.py backend/app/schemas/api_test_case.py backend/app/models/__init__.py backend/app/schemas/__init__.py
git commit -m "feat(models): 添加 ApiTestCase 接口用例专用表"
```

---

### Task 3: 后端 - 创建 FunctionalTestCase 模型

**Files:**
- Create: `backend/app/models/functional_test_case.py`
- Create: `backend/app/schemas/functional_test_case.py`

- [ ] **Step 1: 创建 FunctionalTestCase 模型**

```python
# backend/app/models/functional_test_case.py
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.models.base import Base


class FunctionalTestCase(Base):
    """功能用例专用表"""
    __tablename__ = "functional_test_cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    testcase_id = Column(Integer, ForeignKey("test_cases.id"), unique=True, nullable=False)
    steps = Column(Text, default="[]")  # JSON array of steps
    test_data = Column(Text, default="{}")  # JSON object
    post_action = Column(Text, default="")
    expected_result = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    test_case = relationship("TestCase", back_populates="functional_case")
```

- [ ] **Step 2: 创建 FunctionalTestCase Schema**

```python
# backend/app/schemas/functional_test_case.py
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StepItem(BaseModel):
    """执行步骤项"""
    order: int
    description: str
    expected_result: str
    test_data: Dict[str, Any] = Field(default_factory=dict)


class FunctionalTestCaseCreate(BaseModel):
    steps: List[StepItem] = Field(default_factory=list)
    test_data: Dict[str, Any] = Field(default_factory=dict)
    post_action: str = ""
    expected_result: str = ""


class FunctionalTestCaseUpdate(BaseModel):
    steps: Optional[List[StepItem]] = None
    test_data: Optional[Dict[str, Any]] = None
    post_action: Optional[str] = None
    expected_result: Optional[str] = None


class FunctionalTestCaseResponse(BaseModel):
    id: int
    testcase_id: int
    steps: List[StepItem]
    test_data: Dict[str, Any]
    post_action: str
    expected_result: str
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True
```

- [ ] **Step 3: 更新 __init__.py**

```python
# backend/app/models/__init__.py 添加 FunctionalTestCase 到 __all__
# backend/app/schemas/__init__.py 添加导入
```

- [ ] **Step 4: 提交**

```bash
git add backend/app/models/functional_test_case.py backend/app/schemas/functional_test_case.py backend/app/models/__init__.py backend/app/schemas/__init__.py
git commit -m "feat(models): 添加 FunctionalTestCase 功能用例专用表"
```

---

### Task 4: 后端 - 重构 TestCase Schema

**Files:**
- Modify: `backend/app/schemas/test_case.py`

- [ ] **Step 1: 重构 TestCase Schema**

```python
# backend/app/schemas/test_case.py
from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field


class TestCaseCreate(BaseModel):
    name: str = Field(..., max_length=200)
    description: str = ""
    folder_id: Optional[int] = None
    priority: Literal["P0", "P1", "P2", "P3"] = Field(default="P2")
    tags: List[str] = Field(default_factory=list)
    pre_condition: str = ""
    case_type: Literal["api", "functional"] = Field(default="api")


class TestCaseUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    folder_id: Optional[int] = None
    priority: Optional[Literal["P0", "P1", "P2", "P3"]] = None
    tags: Optional[List[str]] = None
    pre_condition: Optional[str] = None


class TestCaseResponse(BaseModel):
    id: int
    name: str
    description: str = ""
    folder_id: Optional[int] = None
    priority: str = "P2"
    tags: List[str] = []
    pre_condition: str = ""
    case_type: Literal["api", "functional"]
    source_debug_id: Optional[int] = None
    created_by: Optional[int] = None
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class TestCaseListResponse(BaseModel):
    items: List[TestCaseResponse]
    total: int
    page: int
    page_size: int


class DeleteResponse(BaseModel):
    id: int
```

- [ ] **Step 2: 提交**

```bash
git add backend/app/schemas/test_case.py
git commit -m "refactor(schemas): 重构 TestCase Schema，移除接口专用字段"
```

---

### Task 5: 后端 - 更新 Router 和 Service

**Files:**
- Modify: `backend/app/routers/testcase.py`
- Modify: `backend/app/services/test_case_service.py`

- [ ] **Step 1: 更新 TestCaseService**

重构 `TestCaseService` 以处理关联表：

```python
# backend/app/services/test_case_service.py
from sqlalchemy.orm import Session
from app.models.test_case import TestCase
from app.models.api_test_case import ApiTestCase
from app.models.functional_test_case import FunctionalTestCase


class TestCaseService:
    def __init__(self, db: Session):
        self.db = db

    def create_case(self, data: dict) -> TestCase:
        """创建用例"""
        case_data = {
            "name": data["name"],
            "description": data.get("description", ""),
            "folder_id": data.get("folder_id"),
            "priority": data.get("priority", "P2"),
            "tags": json.dumps(data.get("tags", [])),
            "pre_condition": data.get("pre_condition", ""),
            "case_type": data.get("case_type", "api"),
        }
        test_case = TestCase(**case_data)
        self.db.add(test_case)
        self.db.flush()

        # 创建关联专用记录
        if test_case.case_type == "api":
            api_data = data.get("api_case", {})
            api_case = ApiTestCase(
                testcase_id=test_case.id,
                method=api_data.get("method", "GET"),
                url=api_data.get("url", ""),
                headers=json.dumps(api_data.get("headers", {})),
                params=json.dumps(api_data.get("params", {})),
                body_type=api_data.get("body_type", "none"),
                body=api_data.get("body", ""),
                auth_config=json.dumps(api_data.get("auth_config", {})),
                expected_status=api_data.get("expected_status", 200),
                assertions=json.dumps(api_data.get("assertions", [])),
            )
            self.db.add(api_case)
        else:
            func_data = data.get("functional_case", {})
            func_case = FunctionalTestCase(
                testcase_id=test_case.id,
                steps=json.dumps(func_data.get("steps", [])),
                test_data=json.dumps(func_data.get("test_data", {})),
                post_action=func_data.get("post_action", ""),
                expected_result=func_data.get("expected_result", ""),
            )
            self.db.add(func_case)

        self.db.commit()
        self.db.refresh(test_case)
        return test_case

    def get_case(self, case_id: int) -> Optional[dict]:
        """获取用例详情"""
        test_case = self.db.query(TestCase).filter(TestCase.id == case_id).first()
        if not test_case:
            return None

        result = self._case_to_dict(test_case)

        if test_case.case_type == "api":
            api_case = self.db.query(ApiTestCase).filter(ApiTestCase.testcase_id == case_id).first()
            if api_case:
                result["api_case"] = self._api_case_to_dict(api_case)
        else:
            func_case = self.db.query(FunctionalTestCase).filter(FunctionalTestCase.testcase_id == case_id).first()
            if func_case:
                result["functional_case"] = self._func_case_to_dict(func_case)

        return result

    def _case_to_dict(self, test_case):
        import json
        return {
            "id": test_case.id,
            "name": test_case.name,
            "description": test_case.description,
            "folder_id": test_case.folder_id,
            "priority": test_case.priority,
            "tags": json.loads(test_case.tags) if test_case.tags else [],
            "pre_condition": test_case.pre_condition,
            "case_type": test_case.case_type,
            "source_debug_id": test_case.source_debug_id,
            "created_by": test_case.created_by,
            "created_at": test_case.created_at.isoformat() if test_case.created_at else None,
            "updated_at": test_case.updated_at.isoformat() if test_case.updated_at else None,
        }

    def _api_case_to_dict(self, api_case):
        import json
        return {
            "id": api_case.id,
            "testcase_id": api_case.testcase_id,
            "method": api_case.method,
            "url": api_case.url,
            "headers": json.loads(api_case.headers) if api_case.headers else {},
            "params": json.loads(api_case.params) if api_case.params else {},
            "body_type": api_case.body_type,
            "body": api_case.body,
            "auth_config": json.loads(api_case.auth_config) if api_case.auth_config else {},
            "expected_status": api_case.expected_status,
            "assertions": json.loads(api_case.assertions) if api_case.assertions else [],
        }

    def _func_case_to_dict(self, func_case):
        import json
        return {
            "id": func_case.id,
            "testcase_id": func_case.testcase_id,
            "steps": json.loads(func_case.steps) if func_case.steps else [],
            "test_data": json.loads(func_case.test_data) if func_case.test_data else {},
            "post_action": func_case.post_action,
            "expected_result": func_case.expected_result,
        }
```

- [ ] **Step 2: 更新 Router**

更新 `backend/app/routers/testcase.py` 以适配新的 Schema：

```python
# backend/app/routers/testcase.py
@router.post("", response_model=TestCaseResponse)
def create_testcase(
    case: TestCaseCreate,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    service = TestCaseService(db)
    data = case.model_dump()
    data["created_by"] = current_user.id
    result = service.create_case(data)
    return result
```

- [ ] **Step 3: 提交**

```bash
git add backend/app/routers/testcase.py backend/app/services/test_case_service.py
git commit -m "refactor(service): 重构 TestCaseService 支持关联专用表"
```

---

### Task 6: 前端 - 创建 CaseManagement 主页面

**Files:**
- Create: `frontend/src/views/case/CaseManagement.vue`

- [ ] **Step 1: 创建三栏布局主页面**

```vue
<!-- frontend/src/views/case/CaseManagement.vue -->
<template>
  <div class="case-management">
    <el-container>
      <el-aside width="240px" class="case-sidebar">
        <CaseSidebar @folder-selected="handleFolderSelected" />
      </el-aside>
      <el-main class="case-list">
        <CaseList
          ref="caseListRef"
          :folder-id="currentFolderId"
          @case-selected="handleCaseSelected"
          @create-case="handleCreateCase"
        />
      </el-main>
      <el-aside width="480px" class="case-detail">
        <CaseDetail
          v-if="currentCase"
          :case-data="currentCase"
          @saved="handleSaved"
          @deleted="handleDeleted"
        />
        <div v-else class="case-detail-empty">
          <el-empty description="请选择用例或新建用例" />
        </div>
      </el-aside>
    </el-container>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import CaseSidebar from './CaseSidebar.vue'
import CaseList from './CaseList.vue'
import CaseDetail from './CaseDetail.vue'

const currentFolderId = ref(null)
const currentCase = ref(null)
const caseListRef = ref(null)

function handleFolderSelected(folderId) {
  currentFolderId.value = folderId
}

function handleCaseSelected(caseItem) {
  currentCase.value = caseItem
}

function handleCreateCase() {
  currentCase.value = { id: null, isNew: true }
}

function handleSaved() {
  caseListRef.value?.reload()
}

function handleDeleted() {
  currentCase.value = null
  caseListRef.value?.reload()
}
</script>

<style scoped>
.case-management {
  height: 100%;
  background: var(--bg-page);
}

.case-sidebar {
  background: var(--bg-container);
  border-right: 1px solid var(--border-color);
  overflow-y: auto;
}

.case-list {
  background: var(--bg-page);
  padding: 0;
  overflow-y: auto;
}

.case-detail {
  background: var(--bg-container);
  border-left: 1px solid var(--border-color);
  overflow-y: auto;
}

.case-detail-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/case/CaseManagement.vue
git commit -m "feat(frontend): 创建 CaseManagement 三栏布局主页面"
```

---

### Task 7: 前端 - 重构 CaseSidebar

**Files:**
- Modify: `frontend/src/views/case/CaseSidebar.vue`

- [ ] **Step 1: 重构分类树组件**

```vue
<!-- frontend/src/views/case/CaseSidebar.vue -->
<template>
  <div class="case-sidebar">
    <div class="sidebar-header">
      <span class="sidebar-title">用例分类</span>
      <el-button size="small" :icon="Plus" @click="handleCreateFolder">新建</el-button>
    </div>

    <div class="folder-search">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索分类"
        size="small"
        clearable
        :prefix-icon="Search"
      />
    </div>

    <div class="folder-tree">
      <el-tree
        :data="folderTree"
        :props="{ label: 'name', children: 'children' }"
        node-key="id"
        :expand-on-click-node="false"
        :filter-node-method="filterNode"
        :default-expand-all="true"
        ref="treeRef"
        @node-click="handleNodeClick"
      >
        <template #default="{ node, data }">
          <span class="folder-node">
            <el-icon><Folder /></el-icon>
            <span class="folder-name">{{ node.label }}</span>
          </span>
        </template>
      </el-tree>
    </div>

    <el-dialog v-model="showFolderDialog" title="新建分类" width="400px">
      <el-form :model="folderForm" label-width="80px">
        <el-form-item label="分类名称">
          <el-input v-model="folderForm.name" placeholder="请输入分类名称" />
        </el-form-item>
        <el-form-item label="上级分类">
          <el-tree-select
            v-model="folderForm.parent_id"
            :data="folderTree"
            :props="{ label: 'name', value: 'id' }"
            placeholder="选择上级分类（可选）"
            clearable
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showFolderDialog = false">取消</el-button>
        <el-button type="primary" @click="handleDoCreateFolder">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Search, Folder, Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { caseApi } from '@/api/case'

const emit = defineEmits(['folder-selected'])

const searchKeyword = ref('')
const folderTree = ref([])
const treeRef = ref(null)
const showFolderDialog = ref(false)
const folderForm = ref({ name: '', parent_id: null })

async function loadFolders() {
  try {
    const res = await caseApi.listFolders({})
    folderTree.value = buildTree(res.data.items)
  } catch {
    ElMessage.error('加载分类失败')
  }
}

function buildTree(folders) {
  const map = {}
  const roots = []
  folders.forEach(f => {
    map[f.id] = { ...f, children: [] }
  })
  folders.forEach(f => {
    if (f.parent_id && map[f.parent_id]) {
      map[f.parent_id].children.push(map[f.id])
    } else {
      roots.push(map[f.id])
    }
  })
  return roots
}

function filterNode(keyword, data) {
  if (!keyword) return true
  return data.name.includes(keyword)
}

function handleNodeClick(data) {
  emit('folder-selected', data.id)
}

function handleCreateFolder() {
  folderForm.value = { name: '', parent_id: null }
  showFolderDialog.value = true
}

async function handleDoCreateFolder() {
  if (!folderForm.value.name) {
    ElMessage.warning('请输入分类名称')
    return
  }
  try {
    await caseApi.createFolder(folderForm.value)
    ElMessage.success('创建成功')
    showFolderDialog.value = false
    loadFolders()
  } catch {
    ElMessage.error('创建失败')
  }
}

watch(searchKeyword, (val) => {
  treeRef.value?.filter(val)
})

onMounted(() => {
  loadFolders()
})

defineExpose({ reload: loadFolders })
</script>

<style scoped>
.case-sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
}

.sidebar-title {
  font-weight: 600;
  color: var(--text-primary);
}

.folder-search {
  padding: 8px 12px;
  border-bottom: 1px solid var(--border-color);
}

.folder-tree {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.folder-node {
  display: flex;
  align-items: center;
  gap: 6px;
}

.folder-name {
  color: var(--text-primary);
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/case/CaseSidebar.vue
git commit -m "refactor(frontend): 重构 CaseSidebar 支持分类CRUD"
```

---

### Task 8: 前端 - 重构 CaseList

**Files:**
- Modify: `frontend/src/views/case/CaseList.vue`

- [ ] **Step 1: 重构用例列表组件**

```vue
<!-- frontend/src/views/case/CaseList.vue -->
<template>
  <div class="case-list-container">
    <div class="list-header">
      <el-input
        v-model="keyword"
        placeholder="搜索用例名称"
        style="width: 300px"
        clearable
        @keyup.enter="handleSearch"
      >
        <template #append>
          <el-button :icon="Search" @click="handleSearch" />
        </template>
      </el-input>
      <el-button type="primary" :icon="Plus" @click="handleCreate">新建用例</el-button>
    </div>

    <el-table
      v-loading="caseStore.loading"
      :data="caseStore.cases"
      style="width: 100%"
      @row-click="handleRowClick"
      highlight-current-row
    >
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="用例名称" min-width="200">
        <template #default="{ row }">
          <span class="text-ellipsis" :title="row.name">{{ row.name }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="case_type" label="类型" width="100">
        <template #default="{ row }">
          <el-tag :type="row.case_type === 'api' ? 'success' : 'warning'" size="small">
            {{ row.case_type === 'api' ? '接口' : '功能' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="priority" label="优先级" width="80">
        <template #default="{ row }">
          <el-tag :type="getPriorityType(row.priority)" size="small">{{ row.priority }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="updated_at" label="更新时间" width="160" />
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" size="small" text @click.stop="handleCopy(row)">复制</el-button>
          <el-button type="danger" size="small" text @click.stop="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="currentPageSize"
      :total="caseStore.total"
      :page-sizes="[10, 20, 50, 100]"
      layout="total, sizes, prev, pager, next"
      style="margin-top: 16px"
      @current-change="handlePageChange"
      @size-change="handleSizeChange"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { Search, Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useCaseStore } from '@/stores/caseStore'

const emit = defineEmits(['case-selected', 'create-case'])

const props = defineProps({
  folderId: {
    type: Number,
    default: null
  }
})

const caseStore = useCaseStore()
const keyword = ref('')
const currentPage = ref(1)
const currentPageSize = ref(20)

function getPriorityType(priority) {
  const map = { P0: 'danger', P1: 'warning', P2: 'info', P3: '' }
  return map[priority] || ''
}

async function loadCases() {
  try {
    await caseStore.fetchCases({
      folder_id: props.folderId || undefined,
      page: currentPage.value,
      page_size: currentPageSize.value,
      keyword: keyword.value || undefined,
    })
  } catch {
    ElMessage.error(caseStore.error || '加载用例失败')
  }
}

function handleSearch() {
  currentPage.value = 1
  loadCases()
}

function handlePageChange(page) {
  currentPage.value = page
  loadCases()
}

function handleSizeChange(size) {
  currentPageSize.value = size
  currentPage.value = 1
  loadCases()
}

function handleRowClick(row) {
  emit('case-selected', row)
}

function handleCreate() {
  emit('create-case')
}

async function handleCopy(row) {
  try {
    await caseApi.copy(row.id)
    ElMessage.success('复制成功')
    loadCases()
  } catch {
    ElMessage.error('复制失败')
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除用例 "${row.name}" 吗？`, '确认删除', { type: 'warning' })
    await caseStore.deleteCase(row.id)
    ElMessage.success('删除成功')
    if (caseStore.cases.length === 0 && currentPage.value > 1) {
      currentPage.value--
      loadCases()
    }
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(caseStore.error || '删除失败')
    }
  }
}

watch(() => props.folderId, () => {
  currentPage.value = 1
  loadCases()
})

onMounted(() => {
  loadCases()
})

defineExpose({ reload: loadCases })
</script>

<style scoped>
.case-list-container {
  padding: 16px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.list-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/views/case/CaseList.vue
git commit -m "refactor(frontend): 重构 CaseList 支持完整筛选"
```

---

### Task 9: 前端 - 重构 CaseDetail（动态表单）

**Files:**
- Modify: `frontend/src/views/case/CaseDetail.vue`
- Create: `frontend/src/views/case/ApiCaseForm.vue`
- Create: `frontend/src/views/case/FunctionalCaseForm.vue`

- [ ] **Step 1: 创建 ApiCaseForm.vue**

```vue
<!-- frontend/src/views/case/ApiCaseForm.vue -->
<template>
  <div class="api-case-form">
    <el-form :model="formData" label-width="100px">
      <el-form-item label="请求方法">
        <el-select v-model="formData.method" style="width: 150px">
          <el-option v-for="m in methods" :key="m" :label="m" :value="m" />
        </el-select>
      </el-form-item>

      <el-form-item label="URL" required>
        <el-input v-model="formData.url" placeholder="请输入请求 URL" />
      </el-form-item>

      <el-form-item label="请求头">
        <KeyValueEditor v-model="formData.headers" placeholder="参数值" />
      </el-form-item>

      <el-form-item label="Query 参数">
        <KeyValueEditor v-model="formData.params" placeholder="参数值" />
      </el-form-item>

      <el-form-item label="Body 类型">
        <el-radio-group v-model="formData.body_type">
          <el-radio label="none">无</el-radio>
          <el-radio label="form">form</el-radio>
          <el-radio label="json">JSON</el-radio>
          <el-radio label="raw">Raw</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="Body 内容" v-if="formData.body_type !== 'none'">
        <el-input
          v-model="formData.body"
          type="textarea"
          :rows="4"
          placeholder="请输入请求体"
        />
      </el-form-item>

      <el-form-item label="认证配置">
        <AuthEditor v-model="formData.auth_config" />
      </el-form-item>

      <el-form-item label="期望状态码">
        <el-input-number v-model="formData.expected_status" :min="100" :max="599" />
      </el-form-item>

      <el-form-item label="断言规则">
        <AssertionEditor v-model="formData.assertions" />
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import KeyValueEditor from '@/components/terminal/KeyValueEditor.vue'
import AuthEditor from '@/components/terminal/AuthEditor.vue'
import AssertionEditor from '@/components/case/AssertionEditor.vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue'])

const methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']

const formData = ref({
  method: 'GET',
  url: '',
  headers: [],
  params: [],
  body_type: 'none',
  body: '',
  auth_config: {},
  expected_status: 200,
  assertions: [],
})

watch(() => props.modelValue, (val) => {
  if (val) {
    formData.value = { ...formData.value, ...val }
  }
}, { immediate: true })

watch(formData, (val) => {
  emit('update:modelValue', val)
}, { deep: true })
</script>

<style scoped>
.api-case-form {
  padding: 16px;
}
</style>
```

- [ ] **Step 2: 创建 FunctionalCaseForm.vue**

```vue
<!-- frontend/src/views/case/FunctionalCaseForm.vue -->
<template>
  <div class="functional-case-form">
    <el-form :model="formData" label-width="100px">
      <el-form-item label="执行步骤">
        <div class="steps-list">
          <div v-for="(step, index) in formData.steps" :key="index" class="step-item">
            <el-input-number v-model="step.order" :min="1" size="small" style="width: 80px" />
            <el-input v-model="step.description" placeholder="步骤描述" size="small" style="flex: 1" />
            <el-input v-model="step.expected_result" placeholder="预期结果" size="small" style="flex: 1" />
            <el-button type="danger" :icon="Delete" size="small" @click="removeStep(index)" />
          </div>
          <el-button :icon="Plus" @click="addStep">添加步骤</el-button>
        </div>
      </el-form-item>

      <el-form-item label="测试数据">
        <el-input
          v-model="testDataJson"
          type="textarea"
          :rows="4"
          placeholder="JSON 格式测试数据"
          @blur="handleTestDataBlur"
        />
      </el-form-item>

      <el-form-item label="后置动作">
        <el-input
          v-model="formData.post_action"
          type="textarea"
          :rows="2"
          placeholder="清理数据、重置状态等"
        />
      </el-form-item>

      <el-form-item label="预期结果">
        <el-input
          v-model="formData.expected_result"
          type="textarea"
          :rows="2"
          placeholder="请输入预期结果"
        />
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { Plus, Delete } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue'])

const formData = ref({
  steps: [],
  test_data: {},
  post_action: '',
  expected_result: '',
})

const testDataJson = computed({
  get: () => JSON.stringify(formData.value.test_data, null, 2),
  set: (val) => {
    try {
      formData.value.test_data = JSON.parse(val)
    } catch {}
  }
})

function addStep() {
  formData.value.steps.push({
    order: formData.value.steps.length + 1,
    description: '',
    expected_result: '',
    test_data: {},
  })
}

function removeStep(index) {
  formData.value.steps.splice(index, 1)
}

function handleTestDataBlur() {
  try {
    formData.value.test_data = JSON.parse(testDataJson.value)
  } catch {
    ElMessage.error('JSON 格式错误')
  }
}

watch(() => props.modelValue, (val) => {
  if (val) {
    formData.value = { ...formData.value, ...val }
  }
}, { immediate: true })

watch(formData, (val) => {
  emit('update:modelValue', val)
}, { deep: true })
</script>

<style scoped>
.functional-case-form {
  padding: 16px;
}

.steps-list {
  width: 100%;
}

.step-item {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  align-items: center;
}
</style>
```

- [ ] **Step 3: 创建 CaseDetail.vue（动态表单）**

```vue
<!-- frontend/src/views/case/CaseDetail.vue -->
<template>
  <div class="case-detail">
    <div class="detail-header">
      <span class="detail-title">{{ isNew ? '新建用例' : '编辑用例' }}</span>
      <div class="detail-actions">
        <el-button @click="handleCancel">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </div>
    </div>

    <el-form :model="caseForm" label-width="100px" class="detail-form">
      <el-form-item label="用例名称" required>
        <el-input v-model="caseForm.name" placeholder="请输入用例名称" />
      </el-form-item>

      <el-form-item label="用例类型">
        <el-radio-group v-model="caseForm.case_type" :disabled="!isNew">
          <el-radio label="api">接口用例</el-radio>
          <el-radio label="functional">功能用例</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="所属分类">
        <el-tree-select
          v-model="caseForm.folder_id"
          :data="folderTree"
          :props="{ label: 'name', value: 'id' }"
          placeholder="选择分类"
          clearable
        />
      </el-form-item>

      <el-form-item label="优先级">
        <el-select v-model="caseForm.priority" style="width: 150px">
          <el-option label="P0" value="P0" />
          <el-option label="P1" value="P1" />
          <el-option label="P2" value="P2" />
          <el-option label="P3" value="P3" />
        </el-select>
      </el-form-item>

      <el-form-item label="标签">
        <el-select v-model="caseForm.tags" multiple placeholder="选择标签" style="width: 100%">
          <el-option v-for="tag in availableTags" :key="tag" :label="tag" :value="tag" />
        </el-select>
      </el-form-item>

      <el-form-item label="前置条件">
        <el-input v-model="caseForm.pre_condition" type="textarea" :rows="2" placeholder="请输入前置条件" />
      </el-form-item>

      <el-form-item label="描述">
        <el-input v-model="caseForm.description" type="textarea" :rows="2" placeholder="请输入描述" />
      </el-form-item>

      <el-divider content-position="left">类型特有字段</el-divider>

      <ApiCaseForm v-if="caseForm.case_type === 'api'" v-model="caseForm.api_case" />
      <FunctionalCaseForm v-else v-model="caseForm.functional_case" />
    </el-form>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useCaseStore } from '@/stores/caseStore'
import { caseApi } from '@/api/case'
import ApiCaseForm from './ApiCaseForm.vue'
import FunctionalCaseForm from './FunctionalCaseForm.vue'

const props = defineProps({
  caseData: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['saved', 'deleted'])

const caseStore = useCaseStore()
const folderTree = ref([])
const availableTags = ['登录', '支付', '用户', '订单', '安全', '性能']

const isNew = computed(() => !props.caseData?.id)
const caseForm = ref({
  name: '',
  case_type: 'api',
  folder_id: null,
  priority: 'P2',
  tags: [],
  pre_condition: '',
  description: '',
  api_case: {},
  functional_case: {},
})

watch(() => props.caseData, (val) => {
  if (val?.id) {
    caseForm.value = { ...caseForm.value, ...val }
  } else {
    caseForm.value = {
      name: '',
      case_type: 'api',
      folder_id: null,
      priority: 'P2',
      tags: [],
      pre_condition: '',
      description: '',
      api_case: {},
      functional_case: {},
    }
  }
}, { immediate: true })

async function loadFolders() {
  try {
    const res = await caseApi.listFolders({})
    folderTree.value = buildTree(res.data.items)
  } catch {}
}

function buildTree(folders) {
  const map = {}
  const roots = []
  folders.forEach(f => {
    map[f.id] = { ...f, children: [] }
  })
  folders.forEach(f => {
    if (f.parent_id && map[f.parent_id]) {
      map[f.parent_id].children.push(map[f.id])
    } else {
      roots.push(map[f.id])
    }
  })
  return roots
}

async function handleSave() {
  if (!caseForm.value.name) {
    return
  }
  try {
    if (isNew.value) {
      await caseApi.create(caseForm.value)
    } else {
      await caseApi.update(props.caseData.id, caseForm.value)
    }
    emit('saved')
  } catch {}
}

function handleCancel() {
  emit('deleted')
}

onMounted(() => {
  loadFolders()
})
</script>

<style scoped>
.case-detail {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
}

.detail-title {
  font-weight: 600;
  color: var(--text-primary);
}

.detail-actions {
  display: flex;
  gap: 8px;
}

.detail-form {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}
</style>
```

- [ ] **Step 4: 提交**

```bash
git add frontend/src/views/case/CaseDetail.vue frontend/src/views/case/ApiCaseForm.vue frontend/src/views/case/FunctionalCaseForm.vue
git commit -m "feat(frontend): 创建 CaseDetail 动态表单及专用表单组件"
```

---

### Task 10: 前端 - 更新路由和菜单

**Files:**
- Modify: `frontend/src/router/index.js`
- Modify: `frontend/src/app/AppShell.vue`
- Delete: `frontend/src/views/case/api/` (旧页面)
- Delete: `frontend/src/views/case/functional/` (旧页面)

- [ ] **Step 1: 更新路由**

```javascript
// frontend/src/router/index.js
{
  path: 'case',
  name: 'CaseManagement',
  component: () => import('../views/case/CaseManagement.vue'),
},
```

- [ ] **Step 2: 更新菜单**

```javascript
// frontend/src/app/AppShell.vue
{
  title: '工具',
  icon: MenuIcon,
  path: '/tools',
  children: [
    { title: '终端调试台', icon: Connection, path: '/terminal' },
    { title: '用例管理', icon: DocumentChecked, path: '/case' },
  ],
},
```

- [ ] **Step 3: 删除旧文件**

```bash
rm -rf frontend/src/views/case/api frontend/src/views/case/functional
```

- [ ] **Step 4: 提交**

```bash
git add frontend/src/router/index.js frontend/src/app/AppShell.vue
git rm -rf frontend/src/views/case/api frontend/src/views/case/functional
git commit -m "refactor(frontend): 统一用例管理入口，删除旧页面"
```

---

### Task 11: 前端 - 更新 caseStore

**Files:**
- Modify: `frontend/src/stores/caseStore.js`
- Modify: `frontend/src/api/case.js`

- [ ] **Step 1: 更新 caseStore**

```javascript
// frontend/src/stores/caseStore.js
export const useCaseStore = defineStore('case', () => {
  const cases = ref([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const currentCase = ref(null)
  const folders = ref([])
  const loading = ref(false)
  const error = ref('')

  async function fetchCases(params = {}) {
    loading.value = true
    error.value = ''
    try {
      const response = await caseApi.list({
        page: params.page || page.value,
        page_size: params.page_size || pageSize.value,
        ...(params.folder_id && { folder_id: params.folder_id }),
        ...(params.keyword && { keyword: params.keyword }),
      })
      cases.value = response.data.items
      total.value = response.data.total
      page.value = response.data.page
      pageSize.value = response.data.page_size
    } catch (err) {
      error.value = err.message || '获取用例列表失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchCase(id) {
    loading.value = true
    error.value = ''
    try {
      const response = await caseApi.get(id)
      currentCase.value = response.data
      return currentCase.value
    } catch (err) {
      error.value = err.message || '获取用例详情失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createCase(data) {
    loading.value = true
    error.value = ''
    try {
      const response = await caseApi.create(data)
      return response.data
    } catch (err) {
      error.value = err.message || '创建用例失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateCase(id, data) {
    loading.value = true
    error.value = ''
    try {
      const response = await caseApi.update(id, data)
      currentCase.value = response.data
      return currentCase.value
    } catch (err) {
      error.value = err.message || '更新用例失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteCase(id) {
    loading.value = true
    error.value = ''
    try {
      await caseApi.delete(id)
      cases.value = cases.value.filter(c => c.id !== id)
      if (currentCase.value?.id === id) {
        currentCase.value = null
      }
      total.value = Math.max(0, total.value - 1)
    } catch (err) {
      error.value = err.message || '删除用例失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    cases, total, page, pageSize, currentCase, folders, loading, error,
    fetchCases, fetchCase, createCase, updateCase, deleteCase,
  }
})
```

- [ ] **Step 2: 更新 caseApi**

```javascript
// frontend/src/api/case.js
export const caseApi = {
  list(params) {
    return client.get('/api/case', { params })
  },
  get(id) {
    return client.get(`/api/case/${id}`)
  },
  create(data) {
    return client.post('/api/case', data)
  },
  update(id, data) {
    return client.put(`/api/case/${id}`, data)
  },
  delete(id) {
    return client.delete(`/api/case/${id}`)
  },
  copy(id) {
    return client.post(`/api/case/${id}/copy`)
  },
  listFolders(params) {
    return client.get('/api/case/folders', { params })
  },
  createFolder(data) {
    return client.post('/api/case/folders', data)
  },
  updateFolder(id, data) {
    return client.put(`/api/case/folders/${id}`, data)
  },
  deleteFolder(id) {
    return client.delete(`/api/case/folders/${id}`)
  },
}
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/stores/caseStore.js frontend/src/api/case.js
git commit -m "feat(frontend): 更新 caseStore 和 caseApi 支持 v2 接口"
```

---

### Task 12: 验证测试

- [ ] **Step 1: 启动后端验证**

```bash
cd backend
python -m uvicorn app.main:app --reload
# 验证接口：
# GET /api/case/folders
# POST /api/case
# GET /api/case/{id}
```

- [ ] **Step 2: 启动前端验证**

```bash
cd frontend
npm run dev
# 验证页面：
# /case 三栏布局
# 分类树加载
# 用例列表加载
# 新建/编辑用例
```

- [ ] **Step 3: 提交最终代码**

```bash
git add -A
git commit -m "feat: 完成用例管理模块 v2 重构"
```

---

## 实施检查清单

| 任务 | 描述 | 状态 |
|------|------|------|
| Task 1 | 后端重构 TestCase 主表 | ⬜ |
| Task 2 | 后端创建 ApiTestCase 模型 | ⬜ |
| Task 3 | 后端创建 FunctionalTestCase 模型 | ⬜ |
| Task 4 | 后端重构 TestCase Schema | ⬜ |
| Task 5 | 后端更新 Router 和 Service | ⬜ |
| Task 6 | 前端创建 CaseManagement 页面 | ⬜ |
| Task 7 | 前端重构 CaseSidebar | ⬜ |
| Task 8 | 前端重构 CaseList | ⬜ |
| Task 9 | 前端重构 CaseDetail（动态表单） | ⬜ |
| Task 10 | 前端更新路由和菜单 | ⬜ |
| Task 11 | 前端更新 caseStore | ⬜ |
| Task 12 | 验证测试 | ⬜ |

---

**Plan complete and saved to `docs/superpowers/plans/2026-05-19-case-module-v2-implementation.md`**