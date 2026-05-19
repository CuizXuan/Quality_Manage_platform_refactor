Dashboard 与终端调试台重设计规格
========================

1. 设计定位

-------

**工作台 Dashboard** 是质量平台的控制台首页，目标是让测试经理、QA、开发快速判断当前项目质量状态，并进入关键工作流。它不应承载完整调试能力，而应提供质量概览、快捷入口、自定义 Widget 和终端调试的轻量入口。

**终端调试台 Terminal Debug** 是接口测试资产生产入口，目标是从手工请求、fetch/curl 粘贴、历史请求复用出发，完成调试、响应分析、健壮性评分、AI 断言生成，并沉淀为测试用例或场景步骤。

2. 当前实现问题

---------

Dashboard.vue 目前把统计条、请求编辑、响应展示、历史列表都塞进一个页面，接近“简化版 Terminal”，缺少真正 Dashboard 应有的质量状态、门禁、缺陷、趋势、快捷入口和自定义 Widget。

requestParser.js 当前解析过度依赖正则，存在明显缺陷：fetch headers 只匹配 headers: {...},，遇到最后一个字段、new Headers()、未加引号 key、转义字符串、多行 body 时容易失败；curl 只支持少量 -H、-d 写法，不能稳定处理 --header、--data-raw、续行、cookie、query 拆分和 shell 转义。

3. Dashboard 总体布局

-----------------

采用专业控制台风格：信息密度高、层级清晰、少装饰、固定操作区、可扫描。

页面结构建议：

DashboardPage
├── DashboardHeader
│   ├── 项目 / 环境 / 时间范围选择
│   ├── 质量门禁状态
│   └── 全局快捷操作
├── QualityStatusStrip
│   ├── 当前通过率
│   ├── 失败数
│   ├── 高危缺陷
│   ├── 平均耗时
│   ├── 健壮性均分
│   └── 最近调试成功率
├── WidgetGrid
│   ├── QualityTrendWidget
│   ├── QualityGateWidget
│   ├── TerminalQuickDebugWidget
│   ├── RecentDebugWidget
│   ├── FrequentFailureApiWidget
│   ├── FavoriteRequestsWidget
│   ├── DefectDistributionWidget
│   └── AiSuggestionWidget
└── WidgetConfigDrawer

首屏建议使用 12 栅格布局：

* 顶部：项目、环境、时间范围、刷新、Widget 配置。

* 第一行：质量状态概览 KPI，固定高度 72-88px。

* 第二行左侧 8 栅格：通过率 / 失败率趋势；右侧 4 栅格：质量门禁状态。

* 第三行左侧 6 栅格：终端快捷调试 Widget；右侧 6 栅格：最近调试 / 收藏请求。

* 第四行：高频失败接口、缺陷分布、AI 建议。
4. Dashboard Widget 设计

----------------------

核心 Widget：

1. **质量状态概览**
   
   * 展示通过率、失败率、阻断缺陷、高危接口、平均耗时、健壮性评分。
   * 每个指标带趋势标识，例如较昨日上升/下降。
   * 状态颜色固定：成功绿色、警告橙色、阻断红色、中性灰蓝。

2. **快捷入口**
   
   * 新建调试、导入 curl/fetch、创建用例、执行场景、查看报告、缺陷中心。
   * 快捷入口使用图标按钮或紧凑按钮组，不做营销式大卡片。

3. **终端快捷调试 Widget**
   
   * 只保留 Method、URL、粘贴解析、发送按钮。
   * 发送后展示状态码、耗时、响应摘要。
   * 提供“打开完整调试台”跳转。
   * 不在 Dashboard 内展示完整 Params/Header/Body 编辑器，避免首页失焦。

4. **最近调试记录**
   
   * 展示 method、URL、状态码、耗时、创建时间、收藏状态。
   * 点击进入 Terminal 并加载该请求。
   * 支持按失败、收藏、当前环境过滤。

5. **收藏请求**
   
   * 面向高频接口复测。
   * 每条支持快速发送、复制 curl、进入详情。

6. **高频失败接口**
   
   * 聚合最近 N 天失败次数、最新状态码、平均耗时。
   * 点击查看历史对比。

7. **AI 建议摘要**
   
   * 展示健壮性低分接口、推荐断言、潜在字段缺失风险。
   * 明确标识“待确认”，不要自动修改用例。

8. **自定义 Widget**
   
   * 支持显示/隐藏、拖拽排序、宽度配置、刷新间隔。
   * 配置可先存 localStorage，后续迁移到用户偏好接口。
   * Widget 组件必须通过统一数据契约接入，避免 Dashboard 继续膨胀。

9. 终端调试台布局

----------

完整 Terminal 页面建议采用三栏控制台布局：

