# Phase 4 模块拆分细化文档

> 基于《质量保障平台 - Phase 4 详细设计文档.md》
> 更新时间：2026-04-11
> 状态：**✅ 全部完成**

---

## 一、整体模块概览

| 模块 | 周期 | 主要功能 | 状态 |
|------|------|----------|------|
| **模块一：多租户与权限系统** | Week 13-14 | 租户/用户/角色/权限/中间件 | ✅ 已完成 |
| **模块二：资产共享中心** | Week 15-16 | 模板市场/共享资产/导入导出 | ✅ 已完成 |
| **模块三：智能分析引擎** | Week 17-18 | 失败聚类/变更影响/智能告警 | ✅ 已完成 |
| **模块四：质量大盘 + 开放API** | Week 19-20 | 仪表盘/组件/API管理 | ✅ 已完成 |

---

## 二、模块一：多租户与权限系统（Week 13-14）✅

### 1.1 数据模型 ✅ 已完成

**已创建的表（16张）：**

| 表名 | 说明 | 状态 |
|------|------|------|
| tenants | 租户表 | ✅ |
| users | 用户表 | ✅ |
| roles | 角色表 | ✅ |
| permissions | 权限表 | ✅ |
| user_roles | 用户角色关联表 | ✅ |
| projects | 项目表 | ✅ |
| project_members | 项目成员表 | ✅ |
| versions | 版本表 | ✅ |
| shared_assets | 共享资产表 | ✅ |
| asset_templates | 资产模板表 | ✅ |
| failure_clusters | 失败聚类表 | ✅ |
| change_impacts | 变更影响表 | ✅ |
| performance_baselines | 性能基线表 | ✅ |
| alert_rules | 告警规则表 | ✅ |
| dashboards | 仪表盘表 | ✅ |
| dashboard_widgets | 仪表盘组件表 | ✅ |

**相关文件：**
- `backend/app/models/tenant.py` - 模型定义
- `backend/migrate_phase4.py` - 迁移脚本

---

### 1.2 认证服务 ✅ 已完成

**API 路由：** `/api/auth`

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| POST | /login | 用户登录 | ✅ |
| POST | /register | 用户注册 | ✅ |
| POST | /refresh | 刷新令牌 | ✅ |
| GET | /me | 获取当前用户信息 | ✅ |
| POST | /logout | 登出 | ✅ |

**相关文件：**
- `backend/app/services/auth_service.py` - 认证服务
- `backend/app/routers/auth.py` - 认证路由
- `backend/app/config.py` - 共享配置

---

### 1.3 RBAC权限 ✅ 已完成

**API 路由：** `/api/tenant`

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| GET | /roles | 获取角色列表 | ✅ |
| GET | /roles/{role_id} | 获取角色详情(含权限) | ✅ |
| POST | /roles | 创建角色 | ✅ |
| PUT | /roles/{role_id} | 更新角色 | ✅ |
| DELETE | /roles/{role_id} | 删除角色 | ✅ |
| POST | /roles/{role_id}/permissions | 添加权限 | ✅ |
| DELETE | /roles/{role_id}/permissions | 移除权限 | ✅ |
| PUT | /roles/{role_id}/permissions | 批量设置权限 | ✅ |
| GET | /users | 获取用户列表 | ✅ |
| GET | /users/{user_id}/roles | 获取用户角色 | ✅ |
| POST | /users/roles | 分配角色 | ✅ |
| DELETE | /users/{user_id}/roles/{role_id} | 移除角色 | ✅ |
| PUT | /users/{user_id}/status | 更新用户状态 | ✅ |

**相关文件：**
- `backend/app/services/rbac_service.py` - RBAC服务
- `backend/app/routers/tenant.py` - 租户路由

---

### 1.4 租户中间件 ✅ 已完成

**功能：**
- JWT Token 解析与验证
- 请求级租户上下文注入
- 路径级豁免/拦截策略

