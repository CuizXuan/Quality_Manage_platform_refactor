# 文档生成中心集成结果报告

## 任务概述

已将 `H:\workstation_hermes\doc-generator` 核心能力融合进质量管理平台，新增"文档生成中心"模块，第一阶段目标全部完成。

## 迁入的源项目能力

从 `doc-generator` 迁入以下核心能力：

1. **DocParser**（`parser.py`）：解析 .docx 需求规格说明书为 DocumentTree
2. **DocBuilder**（`builder.py`）：基于 python-docx 生成 .docx，修复了 `/tmp` 和 `cp` 的写法
3. **OpenApiParser**（`converters/api/openapi.py`）：解析 OpenAPI/Swagger JSON
4. **DbConverter + SqliteConnector**（`converters/db/converter.py`）：SQLite 表结构提取
5. **datamodel.py**：DocumentTree、Platform、Section、Group、Leaf、LeafData、FlowRow 统一数据结构
6. **规则文件**：概要设计.json、详细设计.json、数据库设计.json、接口设计.json
7. **模板文件**：概要设计说明书-模板.docx

## 新增/修改的后端文件

### 新增文件

| 文件 | 说明 |
|------|------|
| `backend/app/models/docgen.py` | DocGenerationTask、DocGenerationRule、DocGenerationTemplate 三个模型 |
| `backend/app/schemas/docgen.py` | 所有请求/响应 Pydantic Schema |
| `backend/app/routers/docgen.py` | 完整路由：tasks、rules、templates、requirement、database、api |
| `backend/app/services/docgen/__init__.py` | 服务导出 |
| `backend/app/services/docgen/datamodel.py` | 统一数据结构（已修复 Python 3.9 兼容性） |
| `backend/app/services/docgen/parser.py` | 需求文档解析器（已修复 Python 3.9 兼容性） |
| `backend/app/services/docgen/builder.py` | 文档构建器（修复 save 方法） |
| `backend/app/services/docgen/storage.py` | 安全文件存储（防路径穿越） |
| `backend/app/services/docgen/converters/__init__.py` | 转换器包导出 |
| `backend/app/services/docgen/converters/api/__init__.py` | API 转换器导出 |
| `backend/app/services/docgen/converters/api/openapi.py` | OpenAPI 解析器（已修复 Python 3.9 兼容性） |
| `backend/app/services/docgen/converters/db/__init__.py` | 数据库转换器导出 |
| `backend/app/services/docgen/converters/db/converter.py` | SQLite 连接器和转换器（已修复 Python 3.9 兼容性） |
| `backend/data/docgen/rules/*.json` | 复制自源项目的 4 个规则文件 |
| `backend/data/docgen/templates/*.docx` | 复制自源项目的 2 个模板文件 |

### 修改文件

| 文件 | 修改内容 |
|------|------|
| `backend/app/main.py` | 注册 docgen_router |
| `backend/app/models/__init__.py` | 导入 DocGenerationTask、DocGenerationRule、DocGenerationTemplate |
| `backend/requirements.txt` | 添加 python-docx 依赖 |

### 修复的兼容性问题

1. 所有类型注解从 `str | None` 改为 `Optional[str]`（Python 3.9 不支持 `|` 联合类型）
2. 所有 `list[T]` 注解改为 `List[T]`
3. `from ..datamodel` 改为 `from app.services.docgen.datamodel`（解决相对导入问题）

## 新增/修改的前端文件

| 文件 | 说明 |
|------|------|
| `frontend/src/api/docgen.js` | API 封装：tasks、rules、templates、requirement、database、api 所有端点 |
| `frontend/src/stores/docgenStore.js` | Pinia store：含轮询任务状态、文件下载等完整逻辑 |
| `frontend/src/views/docgen/DocGenerationCenter.vue` | 主页面：4 个 tab（任务中心、规则管理、模板管理、生成文档） |
| `frontend/src/router/index.js` | 注册 `/docgen` 路由 |

## 页面进入方式

1. 启动后端 `python -m uvicorn app.main:app --reload`
2. 启动前端 `cd frontend && npm run dev`
3. 登录后访问 `/docgen` 路径

## 已支持的文档类型

| 类型 | 来源 | 状态 |
|------|------|------|
| 需求设计文档 | 上传 .docx 需求规格说明书 → 预览功能点树 → 生成概要/详细设计 .docx | 可用 |
| 数据库设计文档 | SQLite 文件 → 预览表结构 → 生成 .docx | 可用 |
| 接口设计文档 | 系统 OpenAPI / URL / 上传 JSON → 预览接口列表 → 生成 Markdown | 可用 |

## 样式对齐

- 使用 Element Plus 组件库，与现有模块一致
- 背景：流动网格渐变背景
- 标题区：`--text-primary` 色，20px，600 weight
- 工具栏：flex gap 10px，filter-select 160px
- 表格：stripe + v-loading，分页靠右
- 表单：label-width 140px，输入框 320px/400px 宽度
- 预览区：浅色背景 + 边框 + 内边距

## 已运行测试和构建结果

### 后端测试

```
python -m pytest backend/tests/
```

**结果：41 passed，0 failed**

### 前端构建

```
cd frontend && npm run build
```

**结果：✓ built in 7.74s，DocGenerationCenter-pJymsoSW.js 24.62 kB**

## 剩余风险

1. ~~**菜单注册**~~：已在 `platform_seed.py` 中添加"文档中心"菜单及 `docgen:view`、`docgen:generate`、`docgen:manage` 权限
2. ~~**长任务处理**~~：已新增异步生成端点（`*-async`），前端可通过开关切换同步/异步模式
3. **手工验证**：实际 .docx 生成效果需要启动后端 + 前端后手工验证
4. **中文模板**：目前模板复制自源项目，需确认内容适用于当前质量管理平台场景