TerminalDebugPage
├── TerminalToolbar
│   ├── 环境选择
│   ├── 粘贴导入
│   ├── 保存为用例
│   ├── 加入收藏
│   └── 历史对比
├── MainSplitLayout
│   ├── HistorySidebar
│   │   ├── 搜索
│   │   ├── 状态过滤
│   │   ├── 收藏过滤
│   │   └── 历史列表
│   ├── RequestPanel
│   │   ├── RequestLine
│   │   ├── ParseNotice
│   │   ├── RequestTabs
│   │   │   ├── ParamsEditor
│   │   │   ├── HeadersEditor
│   │   │   ├── CookiesEditor
│   │   │   ├── AuthEditor
│   │   │   └── BodyEditor
│   │   └── SendBar
│   └── ResponsePanel
│       ├── ResponseSummary
│       ├── ResponseActions
│       ├── ResponseTabs
│       │   ├── BodyViewer
│       │   ├── HeadersViewer
│       │   ├── TimingViewer
│       │   ├── RobustnessViewer
│       │   └── CompareViewer
│       └── AiAssertionsPanel

桌面端三栏比例建议：历史 280px，请求区 45%，响应区 55%。小屏时折叠历史栏，请求与响应上下排列。

6. 请求数据结构

---------

前端内部统一使用接近文档的结构：

`DebugRequest { id, method, url, query_params, headers, cookies, auth_config, body_type, // json | form | multipart | raw | none body, environment_id, source_type, // manual | curl | fetch | url | har }`

响应结果：

`DebugResult { id, debug_request_id, status_code, response_headers, response_body, duration_ms, error_message, created_at, robustness_score, ai_assertions }`

接口按文档目标应对齐：

* POST /debug/send
* GET /debug/history
* POST /debug/save-to-testcase

当前项目已有 /api/terminal/debug、/api/terminal/history，前端应在 terminalApi 做适配层，避免页面组件直接依赖旧路径。

7. fetch/curl 解析规则

------------------

解析器应改为“词法拆分 + 结构解析”，不要只靠单个正则。

### curl 解析

处理流程：

1. 去除首尾空白，合并反斜杠续行：\ + 换行转换为空格。
2. 使用 shell-like tokenizer 拆分参数，保留引号内容和转义字符。
3. 识别 URL：
   * 优先取第一个非 option 参数。
   * 支持单引号、双引号、无引号。
   * URL 中 query 拆入 query_params，基础 URL 保留 path。
4. 识别 method：
   * -X、--request 优先。
   * 若存在 --data* 且未指定 method，则默认 POST。
5. 识别 headers：
   * 支持 -H、--header。
   * 按第一个 : 拆分 key/value。
   * value 保留冒号后的全部内容，避免 token、时间等值被截断。
   * header key 大小写保留，查找时大小写不敏感。
6. 识别 body：
   * 支持 -d、--data、--data-raw、--data-binary、--data-urlencode。
   * 多个 -d 合并为 &，按 form 处理。
   * JSON 可 parse 时设为 body_type=json。
   * a=1&b=2 设为 form。
   * 其他设为 raw。
7. 识别 cookies：
   * 支持 -b、--cookie。
   * Cookie: header 也应拆入 cookies，同时保留 header 是否由产品决定。
8. 识别 auth：
   * -u user:pass、--user user:pass 转为 basic auth。
   * Authorization: Bearer xxx 转为 bearer auth，同时保留 header 展示。

### fetch 解析

处理流程：

1. 使用 JavaScript 解析器优先，如 acorn；若不新增依赖，可实现有限状态扫描。
2. 识别：
   * fetch(url)
   * fetch(url, options)
   * window.fetch(...)
   * await fetch(...)
3. URL：
   * 字符串字面量直接取值。
   * 模板字符串若无变量则取值；有变量时保留原文本并标记“含变量”。
4. method：
   * 从 options.method 取值。
   * 未指定默认 GET。
5. headers：
   * 支持普通对象：headers: { "Content-Type": "application/json" }
   * 支持未加引号 key：headers: { Authorization: "Bearer xxx" }
   * 支持 new Headers({...})
   * 支持数组：new Headers([["a", "b"]])
   * 支持后续 headers.append("k", "v")
6. body：
   * 字符串字面量直接取值。
   * JSON.stringify({...}) 应解析对象并格式化为 JSON。
   * new URLSearchParams({...}) 设为 form。
   * FormData 标记为 multipart，无法静态解析的字段进入 warnings。
7. credentials：
   * credentials: "include" 应提示“浏览器 Cookie 依赖运行态，未自动带入”。
8. 解析结果包含 warnings，用于 UI 提示未能静态还原的变量、函数或 FormData。

### 自动识别粘贴

识别应先 trim() 再判断：

