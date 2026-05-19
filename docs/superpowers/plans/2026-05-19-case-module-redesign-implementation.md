# 用例模块重新设计实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用例模块按功能测试/接口测试分类，采用左侧分类+三栏布局，与终端调试台深度打通

**Architecture:** 前端采用独立页面(/case/functional, /case/api)承载两类用例，每页左侧为分类树(文件夹+标签)，中间为用例列表，右侧为用例详情。后端在现有testcase表增加case_type字段，新增folder/tag表，支持分类筛选。终端调试台"保存为用例"功能直接跳转创建页并预填充数据。

**Tech Stack:** Vue3 + Pinia + Element Plus (前端), FastAPI + SQLAlchemy (后端)

---

## 文件结构

### 后端变更
- Modify: `backend/app/models/test_case.py` — 添加 case_type 字段和文件夹/标签模型
- Modify: `backend/app/schemas/test_case.py` — 添加 case_type 到请求/响应模型
- Modify: `backend/app/routers/testcase.py` — 添加分类相关路由，支持 case_type 筛选
- Create: `backend/app/models/case_folder.py` — 文件夹模型
- Create: `backend/app/schemas/case_folder.py` — 文件夹 Schema
- Create: `backend/app/routers/case_folder.py` — 文件夹 CRUD 路由

### 前端变更
- Modify: `frontend/src/router/index.js` — 添加 /case/functional 和 /case/api 路由
- Create: `frontend/src/views/case/CaseSidebar.vue` — 左侧分类树组件
- Create: `frontend/src/views/case/functional/FunctionalCase.vue` — 功能测试用例页面
- Create: `frontend/src/views/case/api/ApiCase.vue` — 接口测试用例页面
- Modify: `frontend/src/api/case.js` — 添加分类相关 API
- Modify: `frontend/src/stores/caseStore.js` — 支持 case_type、folders、tags 状态
- Modify: `frontend/src/views/terminal/Terminal.vue` — 添加"保存为用例"按钮

---

## 任务分解

### Task 1: 后端 - 添加 case_type 字段到 TestCase 模型

**Files:**
- Modify: `backend/app/models/test_case.py:9-31`

- [ ] **Step 1: 添加 case_type 字段到 TestCase 模型**

```python
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class TestCase(Base):
    """Test case for API testing."""
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_type = Column(String(20), nullable=False, default="api")  # 'functional' | 'api'
    folder_id = Column(Integer, nullable=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    method = Column(String(10), nullable=False, default="GET")
    url = Column(String(2000), nullable=False)
    query_params = Column(Text, default="{}")  # JSON string
    headers = Column(Text, default="{}")  # JSON string
    cookies = Column(Text, default="{}")  # JSON string
    auth_config = Column(Text, default="{}")  # JSON string
    body_type = Column(String(20), default="none")  # none, json, form, raw
    body = Column(Text, default="")
    expected_status = Column(Integer, nullable=True)
    source_debug_id = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    variants = relationship("CaseVariant", back_populates="test_case", cascade="all, delete-orphan")
```

- [ ] **Step 2: 更新 TestCaseCreate 和 TestCaseUpdate Schema**

```python
class TestCaseCreate(BaseModel):
    case_type: str = Field(default="api", max_length=20)  # 'functional' | 'api'
    folder_id: Optional[int] = None
    name: str = Field(..., max_length=200)
    description: str = ""
    method: str = Field(default="GET", max_length=10)
    url: str = Field(..., max_length=2000)
    query_params: Dict[str, Any] = Field(default_factory=dict)
    headers: Dict[str, Any] = Field(default_factory=dict)
    cookies: Dict[str, Any] = Field(default_factory=dict)
    auth_config: Dict[str, Any] = Field(default_factory=dict)
    body_type: str = Field(default="none", max_length=20)
    body: str = ""
    expected_status: Optional[int] = None
    source_debug_id: Optional[int] = None


class TestCaseUpdate(BaseModel):
    case_type: Optional[str] = Field(None, max_length=20)
    folder_id: Optional[int] = None
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    method: Optional[str] = Field(None, max_length=10)
    url: Optional[str] = Field(None, max_length=2000)
    query_params: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, Any]] = None
    cookies: Optional[Dict[str, Any]] = None
    auth_config: Optional[Dict[str, Any]] = None
    body_type: Optional[str] = Field(None, max_length=20)
    body: Optional[str] = None
    expected_status: Optional[int] = None
    source_debug_id: Optional[int] = None


class TestCaseResponse(BaseModel):
    id: int
    case_type: str
    folder_id: Optional[int] = None
    name: str
    description: str = ""
    method: str
    url: str
    query_params: Dict[str, Any]
    headers: Dict[str, Any]
    cookies: Dict[str, Any]
    auth_config: Dict[str, Any]
    body_type: str
    body: str
    expected_status: Optional[int] = None
    source_debug_id: Optional[int] = None
    created_by: Optional[int] = None
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True
```

