# 用例管理模块详细测试用例

## 模块概述
用例管理模块负责测试用例的 CRUD 操作，包括用例的创建、执行、复制、批量删除等功能。用例通过 folder_path 进行组织，支持按文件夹、方法、关键词进行过滤。

## API 端点清单
| 方法 | 端点 | 功能 |
|------|------|------|
| GET | `/api/cases` | 获取用例列表（过滤、分页） |
| POST | `/api/cases` | 创建用例 |
| GET | `/api/cases/{case_id}` | 获取单个用例 |
| PUT | `/api/cases/{case_id}` | 更新用例 |
| DELETE | `/api/cases/{case_id}` | 删除用例 |
| POST | `/api/cases/{case_id}/duplicate` | 复制用例 |
| POST | `/api/cases/batch-delete` | 批量删除用例 |
| POST | `/api/cases/{case_id}/run` | 执行用例 |

---

## P0 测试用例（核心流程）

### P0.1 用例 CRUD 核心流程

| 用例ID | 功能描述 | 前置条件 | 测试步骤 | 预期结果 |
|--------|----------|----------|----------|----------|
| P0_TC001 | 创建用例-完整参数 | 已登录认证 | 1. POST `/api/cases` 传入完整参数：name="登录接口测试"、method="POST"、url="https://api.example.com/login"、headers={"Content-Type":"application/json"}、params={}、body={"username":"test"}、body_type="json"、auth_type="none"、auth_config={}、folder_path="/api/user"、sort_order=1、assertions=[{"type":"status_code","expected":200}]、timeout=30、follow_redirects=true、verify_ssl=true<br>2. 发送请求 | 返回 201，data 包含新建用例完整信息，id 已生成 |
| P0_TC002 | 获取用例列表-分页 | 数据库存在≥10条用例 | 1. GET `/api/cases?skip=0&limit=10`<br>2. 发送请求 | 返回用例列表，总数≥10，返回10条，结构包含 id/name/method/url 等字段 |
| P0_TC003 | 获取单个用例-存在 | 数据库存在 id=1 的用例 | 1. GET `/api/cases/1`<br>2. 发送请求 | 返回该用例完整信息，HTTP 200 |
| P0_TC004 | 更新用例-存在 | 数据库存在 id=1 的用例 | 1. PUT `/api/cases/1` 传入 {"name":"更新后的名称"}<br>2. 发送请求 | 返回更新后的用例信息，name 已变更 |
| P0_TC005 | 删除用例-存在 | 数据库存在 id=1 的用例 | 1. DELETE `/api/cases/1`<br>2. 发送请求 | 返回 {"code":0,"message":"deleted"}，用例已从数据库删除 |
| P0_TC006 | 执行用例-正常 | 存在用例和环境配置 | 1. POST `/api/cases/1/run` 传入 {"environment_id":1}<br>2. 发送请求 | 返回执行结果，包含 status、response 字段，ExecutionLog 已创建 |
| P0_TC007 | 批量删除用例-正常 | 数据库存在 id=[1,2,3] 的用例 | 1. POST `/api/cases/batch-delete` 传入 {"ids":[1,2,3]}<br>2. 发送请求 | 返回 {"code":0,"message":"deleted 3 cases"}，3个用例已删除 |

### P0.2 执行用例核心流程

| 用例ID | 功能描述 | 前置条件 | 测试步骤 | 预期结果 |
|--------|----------|----------|----------|----------|
| P0_TC008 | 执行用例-使用默认环境 | 存在用例和有 is_default=true 的环境 | 1. POST `/api/cases/1/run` 不传 environment_id<br>2. 发送请求 | 使用默认环境执行，env_id 为默认环境ID |
| P0_TC009 | 执行用例-记录保存验证 | 存在用例 | 1. 执行用例<br>2. 查询 ExecutionLog 表 | ExecutionLog 记录已创建，包含 case_id/execution_id/response_status 等字段 |

---

## P1 测试用例（重要功能）

### P1.1 用例列表查询