* curl 、curl.exe
* fetch(
* await fetch(
* window.fetch(
* XMLHttpRequest
* 纯 URL：http:// 或 https://

粘贴后不直接发送，只填充表单并展示解析摘要：识别来源、提取到的 headers 数、body 类型、警告数量。

8. 响应查看器

--------

响应区必须包含：

1. **摘要条**
   
   * 状态码 + 文案。
   * 耗时 duration_ms。
   * 响应大小。
   * Content-Type。
   * 健壮性评分。
   * 请求时间。

2. **Body 视图**
   
   * JSON 格式化。
   * 原始文本。
   * 表格视图：仅 JSON array/object 可用。
   * 自动折叠大对象。
   * JSON parse 失败时展示原始文本和错误提示。

3. **搜索**
   
   * Body 内全文搜索。
   * JSON key/value 搜索。
   * 命中数、上一个、下一个。
   * 搜索词高亮。

4. **复制**
   
   * 复制完整 Body。
   * 复制选中内容。
   * 复制 JSONPath。
   * 复制响应头。
   * 复制为 curl。

5. **Headers**
   
   * key/value 表格。
   * 支持搜索、复制单行。
   * Content-Type、Set-Cookie、TraceId 等常用字段置顶。

6. **历史对比**
   
   * 选择当前请求的任意两次结果。
   * 对比状态码、耗时、响应头差异、JSON diff。
   * 标记新增、删除、变更字段。

7. **健壮性分析**
   
   * 展示 robustness_score。
   * 字段完整性、类型正确性、异常值检测分项。
   * 展示 AI 生成断言列表。
   * 每条断言支持采纳、编辑、忽略。
   * 采纳后可随 save-to-testcase 保存。

8. 深浅色主题

--------

所有颜色使用 Element Plus 变量和项目主题变量：

* 背景：var(--el-bg-color)、var(--el-fill-color-light)
* 边框：var(--el-border-color)、var(--el-border-color-lighter)
* 文本：var(--el-text-color-primary)、secondary
* 状态色：var(--el-color-success)、warning、danger、info

控制台风格建议：

* 卡片半径不超过 4-8px。

* 避免大面积渐变和装饰背景。

* 等宽字体只用于 URL、headers、JSON、耗时、状态码。

* 深色模式下响应 body 区使用更深的代码背景，但边框仍跟随主题变量。

* 状态色不要只依赖颜色，需同时显示状态码、文案或图标。
10. 组件拆分建议

----------

Dashboard.vue 应只负责页面编排和数据聚合，拆分为：

`views/platform/Dashboard.vue components/dashboard/DashboardHeader.vue components/dashboard/QualityStatusStrip.vue components/dashboard/WidgetGrid.vue components/dashboard/widgets/*.vue components/terminal/TerminalQuickDebug.vue`

Terminal.vue 拆分为：

`views/terminal/Terminal.vue components/terminal/HistorySidebar.vue components/terminal/RequestLine.vue components/terminal/RequestConfigTabs.vue components/terminal/KeyValueEditor.vue components/terminal/BodyEditor.vue components/terminal/ResponseViewer.vue components/terminal/ResponseBodyViewer.vue components/terminal/ResponseHeadersViewer.vue components/terminal/HistoryComparePanel.vue components/terminal/RobustnessPanel.vue`

解析逻辑拆分为：

`utils/requestParser.js utils/parsers/curlParser.js utils/parsers/fetchParser.js utils/parsers/parserUtils.js`

11. 交互规范

--------

* Dashboard 中所有 Widget 点击后进入对应完整模块，不在首页展开复杂编辑。

* Terminal 中“发送”始终固定在请求区顶部或底部，避免滚动后丢失主操作。

* 粘贴解析成功后展示可撤销提示：“已解析 cURL，可恢复粘贴前内容”。

* 保存为用例时弹出轻量表单：用例名、目录、期望状态码、是否保存 AI 断言。

* 收藏请求使用星标，历史列表可直接切换收藏。

* 请求发送中禁用重复发送，但允许取消。

* 错误响应不只显示 message，还应保留请求配置，方便修改后重试。

* 历史记录加载时使用骨架或紧凑 loading，不让布局跳动。
12. 实施优先级

---------

P0：

* Dashboard 改为真实质量工作台布局。
* Terminal 与 Dashboard 拆分职责。
* 修复 fetch/curl headers/body 解析。
* 响应区补齐搜索、复制、JSON 格式化、headers 展示。

P1：

* 收藏请求、历史对比、保存为用例。
* 健壮性评分展示、AI 断言列表。
* Widget 显示/隐藏和排序。

P2：

* Widget 持久化配置。
* JSON 表格视图。
* HAR / 抓包工具格式导入。
* 更完整的 AI 分析闭环。
