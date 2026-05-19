# Quality Manage Platform - 编码规范

> 本文档整合 Karpathy 编码约束与项目实际情况，为 AI 辅助编码提供明确指导。

---

## 一、核心原则（Karpathy 约束）

### 1.1 代码的终极目标
**代码是给人看的**，其次才是给机器执行的。清晰可读优于巧妙简洁。

### 1.2 关键约束
| 约束 | 说明 |
|------|------|
| **小即是好** | 单个函数不超过 40 行，单个文件不超过 300 行 |
| **单一职责** | 每个函数只做一件事 |
| **命名即文档** | 变量/函数名应自解释，无需注释即可理解 |
| **删除优于修改** | 设计代码时考虑可删除性，而非可扩展性 |
| **纯函数优先** | 无副作用的函数更易测试和推理 |
| **最小依赖** | 避免不必要的外部依赖 |
| **无魔法操作** | 避免隐式行为，拒绝黑魔法 |

---

## 二、后端规范（Python / FastAPI）

### 2.1 项目结构
```
backend/app/
├── main.py              # 应用入口，路由注册，中间件配置
├── config.py             # 配置管理
├── database.py           # 数据库连接
├── models/               # SQLAlchemy 模型（一个模型一个文件）
├── schemas/              # Pydantic 请求/响应模型
├── routers/              # API 路由（按功能模块分离）
├── services/             # 业务逻辑层
│   └── ai/               # AI 相关服务
├── middleware/           # 中间件
└── tests/                # 测试
```

### 2.2 命名规范
| 类型 | 规范 | 示例 |
|------|------|------|
| 文件 | `snake_case.py` | `test_case.py`, `auth_service.py` |
| 类名 | `PascalCase` | `TestCase`, `UserService` |
| 函数 | `snake_case` | `get_user_by_id`, `execute_scenario` |
| 变量 | `snake_case` | `user_id`, `case_list` |
| 常量 | `UPPER_SNAKE_CASE` | `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT` |
| 路由路径 | `/snake_case` | `/test-cases`, `/defect-list` |

### 2.3 函数设计
```python
# ✅ 正确：小函数，单一职责
def parse_case(case: TestCase) -> dict:
    """解析用例模型为字典"""
    return {
        "id": case.id,
        "name": case.name,
        "method": case.method,
    }

def validate_case_data(data: TestCaseCreate) -> None:
    """验证用例数据"""
    if not data.name:
        raise HTTPException(status_code=400, detail="Name is required")

# ❌ 错误：函数过长，职责过多
async def run_case(case_id: int, body: RunCaseRequest, db: Session):
    # 获取用例、验证环境、执行请求、保存日志... 全部混在一起
```

### 2.4 API 路由模式
```python
# ✅ 每个路由操作对应独立函数，职责清晰
@router.get("", response_model=List[TestCaseResponse])
def list_cases(...):
    """获取用例列表"""
    ...

@router.post("", response_model=TestCaseResponse)
def create_case(...):
    """创建用例"""
    ...

# ❌ 错误：所有操作堆在一个函数里用 action 参数区分
@router.post("")
def handle_case(action: str, ...):
    if action == "list": ...
    elif action == "create": ...
```

### 2.5 数据库操作
```python
# ✅ 使用依赖注入获取数据库会话
from app.database import get_db

@router.get("/{case_id}")
def get_case(case_id: int, db: Session = Depends(get_db)):
    case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case

# ✅ 使用上下文管理器处理事务
def update_case(case_id: int, data: TestCaseUpdate, db: Session):
    case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    for key, value in data.model_dump(exclude_unset=True).items():
        if value is None:
            continue
        setattr(case, key, value)
    
    db.commit()
    db.refresh(case)
    return case
```