| 用例ID | 功能描述 | 前置条件 | 测试步骤 | 预期结果 |
|--------|----------|----------|----------|----------|
| P1_TC001 | 列表-按folder过滤 | 存在多个folder的用例 | 1. GET `/api/cases?folder=/api/user`<br>2. 发送请求 | 只返回 folder_path="/api/user" 的用例 |
| P1_TC002 | 列表-按method过滤 | 存在多种method的用例 | 1. GET `/api/cases?method=POST`<br>2. 发送请求 | 只返回 method="POST" 的用例 |
| P1_TC003 | 列表-关键词搜索 | 存在 name 包含"登录"的用例 | 1. GET `/api/cases?keyword=登录`<br>2. 发送请求 | 返回 name 或 url 包含"登录"的用例 |
| P1_TC004 | 列表-多条件组合过滤 | 存在符合条件的用例 | 1. GET `/api/cases?folder=/api/user&method=POST&keyword=登录`<br>2. 发送请求 | 同时满足 folder、method、keyword 条件的用例 |
| P1_TC005 | 列表-按name升序排序 | 存在多个用例 | 1. GET `/api/cases`<br>2. 检查返回顺序 | 按 folder_path 和 sort_order 排序 |

### P1.2 用例复制与更新

| 用例ID | 功能描述 | 前置条件 | 测试步骤 | 预期结果 |
|--------|----------|----------|----------|----------|
| P1_TC006 | 复制用例-正常 | 存在 id=1 的用例 | 1. POST `/api/cases/1/duplicate`<br>2. 发送请求 | 生成新用例，name="原名称 (copy)"，返回新用例信息 |
| P1_TC007 | 复制用例-folder保持一致 | 存在 folder_path="/api/user" 的用例 | 1. 复制该用例<br>2. 检查新用例 folder_path | 新用例 folder_path 与原用例相同 |
| P1_TC008 | 更新用例-headers | 存在用例 | 1. PUT `/api/cases/1` 传入 {"headers":{"Authorization":"Bearer xxx"}}<br>2. 发送请求 | headers 已更新，格式为 JSON 字符串 |
| P1_TC009 | 更新用例-断言规则 | 存在用例 | 1. PUT `/api/cases/1` 传入 {"assertions":[{"type":"status_code","expected":200}]}<br>2. 发送请求 | assertions 已更新 |
| P1_TC010 | 更新用例-认证信息 | 存在用例 | 1. PUT `/api/cases/1` 传入 {"auth_type":"bearer","auth_config":{"token":"xxx"}}<br>2. 发送请求 | auth_type 和 auth_config 已更新 |

### P1.3 执行用例功能

| 用例ID | 功能描述 | 前置条件 | 测试步骤 | 预期结果 |
|--------|----------|----------|----------|----------|
| P1_TC011 | 执行用例-GET方法 | 存在 GET 方法用例，指向可访问的URL | 1. POST `/api/cases/1/run` 传入 {"environment_id":1}<br>2. 发送请求 | 返回 200，response 包含 body/headers/status_code |
| P1_TC012 | 执行用例-POST方法带JSON | 存在 POST 方法用例 | 1. POST `/api/cases/1/run` 传入 {"environment_id":1}<br>2. 发送请求 | 请求携带正确 Content-Type 和 body，执行成功 |
| P1_TC013 | 执行用例-断言失败场景 | 用例断言设置为不可能满足的条件 | 1. 执行用例，断言 status_code=999<br>2. 检查返回 | status 包含 fail 或 passed with failures |
| P1_TC014 | 执行用例-无默认环境 | 存在用例，无默认环境配置 | 1. POST `/api/cases/1/run` 不传 environment_id<br>2. 发送请求 | 执行成功，env_vars 为空对象 |

### P1.4 异常与边界

