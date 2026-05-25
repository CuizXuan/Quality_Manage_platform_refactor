# 集成 doc-generator：文档生成中心第一阶段

## 任务目标

请将 `H:\workstation_hermes\doc-generator` 的核心能力融合进当前质量管理平台，新增一个“文档生成中心”模块。

第一阶段目标是形成可用闭环：

```text
需求规格说明书 docx -> 生成概要设计/详细设计 docx
数据库结构来源 -> 生成数据库设计文档
FastAPI/OpenAPI/Swagger -> 生成接口设计文档
模板/规则可管理
生成结果可下载
```

本任务要求编码实现，不只是方案文档。

## 非常重要：样式要求

前端必须完全贴合当前质量管理平台现有模块风格，不能直接搬运 `doc-generator/ui/frontend` 的界面。

样式基准优先参考：

- `frontend/src/views/case/CaseManagement.vue`
- `frontend/src/views/case/CaseList.vue`
- `frontend/src/views/scenario/ScenarioList.vue`
- `frontend/src/views/report/DefectList.vue`
- `frontend/src/views/ai/AIPromptTemplates.vue`

必须满足：

- 页面背景使用当前平台偏绿色/蓝色的流动网格背景风格。
- 标题区、查询区、表格区、表单区透明度、层级、边框、阴影与 CaseManagement/ScenarioList 保持一致。
- 查询栏 label 必须左对齐并带中文冒号，例如 `文档类型：输入框`。
- 表单控件高度、按钮高度、间距、圆角和当前模块一致。
- 表格透明度、表头、hover、分页与当前模块一致。
- 不创建营销页、介绍页或独立 landing page，第一屏就是可用工具界面。
- 不使用 `doc-generator` 原前端的页面布局和 CSS。
- 不嵌套卡片套卡片。
- 不引入单独主题，不破坏现有平台整体视觉。
- 所有用户可见文案必须使用中文。

## 背景说明

源项目路径：

```text
H:\workstation_hermes\doc-generator
```

源项目现有能力：

- `engine/parser.py`：解析 `.docx` 需求规格说明书。
- `engine/pipeline.py`：按规则和模板执行多阶段文档生成。
- `engine/builder.py`：基于 `python-docx` 生成 `.docx`。
- `rules/*.json`：概要设计、详细设计、数据库设计、接口设计规则。
- `converters/db/*`：MySQL/PostgreSQL/SQLite 数据库结构转换。
- `converters/api/openapi.py`：OpenAPI/Swagger 解析和接口文档导出。
- `ui/backend.py`：独立 FastAPI 后端，仅供参考，不要照搬路由结构。
- `ui/frontend/`：独立 Vue 前端，仅供理解功能，不要直接迁入页面样式。

当前质量管理平台路径：

```text
H:\workstation_hermes\Quality_Manage_platform_refactor
```

## 必读文件

当前平台：

- `AGENTS.md`
- `CLAUDE.md`
- `.ai/INDEX.md`
- `backend/app/main.py`
- `backend/app/database.py`
- `backend/app/models/__init__.py`
- `backend/app/routers/platform_auth.py`
- `backend/app/services/platform_seed.py`
- `backend/app/routers/platform_system.py`
- `backend/requirements.txt`
- `frontend/src/router/index.js`
- `frontend/src/app/AppShell.vue`
- `frontend/src/api/client.js`
- `frontend/src/views/case/CaseManagement.vue`
- `frontend/src/views/scenario/ScenarioList.vue`
- `frontend/src/views/report/DefectList.vue`
- `frontend/src/views/ai/AIPromptTemplates.vue`

源项目：

