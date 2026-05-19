# Phase 2 全面测试报告 - Cases/Scenarios/Environments/Logs

**测试日期**: 2026-05-06  
**测试范围**: Cases/Scenarios/Environments/Audit Logs API  
**后端**: http://localhost:8000  
**前端**: http://localhost:3000  
**认证**: admin/admin123

---

## 一、Cases API 测试结果

| # | 接口 | 方法 | 路径 | 结果 | 说明 |
|---|------|------|------|------|------|
| 1 | 用例列表 | GET | /api/cases | PASS | 返回21+条用例数据 |
| 2 | 创建用例 | POST | /api/cases | PASS | 创建成功，返回完整用例对象 |
| 3 | 获取单个 | GET | /api/cases/{id} | PASS | 返回指定ID的用例详情 |
| 4 | 更新用例 | PUT | /api/cases/{id} | PASS | 字段更新成功 |
| 5 | 运行用例 | POST | /api/cases/{id}/run | PASS | 执行成功，返回response_time等 |
| 6 | 批量删除 | POST | /api/cases/batch-delete | PASS | 正确格式: 直接传列表 [ids] |
| 7 | 删除用例 | DELETE | /api/cases/{id} | PASS | 返回 {"code":0,"message":"deleted"} |

### 问题发现
- **BUG**: batch-delete 接收 `{"ids": [...]}` 格式报错，需直接传列表 `[...]`

---

## 二、Scenarios API 测试结果

| # | 接口 | 方法 | 路径 | 结果 | 说明 |
|---|------|------|------|------|------|
| 1 | 场景列表 | GET | /api/scenarios | PASS | 返回21个场景 |
| 2 | 创建场景 | POST | /api/scenarios | PASS | 创建成功，steps自动初始化为空数组 |
| 3 | 获取单个 | GET | /api/scenarios/{id} | PASS | 场景详情包含steps数组 |
| 4 | 更新场景 | PUT | /api/scenarios/{id} | PASS | 字段更新成功 |
| 5 | 运行场景 | POST | /api/scenarios/{id}/run | PASS | 执行成功，返回summary统计 |
| 6 | 添加步骤 | POST | /api/scenarios/{id}/steps | PASS | 步骤添加成功 |
| 7 | 更新步骤 | PUT | /api/scenarios/{id}/steps/{step_id} | PASS | 步骤更新成功 |
| 8 | 删除步骤 | DELETE | /api/scenarios/{id}/steps/{step_id} | PASS | 返回 {"code":0,"message":"deleted"} |
| 9 | 获取步骤 | GET | /api/scenarios/{id}/steps | FAIL | 返回405 Method Not Allowed |
| 10 | 删除场景 | DELETE | /api/scenarios/{id} | PASS | 删除成功 |

### 问题发现
- **BUG**: GET /api/scenarios/{id}/steps 不支持(405)，步骤应通过 GET /api/scenarios/{id} 获取
- **根因**: OpenAPI文档显示该路由仅支持POST，无GET方法

---

## 三、Environments API 测试结果

| # | 接口 | 方法 | 路径 | 结果 | 说明 |
|---|------|------|------|------|------|
| 1 | 环境列表 | GET | /api/environments | PASS | 返回7个环境 |
| 2 | 创建环境 | POST | /api/environments | PASS | dict格式variables可创建成功 |
| 3 | 获取单个 | GET | /api/environments/{id} | PASS | 环境详情正常 |
| 4 | 更新环境 | PUT | /api/environments/{id} | PASS | 更新成功 |
| 5 | 设置默认 | POST | /api/environments/{id}/set-default | PASS | 返回 {"code":0,"message":"set as default"} |
| 6 | 删除环境 | DELETE | /api/environments/{id} | PASS | 删除成功 |

### 问题发现
- **BUG**: POST/PUT时variables字段格式需为dict类型，非数组格式
- **API设计**: list格式 `[{"key":"base_url","value":"..."}]` 会报 dict_type 错误

---

## 四、Audit Logs API 测试结果

| # | 接口 | 方法 | 路径 | 结果 | 说明 |
|---|------|------|------|------|------|
| 1 | 日志查询 | GET | /api/audit/logs | PASS | 返回 {"total":0,"items":[]} |
| 2 | 统计概览 | GET | /api/audit/stats/overview | FAIL | 返回500 Internal Server Error |

### 问题发现
- **BUG**: GET /api/audit/stats/overview 500错误，需检查后端日志
- **可能原因**: 统计SQL查询错误或数据库表结构不匹配

---

## 五、前端UI验证结果

| 页面 | 导航 | 结果 | 说明 |
|------|------|------|------|
| 登录页 | /login | PASS | 登录表单正常显示 |
| 用例管理 | /cases | PASS | 用例列表、搜索框、新建按钮正常 |
| 场景编排 | /scenarios | PASS | 场景列表、编辑/删除/运行按钮正常 |
| 环境管理 | /environments | PASS | 环境列表、编辑/星标/删除按钮正常 |
| 执行日志 | /logs | PASS | 日志列表、状态筛选器正常 |

---

## 六、测试数据清理

已清理测试数据:
- 测试用例: 516, 517, 518, 519, 520, 522, 523, 524 (批量删除)
- 测试场景: 23
- 测试环境: 8

---

## 七、缺陷汇总与建议

| 优先级 | 缺陷 | 描述 | 建议 |
|--------|------|------|------|
| HIGH | GET /api/audit/stats/overview 500错误 | 审计统计概览功能不可用 | 立即排查后端错误日志 |
| MEDIUM | POST /api/cases/batch-delete 格式问题 | {"ids": [1,2,3]} 报错，需直接传 [1,2,3] | 统一API设计，明确参数格式 |
| MEDIUM | GET /api/scenarios/{id}/steps 405 | 步骤获取路由未定义 | 如需独立API，添加GET路由 |
| LOW | POST/PUT /api/environments variables格式 | 仅接受dict，不支持数组格式 | 在API文档中明确标注 |

---

## 测试结论

**API核心功能可用，发现4个缺陷需修复**

- Cases API: 7/7 通过
- Scenarios API: 9/10 通过
- Environments API: 6/6 通过
- Audit Logs API: 1/2 通过
- 前端UI: 5/5 通过
