# Phase 5 开发指南

## 一、Phase 5 模块总览

| 模块 | 名称 | 优先级 | 工时 | 状态 |
|------|------|--------|------|------|
| P5-M1 | AI 测试生成引擎 | P0 | 3周 | 待开发 |
| P5-M2 | 测试自愈引擎 | P0 | 2周 | 待开发 |
| P5-M3 | 全链路压测引擎 | P1 | 2周 | 待开发 |
| P5-M4 | 混沌工程引擎 | P1 | 1.5周 | 待开发 |
| P5-M5 | 测试数据工厂 | P1 | 1.5周 | 待开发 |
| P5-M6 | AI 质量顾问 | P2 | 2周 | 待开发 |
| P5-M7 | 开发者生态 | P2 | 2周 | 待开发 |
| P5-M8 | 企业级基础设施 | P3 | 1周 | 待开发 |

**总计**: 约 8 周

## 二、新增数据库表 (共20张)

### AI 相关 (6张)
1. `ai_gen_history` - AI 生成历史
2. `self_heal_log` - 自愈日志
3. `smart_orch_rule` - 智能编排规则
4. `vector_doc` - 向量文档
5. `ai_advisor_chat` - AI 顾问对话
6. `embedding_cache` - Embedding 缓存

### 全链路压测 (5张)
7. `traffic_record` - 流量录制
8. `traffic_replay` - 流量回放
9. `traffic_tag` - 流量标签
10. `diff_report` - Diff 报告
11. `compare_result` - 对比结果

### 混沌工程 (5张)
12. `chaos_experiment` - 混沌实验
13. `fault_injection` - 故障注入
14. `fault_type` - 故障类型
15. `chaos_metric` - 混沌指标
16. `resilience_score` - 韧性评分

### 测试数据 (4张)
17. `data_mask_rule` - 脱敏规则
18. `data_gen_template` - 数据生成模板
19. `data_snapshot` - 数据快照
20. `data_clone_task` - 数据克隆任务

## 三、新增前端页面

| 页面 | 路由 | 对应模块 |
|------|------|----------|
| AI 实验室 | `/ai-lab` | M1, M2, M6 |
| 全链路压测 | `/load-test` | M3 |
| 混沌工程 | `/chaos` | M4 |
| 测试数据 | `/test-data` | M5 |
| 插件市场 | `/marketplace` | M7 |
| 企业设置 | `/enterprise` | M8 |

## 四、推荐开发顺序

### 第一批 (核心功能) - 建议优先开发
1. **P5-M1 AI 测试生成引擎** - 最复杂，先攻克
2. **P5-M2 测试自愈引擎** - 依赖 M1 的部分能力

### 第二批 (平台能力)
3. **P5-M3 全链路压测引擎**
4. **P5-M4 混沌工程引擎**
5. **P5-M5 测试数据工厂**

### 第三批 (增值服务)
6. **P5-M6 AI 质量顾问**
7. **P5-M7 开发者生态**
8. **P5-M8 企业级基础设施**

## 五、开发前置准备

### 1. 环境准备
```bash
# 准备 LLM API (OpenAI/GPT-4 或 Claude)
# 准备向量数据库 (可选，本地模式可先用 SQLite)

# 安装依赖
pip install openai anthropic chromadb
```

### 2. 数据库迁移
```bash
# 创建 Phase 5 相关表
cd backend
alembic revision --autogenerate -m "Phase 5 AI and Chaos tables"
```

## 六、详细设计文档

| 模块 | 文档路径 |
|------|----------|
| P5-M1 | `docs/phase5/P5-M1_AI测试生成引擎.md` |
| P5-M2 | `docs/phase5/P5-M2_测试自愈引擎.md` |
| P5-M3 | `docs/phase5/P5-M3_全链路压测引擎.md` |
| P5-M4 | `docs/phase5/P5-M4_混沌工程引擎.md` |
| P5-M5 | `docs/phase5/P5-M5_测试数据工厂.md` |
| P5-M6 | `docs/phase5/P5-M6_AI质量顾问.md` |
| P5-M7 | `docs/phase5/P5-M7_开发者生态.md` |
| P5-M8 | `docs/phase5/P5-M8_企业级基础设施.md` |

## 七、下一步

请确认是否开始 Phase 5 开发。推荐从 **P5-M1 (AI 测试生成引擎)** 开始。

如需开始开发，请回复 **"开始 P5-M1"** 或指定其他模块。
