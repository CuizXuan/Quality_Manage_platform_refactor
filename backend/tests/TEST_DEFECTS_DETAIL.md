# 缺陷管理模块详细测试用例

## 1. 模块概述

### 1.1 功能描述
缺陷管理模块负责缺陷的创建、跟踪、状态流转，支持从执行记录一键创建缺陷，包含评论和附件功能。

### 1.2 缺陷状态机
```
open → in_progress → resolved → closed
         ↑_______________↓
              (reopen)
```

| 状态 | 说明 |
|------|------|
| open | 新建/重新打开 |
| in_progress | 处理中 |
| resolved | 已修复 |
| closed | 已关闭 |

### 1.3 枚举值说明

| 字段 | 可选值 |
|------|--------|
| severity（严重程度） | critical, high, medium, low |
| priority（优先级） | critical, high, medium, low |
| status（状态） | open, in_progress, resolved, closed |
| defect_type（缺陷类型） | functional, performance, security, ui, other |

---

## 2. API 端点总览

| 方法 | 端点 | 功能 |
|------|------|------|
| GET | `/api/defects` | 获取缺陷列表（支持多条件过滤） |
| POST | `/api/defects` | 创建缺陷 |
| GET | `/api/defects/{defect_id}` | 获取缺陷详情（含评论、附件） |
| PUT | `/api/defects/{defect_id}` | 更新缺陷 |
| DELETE | `/api/defects/{defect_id}` | 删除缺陷（级联删除评论和附件） |
| POST | `/api/defects/{defect_id}/comments` | 添加评论 |
| POST | `/api/defects/{defect_id}/attachments` | 上传附件 |
| POST | `/api/defects/from-execution` | 从执行记录创建缺陷 |
| GET | `/api/defects/stats/summary` | 缺陷统计看板 |

---

## 3. P0 核心流程测试用例

### 3.1 缺陷 CRUD 核心流程

| 用例ID | 功能描述 | 前置条件 | 测试步骤 | 预期结果 |
|--------|----------|----------|----------|----------|
| P0_D001 | 创建缺陷-完整参数 | 已登录系统 | 1. POST /api/defects<br>2. 请求体包含：title="登录页面无法加载"、description="Chrome浏览器下登录失败"、severity="high"、priority="high"、reporter="tester01"、defect_type="functional"、environment="Chrome最新版本"、steps_to_reproduce="1.打开首页 2.点击登录"、expected_result="显示登录框"、actual_result="页面白屏" | 返回201，data包含缺陷ID，状态为open |
| P0_D002 | 创建缺陷-必填字段最小化 | 已登录系统 | 1. POST /api/defects<br>2. 仅传title="接口超时"、reporter="tester01" | 返回201，缺陷创建成功，status默认open，severity/priority默认medium |
| P0_D003 | 获取缺陷详情-包含关联数据 | 数据库存在缺陷ID=1，有2条评论和1个附件 | 1. GET /api/defects/1 | 返回defect对象、comments数组（按时间升序）、attachments数组 |
| P0_D004 | 更新缺陷-状态变更为resolved | 数据库存在open状态缺陷ID=2 | 1. PUT /api/defects/2<br>2. body: {"status": "resolved", "resolution": "已修复代码"} | 返回200，status=resolved，resolved_at被自动设置为当前时间 |
| P0_D005 | 删除缺陷-级联删除 | 数据库存在缺陷ID=3，有评论和附件 | 1. DELETE /api/defects/3 | 返回200，缺陷已删除，关联的DefectComment和DefectAttachment记录一并删除 |
| P0_D006 | 缺陷完整生命周期流转 | 存在open状态缺陷ID=10 | 1. PUT /api/defects/10 status=in_progress<br>2. PUT /api/defects/10 status=resolved<br>3. PUT /api/defects/10 status=closed | 每次更新返回200，状态依次变为in_progress→resolved→closed |

---

## 4. P1 重要功能测试用例

### 4.1 列表查询与过滤

| 用例ID | 功能描述 | 前置条件 | 测试步骤 | 预期结果 |
|--------|----------|----------|----------|----------|
| P1_D001 | 列表查询-按状态过滤 | 存在多个不同状态缺陷 | GET /api/defects?status=open | 仅返回status=open的缺陷列表 |
| P1_D002 | 列表查询-按严重程度过滤 | 存在多个不同severity缺陷 | GET /api/defects?severity=high | 仅返回severity=high的缺陷 |
| P1_D003 | 列表查询-按指派人过滤 | 存在指派给不同人的缺陷 | GET /api/defects?assignee=zhangsan | 仅返回assignee=zhangsan的缺陷 |
| P1_D004 | 列表查询-关键词搜索 | 存在标题/描述含"登录"的缺陷 | GET /api/defects?keyword=登录 | 返回title或description包含"登录"的缺陷 |
| P1_D005 | 列表查询-多条件组合 | 存在多种组合数据 | GET /api/defects?status=open&severity=high&assignee=wangwu | 仅返回同时满足三个条件的缺陷 |
| P1_D006 | 列表查询-返回结果排序 | 存在多个缺陷 | GET /api/defects | 返回结果按updated_at降序排列 |

