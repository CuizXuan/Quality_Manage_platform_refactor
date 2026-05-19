# P5-M1: AI 测试生成引擎

## 1. 模块概述

**功能**: 基于多种输入源(代码/OpenAPI/cURL/文字描述)自动生成 API 测试用例

**核心能力**:
- 多源输入解析
- RAG 向量检索增强上下文
- LLM 生成结构化测试用例
- 后处理与去重

## 2. 数据库设计

### 2.1 AI 生成历史表 `ai_gen_history`

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 自增主键 |
| source_type | VARCHAR(50) | NOT NULL | code/doc/curl/description |
| source_content | TEXT | NOT NULL | 源内容 |
| generated_case | TEXT | NOT NULL | 生成的用例 JSON |
| accepted | BOOLEAN | | 是否被采纳 |
| modified_after_accept | BOOLEAN | | 采纳后是否被修改 |
| feedback_score | INTEGER | | 1-5 分评价 |
| feedback_comment | TEXT | | 反馈评论 |
| model_used | VARCHAR(50) | | 使用的模型 |
| prompt_tokens | INTEGER | | Prompt Token 数 |
| completion_tokens | INTEGER | | 生成 Token 数 |
| project_id | INTEGER | FK | 所属项目 |
| created_by | INTEGER | FK | 创建人 |
| created_at | TIMESTAMP | DEFAULT | 创建时间 |

### 2.2 向量文档表 `vector_doc`

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 自增主键 |
| doc_type | VARCHAR(50) | NOT NULL | test_case/api_doc/code/issue |
| content | TEXT | NOT NULL | 原始内容 |
| embedding_id | VARCHAR(100) | | 向量数据库 ID |
| metadata | TEXT | | JSON 元数据 |
| chunk_index | INTEGER | | 分块索引 |
| project_id | INTEGER | FK | 所属项目 |
| created_at | TIMESTAMP | DEFAULT | 创建时间 |

### 2.3 Embedding 缓存表 `embedding_cache`

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 自增主键 |
| content_hash | VARCHAR(64) | UNIQUE | 内容哈希 |
| embedding | TEXT | | 向量 JSON |
| model | VARCHAR(50) | | 使用的模型 |
| created_at | TIMESTAMP | DEFAULT | 创建时间 |
| expires_at | TIMESTAMP | | 过期时间 |

## 3. API 设计

### 3.1 用例生成

```
POST /api/ai/generate
Authorization: Bearer <token>

Request:
{
  "source_type": "code|doc|curl|description",
  "source_content": "...",
  "options": {
    "include_success": true,
    "include_error": true,
    "include_boundary": false,
    "include_performance": false
  },
  "project_id": 1
}

Response:
{
  "success": true,
  "cases": [
    {
      "name": "用户登录成功",
      "method": "POST",
      "url": "/api/users/login",
      "headers": {...},
      "body": {...},
      "assertions": [
        {"type": "status", "expected": 200},
        {"type": "json_path", "path": "$.code", "expected": 0}
      ]
    }
  ],
  "model_used": "gpt-4",
  "tokens_used": {"prompt": 500, "completion": 300}
}
```

### 3.2 向量检索增强

```
POST /api/ai/retrieve-context
Request:
{
  "query": "用户登录接口",
  "project_id": 1,
  "top_k": 5
}
Response:
{
  "contexts": [
    {"doc_type": "api_doc", "content": "...", "similarity": 0.95},
    {"doc_type": "test_case", "content": "...", "similarity": 0.88}
  ]
}
```

## 4. 服务层设计

### 4.1 `AI_gen_service.py`

```python
class AIGenService:
    """AI 测试生成服务"""
    
    def generate_from_code(self, code: str, project_id: int, options: dict) -> list:
        """从代码生成用例"""
        
    def generate_from_openapi(self, spec: dict, project_id: int) -> list:
        """从 OpenAPI 规范生成用例"""
        
    def generate_from_curl(self, curl_cmd: str, project_id: int) -> list:
        """从 cURL 命令生成用例"""
        
    def generate_from_description(self, description: str, project_id: int) -> list:
        """从文字描述生成用例"""
        
    def _build_prompt(self, source_type: str, source_content: str, context: list) -> str:
        """构建 Prompt"""
        
    def _call_llm(self, prompt: str, model: str) -> dict:
        """调用 LLM"""
        
    def _post_process(self, raw_output: dict) -> list:
        """后处理: 格式校验、变量补全、去重"""
```

### 4.2 `RAG_service.py`

```python
class RAGService:
    """RAG 向量检索服务"""
    
    def retrieve(self, query: str, project_id: int, top_k: int = 5) -> list:
        """向量检索"""
        
    def index_document(self, doc_type: str, content: str, project_id: int, metadata: dict):
        """索引文档"""
        
    def get_embedding(self, text: str, model: str = "text-embedding-ada-002") -> list:
        """获取文本向量"""
```

## 5. 前端页面

### 5.1 AI 实验室 `/ai-lab`

**组件**: `AIStudio.vue`

**功能**:
- 输入源选择 (代码/OpenAPI/cURL/描述)
- 代码编辑器
- 生成选项配置
- 生成结果展示
- 用例采纳/编辑/忽略

## 6. 实现计划

| 阶段 | 任务 | 工时 |
|------|------|------|
| 1 | 数据库表创建 + Service 基础架构 | 2天 |
| 2 | 向量检索 (RAG) 服务 | 3天 |
| 3 | Prompt 模板 + LLM 调用 | 2天 |
| 4 | 多源解析器 (代码/OpenAPI/cURL) | 3天 |
| 5 | 后处理与去重逻辑 | 2天 |
| 6 | 前端 AI 实验室页面 | 3天 |
| 7 | 反馈与评分系统 | 2天 |

**总计**: 约 3 周