**豁免路径：**
```
/api/auth/login
/api/auth/register
/api/auth/refresh
/api/health
/docs, /redoc, /openapi.json
/api/openapi/endpoints
/api/openapi/docs
/api/openapi/auth/token
/api/openapi/public
```

**相关文件：**
- `backend/app/middleware/tenant_middleware.py` - 中间件
- `backend/app/middleware/__init__.py` - 导出

---

### 1.5 项目管理 ✅ 已完成

**API 路由：** `/api/projects`

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| GET | /projects | 获取项目列表 | ✅ |
| POST | /projects | 创建项目 | ✅ |
| GET | /projects/{id} | 获取项目详情 | ✅ |
| PUT | /projects/{id} | 更新项目 | ✅ |
| DELETE | /projects/{id} | 删除项目 | ✅ |
| GET | /projects/{id}/members | 获取成员列表 | ✅ |
| POST | /projects/{id}/members | 添加成员 | ✅ |
| PUT | /projects/{id}/members/{user_id} | 更新成员角色 | ✅ |
| DELETE | /projects/{id}/members/{user_id} | 移除成员 | ✅ |

**相关文件：**
- `backend/app/services/project_service.py` - 项目服务
- `backend/app/routers/projects.py` - 项目路由

---

### 1.6 版本管理 ✅ 已完成

**API 路由：** `/api/versions`

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| GET | /versions | 获取版本列表 | ✅ |
| POST | /versions | 创建版本 | ✅ |
| GET | /versions/{id} | 获取版本详情 | ✅ |
| PUT | /versions/{id} | 更新版本 | ✅ |
| DELETE | /versions/{id} | 删除版本 | ✅ |
| POST | /versions/{id}/report | 绑定质量报告 | ✅ |
| GET | /versions/{id}/report | 获取质量报告 | ✅ |
| GET | /versions/{id}/summary | 获取测试摘要 | ✅ |
| POST | /versions/{id}/release | 发布版本 | ✅ |
| POST | /versions/{id}/archive | 归档版本 | ✅ |
| GET | /versions/compare/{v1}/{v2} | 对比两个版本 | ✅ |

**相关文件：**
- `backend/app/services/version_service.py` - 版本服务
- `backend/app/routers/versions.py` - 版本路由

---

### 1.7 前端-登录注册 ✅ 已完成

**文件：** `frontend/src/views/Auth.vue`

**功能：**
- 登录/注册表单切换
- 密码强度指示
- 错误提示
- Token 存储与自动刷新

**相关文件：**
- `frontend/src/stores/auth.js` - Pinia 认证状态
- `frontend/src/router/index.js` - 路由守卫

---

### 1.8 前端-用户管理 ✅ 已完成

**文件：** `frontend/src/views/UserManage.vue`

**功能：**
- 用户列表表格
- 用户详情弹窗

---

### 1.9 前端-项目管理 ✅ 已完成

**文件：** `frontend/src/views/ProjectManage.vue`

**功能：**
- 项目卡片网格
- 创建项目弹窗
- 搜索和状态筛选

---

## 三、模块二：资产共享中心（Week 15-16）✅

### 2.1 数据模型 ✅ 已完成

### 2.2 共享服务 ✅ 已完成

**API 路由：** `/api/share`

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| GET | /assets | 获取共享资产列表 | ✅ |
| GET | /assets/received | 获取收到的共享 | ✅ |
| GET | /assets/sent | 获取发出的共享 | ✅ |
| POST | /assets | 分享资产 | ✅ |
| PUT | /assets/{id} | 更新共享 | ✅ |
| DELETE | /assets/{id} | 取消分享 | ✅ |
| POST | /assets/import | 导入共享资产 | ✅ |

**相关文件：**
- `backend/app/services/share_service.py` - 共享服务
- `backend/app/routers/share.py` - 共享路由

---

### 2.3 模板服务 ✅ 已完成

