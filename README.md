# Quality Manage Platform

全栈质量测试管理平台，集成接口调试、自动化测试、AI 测试生成、混沌工程、压测、覆盖率分析等功能。

## 功能模块

| 模块 | 说明 |
|------|------|
| 📋 **接口调试** | 粘贴 cURL/Fetch 自动解析，支持 GET/POST/PUT/DELETE/PATCH |
| 📁 **用例管理** | 接口集合管理，文件夹组织，参数化变量 |
| 🤖 **AI 测试** | AI 生成测试用例、智能断言、自愈测试（Self-Healing） |
| 🧪 **自动化测试** | 场景编排，断言引擎，数据驱动 |
| 🔥 **混沌工程** | 故障注入，稳定性测试 |
| ⚡ **压力测试** | 循环调用 + 并发测试，性能分析 |
| 🐛 **缺陷管理** | 缺陷跟踪，与禅道/Jira 集成 |
| 📊 **质量看板** | 覆盖率、执行趋势、质量门禁 |
| 🎭 **Mock 服务** | 动态 Mock 规则，接口模拟 |
| 📦 **数据工厂** | 测试数据生成、脱敏、克隆 |
| 🚦 **流量录制** | 流量回放，Diff 比对 |
| 📑 **报告系统** | 自动生成测试报告，支持多模板 |

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Element Plus + Pinia |
| 后端 | FastAPI + SQLAlchemy + SQLite/PostgreSQL |
| AI | 大模型 API（自定义接入） |
| 存储 | SQLite（开发）/ PostgreSQL（生产） |

## 项目结构

```
Quality_Manage_platform/
├── frontend/               # Vue3 前端
│   ├── src/
│   │   ├── api/           # API 调用
│   │   ├── components/    # 组件
│   │   ├── views/         # 页面视图
│   │   ├── stores/        # Pinia 状态管理
│   │   ├── router/        # 路由配置
│   │   └── utils/         # 工具函数
│   └── package.json
│
├── backend/                # FastAPI 后端
│   ├── app/
│   │   ├── main.py        # 应用入口
│   │   ├── config.py      # 配置管理
│   │   ├── database.py    # 数据库连接
│   │   ├── models/        # SQLAlchemy 模型
│   │   ├── schemas/       # Pydantic 请求/响应
│   │   ├── routers/       # API 路由
│   │   ├── services/      # 业务逻辑
│   │   └── middleware/    # 中间件
│   ├── tests/             # pytest 测试
│   └── requirements.txt
│
├── docs/                   # 设计文档
│   ├── phase5/            # Phase 5 模块设计
│   ├── testing/           # 测试报告
│   └── superpowers/       # 设计规格
│
├── test-reports/           # 测试报告输出
├── test-results/           # 测试结果数据
├── report_output/          # 报告生成输出
├── AGENTS.md               # AI 编码规范
├── CLAUDE.md               # Claude 配置
├── PROJECT_NOTES.md        # 项目笔记
└── README.md
```

## 快速启动

### 1. 安装依赖

**前端**
```bash
cd frontend
npm install --registry https://registry.npmmirror.com
```

**后端**
```bash
cd backend
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

### 2. 启动服务

**前端**（端口 3000）
```bash
cd frontend
npm run dev -- --host
```

**后端**（端口 8000）
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

或双击 `启动脚本.bat`。

### 3. 访问

- 前端：http://localhost:3000
- 后端 API 文档：http://localhost:8000/docs

## 开发规范

参见 [AGENTS.md](AGENTS.md) 了解更多编码规范和约束。