### 4.2 评论功能

| 用例ID | 功能描述 | 前置条件 | 测试步骤 | 预期结果 |
|--------|----------|----------|----------|----------|
| P1_D007 | 添加评论-正常 | 存在缺陷ID=5 | POST /api/defects/5/comments<br>body: {"content": "请尽快处理", "author": "leader01"} | 返回201，评论创建成功 |
| P1_D008 | 添加评论-缺陷不存在 | 无 | POST /api/defects/99999/comments<br>body: {"content": "测试", "author": "tester"} | 返回404，"缺陷不存在" |
| P1_D009 | 获取评论-时间顺序 | 缺陷5有3条评论 | GET /api/defects/5 | 返回的comments数组按created_at升序排列 |

### 4.3 附件功能

| 用例ID | 功能描述 | 前置条件 | 测试步骤 | 预期结果 |
|--------|----------|----------|----------|----------|
| P1_D010 | 上传附件-正常 | 存在缺陷ID=6 | POST /api/defects/6/attachments<br>multipart/form-data: file=截图.png | 返回201，附件记录创建成功，文件保存到data/defect_attachments/ |
| P1_D011 | 上传附件-缺陷不存在 | 无 | POST /api/defects/99999/attachments<br>file=test.png | 返回404，"缺陷不存在" |
| P1_D012 | 获取附件列表 | 缺陷6有1个附件 | GET /api/defects/6 | 返回的attachments数组包含文件信息（file_name, file_path, file_size, file_type） |

### 4.4 从执行记录创建

| 用例ID | 功能描述 | 前置条件 | 测试步骤 | 预期结果 |
|--------|----------|----------|----------|----------|
| P1_D013 | 从执行记录创建-正常 | 存在ExecutionLog ID=100（关联case_id=10） | POST /api/defects/from-execution<br>body: {"execution_log_id": 100, "title": "API超时", "reporter": "system"} | 返回201，缺陷创建成功，自动填充case_id=10 |
| P1_D014 | 从执行记录创建-执行记录不存在 | 无 | POST /api/defects/from-execution<br>body: {"execution_log_id": 99999} | 返回201，使用默认标题"[API] 接口执行异常"创建缺陷 |

### 4.5 统计看板

| 用例ID | 功能描述 | 前置条件 | 测试步骤 | 预期结果 |
|--------|----------|----------|----------|----------|
| P1_D015 | 统计看板-正常 | 存在多个缺陷，状态分布为open:3, resolved:2, closed:1 | GET /api/defects/stats/summary | 返回{total:6, by_status:{open:3, resolved:2, closed:1}, by_severity:{...}} |
| P1_D016 | 统计看板-空数据 | 无缺陷数据 | GET /api/defects/stats/summary | 返回{total:0, by_status:{}, by_severity:{}} |

### 4.6 状态更新与字段修改

| 用例ID | 功能描述 | 前置条件 | 测试步骤 | 预期结果 |
|--------|----------|----------|----------|----------|
| P1_D017 | 更新缺陷-修改严重程度 | 存在缺陷ID=7 | PUT /api/defects/7<br>body: {"severity": "critical"} | 返回200，severity更新为critical |
| P1_D018 | 更新缺陷-修改优先级 | 存在缺陷ID=7 | PUT /api/defects/7<br>body: {"priority": "high"} | 返回200，priority更新为high |
| P1_D019 | 更新缺陷-修改指派人 | 存在缺陷ID=7 | PUT /api/defects/7<br>body: {"assignee": "lisi"} | 返回200，assignee更新为lisi |
| P1_D020 | 更新缺陷-关联外部系统 | 存在缺陷ID=7 | PUT /api/defects/7<br>body: {"external_id": "JIRA-123", "external_url": "https://jira.example.com/browse/JIRA-123"} | 返回200，external_id和external_url更新成功 |
| P1_D021 | 更新缺陷-缺陷不存在 | 无 | PUT /api/defects/99999<br>body: {"title": "test"} | 返回404，"缺陷不存在" |
| P1_D022 | 删除缺陷-缺陷不存在 | 无 | DELETE /api/defects/99999 | 返回404，"缺陷不存在" |