**API 路由：** `/api/templates`

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| GET | /templates | 获取模板列表 | ✅ |
| GET | /templates/market | 模板市场 | ✅ |
| GET | /templates/mine | 我的模板 | ✅ |
| POST | /templates | 创建模板 | ✅ |
| GET | /templates/{id} | 获取模板详情 | ✅ |
| PUT | /templates/{id} | 更新模板 | ✅ |
| DELETE | /templates/{id} | 删除模板 | ✅ |
| POST | /templates/{id}/use | 使用模板 | ✅ |

**相关文件：**
- `backend/app/services/template_service.py` - 模板服务
- `backend/app/routers/templates.py` - 模板路由

---

### 2.4 前端-资产中心 ✅ 已完成

**文件：** `frontend/src/views/AssetCenter.vue`

**功能：**
- 模板市场/我的模板/收到的共享 Tab切换
- 模板搜索和类型筛选
- 模板使用弹窗

---

## 四、模块三：智能分析引擎（Week 17-18）✅

### 3.1 失败聚类服务 ✅ 已完成

**API 路由：** `/api/ai/clusters`

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| GET | /clusters | 获取聚类列表 | ✅ |
| GET | /clusters/{id} | 获取聚类详情 | ✅ |
| POST | /clusters/{id}/analyze | AI根因分析 | ✅ |
| PUT | /clusters/{id}/resolve | 标记已解决 | ✅ |
| DELETE | /clusters/{id}/ignore | 忽略聚类 | ✅ |

---

### 3.2 变更影响服务 ✅ 已完成

**API 路由：** `/api/ai/impact`

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| POST | /predict | 预测变更影响 | ✅ |
| GET | /history | 获取预测历史 | ✅ |
| GET | /{id} | 获取预测详情 | ✅ |

---

### 3.3 智能告警服务 ✅ 已完成

**API 路由：** `/api/ai/alerts`

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| GET | /rules | 获取告警规则列表 | ✅ |
| POST | /rules | 创建告警规则 | ✅ |
| PUT | /rules/{id} | 更新告警规则 | ✅ |
| DELETE | /rules/{id} | 删除告警规则 | ✅ |
| PUT | /rules/{id}/toggle | 启用/禁用规则 | ✅ |
| POST | /check | 检查告警触发 | ✅ |

---

### 3.4 性能基线服务 ✅ 已完成

**API 路由：** `/api/ai/baselines`

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| GET | /baselines | 获取基线列表 | ✅ |
| POST | /baselines | 创建基线 | ✅ |
| POST | /baselines/{id}/collect | 采集数据 | ✅ |
| DELETE | /baselines/{id} | 删除基线 | ✅ |

---

### 3.5 前端-智能分析 ✅ 已完成

**文件：** `frontend/src/views/AIAnalysis.vue`

**功能：**
- 失败聚类/变更影响/告警配置/性能基线 4个Tab
- AI根因分析弹窗
- 告警规则启用/禁用

**相关文件：**
- `backend/app/services/ai_service.py` - AI分析服务（4合一）
- `backend/app/routers/ai.py` - AI路由

---

## 五、模块四：质量大盘 + 开放API（Week 19-20）✅

### 4.1 仪表盘服务 ✅ 已完成

**API 路由：** `/api/dashboards`

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| GET | /dashboards | 获取仪表盘列表 | ✅ |
| POST | /dashboards | 创建仪表盘 | ✅ |
| GET | /dashboards/{id} | 获取仪表盘详情 | ✅ |
| PUT | /dashboards/{id} | 更新仪表盘 | ✅ |
| DELETE | /dashboards/{id} | 删除仪表盘 | ✅ |
| GET | /dashboards/{id}/widgets | 获取组件列表 | ✅ |
| POST | /dashboards/{id}/widgets | 添加组件 | ✅ |
| PUT | /widgets/{id} | 更新组件 | ✅ |
| DELETE | /widgets/{id} | 删除组件 | ✅ |

**组件类型：** metric_card, line_chart, bar_chart, pie_chart, table, text, heatmap, gauge, iframe

---

### 4.2 开放API服务 ✅ 已完成