### 2.6 错误处理
```python
# ✅ 统一错误响应格式
@router.get("/{case_id}")
def get_case(case_id: int, db: Session = Depends(get_db)):
    case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case

# ✅ 在服务层处理业务逻辑错误
class CaseNotFoundError(Exception):
    pass

def get_case_or_raise(case_id: int, db: Session) -> TestCase:
    case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not case:
        raise CaseNotFoundError(f"Case {case_id} not found")
    return case
```

### 2.7 JSON 序列化
```python
# ✅ JSON 字段存储使用 json.dumps/loads 显式处理
import json

class TestCase(Base):
    headers = Column(Text, default="{}")  # JSON 字符串
    
    @property
    def headers_dict(self):
        return json.loads(self.headers or "{}")
    
    def set_headers(self, value: dict):
        self.headers = json.dumps(value)
```

---

## 三、前端规范（Vue 3 / JavaScript）

### 3.1 项目结构
```
frontend/src/
├── main.ts               # 入口
├── App.vue               # 根组件
├── api/                  # API 调用（一个模块一个文件）
├── components/           # 组件
│   ├── common/           # 通用组件
│   ├── request/          # 请求相关组件
│   └── response/         # 响应相关组件
├── views/                # 页面视图
├── stores/               # Pinia 状态管理
├── router/               # 路由配置
└── utils/                # 工具函数
```

### 3.2 命名规范
| 类型 | 规范 | 示例 |
|------|------|------|
| 组件文件 | `PascalCase.vue` | `RequestBar.vue`, `JsonViewer.vue` |
| 组件名 | `PascalCase` | `RequestBar`, `DefectDetail` |
| 变量/函数 | `camelCase` | `caseList`, `fetchCaseById` |
| 常量 | `UPPER_SNAKE_CASE` | `API_BASE_URL`, `MAX_PAGE_SIZE` |
| 事件名 | `kebab-case` | `case-updated`, `item-selected` |
| CSS 类名 | `kebab-case` | `case-item`, `btn-primary` |

### 3.3 Vue 组件规范
```vue
<!-- ✅ 正确：组件职责单一，模板清晰 -->
<template>
  <div class="case-item">
    <span class="method-badge">{{ method }}</span>
    <span class="case-name">{{ name }}</span>
    <el-button @click="handleRun">执行</el-button>
  </div>
</template>

<script setup lang="ts">
// 定义 props 和 emits
const props = defineProps<{
  id: number
  name: string
  method: string
}>()

const emit = defineEmits<{
  (e: 'run', id: number): void
}>()

// 事件处理
const handleRun = () => {
  emit('run', props.id)
}
</script>

<!-- ❌ 错误：一个组件处理太多不相关功能 -->
```

### 3.4 API 调用模式
```javascript
// ✅ 统一封装，分离 concerns
// api/client.js
import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

client.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = 'Bearer ' + token
  return config
})

export default client

// api/case.js
import client from './client'

export const casesApi = {
  list: (params = {}) => client.get('/cases', { params }),
  get: (id) => client.get('/cases/' + id),
  create: (data) => client.post('/cases', data),
  update: (id, data) => client.put('/cases/' + id, data),
  delete: (id) => client.delete('/cases/' + id),
  run: (id, data) => client.post('/cases/' + id + '/run', data),
}
```

### 3.5 状态管理（Pinia）
```javascript
// ✅ 每个 store 单一职责
// stores/caseStore.js
import { defineStore } from 'pinia'
import { casesApi } from '@/api/case'

export const useCaseStore = defineStore('case', {
  state: () => ({
    cases: [],
    currentCase: null,
  }),
  
  actions: {
    async fetchCases(params) {
      const response = await casesApi.list(params)
      this.cases = response.data
    },
    
    async createCase(data) {
      const response = await casesApi.create(data)
      this.cases.push(response.data)
      return response.data
    },
  },
})
```

---

## 四、测试规范

### 4.1 pytest 配置
```ini
# pytest.ini
[pytest]
minversion = 8.0
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
```