| 用例ID | 功能描述 | 前置条件 | 测试步骤 | 预期结果 |
|--------|----------|----------|----------|----------|
| P1_TC015 | 获取单个用例-不存在 | 用例库为空或不存在 id=9999 | 1. GET `/api/cases/9999`<br>2. 发送请求 | 返回 404，detail="Case not found" |
| P1_TC016 | 更新用例-不存在 | 不存在 id=9999 的用例 | 1. PUT `/api/cases/9999`<br>2. 发送请求 | 返回 404，detail="Case not found" |
| P1_TC017 | 删除用例-不存在 | 不存在 id=9999 的用例 | 1. DELETE `/api/cases/9999`<br>2. 发送请求 | 返回 404，detail="Case not found" |
| P1_TC018 | 复制用例-不存在 | 不存在 id=9999 的用例 | 1. POST `/api/cases/9999/duplicate`<br>2. 发送请求 | 返回 404，detail="Case not found" |
| P1_TC019 | 执行用例-用例不存在 | 不存在 id=9999 的用例 | 1. POST `/api/cases/9999/run`<br>2. 发送请求 | 返回 404，detail="Case not found" |

---

## P2 测试用例（边界/异常）

### P2.1 分页边界

| 用例ID | 功能描述 | 前置条件 | 测试步骤 | 预期结果 |
|--------|----------|----------|----------|----------|
| P2_TC001 | limit=0边界 | 存在用例 | 1. GET `/api/cases?limit=0`<br>2. 发送请求 | 返回 422 或 400，detail 包含验证错误 |
| P2_TC002 | limit>500边界 | 存在用例 | 1. GET `/api/cases?limit=501`<br>2. 发送请求 | 返回 422 或 400，detail 包含"le=500"验证错误 |
| P2_TC003 | limit=500最大 | 存在用例 | 1. GET `/api/cases?limit=500`<br>2. 发送请求 | 返回成功，最多500条 |
| P2_TC004 | skip超出现有数据量 | 存在5条用例 | 1. GET `/api/cases?skip=1000`<br>2. 发送请求 | 返回空数组 [] |
| P2_TC005 | skip=0正常 | 存在用例 | 1. GET `/api/cases?skip=0`<br>2. 发送请求 | 返回从第一条开始的用例 |

### P2.2 字段验证

| 用例ID | 功能描述 | 前置条件 | 测试步骤 | 预期结果 |
|--------|----------|----------|----------|----------|
| P2_TC006 | method小写自动转大写 | 已登录 | 1. POST `/api/cases` 传入 method="get"<br>2. 发送请求 | method 自动转为 "GET" 存储 |
| P2_TC007 | headers空对象 | 已登录 | 1. POST `/api/cases` 传入 headers={}<br>2. 发送请求 | 创建成功，headers 存储为 "{}" |
| P2_TC008 | params空对象 | 已登录 | 1. POST `/api/cases` 传入 params={}<br>2. 发送请求 | 创建成功，params 存储为 "{}" |
| P2_TC009 | assertions空数组 | 已登录 | 1. POST `/api/cases` 传入 assertions=[]<br>2. 发送请求 | 创建成功，assertions 存储为 "[]" |
| P2_TC010 | body为空字符串 | 已登录 | 1. POST `/api/cases` 传入 body=""<br>2. 发送请求 | 创建成功，body 为空字符串 |
| P2_TC011 | timeout=0 | 已登录 | 1. POST `/api/cases` 传入 timeout=0<br>2. 发送请求 | 创建成功，使用默认值或0 |
| P2_TC012 | timeout负数 | 已登录 | 1. POST `/api/cases` 传入 timeout=-1<br>2. 发送请求 | 返回 422 或创建成功但timeout=-1 |
| P2_TC013 | sort_order递增 | 原用例 sort_order=5 | 1. 复制 sort_order=5 的用例<br>2. 检查新用例 sort_order | 新用例 sort_order=6 |

### P2.3 批量操作边界