- [ ] **Step 3: 更新 list_testcases 路由支持 case_type 筛选**

```python
@router.get("", response_model=TestCaseListResponse)
def list_testcases(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    case_type: Optional[str] = Query(None, description="用例类型: functional 或 api"),
    folder_id: Optional[int] = Query(None),
    keyword: Optional[str] = Query(None),
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    """List test cases with pagination."""
    service = TestCaseService(db)
    items, total = service.list_cases(
        page=page, page_size=page_size, case_type=case_type, folder_id=folder_id, keyword=keyword
    )
    return TestCaseListResponse(items=items, total=total, page=page, page_size=page_size)
```

- [ ] **Step 4: 提交代码**

```bash
git add backend/app/models/test_case.py backend/app/schemas/test_case.py backend/app/routers/testcase.py
git commit -m "feat(backend): 添加 case_type 字段到 TestCase 模型"
```

---

### Task 2: 后端 - 创建 CaseFolder 文件夹模型和路由

**Files:**
- Create: `backend/app/models/case_folder.py`
- Create: `backend/app/schemas/case_folder.py`
- Create: `backend/app/routers/case_folder.py`
- Modify: `backend/app/models/__init__.py` — 导出新模型
- Modify: `backend/app/routers/__init__.py` — 注册新路由

- [ ] **Step 1: 创建 CaseFolder 模型**

```python
# backend/app/models/case_folder.py
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.models.base import Base


class CaseFolder(Base):
    """用例文件夹分类"""
    __tablename__ = "case_folders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_type = Column(String(20), nullable=False, default="api")  # 'functional' | 'api'
    parent_id = Column(Integer, nullable=True)
    name = Column(String(200), nullable=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

- [ ] **Step 2: 创建 CaseFolder Schema**

```python
# backend/app/schemas/case_folder.py
from typing import List, Optional

from pydantic import BaseModel, Field


class CaseFolderCreate(BaseModel):
    case_type: str = Field(default="api", max_length=20)
    parent_id: Optional[int] = None
    name: str = Field(..., max_length=200)
    sort_order: int = Field(default=0)


class CaseFolderUpdate(BaseModel):
    parent_id: Optional[int] = None
    name: Optional[str] = Field(None, max_length=200)
    sort_order: Optional[int] = None


class CaseFolderResponse(BaseModel):
    id: int
    case_type: str
    parent_id: Optional[int] = None
    name: str
    sort_order: int
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class CaseFolderTreeResponse(BaseModel):
    items: List[CaseFolderResponse]
    total: int
```

- [ ] **Step 3: 创建 CaseFolder 路由**

```python
# backend/app/routers/case_folder.py
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.platform import PlatformUser
from app.routers.platform_auth import get_current_platform_user
from app.schemas.case_folder import (
    CaseFolderCreate,
    CaseFolderResponse,
    CaseFolderTreeResponse,
    CaseFolderUpdate,
)

router = APIRouter(prefix="/api/case/folders", tags=["用例分类"])