### 4.2 测试文件组织
```
backend/tests/
├── conftest.py              # 共享 fixtures
├── conftest_report.py       # 报告相关 fixtures
├── routers/
│   ├── test_cases.py
│   ├── test_scenarios.py
│   └── test_defects.py
└── report/
    └── __init__.py
```

### 4.3 测试标记
```python
# 按优先级
@pytest.mark.p0   # 核心流程冒烟测试
@pytest.mark.p1   # 重要功能测试
@pytest.mark.p2   # 边界/异常测试

# 按模块
@pytest.mark.cases
@pytest.mark.scenarios
@pytest.mark.defects

# 按类型
@pytest.mark.api
@pytest.mark.unit
@pytest.mark.integration
```

### 4.4 测试编写原则
```python
# ✅ 清晰的测试结构
def test_create_case_success():
    """创建用例成功"""
    # Arrange
    case_data = {"name": "Test Case", "method": "GET", "url": "http://example.com"}
    
    # Act
    response = client.post("/api/cases", json=case_data)
    
    # Assert
    assert response.status_code == 201
    assert response.json()["name"] == "Test Case"

# ✅ 使用 fixtures 复用测试数据
def test_get_case(db_session, sample_case):
    response = client.get(f"/api/cases/{sample_case.id}")
    assert response.status_code == 200
```

---

## 五、Git 提交规范

### 5.1 提交信息格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

### 5.2 Type 类型
| Type | 说明 |
|------|------|
| feat | 新功能 |
| fix | Bug 修复 |
| docs | 文档变更 |
| style | 代码格式（不影响功能） |
| refactor | 重构 |
| test | 测试相关 |
| chore | 构建/工具变更 |

### 5.3 示例
```
feat(cases): 添加用例批量删除功能

- 支持选择多个用例一键删除
- 返回删除数量统计

Closes #123
```

---

## 六、安全规范

### 6.1 认证与授权
```python
# ✅ 使用 Bearer Token 认证
from fastapi import Header

async def get_current_user(authorization: str = Header(...)):
    scheme, token = authorization.split()
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401)
    # 验证 token...
```

### 6.2 输入验证
```python
# ✅ 所有输入都需验证
from pydantic import BaseModel, validator

class TestCaseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    method: str = Field(..., pattern="^(GET|POST|PUT|DELETE|PATCH)$")
    url: str = Field(..., max_length=2000)
    
    @validator('url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v
```

### 6.3 SQL 注入防护
```python
# ✅ 使用参数化查询（SQLAlchemy 自动处理）
case = db.query(TestCase).filter(TestCase.id == case_id).first()

# ❌ 绝对禁止：字符串拼接 SQL
query = f"SELECT * FROM test_case WHERE id = {case_id}"
```

---

## 七、代码审查清单

### 7.1 功能层面
- [ ] 函数是否单一职责？
- [ ] 函数是否不超过 40 行？
- [ ] 变量命名是否自解释？
- [ ] 错误处理是否完善？
- [ ] 是否有必要的日志记录？

### 7.2 代码质量
- [ ] 是否有重复代码可以抽取？
- [ ] 是否有不必要的复杂度？
- [ ] 依赖是否最小化？
- [ ] 是否有魔法操作需要避免？

### 7.3 安全层面
- [ ] 用户输入是否验证？
- [ ] 敏感信息是否硬编码？
- [ ] 认证授权是否正确处理？

### 7.4 测试层面
- [ ] 是否有对应的单元测试？
- [ ] 核心路径是否有 P0 测试覆盖？
- [ ] 测试是否可重复执行？

---

## 八、参考

- [Karpathy's Coding Constraints](https://github.com/karpathy/llm.c) - 核心原则来源
- [Python PEP 8](https://pep8.org/) - Python 代码风格
- [Vue 3 风格指南](https://vuejs.org/style-guide/) - Vue 组件最佳实践
- [FastAPI 最佳实践](https://fastapi.tiangolo.com/zh/tutorial/) - API 设计指南
