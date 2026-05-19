# Codex-Guided-Dev 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建一个skill，用户通过关键词触发后，Claude调用Codex CLI生成开发细节文档，然后基于该文档进行详细开发。

**Architecture:** Skill放在用户本地 `~/.claude/skills/codex-guided-dev/SKILL.md`，工作流包含：解析需求→调用Codex→验证文件→分析项目→生成计划→用户确认→执行开发。

**Tech Stack:** Codex CLI, Claude Code Skill system

---

## File Structure

```
~/.claude/skills/codex-guided-dev/
  SKILL.md    # 主技能文件（包含完整workflow和Codex prompt模板）
```

---

## Task 1: 创建SKILL.md主文件

**Files:**
- Create: `~/.claude/skills/codex-guided-dev/SKILL.md`

- [ ] **Step 1: 编写SKILL.md文件结构**

```markdown
---
name: codex-guided-dev
description: Use when 用户说 "用codex帮我设计XXX模块" 或 "基于codex开发XXX" — 需要用户提供系统设计方案和模块详细设计方案路径
---

# Codex-Guided-Dev

## Overview

用户触发后，Claude调用Codex CLI基于设计文档生成开发细节，然后结合现有项目进行详细开发。确保开发细节严格遵循设计文档，不凭空杜撰。

## When to Use

**触发关键词（任一）：**
- "用codex帮我设计{模块名}"
- "基于codex开发{模块名}"
- "codex生成{模块名}开发细节"

**必须前置条件：**
- 用户提供了系统设计方案路径
- 用户提供了模块详细设计方案路径
- 用户指定了模块名称

## Workflow

### Step 1: 解析用户需求

解析用户输入，提取：
- **模块名称：** 从用户话语中提取
- **系统设计方案路径：** 用户指定
- **模块详细设计路径：** 用户指定

### Step 2: 调用Codex生成开发细节

**输出文件：** `docs/codex/codex-{模块名}开发细节.md`

Claude执行Codex CLI命令：
```bash
codex -p "你的prompt"
```

**Prompt模板：**
\`\`\`
# 任务：基于设计文档生成{模块名}的详细开发方案

## 系统设计背景
请阅读以下系统设计方案：
{系统设计方案内容}

## 模块详细设计
请阅读以下模块详细设计方案：
{模块详细设计内容}

## 要求
基于上述两份文档，生成详细的开发细节文档，包含：

1. **API接口设计** - 路由、参数、响应、状态码
2. **数据模型设计** - 表结构、字段、关联
3. **业务逻辑流程** - 流程、服务层逻辑、业务规则
4. **错误处理方案** - 异常类型、错误码、容错
5. **前端组件设计** - 页面组件、组件接口、状态管理

## 输出格式
生成完整的Markdown文档，严格遵循设计文档的约束，不要凭空添加设计。
\`\`\`

### Step 3: 验证文件生成

检查 `docs/codex/codex-{模块名}开发细节.md` 是否存在：
- 存在：继续Step 4
- 不存在：告知用户Codex执行失败，询问是否重试

### Step 4: 分析现有项目结构

读取并分析：
- 项目模块结构：`backend/app/`、`frontend/src/`
- 现有路由定义
- 已有的数据模型
- 代码规范文档

### Step 5: 生成开发计划

结合：
- Codex生成的开发细节文档
- 现有项目结构
- 代码规范

生成开发计划，包含：
- 文件创建/修改列表
- 具体改动点
- 开发顺序

### Step 6: 询问用户确认

向用户展示开发计划，询问：
"开发计划已生成，是否开始执行？"

### Step 7: 执行开发

用户确认后，按计划执行开发。

## Common Mistakes

| 错误 | 正确做法 |
|------|----------|
| Codex凭空设计 | 必须提供系统设计+模块详细设计两份文档 |
| 生成后不验证文件 | 必须检测文件是否成功生成 |
| 脱离现有项目结构开发 | 必须先分析现有代码再生成计划 |
| 跳过用户确认直接开发 | 必须询问用户是否开始开发 |

## Codex调用示例

用户输入：
```
用codex帮我设计终端模块，参考文档：
- 系统设计方案：docs/系统设计.md
- 模块详细设计：docs/终端模块详细设计.md
```

Claude执行：
```bash
codex -p "基于设计文档生成终端模块的详细开发方案..."
```

输出文件：`docs/codex/codex-终端模块开发细节.md`
```

- [ ] **Step 2: 验证文件语法完整性**

检查SKILL.md包含：
- ✅ YAML frontmatter（name, description）
- ✅ Description以"Use when"开头
- ✅ 完整的workflow步骤
- ✅ Codex prompt模板
- ✅ 错误处理说明
- ✅ 文件路径使用正斜杠

- [ ] **Step 3: 提交更改**

```bash
git add docs/superpowers/
git commit -m "feat: add codex-guided-dev skill implementation plan"
```

---

## Self-Review Checklist

1. **Spec coverage:** 设计文档的每个要求都有对应实现
   - [x] 触发关键词识别
   - [x] 解析用户需求
   - [x] Codex调用
   - [x] 文件验证
   - [x] 项目分析
   - [x] 开发计划生成
   - [x] 用户确认

2. **Placeholder scan:** 无TBD/TODO/placeholder

3. **Type consistency:** N/A（纯文档skill）

---

## Execution Options

**Plan complete.** 两个执行选项：

**1. Subagent-Driven (recommended)** - 派遣subagent执行创建任务

**2. Inline Execution** - 本会话直接执行

选择哪个？
