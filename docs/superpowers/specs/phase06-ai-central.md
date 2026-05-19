# 第六阶段：AI 中枢 — 实施方案

> **依据文档：** `详细设计.md` §5 + `整合文档.md` §2.7 + `05_后端开发规范.md` + `06_前端组件与页面规范.md` + `07_开发顺序与验收标准.md` §6

## 1. 需求理解

### 核心功能
- 模型配置（API Key、Base URL、模型选择）
- Prompt 模板管理
- 从接口/调试历史生成用例
- 从基础用例自动派生变体
- 自动生成断言
- 执行失败归因分析
- 报告总结与风险预测

### 关键数据结构

```
AIAnalysis {
  id, target_type: 'case'|'variant'|'scenario'|'execution',
  target_id, analysis_type,
  payload: any,
  suggestions: AISuggestion[]
}

AISuggestion {
  id, analysis_id, type, content,
  accepted: bool, accepted_at?, accepted_by?
}
```

### 验收标准（来自 07_开发顺序与验收标准.md §6）
- ✅ AI 输出结构化 JSON
- ✅ AI 建议可预览
- ✅ AI 建议可采纳
- ✅ 采纳动作可追溯

---

## 2. 技术方案

### 2.1 AI 模型配置

**设计：** 使用 MiniMax-M2.7（与 Hermes 一致），在 `app/config.py` 或独立 `ai_config` 表管理。

```python
# AI 配置模型
class AIConfig(Base):
    __tablename__ = "ai_configs"
    id: int
    name: str  # "MiniMax"
    api_key: str
    base_url: str  # "https://api.minimaxi.com"
    model: str  # "MiniMax-M2.7"
    enabled: bool
```

### 2.2 Prompt 模板

```python
class AIPromptTemplate(Base):
    __tablename__ = "ai_prompt_templates"
    id: int
    name: str  # "生成用例变体"
    template_type: str  # "variant_generation" | "assertion_generation" | "failure_analysis"
    system_prompt: str
    user_prompt_template: str
    variables: List[str]  # ["case_name", "method", "url"]
```

### 2.3 AI 调用封装

使用统一的 `AIService` 封装：

```python
class AIService:
    def __init__(self, config: AIConfig):
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )

    def generate_variants(self, case: dict) -> list[dict]:
        """从基础用例生成变体"""

    def generate_assertions(self, response: dict) -> list[dict]:
        """从响应生成断言"""

    def analyze_failure(self, execution_step: dict) -> dict:
        """执行失败归因"""

    def summarize_report(self, report_data: dict) -> str:
        """报告总结"""
```

### 2.4 采纳追溯

每条 `AISuggestion` 有 `accepted` 字段，采纳时记录：
- `accepted_at`: 采纳时间
- `accepted_by`: 采纳人 ID
- `accepted_comment`: 采纳备注（可选）

---

## 3. 任务拆解

### 阶段一：后端模型 & Schema

#### Task 1: 创建 AI 相关模型
- **文件：** `backend/app/models/ai.py`
- **内容：** AIConfig, AIPromptTemplate, AIAnalysis, AISuggestion
- **验证：** `python -c "from app.models.ai import AIConfig, AIPromptTemplate, AIAnalysis, AISuggestion; print('OK')"`

#### Task 2: 创建 AI Pydantic Schemas
- **文件：** `backend/app/schemas/ai.py`
- **验证：** `python -c "from app.schemas.ai import *; print('OK')"`

### 阶段二：后端 AI Service

#### Task 3: 创建 AIService（AI 调用封装）
- **文件：** `backend/app/services/ai_service.py`
- **内容：**
  - `generate_variants(case_data)` — 调用模型生成变体，返回结构化 JSON
  - `generate_assertions(response_body)` — 生成断言建议
  - `analyze_failure(execution_step)` — 失败归因
  - `summarize_report(report_data)` — 报告总结
- **遵循规范：** 函数不超过 40 行，单一职责
- **验证：** `pytest tests/services/test_ai_service.py -v`

#### Task 4: 创建 AI Repository
- **文件：** `backend/app/repositories/ai_repository.py`
- **内容：** AI 配置 CRUD，Prompt 模板 CRUD，分析结果保存，采纳记录

### 阶段三：后端 Router

