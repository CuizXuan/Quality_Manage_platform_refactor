# 第一周任务清单 - API 调试工具

> 项目：api-debug-tool
> 目标：完成 P0 阶段，交付可用的 API 调试核心功能
> 设计稿参考：桌面 `API抓包测试系统-设计方案.md`

---

## Day 1 · 项目初始化 + 基础框架

### 前端

- [ ] 创建 Vue3 项目（Vite）
  ```bash
  npm create vite@latest api-debug-tool -- --template vue
  cd api-debug-tool
  ```
- [ ] 安装依赖
  ```bash
  npm install element-plus pinia axios monaco-editor
  npm install @vueuse/core -D
  ```
- [ ] 安装 pnpm（如未安装）
  ```bash
  npm install -g pnpm --registry https://registry.npmmirror.com
  ```
- [ ] 配置路由（Vue Router）
  - `/` → Dashboard 主调试界面
  - `/settings` → 系统设置
  - `/shortcuts` → 快捷键帮助
- [ ] 搭建整体布局骨架
  - `AppHeader.vue` — 顶部栏（Logo + 环境切换 + 用户）
  - `Sidebar.vue` — 左侧边栏（集合树 / 历史记录切换）
  - 主内容区（请求解析 + 请求配置 + 响应展示）
  - `StatusBar.vue` — 底部状态栏
- [ ] 定义全局 CSS 变量（深色科技主题）
  - 背景色：#0A0E17 / #111827 / #1F2937
  - 科技蓝：#3B82F6 / 霓虹紫：#8B5CF6
  - 成功绿：#10B981 / 警告橙：#F59E0B / 危险红：#EF4444

### 后端

- [ ] 创建 FastAPI 项目结构
  ```
  backend/
  ├── app/
  │   ├── main.py
  │   ├── routers/
  │   │   └── proxy.py
  │   └── services/
  │       └── http_client.py
  └── requirements.txt
  ```
- [ ] 安装后端依赖
  ```bash
  pip install fastapi uvicorn httpx pydantic python-multipart
  ```
- [ ] 配置 CORS（允许前端 localhost 调用）
- [ ] 实现 `/proxy` 代理转发接口
  - 接收：method, url, headers, body, params
  - 转发请求到目标地址
  - 返回：status_code, headers, content, duration

---

## Day 2 · 请求配置区

### 前端组件

- [ ] `RequestBar.vue` — 请求行
  - Method 下拉（GET/POST/PUT/DELETE/PATCH，颜色区分）
  - URL 输入框
  - 发送按钮（Ctrl+Enter 快捷键）
- [ ] `HeadersTable.vue` — Headers 编辑表格
  - 键值对表格，增删改操作
  - 常用 Header 模板快捷插入（Content-Type / Authorization 等）
  - 敏感信息脱敏提示（Authorization / Cookie 字段）
- [ ] `ParamsTable.vue` — Query 参数表格
  - 键值对表格
  - URL 自动同步
- [ ] `BodyEditor.vue` — Body 编辑器
  - Tab 切换：none / form-data / x-www-form-urlencoded / JSON / raw
  - JSON 模式：Monaco Editor，语法高亮
  - 快捷按钮：格式化 / 压缩 / 复制

---

## Day 3 · 响应展示 + 前后端联调

### 前端组件

- [ ] `ResponsePanel.vue` — 响应展示面板
  - 顶部概览栏：状态码（颜色区分）/ 响应时间 / 响应大小
  - 复制 / 下载按钮
  - 响应体展示（JSON 高亮、格式化、折叠）
  - 响应 Headers 折叠面板
- [ ] 前后端联调
  - 前端发送请求 → 后端 `/proxy` 转发 → 返回响应 → 前端展示
  - 错误处理（网络错误 / 超时 / 4xx / 5xx 展示）
- [ ] 暗色主题细节优化
  - 毛玻璃效果（backdrop-filter）
  - 边框发光效果
  - 按钮悬停动效

---

## Day 4 · 请求解析器

### 前端

- [ ] `RequestParser.vue` — 请求解析器组件
  - 文本输入框（支持粘贴）
  - 格式检测图标（自动识别 cURL / Fetch）
  - 解析按钮（智能解析）
  - 解析失败时显示红色错误提示
  - 清空按钮
- [ ] 实现 cURL 解析逻辑
  - 正则提取 Method、URL、Headers、Body
  - 自动识别 Query 参数
  - 自动提取 Bearer Token
- [ ] 实现 Fetch 代码解析逻辑
  - 解析 fetch(url, options) 格式
  - 提取 method、headers、body
- [ ] 解析成功后自动填充右侧请求配置表单

---

## Day 5 · 历史记录 + 本地存储

### 前端

- [ ] `historyStore.js`（Pinia）
  - 请求记录数据结构：时间、URL、Method、完整请求信息、响应状态、耗时
  - 保存到 LocalStorage
  - 读取 / 删除 / 批量删除
  - 自动清理策略（保留 30 天 / 最多 500 条）