**API 路由：** `/api/openapi`

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| GET | /endpoints | 获取API端点列表 | ✅ |
| GET | /docs | API文档信息 | ✅ |
| GET | /keys | 获取API Key列表 | ✅ |
| POST | /keys | 创建API Key | ✅ |
| DELETE | /keys/{id} | 删除API Key | ✅ |
| POST | /auth/token | 获取访问令牌 | ✅ |
| GET | /public/health | 公共健康检查 | ✅ |
| GET | /public/projects | 公开项目列表 | ✅ |

**相关文件：**
- `backend/app/services/dashboard_service.py` - 仪表盘+开放API服务
- `backend/app/routers/dashboard.py` - 仪表盘路由
- `backend/app/routers/openapi.py` - 开放API路由

---

### 4.3 前端-质量大盘 ✅ 已完成

**文件：** `frontend/src/views/QualityDashboard.vue`

**功能：**
- 个人/项目/租户仪表盘 Tab切换
- 仪表盘选择器
- 组件网格布局
- 创建仪表盘弹窗
- 添加组件弹窗（支持6种类型）

---

## 六、测试与验收

### 6.1 模块一测试用例 ✅

| 序号 | 测试项 | 测试结果 |
|------|--------|----------|
| 1 | 用户登录 | ✅ 通过 |
| 2 | 用户注册 | ✅ 通过 |
| 3 | Token刷新 | ✅ 通过 |
| 4 | 获取当前用户信息 | ✅ 通过 |
| 5 | 获取角色列表 | ✅ 通过 |
| 6 | 获取角色详情 | ✅ 通过 |
| 7 | 获取用户列表 | ✅ 通过 |
| 8 | 创建项目 | ✅ 通过 |
| 9 | 获取项目列表 | ✅ 通过 |
| 10 | 更新项目 | ✅ 通过 |
| 11 | 添加项目成员 | ✅ 通过 |
| 12 | 删除项目 | ✅ 通过 |
| 13 | 重复key创建项目 | ✅ 400报错正确 |

### 6.2 模块二测试用例 ✅

| 序号 | 测试项 | 测试结果 |
|------|--------|----------|
| 1 | 创建模板 | ✅ 通过 |
| 2 | 获取模板列表 | ✅ 通过 |
| 3 | 获取模板市场 | ✅ 通过 |
| 4 | 获取我的模板 | ✅ 通过 |
| 5 | 使用模板 | ✅ 通过 |
| 6 | 更新模板 | ✅ 通过 |
| 7 | 分享资产 | ✅ 通过 |
| 8 | 获取共享列表 | ✅ 通过 |
| 9 | 获取发出的共享 | ✅ 通过 |
| 10 | 取消分享 | ✅ 通过 |

### 6.3 模块三测试用例 ✅

| 序号 | 测试项 | 测试结果 |
|------|--------|----------|
| 1 | 创建告警规则 | ✅ 通过 |
| 2 | 获取告警规则列表 | ✅ 通过 |
| 3 | 检查告警触发 | ✅ 通过 |
| 4 | 预测变更影响 | ✅ 通过 |
| 5 | 获取影响历史 | ✅ 通过 |
| 6 | 创建性能基线 | ✅ 通过 |
| 7 | 获取基线列表 | ✅ 通过 |
| 8 | 采集基线数据 | ✅ 通过 |
| 9 | 切换告警状态 | ✅ 通过 |
| 10 | 删除告警规则 | ✅ 通过 |

### 6.4 模块四测试用例 ✅

| 序号 | 测试项 | 测试结果 |
|------|--------|----------|
| 1 | 创建仪表盘 | ✅ 通过 |
| 2 | 获取仪表盘列表 | ✅ 通过 |
| 3 | 获取仪表盘详情 | ✅ 通过 |
| 4 | 添加指标卡片组件 | ✅ 通过 |
| 5 | 添加折线图组件 | ✅ 通过 |
| 6 | 获取API端点列表 | ✅ 通过 |
| 7 | 公共健康检查 | ✅ 通过 |
| 8 | Token获取接口 | ✅ 通过 |
| 9 | 删除仪表盘 | ✅ 通过 |