| 用例ID | 功能描述 | 前置条件 | 测试步骤 | 预期结果 |
|--------|----------|----------|----------|----------|
| P2_TC014 | 批量删除-空列表 | 已登录 | 1. POST `/api/cases/batch-delete` 传入 {"ids":[]}<br>2. 发送请求 | 返回成功，message="deleted 0 cases" |
| P2_TC015 | 批量删除-部分不存在 | 存在 id=1,2 的用例 | 1. POST `/api/cases/batch-delete` 传入 {"ids":[1,2,9999]}<br>2. 发送请求 | 只删除存在的 id=1,2，返回成功 |
| P2_TC016 | 批量删除-全部不存在 | 不存在这些ID | 1. POST `/api/cases/batch-delete` 传入 {"ids":[9999,9998]}<br>2. 发送请求 | 返回成功，无用例被删除 |

### P2.4 执行用例边界

| 用例ID | 功能描述 | 前置条件 | 测试步骤 | 预期结果 |
|--------|----------|----------|----------|----------|
| P2_TC017 | 执行用例-变量覆盖 | 存在用例和环境 | 1. POST `/api/cases/1/run` 传入 {"environment_id":1,"variables":{"key":"override_value"}}<br>2. 发送请求 | 使用覆盖后的变量执行 |
| P2_TC018 | 执行用例-环境不存在 | 存在用例 | 1. POST `/api/cases/1/run` 传入 {"environment_id":9999}<br>2. 发送请求 | 使用空环境变量执行，不报错 |
| P2_TC019 | 执行用例-GET带params | 存在 GET 用例 | 1. 执行用例，params={"page":1}<br>2. 检查请求 | URL 自动拼接 query string |

### P2.5 认证与脚本

| 用例ID | 功能描述 | 前置条件 | 测试步骤 | 预期结果 |
|--------|----------|----------|----------|----------|
| P2_TC020 | 创建用例-带认证配置 | 已登录 | 1. POST `/api/cases` 传入 auth_type="bearer", auth_config={"token":"xxx"}<br>2. 发送请求 | 创建成功，auth_config 正确存储 |
| P2_TC021 | 创建用例-带前置脚本 | 已登录 | 1. POST `/api/cases` 传入 pre_script="console.log('before')"<br>2. 发送请求 | 创建成功，pre_script 正确存储 |
| P2_TC022 | 创建用例-带后置脚本 | 已登录 | 1. POST `/api/cases` 传入 post_script="console.log('after')"<br>2. 发送请求 | 创建成功，post_script 正确存储 |
| P2_TC023 | 创建用例-SSL验证关闭 | 已登录 | 1. POST `/api/cases` 传入 verify_ssl=false<br>2. 发送请求 | 创建成功，verify_ssl=false |
| P2_TC024 | 创建用例-跟随重定向 | 已登录 | 1. POST `/api/cases` 传入 follow_redirects=true<br>2. 发送请求 | 创建成功，follow_redirects=true |

---

## 测试数据要求

### 预置环境数据
| 环境名称 | variables |
|----------|-----------|
| 测试环境 | {"base_url":"https://httpbin.org","token":"test_token_123"} |
| 默认环境 | {"base_url":"https://httpbin.org"} |

### 预置用例数据
| 用例名称 | method | url | folder_path | 用途 |
|----------|--------|-----|------------|------|
| GET测试 | GET | /get | /api/test | 测试GET请求 |
| POST测试 | POST | /post | /api/test | 测试POST请求 |
| Headers测试 | GET | /headers | /api/test | 测试Headers |
| 登录接口 | POST | /api/login | /api/user | 测试认证 |

---

## 测试结果验收标准

### 通过标准
- P0 测试用例：100% 通过
- P1 测试用例：≥95% 通过
- P2 测试用例：≥90% 通过

### 测试覆盖维度
| 维度 | 覆盖说明 |
|------|----------|
| 正常场景 | P0_TC001-009，覆盖 CRUD 和执行核心流程 |
| 异常场景 | P1_TC015-019，P2_TC014-016，覆盖 404/空列表等 |
| 边界条件 | P2_TC001-013，覆盖分页边界、字段验证边界 |
| 关联功能 | 用例与环境变量的结合执行 |