#### Task 5: 创建 ai.py Router
- **文件：** `backend/app/routers/ai.py`
- **端点：**
  - `GET /api/ai/config` — 获取 AI 配置
  - `PUT /api/ai/config` — 更新 AI 配置
  - `GET /api/ai/templates` — Prompt 模板列表
  - `POST /api/ai/templates` — 创建 Prompt 模板
  - `PUT /api/ai/templates/{id}` — 更新 Prompt 模板
  - `DELETE /api/ai/templates/{id}` — 删除 Prompt 模板
  - `POST /api/ai/generate-variants` — 生成变体（body: case_id 或完整用例数据）
  - `POST /api/ai/generate-assertions` — 生成断言（body: response 或 execution_step_id）
  - `POST /api/ai/analyze-failure` — 失败归因（body: execution_step_id）
  - `POST /api/ai/summarize-report` — 报告总结（body: report_id）
  - `POST /api/ai/suggestions/{id}/accept` — 采纳建议
  - `GET /api/ai/analysis/{id}` — 查看分析结果
- **验证：** `curl http://localhost:8000/docs` 确认路由

### 阶段四：前端 API

#### Task 6: 创建 ai.js API 封装
- **文件：** `frontend/src/views/ai/api/ai.js`

#### Task 7: 创建 aiStore
- **文件：** `frontend/src/stores/aiStore.js`

### 阶段五：前端页面

#### Task 8: 创建 AIModelConfig.vue（模型配置页面）
- **文件：** `frontend/src/views/ai/AIModelConfig.vue`
- **内容：** API Key、Base URL、模型选择，连接测试按钮

#### Task 9: 创建 AIPromptTemplates.vue（Prompt 模板管理）
- **文件：** `frontend/src/views/ai/AIPromptTemplates.vue`
- **内容：** 模板列表、新建/编辑/删除，支持变量预览

#### Task 10: 创建 VariantGenerator.vue（变体生成）
- **文件：** `frontend/src/views/ai/VariantGenerator.vue`
- **内容：** 选择用例 → 一键生成变体 → 预览 → 批量采纳
- **交互：** 显示每个变体的 variant_type + override 配置，支持逐个采纳

#### Task 11: 创建 AssertionGenerator.vue（断言生成）
- **文件：** `frontend/src/views/ai/AssertionGenerator.vue`
- **内容：** 选择用例/变体 → 输入响应 JSON → 生成断言 → 预览 → 采纳

#### Task 12: 创建 FailureAnalyzer.vue（失败归因）
- **文件：** `frontend/src/views/ai/FailureAnalyzer.vue`
- **内容：** 选择执行历史中的失败步骤 → AI 归因分析 → 修复建议 → 采纳

#### Task 13: 创建 ReportSummarizer.vue（报告总结）
- **文件：** `frontend/src/views/ai/ReportSummarizer.vue`
- **内容：** 选择报告 → AI 总结 + 风险预测 → 可编辑 → 采纳

#### Task 14: 创建 SuggestionHistory.vue（采纳历史）
- **文件：** `frontend/src/views/ai/SuggestionHistory.vue`
- **内容：** 所有 AI 建议列表，accepted/rejected 状态，可筛选

#### Task 15: 路由注册
- **文件：** `frontend/src/router/index.js`
- **内容：** `/ai/config`, `/ai/templates`, `/ai/variant-generator`, `/ai/assertion-generator`, `/ai/failure-analyzer`, `/ai/report-summarizer`, `/ai/suggestion-history`

### 阶段六：集成测试

#### Task 16: AI Service 测试（Mock）
- **文件：** `backend/tests/services/test_ai_service.py`
- **使用 Mock** 避免真实 API 调用
- **验证：** `pytest tests/services/test_ai_service.py -v` 全绿

#### Task 17: 前端集成验证
- **验证清单：**
  - [ ] 配置 AI 模型 → 连接测试成功
  - [ ] 选择用例 → 生成变体 → 采纳 → 进入用例变体列表
  - [ ] 输入响应 → 生成断言 → 采纳 → 进入用例断言配置
  - [ ] 选择失败步骤 → AI 归因 → 采纳 → 记录到采纳历史
  - [ ] 选择报告 → AI 总结 → 采纳 → 记录到采纳历史

---

## 4. 验收标准检查表

| 检查项 | 标准 |
|--------|------|
| AI 配置 | 可配置 API Key / Base URL / 模型 |
| Prompt 模板 | 可管理模板，可预览渲染结果 |
| 变体生成 | AI 返回 12 种标准变体类型，结构化 JSON |
| 断言生成 | 支持状态码 + JSONPath 断言 |
| 失败归因 | 返回根因 + 修复建议 |
| 报告总结 | 返回 markdown 格式总结 + 风险评分 |
| 采纳功能 | 可逐个/批量采纳建议 |
| 采纳追溯 | accepted_at + accepted_by 全量记录 |
| 错误处理 | API 超时/失败有友好提示 |
| 权限编码 | 所有操作有 permission_code |
| 测试覆盖 | AI Service 有 Mock 测试 |