---

## 七、文件清单

### 7.1 后端文件结构

```
backend/
├── app/
│   ├── models/
│   │   ├── tenant.py          # ✅ Phase 4 模型（16张表）
│   │   └── __init__.py
│   ├── services/
│   │   ├── auth_service.py       # ✅ 认证服务
│   │   ├── rbac_service.py       # ✅ RBAC服务
│   │   ├── project_service.py    # ✅ 项目服务
│   │   ├── version_service.py    # ✅ 版本服务
│   │   ├── share_service.py     # ✅ 共享服务
│   │   ├── template_service.py  # ✅ 模板服务
│   │   ├── ai_service.py        # ✅ AI分析服务
│   │   └── dashboard_service.py  # ✅ 仪表盘+开放API
│   ├── routers/
│   │   ├── auth.py              # ✅ 认证路由
│   │   ├── tenant.py           # ✅ 租户路由
│   │   ├── projects.py          # ✅ 项目路由
│   │   ├── versions.py         # ✅ 版本路由
│   │   ├── share.py            # ✅ 共享路由
│   │   ├── templates.py         # ✅ 模板路由
│   │   ├── ai.py               # ✅ AI路由
│   │   ├── dashboard.py         # ✅ 仪表盘路由
│   │   └── openapi.py          # ✅ 开放API路由
│   ├── middleware/
│   │   ├── tenant_middleware.py # ✅ 租户中间件
│   │   └── __init__.py
│   ├── config.py                # ✅ 共享配置
│   └── main.py                  # ✅ 主入口
├── migrate_phase4.py            # ✅ 数据库迁移
└── test_*.py                   # ✅ 测试脚本
```

### 7.2 前端文件结构

```
frontend/src/
├── views/
│   ├── Auth.vue                  # ✅ 登录注册
│   ├── ProjectManage.vue        # ✅ 项目管理
│   ├── UserManage.vue           # ✅ 用户管理
│   ├── TeamManage.vue           # ✅ 团队管理
│   ├── AssetCenter.vue          # ✅ 资产中心
│   ├── AIAnalysis.vue           # ✅ AI分析
│   └── QualityDashboard.vue     # ✅ 质量大盘
├── stores/
│   └── auth.js                 # ✅ 认证状态
├── router/
│   └── index.js                # ✅ 路由配置
└── vite.config.ts              # ✅ API代理配置
```

---

## 八、数据保留

**数据库文件：** `backend/data/api_debug.db`

**测试数据：**
- 用户：admin, newuser
- 项目：API_DEBUG, VERSION_TEST
- 版本：v1.0.0 (已归档), v1.1.0 (draft)
- 模板：3个
- 共享资产：多条
- AI预测记录、告警规则、性能基线
- 仪表盘：多个

---

## 九、开发进度总览

```
Week 13-14: 模块一
├── 1.1 数据模型 ✅
├── 1.2 认证服务 ✅
├── 1.3 RBAC权限 ✅
├── 1.4 租户中间件 ✅
├── 1.5 项目管理 ✅
├── 1.6 版本管理 ✅
├── 1.7 前端-登录注册 ✅
├── 1.8 前端-用户管理 ✅
└── 1.9 前端-项目管理 ✅

Week 15-16: 模块二
├── 2.1 数据模型 ✅
├── 2.2 共享服务 ✅
├── 2.3 模板服务 ✅
└── 2.4 前端-资产中心 ✅

Week 17-18: 模块三
├── 3.1 失败聚类 ✅
├── 3.2 变更影响 ✅
├── 3.3 智能告警 ✅
├── 3.4 性能基线 ✅
└── 3.5 前端-智能分析 ✅

Week 19-20: 模块四
├── 4.1 仪表盘服务 ✅
├── 4.2 开放API ✅
├── 4.3 插件体系 (预留)
└── 4.4 前端-质量大盘 ✅
```

---

*文档版本：v2.0*
*最后更新：2026-04-11*
*状态：✅ Phase 4 全部完成*
