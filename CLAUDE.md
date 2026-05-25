# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Quality Manage Platform - 现代化质量管理平台，采用 FastAPI + Vue 3 技术栈。

当前版本保留平台底座（登录、用户、角色、权限、组织、菜单管理），业务模块（用例、场景、报告、AI功能等）正在新体系上开发。

## 开发命令

### 前端
```bash
cd frontend
npm install              # 安装依赖
npm run dev -- --host   # 开发模式运行（0.0.0.0:3000）
npm run build            # 生产构建
npm run preview          # 预览构建结果
```

### 后端
```bash
cd backend
pip install -r requirements.txt                              # 安装依赖
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000    # 运行服务
python -m pytest                                               # 运行所有测试
python -m pytest tests/services/test_ai_service.py            # 运行单个测试文件
```

### 测试标记
- `@pytest.mark.p0` - 核心流程冒烟测试
- `@pytest.mark.p1` - 重要功能测试
- `@pytest.mark.p2` - 边界/异常测试
- `@pytest.mark.api` - API测试
- `@pytest.mark.unit` - 单元测试

### 默认账号
```
用户名: admin
密码: admin123
```

## 架构概览

```
backend/
├── app/
│   ├── main.py          # FastAPI 应用入口
│   ├── config.py        # 配置管理
│   ├── database.py      # SQLAlchemy 数据库连接
│   ├── models/          # SQLAlchemy 模型
│   ├── schemas/         # Pydantic 请求/响应模型
│   ├── routers/         # API 路由（按功能模块分离）
│   ├── services/        # 业务逻辑层
│   │   └── ai/         # AI 相关服务
│   └── repositories/    # 数据访问层
└── tests/               # pytest 测试

frontend/src/
├── api/                 # API 调用封装（axios）
├── components/           # Vue 组件（common/通用, dashboard/, terminal/, case/）
├── views/               # 页面视图
│   ├── ai/             # AI 功能页面
│   ├── case/           # 用例管理
│   ├── docgen/         # 文档生成
│   ├── platform/       # 平台管理（用户、角色、组织等）
│   ├── report/         # 报告管理
│   └── scenario/       # 场景管理
├── stores/              # Pinia 状态管理
├── router/              # Vue Router 配置
└── utils/               # 工具函数
```

## 技术栈

- **前端**: Vue 3, Vite, Pinia, Vue Router, Element Plus, Axios
- **后端**: FastAPI, SQLAlchemy, Pydantic v2, SQLite
- **测试**: pytest

## 协作模式

本项目采用 "Codex 规划与审查，Claude Code 实现与验证" 的协作模式。

Claude 必须遵循的工作流：
- `/codex-task .ai/tasks/<task-file>.md` - 执行实现任务包
- `/codex-review-fix .ai/reviews/<review-file>.md` - 修复审查问题

详细规范见 `AGENTS.md` 和 `.ai/INDEX.md`。

## 前端新增页面/菜单规则

当任务涉及新增页面、菜单、弹窗、抽屉、表格页、查询栏或主题样式时：

1. 必须先读取任务包中的“视觉/交互基准页”。
2. 必须先复用最接近的现有页面结构和样式模式，再做局部改造。
3. 不允许自行设计一套新的 header、filters、table、background、sidebar 菜单风格。
4. 如任务涉及左侧菜单，必须对照 `frontend/src/app/AppShell.vue` 的 `menuList` 写法。
5. 如任务涉及浅色/深色主题，必须同时检查 `html:not(.dark)` 和默认深色分支。
6. 如果没有明确基准页，先从现有同类页面中选一个最接近的页面作为基准，再开始改动。