---

## 5. P2 边界/异常测试用例

### 5.1 字段边界值测试

| 用例ID | 功能描述 | 前置条件 | 测试步骤 | 预期结果 |
|--------|----------|----------|----------|----------|
| P2_D001 | 标题-最大长度边界 | 已登录 | 创建缺陷，title长度=200字符 | 返回201，标题保存完整 |
| P2_D002 | 标题-超长截断/拒绝 | 已登录 | 创建缺陷，title长度=201字符 | 返回422或200（截断处理），具体依赖业务规则 |
| P2_D003 | 描述-超长内容 | 已登录 | 创建缺陷，description长度=5000字符 | 返回201，描述保存完整 |
| P2_D004 | 描述-超长拒绝 | 已登录 | 创建缺陷，description长度=5001字符 | 返回422参数校验失败 |
| P2_D005 | 评论内容-最大长度 | 存在缺陷 | 添加评论content长度=2000字符 | 返回201，评论保存完整 |

### 5.2 枚举值异常测试

| 用例ID | 功能描述 | 前置条件 | 测试步骤 | 预期结果 |
|--------|----------|----------|----------|----------|
| P2_D006 | severity-非法枚举值 | 已登录 | 创建缺陷severity="invalid_value" | 返回422参数校验失败 |
| P2_D007 | priority-非法枚举值 | 已登录 | 创建缺陷priority="invalid_value" | 返回422参数校验失败 |
| P2_D008 | status-非法枚举值 | 已登录 | 创建缺陷status="invalid_value" | 返回422参数校验失败 |
| P2_D009 | defect_type-非法枚举值 | 已登录 | 创建缺陷defect_type="invalid_value" | 返回422参数校验失败 |

### 5.3 状态机边界测试

| 用例ID | 功能描述 | 前置条件 | 测试步骤 | 预期结果 |
|--------|----------|----------|----------|----------|
| P2_D010 | 状态-从resolved重新打开 | 存在resolved状态缺陷ID=20 | PUT /api/defects/20<br>body: {"status": "open"} | 返回200，status=open，resolved_at字段保留原值（代码未做清空处理） |
| P2_D011 | 状态-从closed重新打开 | 存在closed状态缺陷ID=21 | PUT /api/defects/21<br>body: {"status": "open"} | 返回200，status=open（允许流转，具体看业务规则是否允许） |
| P2_D012 | resolved_at自动时间戳 | 存在in_progress状态缺陷ID=22 | PUT /api/defects/22<br>body: {"status": "resolved"} | 返回200，缺陷的resolved_at被自动设置为当前时间 |

### 5.4 关联关系边界测试

| 用例ID | 功能描述 | 前置条件 | 测试步骤 | 预期结果 |
|--------|----------|----------|----------|----------|
| P2_D013 | 关联-无效execution_log_id | 已登录 | POST /api/defects/from-execution<br>body: {"execution_log_id": 99999} | 返回201，缺陷创建成功，case_id为null |
| P2_D014 | 关联-无效case_id | 已登录 | 创建缺陷case_id=99999 | 返回201，case_id存入数据库（外键约束依赖数据库设计） |
| P2_D015 | 关联-无效scenario_id | 已登录 | 创建缺陷scenario_id=99999 | 返回201，scenario_id存入数据库 |
| P2_D016 | 评论-缺陷ID不存在 | 无 | POST /api/defects/99999/comments<br>body: {"content": "test", "author": "user"} | 返回404 |
| P2_D017 | 附件-缺陷ID不存在 | 无 | POST /api/defects/99999/attachments<br>file=test.png | 返回404 |

### 5.5 附件边界测试

| 用例ID | 功能描述 | 前置条件 | 测试步骤 | 预期结果 |
|--------|----------|----------|----------|----------|
| P2_D018 | 附件-文件名特殊字符 | 存在缺陷ID=8 | 上传文件名包含空格和中文：`"错误 截图.png"` | 返回201，文件成功保存，file_name字段保存原始文件名 |
| P2_D019 | 附件-空文件上传 | 存在缺陷ID=8 | 上传空文件（0字节） | 返回201，附件记录创建成功，file_size=0 |
| P2_D020 | 附件-大文件上传 | 存在缺陷ID=8 | 上传超过50MB的文件 | 返回201或413（取决于服务器配置） |
| P2_D021 | 附件-多种文件类型 | 存在缺陷ID=8 | 分别上传.png、.jpg、.pdf、.zip文件 | 返回201，各种文件类型均能上传成功 |