@router.post("", response_model=CaseFolderResponse)
def create_folder(
    folder: CaseFolderCreate,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    """Create a new folder."""
    from app.models.case_folder import CaseFolder
    db_folder = CaseFolder(**folder.model_dump())
    db.add(db_folder)
    db.commit()
    db.refresh(db_folder)
    return db_folder


@router.get("", response_model=CaseFolderTreeResponse)
def list_folders(
    case_type: Optional[str] = Query(None, description="用例类型: functional 或 api"),
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    """List folders."""
    from app.models.case_folder import CaseFolder
    query = db.query(CaseFolder)
    if case_type:
        query = query.filter(CaseFolder.case_type == case_type)
    folders = query.order_by(CaseFolder.sort_order, CaseFolder.id).all()
    return CaseFolderTreeResponse(items=folders, total=len(folders))


@router.get("/{folder_id}", response_model=CaseFolderResponse)
def get_folder(
    folder_id: int,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    """Get a folder by ID."""
    from app.models.case_folder import CaseFolder
    folder = db.query(CaseFolder).filter(CaseFolder.id == folder_id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    return folder


@router.put("/{folder_id}", response_model=CaseFolderResponse)
def update_folder(
    folder_id: int,
    folder: CaseFolderUpdate,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    """Update a folder."""
    from app.models.case_folder import CaseFolder
    db_folder = db.query(CaseFolder).filter(CaseFolder.id == folder_id).first()
    if not db_folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    update_data = folder.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_folder, key, value)
    db.commit()
    db.refresh(db_folder)
    return db_folder


@router.delete("/{folder_id}")
def delete_folder(
    folder_id: int,
    current_user: PlatformUser = Depends(get_current_platform_user),
    db: Session = Depends(get_db),
):
    """Delete a folder."""
    from app.models.case_folder import CaseFolder
    folder = db.query(CaseFolder).filter(CaseFolder.id == folder_id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    db.delete(folder)
    db.commit()
    return {"id": folder_id}
```

- [ ] **Step 4: 更新 models/__init__.py**

```python
# backend/app/models/__init__.py
from .base import Base
from .platform import PlatformUser, PlatformRole, PlatformOrganization, PlatformMenu
from .terminal import DebugRequest, DebugResult
from .test_case import TestCase, CaseVariant
from .case_folder import CaseFolder

__all__ = [
    "Base",
    "PlatformUser",
    "PlatformRole",
    "PlatformOrganization",
    "PlatformMenu",
    "DebugRequest",
    "DebugResult",
    "TestCase",
    "CaseVariant",
    "CaseFolder",
]
```

- [ ] **Step 5: 注册路由到 main.py**

```python
# backend/app/main.py 中添加
from app.routers import case_folder

app.include_router(case_folder.router)
```

- [ ] **Step 6: 提交代码**

```bash
git add backend/app/models/case_folder.py backend/app/schemas/case_folder.py backend/app/routers/case_folder.py backend/app/models/__init__.py backend/app/main.py
git commit -m "feat(backend): 添加用例文件夹分类模型和路由"
```

---

### Task 3: 前端 - 创建用例模块路由和基础结构

**Files:**
- Modify: `frontend/src/router/index.js:41-51`
- Create: `frontend/src/views/case/CaseSidebar.vue`
- Create: `frontend/src/views/case/functional/FunctionalCase.vue`
- Create: `frontend/src/views/case/api/ApiCase.vue`

- [ ] **Step 1: 更新路由配置**

```javascript
// frontend/src/router/index.js
{
  path: 'case',
  name: 'Case',
  component: () => import('../views/case/Case.vue'),
  redirect: '/case/api',
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
  ],
},
```

- [ ] **Step 2: 创建 CaseSidebar.vue 组件**

```vue
<!-- frontend/src/views/case/CaseSidebar.vue -->
<template>
  <div class="case-sidebar">
    <div class="sidebar-tabs">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="功能测试" name="functional" />
        <el-tab-pane label="接口测试" name="api" />
      </el-tabs>
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
        ref="treeRef"
        @node-click="handleNodeClick"
      >
        <template #default="{ node, data }">
          <span class="folder-node">
            <el-icon><Folder /></el-icon>
            <span>{{ node.label }}</span>
            <span class="case-count">({{ data.case_count || 0 }})</span>
          </span>
        </template>
      </el-tree>
    </div>

    <div class="sidebar-footer">
      <el-button size="small" :icon="Plus" @click="handleCreateFolder">新建分类</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { Search, Folder, Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { caseApi } from '@/api/case'

const props = defineProps({
  caseType: {
    type: String,
    default: 'api'
  }
})

const emit = defineEmits(['folder-selected', 'case-type-change'])

const activeTab = ref(props.caseType)
const searchKeyword = ref('')
const folderTree = ref([])
const treeRef = ref(null)

watch(() => props.caseType, (newType) => {
  activeTab.value = newType
  loadFolders()
})

function handleTabChange(tab) {
  emit('case-type-change', tab)
  loadFolders()
}

async function loadFolders() {
  try {
    const res = await caseApi.listFolders({ case_type: activeTab.value })
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

watch(searchKeyword, (val) => {
  treeRef.value?.filter(val)
})

function handleCreateFolder() {
  // TODO: 弹出创建分类对话框
}

defineExpose({
  reload: loadFolders,
})

onMounted(() => {
  loadFolders()
})
</script>

<style scoped>
.case-sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-container);
}

.sidebar-tabs {
  padding: 8px 12px;
  border-bottom: 1px solid var(--border-color);
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
  gap: 4px;
}

.case-count {
  color: var(--text-secondary);
  font-size: 12px;
}

.sidebar-footer {
  padding: 8px 12px;
  border-top: 1px solid var(--border-color);
}
</style>
```

- [ ] **Step 3: 创建 FunctionalCase.vue 页面**

```vue
<!-- frontend/src/views/case/functional/FunctionalCase.vue -->
<template>
  <div class="case-page">
    <aside class="case-sidebar">
      <CaseSidebar case-type="functional" @folder-selected="handleFolderSelected" @case-type-change="handleCaseTypeChange" />
    </aside>
    <main class="case-list">
      <CaseList ref="caseListRef" :case-type="caseType" :folder-id="currentFolderId" @case-selected="handleCaseSelected" @create-case="handleCreateCase" />
    </main>
    <aside class="case-detail">
      <CaseDetail v-if="selectedCase" :case-data="selectedCase" @saved="handleSaved" />
    </aside>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import CaseSidebar from '../CaseSidebar.vue'
import CaseList from '../CaseList.vue'
import CaseDetail from '../CaseDetail.vue'

const caseType = ref('functional')
const currentFolderId = ref(null)
const selectedCase = ref(null)
const caseListRef = ref(null)

function handleFolderSelected(folderId) {
  currentFolderId.value = folderId
}

function handleCaseTypeChange(type) {
  caseType.value = type
  currentFolderId.value = null
  selectedCase.value = null
}

function handleCaseSelected(caseItem) {
  selectedCase.value = caseItem
}

function handleCreateCase() {
  // 打开创建用例对话框
}

function handleSaved() {
  caseListRef.value?.reload()
}
</script>

<style scoped>
.case-page {
  display: flex;
  height: 100%;
  overflow: hidden;
}

.case-sidebar {
  width: 240px;
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
</style>
```

- [ ] **Step 4: 创建 ApiCase.vue 页面**

```vue
<!-- frontend/src/views/case/api/ApiCase.vue -->
<template>
  <div class="case-page">
    <aside class="case-sidebar">
      <CaseSidebar case-type="api" @folder-selected="handleFolderSelected" @case-type-change="handleCaseTypeChange" />
    </aside>
    <main class="case-list">
      <CaseList ref="caseListRef" :case-type="caseType" :folder-id="currentFolderId" @case-selected="handleCaseSelected" @create-case="handleCreateCase" />
    </main>
    <aside class="case-detail">
      <CaseDetail v-if="selectedCase" :case-data="selectedCase" @saved="handleSaved" />
    </aside>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import CaseSidebar from '../CaseSidebar.vue'
import CaseList from '../CaseList.vue'
import CaseDetail from '../CaseDetail.vue'

const caseType = ref('api')
const currentFolderId = ref(null)
const selectedCase = ref(null)
const caseListRef = ref(null)

function handleFolderSelected(folderId) {
  currentFolderId.value = folderId
}

function handleCaseTypeChange(type) {
  caseType.value = type
  currentFolderId.value = null
  selectedCase.value = null
}

function handleCaseSelected(caseItem) {
  selectedCase.value = caseItem
}

function handleCreateCase() {
  // 打开创建用例对话框
}

function handleSaved() {
  caseListRef.value?.reload()
}
</script>

<style scoped>
.case-page {
  display: flex;
  height: 100%;
  overflow: hidden;
}

.case-sidebar {
  width: 240px;
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
</style>
```

- [ ] **Step 5: 提交代码**

```bash
git add frontend/src/router/index.js frontend/src/views/case/CaseSidebar.vue frontend/src/views/case/functional/FunctionalCase.vue frontend/src/views/case/api/ApiCase.vue
git commit -m "feat(frontend): 添加用例模块独立页面路由和基础结构"
```

---

### Task 4: 前端 - 更新 CaseList 支持 case_type 和 folder_id 筛选

**Files:**
- Modify: `frontend/src/views/case/CaseList.vue`
- Modify: `frontend/src/stores/caseStore.js`
- Modify: `frontend/src/api/case.js`

- [ ] **Step 1: 更新 caseApi 添加分类相关接口**

```javascript
// frontend/src/api/case.js
import client from './client'

export const caseApi = {
  /** List test cases with pagination */
  list(params) {
    return client.get('/api/testcase', { params })
  },

  /** Get a test case by ID */
  get(id) {
    return client.get(`/api/testcase/${id}`)
  },

  /** Create a test case */
  create(data) {
    return client.post('/api/testcase', data)
  },

  /** Update a test case */
  update(id, data) {
    return client.put(`/api/testcase/${id}`, data)
  },

  /** Delete a test case */
  delete(id) {
    return client.delete(`/api/testcase/${id}`)
  },

  /** List variants for a test case */
  listVariants(id, params) {
    return client.get(`/api/testcase/${id}/variant`, { params })
  },

  /** Create a variant for a test case */
  createVariant(id, data) {
    return client.post(`/api/testcase/${id}/variant`, data)
  },

  /** List folders */
  listFolders(params) {
    return client.get('/api/case/folders', { params })
  },

  /** Create a folder */
  createFolder(data) {
    return client.post('/api/case/folders', data)
  },

  /** Update a folder */
  updateFolder(id, data) {
    return client.put(`/api/case/folders/${id}`, data)
  },

  /** Delete a folder */
  deleteFolder(id) {
    return client.delete(`/api/case/folders/${id}`)
  },
}
```

- [ ] **Step 2: 更新 caseStore 支持 case_type 和 folder_id**

```javascript
// frontend/src/stores/caseStore.js (部分更新)
export const useCaseStore = defineStore('case', () => {
  // State
  const caseType = ref('api')  // 'functional' | 'api'
  const folders = ref([])
  const tags = ref([])
  const cases = ref([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const currentCase = ref(null)
  const variants = ref([])
  const variantTotal = ref(0)
  const variantPage = ref(1)
  const variantPageSize = ref(20)
  const loading = ref(false)
  const error = ref('')

  // Actions
  async function fetchCases(params = {}) {
    loading.value = true
    error.value = ''
    try {
      const queryParams = {
        case_type: params.case_type || caseType.value,
        page: params.page || page.value,
        page_size: params.page_size || pageSize.value,
        ...(params.folder_id && { folder_id: params.folder_id }),
        ...(params.keyword && { keyword: params.keyword }),
      }
      const response = await caseApi.list(queryParams)
      cases.value = response.data.items
      total.value = response.data.total
      page.value = response.data.page
      pageSize.value = response.data.page_size
      return cases.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取用例列表失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchFolders() {
    try {
      const response = await caseApi.listFolders({ case_type: caseType.value })
      folders.value = response.data.items
      return folders.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取分类失败'
      throw err
    }
  }

  // ... (其他代码保持不变)

  return {
    // State
    caseType,
    folders,
    tags,
    cases,
    total,
    page,
    pageSize,
    currentCase,
    variants,
    variantTotal,
    variantPage,
    variantPageSize,
    loading,
    error,
    // Actions
    fetchCases,
    fetchFolders,
    fetchCase,
    createCase,
    updateCase,
    deleteCase,
    fetchVariants,
    createVariant,
    clearCurrentCase,
  }
})
```

- [ ] **Step 3: 更新 CaseList 组件支持 props**

```vue
<!-- frontend/src/views/case/CaseList.vue 修改 -->
<script setup>
import { ref, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus } from '@element-plus/icons-vue'
import { useCaseStore } from '@/stores/caseStore'

const props = defineProps({
  caseType: {
    type: String,
    default: 'api'
  },
  folderId: {
    type: Number,
    default: null
  }
})

const emit = defineEmits(['case-selected', 'create-case'])

const caseStore = useCaseStore()

const keyword = ref('')
const currentPage = ref(1)
const currentPageSize = ref(20)

const methodTypes = {
  GET: '',
  POST: 'success',
  PUT: 'warning',
  DELETE: 'danger',
  PATCH: 'info',
}

function getMethodType(method) {
  return methodTypes[method?.toUpperCase()] || ''
}

async function loadCases() {
  try {
    await caseStore.fetchCases({
      case_type: props.caseType,
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

async function handleCreate() {
  emit('create-case')
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除用例 "${row.name}" 吗？`, '确认删除', {
      type: 'warning',
    })
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

watch(() => props.caseType, () => {
  currentPage.value = 1
  loadCases()
})

watch(() => props.folderId, () => {
  currentPage.value = 1
  loadCases()
})

onMounted(() => {
  loadCases()
})

defineExpose({
  reload: loadCases,
})
</script>
```

- [ ] **Step 4: 提交代码**

```bash
git add frontend/src/api/case.js frontend/src/stores/caseStore.js frontend/src/views/case/CaseList.vue
git commit -m "feat(frontend): 更新用例列表支持 case_type 和 folder_id 筛选"
```

---

### Task 5: 前端 - 终端调试台添加"保存为用例"功能

**Files:**
- Modify: `frontend/src/views/terminal/Terminal.vue`
- Create: `frontend/src/components/case/SaveToCaseDialog.vue`

- [ ] **Step 1: 添加"保存为用例"按钮到 Terminal.vue**

在响应区域添加按钮：

```vue
<!-- 在 response-bar-actions 中添加 -->
<el-button v-if="responseData" size="small" text :icon="Document" @click="showSaveToCaseDialog">
  保存为用例
</el-button>
```

添加对话框组件：

```vue
<!-- 在 Terminal.vue 的 template 末尾添加 -->
<SaveToCaseDialog
  v-model="showSaveToCaseDialog"
  :request-data="getRequestDataForCase()"
  @success="handleSaveToCaseSuccess"
/>
```

在 script 中添加：

```javascript
import SaveToCaseDialog from '@/components/case/SaveToCaseDialog.vue'

const showSaveToCaseDialog = ref(false)

function getRequestDataForCase() {
  return {
    method: requestForm.value.method,
    url: requestForm.value.url,
    query_params: Object.fromEntries(requestForm.value.queryParams.filter(p => p.key).map(p => [p.key, p.value])),
    headers: Object.fromEntries(requestForm.value.headers.filter(h => h.key).map(h => [h.key, h.value])),
    cookies: Object.fromEntries(requestForm.value.cookies.filter(c => c.key).map(c => [c.key, c.value])),
    body_type: requestForm.value.bodyType,
    body: requestForm.value.body,
    auth_config: requestForm.value.authConfig,
    expected_status: responseData.value?.status_code,
    source_debug_id: currentRequestId.value,
  }
}

function showSaveToCaseDialog() {
  showSaveToCaseDialog.value = true
}

function handleSaveToCaseSuccess() {
  ElMessage.success('已保存为用例')
  showSaveToCaseDialog.value = false
}
```

- [ ] **Step 2: 创建 SaveToCaseDialog.vue**

```vue
<!-- frontend/src/components/case/SaveToCaseDialog.vue -->
<template>
  <el-dialog
    v-model="dialogVisible"
    title="保存为用例"
    width="600px"
    @close="handleClose"
  >
    <el-form :model="form" label-width="100px">
      <el-form-item label="用例类型" required>
        <el-radio-group v-model="form.case_type">
          <el-radio label="functional">功能测试用例</el-radio>
          <el-radio label="api">接口测试用例</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="用例名称" required>
        <el-input v-model="form.name" placeholder="请输入用例名称" />
      </el-form-item>

      <el-form-item label="所属分类">
        <el-select v-model="form.folder_id" placeholder="请选择分类" clearable style="width: 100%">
          <el-option
            v-for="folder in folders"
            :key="folder.id"
            :label="folder.name"
            :value="folder.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="描述">
        <el-input v-model="form.description" type="textarea" :rows="2" placeholder="请输入描述" />
      </el-form-item>

      <el-form-item label="请求方法">
        <el-tag>{{ form.method }}</el-tag>
      </el-form-item>

      <el-form-item label="URL">
        <el-input v-model="form.url" disabled />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { caseApi } from '@/api/case'

const props = defineProps({
  modelValue: Boolean,
  requestData: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const form = ref({
  case_type: 'api',
  name: '',
  folder_id: null,
  description: '',
  method: 'GET',
  url: '',
  query_params: {},
  headers: {},
  cookies: {},
  body_type: 'none',
  body: '',
  auth_config: {},
  expected_status: null,
  source_debug_id: null,
})

const folders = ref([])
const saving = ref(false)

watch(() => props.requestData, (newData) => {
  if (newData) {
    form.value = {
      ...form.value,
      ...newData,
      name: newData.url ? extractNameFromUrl(newData.url) : '',
    }
  }
}, { immediate: true })

watch(() => props.modelValue, (visible) => {
  if (visible) {
    loadFolders()
  }
})

function extractNameFromUrl(url) {
  try {
    const parsed = new URL(url)
    return parsed.pathname.split('/').filter(Boolean).slice(-1)[0] || '未命名用例'
  } catch {
    return '未命名用例'
  }
}

async function loadFolders() {
  try {
    const res = await caseApi.listFolders({ case_type: form.value.case_type })
    folders.value = res.data.items
  } catch {
    console.error('加载分类失败')
  }
}

async function handleSave() {
  if (!form.value.name) {
    ElMessage.warning('请输入用例名称')
    return
  }

  saving.value = true
  try {
    await caseApi.create(form.value)
    ElMessage.success('保存成功')
    emit('success')
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

function handleClose() {
  dialogVisible.value = false
}
</script>
```

- [ ] **Step 3: 提交代码**

```bash
git add frontend/src/views/terminal/Terminal.vue frontend/src/components/case/SaveToCaseDialog.vue
git commit -m "feat(terminal): 添加保存为用例功能"
```

---

### Task 6: 前端 - 创建独立的 Case.vue 重构版本

**Files:**
- Modify: `frontend/src/views/case/Case.vue` — 简化为空壳，重定向到 /case/api

- [ ] **Step 1: 更新 Case.vue 简化版本**

```vue
<!-- frontend/src/views/case/Case.vue -->
<template>
  <div class="case-redirect">
    <el-skeleton :rows="5" animated />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

onMounted(() => {
  router.replace('/case/api')
})
</script>

<style scoped>
.case-redirect {
  padding: 20px;
}
</style>
```

- [ ] **Step 2: 提交代码**

```bash
git add frontend/src/views/case/Case.vue
git commit -m "refactor(case): 简化 Case.vue 入口页面"
```

---

### Task 7: 验证和测试

- [ ] **Step 1: 启动后端服务验证**

```bash
cd backend
python -m uvicorn app.main:app --reload
# 验证路由:
# GET /api/case/folders?case_type=api
# POST /api/case/folders
# GET /api/testcase?case_type=api
# POST /api/testcase (带 case_type)
```

- [ ] **Step 2: 启动前端服务验证**

```bash
cd frontend
npm run dev
# 验证路由:
# /case/functional 页面显示
# /case/api 页面显示
# 左侧分类树显示
# 用例列表加载
# Terminal 保存为用例按钮
```

- [ ] **Step 3: 提交最终代码**

```bash
git add -A
git commit -m "feat: 完成用例模块重新设计第一阶段"
```

---

## 实施检查清单

| 任务 | 描述 | 状态 |
|------|------|------|
| Task 1 | 后端添加 case_type 字段 | ⬜ |
| Task 2 | 后端创建文件夹分类模型和路由 | ⬜ |
| Task 3 | 前端创建独立页面路由和组件 | ⬜ |
| Task 4 | 前端更新 CaseList 支持筛选 | ⬜ |
| Task 5 | 终端调试台保存为用例功能 | ⬜ |
| Task 6 | Case.vue 入口简化 | ⬜ |
| Task 7 | 验证测试 | ⬜ |

---

## 后续任务（不在本次计划内）

1. 功能测试用例的步骤配置功能
2. 用例版本管理
3. 标签分类管理
4. 变体管理的 AI 辅助生成
5. 批量操作功能

---

**Plan complete and saved to `docs/superpowers/plans/2026-05-19-case-module-redesign-implementation.md`**