- [ ] `HistoryList.vue` — 历史记录组件
  - 时间格式化展示（刚刚 / 2分钟前 / 1小时前）
  - 按时间 / Method / 状态筛选
  - 关键词搜索（URL）
  - 固定重要记录
  - 点击加载历史请求到调试区
  - 右键菜单：重新加载 / 删除 / 固定

---

## Day 6 · 集合管理

### 前端

- [ ] `collectionStore.js`（Pinia）
  - 集合树形结构：Collection { id, name, children[], requests[] }
  - 接口数据结构：id, collection_id, name, method, url, headers, params, body, remark
  - 保存到 LocalStorage
- [ ] `CollectionTree.vue` — 集合树组件
  - 搜索框过滤
  - 新建集合按钮
  - 树形展示（支持展开/折叠）
  - 接口名前显示方法颜色圆点
  - 悬停显示操作菜单（...）：重命名 / 删除
  - 拖拽排序
- [ ] `SaveDialog.vue` — 保存接口弹窗
  - 选择目标集合或新建集合
  - 输入接口名称
  - 添加备注
  - 标签（GET / POST / 重要 / 废弃）
- [ ] 从集合加载接口到调试区

---

## Day 7 · 压力测试（简单版）

### 前端

- [ ] `StressTestPanel.vue` — 压力测试面板（可折叠）
  - 调用次数输入（默认 1 次）
  - 并发数输入（默认 1）
  - 延迟间隔输入（ms，默认 0）
  - 停止条件：失败次数阈值 / 手动停止
  - 开始 / 停止按钮
- [ ] 测试结果展示
  - 实时进度条
  - 成功 / 失败计数器
  - 平均响应时间、最快耗时、最慢耗时
  - 失败请求错误汇总列表
- [ ] 简单图表展示
  - 响应时间趋势（用文字/数字展示即可，图表 V2）

### 后端

- [ ] 扩展 `/proxy` 接口支持批量转发
  - 接收请求数组
  - 使用 httpx 异步并发执行
  - 返回每个请求的响应结果

---

## 第一周验收检查清单

### P0 功能验收

| # | 检查点 | 要求 |
|---|--------|------|
| 1 | 手动 GET 请求 | 能发送并看到正确响应 |
| 2 | 手动 POST JSON 请求 | 能发送并看到正确响应 |
| 3 | Headers 表格 | 增删改正常 |
| 4 | Query 参数表格 | URL 自动同步 |
| 5 | Body 编辑器 | JSON 格式化/压缩/复制 |
| 6 | 响应展示 | 状态码/耗时/大小正确，JSON 高亮 |
| 7 | 粘贴 cURL 解析 | 正确解析并填充表单 |
| 8 | 粘贴 Fetch 解析 | 正确解析并填充表单 |
| 9 | 历史记录 | 保存/加载/筛选正常 |
| 10 | 集合管理 | 创建/保存/加载/删除正常 |
| 11 | 压力测试 | 循环 N 次执行，结果统计正确 |
| 12 | 页面样式 | 无明显错乱，深色主题一致 |

### 技术验收

- [ ] 后端 `/proxy` 接口正常转发请求
- [ ] 前端请求通过代理调用，无跨域问题
- [ ] LocalStorage 数据持久化正常
- [ ] 快捷键 Ctrl+Enter 发送请求生效
- [ ] 错误情况有友好提示（非 200 状态码 / 网络错误 / 超时）
- [ ] 敏感字段（Authorization）有脱敏提示

---

## 技术栈汇总

| 层级 | 技术 |
|------|------|
| 前端框架 | Vue 3 + Vite |
| UI 组件库 | Element Plus |
| 状态管理 | Pinia |
| HTTP 客户端 | Axios |
| 代码编辑器 | Monaco Editor |
| 后端框架 | FastAPI |
| HTTP 转发 | httpx |
| 存储 | LocalStorage（本期）/ SQLite 后期 |

---

## 目录结构（目标）

```
api-debug-tool/
├── frontend/
│   ├── src/
│   │   ├── assets/styles/
│   │   │   ├── variables.css    # 全局 CSS 变量
│   │   │   └── global.css       # 全局样式
│   │   ├── components/
│   │   │   ├── common/          # AppHeader / Sidebar / StatusBar / Toast
│   │   │   ├── request/         # RequestBar / HeadersTable / ParamsTable / BodyEditor / RequestParser
│   │   │   ├── response/         # ResponsePanel
│   │   │   ├── collection/       # CollectionTree / SaveDialog
│   │   │   └── stress/           # StressTestPanel
│   │   ├── views/               # Dashboard / Settings / Shortcuts
│   │   ├── stores/              # request / collection / history / environment
│   │   ├── api/                 # axios client / proxy api
│   │   └── utils/               # parser / storage / formatter
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/proxy.py
│   │   └── services/http_client.py
│   └── requirements.txt
│
├── docs/
│   └── API抓包测试系统-设计方案.md
│
└── README.md
```