### 5.6 查询边界测试

| 用例ID | 功能描述 | 前置条件 | 测试步骤 | 预期结果 |
|--------|----------|----------|----------|----------|
| P2_D022 | 查询-空关键词 | 存在缺陷数据 | GET /api/defects?keyword= | 返回所有缺陷（空关键词不过滤） |
| P2_D023 | 查询-不存在的值 | 存在缺陷数据 | GET /api/defects?status=nonexistent_status | 返回空列表 |
| P2_D024 | 查询-特殊字符关键词 | 存在缺陷数据 | GET /api/defects?keyword=' OR '1'='1 | 返回空列表或执行SQL注入防护（返回400/422） |
| P2_D025 | 列表-无数据空返回 | 数据库无缺陷 | GET /api/defects | 返回{"code":0,"data":[]} |

### 5.7 更新边界测试

| 用例ID | 功能描述 | 前置条件 | 测试步骤 | 预期结果 |
|--------|----------|----------|----------|----------|
| P2_D026 | 更新-空更新请求 | 存在缺陷ID=9 | PUT /api/defects/9<br>body: {} | 返回200，所有字段不变 |
| P2_D027 | 更新-只更新部分字段 | 存在缺陷ID=9 | PUT /api/defects/9<br>body: {"title": "新标题"} | 返回200，仅title更新，其他字段不变 |
| P2_D028 | 更新-设置null值 | 存在缺陷ID=9，assignee="zhangsan" | PUT /api/defects/9<br>body: {"assignee": null} | 返回200，assignee被设置为null |

---

## 6. 测试数据要求

### 6.1 预置缺陷数据

| ID | title | status | severity | priority | assignee | reporter |
|----|-------|--------|----------|----------|----------|----------|
| 1 | 登录页面白屏 | open | high | high | zhangsan | tester01 |
| 2 | 按钮点击无响应 | in_progress | medium | medium | lisi | tester02 |
| 3 | 数据加载慢 | resolved | medium | low | wangwu | tester03 |
| 4 | 样式错位 | closed | low | low | zhangsan | tester01 |
| 5 | 接口超时 | open | high | high | lisi | tester02 |

### 6.2 预置评论数据

| 缺陷ID | 评论内容 | 作者 |
|--------|----------|------|
| 1 | 请尽快确认问题 | leader01 |
| 1 | 已复现，Chrome和Firefox都有 | tester01 |
| 2 | 正在排查中 | lisi |

### 6.3 预置附件数据

| 缺陷ID | 文件名 | 说明 |
|--------|--------|------|
| 1 | screenshot.png | 问题截图 |
| 2 | log.txt | 错误日志 |

---

## 7. 缺陷状态机详细测试矩阵

| 当前状态 | 操作 | 目标状态 | 预期结果 | 用例ID |
|----------|------|----------|----------|--------|
| open | update status=in_progress | in_progress | 成功 | P0_D006 |
| open | update status=resolved | resolved | 成功，resolved_at被设置 | P2_D012 |
| open | update status=closed | closed | 成功 | - |
| in_progress | update status=open | open | 成功 | - |
| in_progress | update status=resolved | resolved | 成功，resolved_at被设置 | P0_D006 |
| in_progress | update status=closed | closed | 成功 | - |
| resolved | update status=open | open | 成功（重新打开），resolved_at保留 | P2_D010 |
| resolved | update status=in_progress | in_progress | 成功 | - |
| resolved | update status=closed | closed | 成功 | P0_D006 |
| closed | update status=open | open | 成功（重新打开） | P2_D011 |
| closed | update status=resolved | resolved | 成功 | - |
| closed | update status=in_progress | in_progress | 成功 | - |

---

## 8. 验收检查清单

### P0 核心流程（必须通过）
- [ ] 缺陷创建成功（最小参数和完整参数）
- [ ] 缺陷详情查询返回完整数据
- [ ] 状态变更为resolved时resolved_at自动设置
- [ ] 删除缺陷时评论和附件一并删除
- [ ] 完整生命周期：open → in_progress → resolved → closed

### P1 重要功能（必须通过）
- [ ] 列表查询各过滤条件生效
- [ ] 评论添加和展示正确
- [ ] 附件上传和展示正确
- [ ] 从执行记录创建缺陷
- [ ] 统计看板数据准确

### P2 边界异常（建议覆盖）
- [ ] 字段长度边界
- [ ] 非法枚举值拒绝
- [ ] 状态机异常流转
- [ ] 关联不存在资源
- [ ] SQL注入防护