- `H:\workstation_hermes\doc-generator\README.md`
- `H:\workstation_hermes\doc-generator\engine\datamodel.py`
- `H:\workstation_hermes\doc-generator\engine\parser.py`
- `H:\workstation_hermes\doc-generator\engine\pipeline.py`
- `H:\workstation_hermes\doc-generator\engine\builder.py`
- `H:\workstation_hermes\doc-generator\converters\db\base.py`
- `H:\workstation_hermes\doc-generator\converters\db\converter.py`
- `H:\workstation_hermes\doc-generator\converters\db\mysql.py`
- `H:\workstation_hermes\doc-generator\converters\db\postgres.py`
- `H:\workstation_hermes\doc-generator\converters\db\sqlite.py`
- `H:\workstation_hermes\doc-generator\converters\api\openapi.py`
- `H:\workstation_hermes\doc-generator\rules\概要设计.json`
- `H:\workstation_hermes\doc-generator\rules\详细设计.json`
- `H:\workstation_hermes\doc-generator\rules\数据库设计.json`
- `H:\workstation_hermes\doc-generator\rules\接口设计.json`
- `H:\workstation_hermes\doc-generator\docs\templates\`

## 建议目标结构

后端建议新增：

```text
backend/app/models/docgen.py
backend/app/schemas/docgen.py
backend/app/routers/docgen.py
backend/app/services/docgen/
├── __init__.py
├── datamodel.py
├── parser.py
├── builder.py
├── pipeline.py
├── rule_service.py
├── template_service.py
├── generation_service.py
├── storage.py
├── converters/
│   ├── __init__.py
│   ├── db/
│   └── api/
└── default_rules/
```

也可以采用更简洁结构，但必须符合当前平台分层：

- router 只处理 HTTP 入参、鉴权、响应。
- service 处理业务逻辑。
- model 持久化任务、模板、规则、生成结果元数据。
- schema 定义请求/响应。

前端建议新增：

```text
frontend/src/api/docgen.js
frontend/src/stores/docgenStore.js
frontend/src/views/docgen/DocGenerationCenter.vue
frontend/src/views/docgen/RequirementDocGenerator.vue
frontend/src/views/docgen/DatabaseDocGenerator.vue
frontend/src/views/docgen/ApiDocGenerator.vue
frontend/src/views/docgen/DocRuleTemplateManager.vue
```

如果为了第一阶段减少文件数量，也可以合并为一个主页面 + tab，但必须保持组件职责清晰。

## 允许修改范围

后端：

- `backend/app/main.py`
- `backend/app/models/__init__.py`
- `backend/app/models/docgen.py`
- `backend/app/schemas/docgen.py`
- `backend/app/routers/docgen.py`
- `backend/app/services/docgen/**`
- `backend/app/services/platform_seed.py`
- `backend/app/database.py` 中必要的轻量迁移
- `backend/requirements.txt`
- `backend/tests/**`

前端：

- `frontend/src/api/docgen.js`
- `frontend/src/stores/docgenStore.js`
- `frontend/src/router/index.js`
- `frontend/src/views/docgen/**`
- 如菜单常量或侧边栏依赖其他文件，可最小范围修改对应文件

资源：

- 可复制 `doc-generator/rules/*.json` 到平台后端默认规则目录。
- 可复制必要 `.docx` 模板到平台受控目录。

结果：

- 可写入 `.ai/results/2026-05-25-integrate-doc-generator-center-result.md`

## 禁止事项

- 不直接把 `doc-generator/ui/frontend` 复制到当前前端。
- 不通过 iframe 嵌入独立 doc-generator 前端。
- 不启动第二套长期服务作为平台功能入口。
- 不把数据库密码明文持久化到数据库；第一阶段如需要连接数据库，只用于本次请求，不落库保存密码。
- 不直接暴露服务器任意路径文件下载。
- 不允许上传文件覆盖任意路径。
- 不使用原始上传文件名直接拼接保存路径。
- 不保留 `DocBuilder.save()` 中 `/tmp` 和 `cp` 的写法，必须改成 Windows/Linux 都可用。
- 不破坏现有质量中心、AI 中枢、系统管理等模块。
- 不引入大型依赖；必要依赖必须写入 `backend/requirements.txt` 并说明用途。

## 后端实现要求

### 1. 文档生成数据模型

请新增文档生成相关模型，至少支持：

- 生成任务 `DocGenerationTask`
  - `id`
  - `task_type`：`requirement_design` / `database_design` / `api_design`
  - `name`
  - `status`：`pending` / `running` / `success` / `failed`
  - `source_filename`
  - `output_filename`
  - `output_path`
  - `message`
  - `created_by`
  - `created_at`
  - `finished_at`

- 规则 `DocGenerationRule`
  - `id`
  - `name`
  - `doc_type`
  - `filename`
  - `content`
  - `enabled`
  - `created_at`
  - `updated_at`

- 模板 `DocGenerationTemplate`
  - `id`
  - `name`
  - `doc_type`
  - `filename`
  - `file_path`
  - `created_at`

如果当前迁移体系不完整，可以在 `database.py` 的 `_run_migrations()` 中补轻量 SQLite 兼容迁移。

### 2. 文件存储

请在平台后端内建立受控目录，例如：

```text
backend/data/docgen/
├── uploads/
├── outputs/
├── templates/
└── rules/
```

要求：

- 上传文件名必须做安全清洗。
- 实际保存文件名建议带 timestamp 或 uuid。
- 下载接口只能下载 `backend/data/docgen/outputs` 或 templates 内受控文件。
- 不允许根据用户传入路径任意读取服务器文件。

### 3. 迁移核心引擎

从源项目迁入以下能力：

- 需求 docx 解析。
- 规则驱动 docx 构建。
- 多阶段生成。
- 数据库结构转换。
- OpenAPI/Swagger 解析。

必须修复：

- `DocBuilder.save()` 不能使用 `/tmp` 和 shell `cp`。
- 使用 `tempfile.NamedTemporaryFile` 或直接 `self._doc.save(output_path)`。
- 如需临时文件，使用 `tempfile` 和 `shutil`，保证 Windows 可用。

### 4. 默认规则和模板

首次启动或初始化时，应能使用默认规则：

- 概要设计
- 详细设计
- 数据库设计
- 接口设计

可从源项目复制 JSON 文件。

模板处理：

- 如果源项目有可用默认模板，复制到平台模板目录。
- 如果没有模板或复制失败，接口必须给出清晰中文错误。

### 5. API 设计

新增路由前缀：

```text
/api/docgen
```

建议接口：

```text
GET    /api/docgen/rules
GET    /api/docgen/rules/{id}
POST   /api/docgen/rules
PUT    /api/docgen/rules/{id}
DELETE /api/docgen/rules/{id}

GET    /api/docgen/templates
POST   /api/docgen/templates/upload
DELETE /api/docgen/templates/{id}

POST   /api/docgen/requirement/upload-preview
POST   /api/docgen/requirement/generate

POST   /api/docgen/database/preview
POST   /api/docgen/database/generate

POST   /api/docgen/api/preview
POST   /api/docgen/api/generate

GET    /api/docgen/tasks
GET    /api/docgen/tasks/{id}
GET    /api/docgen/tasks/{id}/download
```

第一阶段可以同步生成，不必做后台队列，但状态必须正确记录：

- 生成开始：`running`
- 成功：`success`
- 失败：`failed` 并记录 message

### 6. 需求文档生成

实现：

- 上传 `.docx` 需求规格说明书。
- 解析预览功能点树。
- 选择生成阶段：
  - 概要设计
  - 详细设计
  - 可多选
- 选择模板。
- 生成 `.docx` 输出。
- 返回任务和下载地址。

### 7. 数据库设计文档生成

第一阶段优先支持两类来源：

1. SQLite 文件路径或上传 SQLite 文件。
2. MySQL/PostgreSQL 连接参数。

如果直连数据库依赖缺失，可以先支持 SQLite，并把 MySQL/PostgreSQL 做成清晰的“依赖未安装/暂不可用”提示。

生成内容：

- 表名。
- 字段名。
- 类型。
- 是否主键。
- 是否允许为空。
- 默认值。
- 注释。
- 索引。

### 8. 接口文档生成

支持：

- 输入 OpenAPI URL。
- 上传 OpenAPI JSON 文件。
- 一键读取当前系统自身 OpenAPI：

```text
http://localhost:8000/openapi.json
```

生成：

- Markdown 接口文档。
- Docx 接口设计文档。

接口预览必须能展示：

- 模块 tag。
- method。
- path。
- summary。
- 参数数量。
- 响应状态码。

## 前端实现要求

### 1. 路由与菜单

新增页面路由：

```text
/docgen
```

建议菜单名称：

```text
文档中心
```

位置建议放在“工具”或“AI 中枢”附近，具体以现有侧边栏结构为准。

如果菜单来自后端种子 `platform_seed.py`，同步新增默认菜单和权限：

```text
docgen:view
docgen:generate
docgen:manage
```

### 2. 页面结构

`DocGenerationCenter.vue` 建议使用 tabs：

- `需求设计文档`
- `数据库设计文档`
- `接口设计文档`
- `规则与模板`
- `生成历史`

每个 tab 内部必须是当前平台风格：

- 顶部标题区。
- 参数/上传表单区。
- 预览区。
- 结果/历史表格区。

不要做大段说明文字，不要做 hero。

### 3. 交互要求

需求设计文档：

- 上传 docx。
- 展示解析预览树。
- 多选生成阶段。
- 选择模板。
- 点击生成。
- 展示生成结果。
- 下载。

数据库设计文档：

- 选择来源类型：SQLite 上传 / MySQL / PostgreSQL。
- 填写连接参数或上传文件。
- 测试连接/解析。
- 选择表。
- 生成文档。
- 下载。

接口设计文档：

- 来源类型：当前系统 OpenAPI / URL / 上传 JSON。
- 解析预览。
- 选择 tag。
- 生成 Markdown 或 Docx。
- 下载。

规则与模板：

- 展示规则列表。
- 展示模板列表。
- 上传模板。
- 不要求第一阶段做复杂 JSON 可视化编辑；可以先支持查看/简单编辑 JSON 文本。

生成历史：

- 表格展示任务。
- 状态 tag。
- 类型。
- 文件名。
- 创建时间。
- 下载按钮。

### 4. 样式细节

请抽取或复用当前模块的视觉模式，但不要做全局破坏性 CSS。

必须注意：

- 查询表单 label 与输入框对齐。
- label 文字含中文冒号。
- 按钮区域靠右，间距一致。
- 表格高度稳定，不因空数据跳动。
- 空状态中文提示。
- 下载/生成/预览按钮使用 lucide/Element Plus 图标，和当前平台按钮风格一致。
- 页面在 1366、1920 宽度下不重叠。

## 测试要求

后端至少补充：

- OpenAPI 解析器测试。
- SQLite 表结构转换测试。
- 文档任务状态流转测试。
- 安全文件名测试。
- 下载接口不能越权读取任意路径的测试。

如果 `python-docx` 生成 docx 测试成本较高，至少测试生成服务能创建任务并处理错误；但实际生成接口必须手工验证。

前端至少保证：

- `cd frontend && npm run build` 通过。

## 验证方式

请至少运行：

```text
python -m pytest backend/tests
cd frontend
npm run build
```

如果 PowerShell 不支持链式 `cd &&`，请分别执行并说明实际命令。

建议手工验证：

```text
启动后端
登录 admin/admin123
进入 /docgen
上传需求 docx
生成概要设计 docx
输入 http://localhost:8000/openapi.json
预览接口
生成接口文档
下载生成文件
查看生成历史
```

## 验收标准

- 后端成功注册 `/api/docgen` 路由。
- 前端成功注册 `/docgen` 页面。
- 菜单能进入“文档中心”。
- 需求 docx 能上传、预览、生成概要/详细设计文档。
- OpenAPI 能预览并生成接口文档，至少支持当前系统 `/openapi.json`。
- 数据库设计文档至少支持 SQLite 来源生成。
- 生成历史可查询。
- 生成结果可下载。
- 文件路径安全，不允许任意路径读取。
- 页面视觉与当前质量平台模块一致。
- `npm run build` 通过。
- 后端测试通过或明确说明阻塞。

## Claude 输出要求

结束时必须用中文汇报：

- 迁入了哪些源项目能力。
- 新增/修改了哪些后端文件。
- 新增/修改了哪些前端文件。
- 文档中心页面如何进入。
- 哪些文档类型已可生成。
- 样式如何对齐现有模块。
- 已运行的测试和构建结果。
- 剩余风险。

请同步写入：

- `.ai/results/2026-05-25-integrate-doc-generator-center-result.md`
