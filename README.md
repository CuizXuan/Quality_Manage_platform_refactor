# Quality Manage Platform

现代化质量管理平台重构脚手架。

当前版本只保留平台底座：

- 登录页
- JWT 登录认证
- 用户管理
- 角色与权限管理
- 组织管理
- 菜单管理
- 深色与浅色主题

业务模块将在新体系上重新开发，不再沿用旧代码。

后续开发规范与模块设计见 [docs/README.md](./docs/README.md)。

## 技术栈

### 前端

- Vue 3
- Vite
- Pinia
- Vue Router
- Element Plus
- Axios

### 后端

- FastAPI
- SQLAlchemy
- Pydantic v2
- SQLite

## 默认账号

```text
username: admin
password: admin123
```

## 启动

### 后端

```powershell
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 前端

```powershell
cd frontend
npm install
npm run dev -- --host
```

## 访问

- 前端：http://localhost:3000
- 后端文档：http://localhost:8000/docs
