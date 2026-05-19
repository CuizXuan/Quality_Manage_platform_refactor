# P5-M6: AI 质量顾问

## 1. 模块概述

**功能**: 7x24 小时智能质量助手，主动发现问题并给出建议

**核心能力**:
- 智能问答 (质量相关问题)
- 主动巡检 (代码/测试/缺陷)
- 日报/周报自动生成
- 预测性告警

## 2. 数据库设计

### 2.1 AI 顾问对话表 `ai_advisor_chat`

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 自增主键 |
| user_id | INTEGER | FK | 用户 ID |
| session_id | VARCHAR(50) | | 会话 ID |
| question | TEXT | NOT NULL | 用户问题 |
| answer | TEXT | NOT NULL | AI 回答 |
| context | TEXT | | 上下文 JSON |
| referenced_docs | TEXT | | 引用的文档 ID 列表 |
| feedback | VARCHAR(20) | | helpful/not_helpful |
| created_at | TIMESTAMP | DEFAULT | 创建时间 |

## 3. API 设计

### 3.1 问答

```
POST /api/ai/advisor/chat
Request:
{
  "question": "这个接口为什么失败？",
  "session_id": "sess_123",
  "context": {
    "case_id": 456,
    "failure_log_id": 789
  }
}

Response:
{
  "answer": "根据分析，该接口失败原因是...",
  "referenced_docs": [
    {"type": "api_doc", "id": 123, "snippet": "..."}
  ],
  "suggestions": [
    "检查数据库连接池配置",
    "添加超时重试机制"
  ]
}
```

### 3.2 主动巡检

```
POST /api/ai/advisor/inspect
Request:
{
  "scope": "project|repository|test_cases",
  "target_id": 1,
  "check_types": ["coverage", "defects", "code_smell"]
}

Response:
{
  "findings": [
    {
      "type": "low_coverage",
      "severity": "warning",
      "description": "UserService.java 覆盖率仅 45%",
      "recommendation": "建议补充单元测试"
    }
  ],
  "overall_score": 78
}
```

### 3.3 报告生成

```
POST /api/ai/advisor/report
Request:
{
  "type": "daily|weekly|monthly",
  "project_id": 1,
  "date_range": {
    "start": "2026-01-01",
    "end": "2026-01-07"
  },
  "channels": ["email", "webhook"]
}
```

## 4. 服务层设计

### 4.1 `AIAdvisorService.py`

```python
class AIAdvisorService:
    """AI 质量顾问服务"""
    
    def chat(self, question: str, user_id: int, session_id: str, context: dict) -> dict:
        """智能问答"""
        
    def _build_context(self, context: dict) -> list:
        """构建上下文"""
        
    def _call_llm(self, prompt: str) -> dict:
        """调用 LLM"""
        
    def _format_response(self, raw_response: dict) -> dict:
        """格式化响应"""
```

### 4.2 `ProactiveInspectService.py`

```python
class ProactiveInspectService:
    """主动巡检服务"""
    
    def inspect_project(self, project_id: int, check_types: list) -> dict:
        """巡检项目"""
        
    def inspect_coverage(self, project_id: int) -> dict:
        """检查测试覆盖率"""
        
    def inspect_defects(self, project_id: int) -> dict:
        """检查缺陷趋势"""
        
    def inspect_code_quality(self, repo_id: int) -> dict:
        """检查代码质量"""
```

### 4.3 `ReportGenService.py`

```python
class ReportGenService:
    """报告生成服务"""
    
    def generate_daily_report(self, project_id: int, date: date) -> dict:
        """生成日报"""
        
    def generate_weekly_report(self, project_id: int, week: int) -> dict:
        """生成周报"""
        
    def _collect_metrics(self, project_id: int, date_range: dict) -> dict:
        """收集指标数据"""
        
    def _build_narrative(self, metrics: dict, report_type: str) -> str:
        """构建报告文本"""
```

## 5. 前端页面

### 5.1 AI 顾问对话 `/ai-lab/advisor`

**组件**: `AIAdvisorChat.vue`

**功能**:
- 对话界面
- 会话历史
- 反馈评价
- 上下文注入

### 5.2 巡检报告 `/ai-lab/inspect`

**组件**: `InspectionReport.vue`

**功能**:
- 巡检配置
- 报告展示
- 问题追踪
- 改进建议

### 5.3 自动报告 `/ai-lab/reports`

**组件**: `AutoReport.vue`

**功能**:
- 报告配置
- 发送渠道
- 历史报告
- 订阅管理

## 6. 实现计划

| 阶段 | 任务 | 工时 |
|------|------|------|
| 1 | 数据库表 + 对话 Service | 2天 |
| 2 | LLM 集成与 Prompt | 2天 |
| 3 | RAG 检索增强 | 2天 |
| 4 | 主动巡检服务 | 3天 |
| 5 | 报告自动生成 | 2天 |
| 6 | 前端页面 | 2天 |

**总计**: 约 2 周
