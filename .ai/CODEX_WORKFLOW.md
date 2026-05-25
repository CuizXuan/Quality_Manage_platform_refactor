# Codex 需求分发与审查流程

## 目标

让 Codex 在本项目中默认担任“需求理解者、任务拆解者、验收者”，把主要编码执行工作交给 Claude Code。

## 默认协作模式

当用户提出功能开发、Bug 修复、页面调整、接口调整、测试补充等编码需求时，Codex 默认先判断用户意图：

- 如果用户明确要求“你直接改”“Codex 直接实现”“现在就修”，Codex 可以直接修改代码。
- 如果用户提到 Claude、任务包、分发、让 Claude 做、vibecoding 协作，或没有明确要求 Codex 直接改代码，Codex 应优先生成 Claude 任务包。

## Codex 生成任务包流程

生成任务包前，Codex 应：

1. 阅读用户需求。
2. 使用 `rg` 定位相关页面、接口、服务、测试文件。
3. 读取少量关键文件，确认现有实现模式。
4. 明确修改范围、禁止事项、验收标准和验证命令。
5. 在 `.ai/tasks/` 下创建日期前缀任务包。

任务包文件名格式：

```text
.ai/tasks/YYYY-MM-DD-short-task-name.md
```

任务包必须包含：

- 任务目标。
- 背景说明。
- 视觉/交互基准页（如适用）。
- 必读文件。
- 允许修改范围。
- 禁止事项。
- 实现要求。
- 验收标准。
- 建议验证。
- Claude 输出要求。

任务包必须使用中文编写。代码、路径、命令、接口字段、第三方库名称可以保留原文。

## 前端页面与菜单开发特别规则

当需求涉及“新增菜单”“新增页面”“新增模块页面”“基于现有页面扩展一个新页面”“统一页面样式”时，Codex 和 Claude 必须默认遵循以下规则：

1. 先找标准页，不允许凭空发挥。
2. 必须在任务包中明确写出“视觉/结构基准页”。
3. Claude 实现时应先复制一份最接近的标准页结构或样式写法，再做最小必要改造。
4. 不允许为了做一个新页面，自行发明一套新的 header、filters、table、background、menu 样式。
5. 如果标准页是：
   - 列表型业务页：优先参考 `frontend/src/views/scenario/ScenarioList.vue`
   - 用例中心型页：优先参考 `frontend/src/views/case/CaseManagement.vue`
   - 平台管理型页：优先参考同类现有平台页
6. 如果是新增左侧菜单：
   - 必须先对照 `frontend/src/app/AppShell.vue` 中现有 `menuList` 的写法
   - 图标、title、path、children 结构、排序方式必须沿用现有模式
   - 不允许自行创造新的菜单组织方式
7. 如果是浅色/深色主题适配：
   - 必须同时检查 `html:not(.dark)` 分支
   - 不允许只修深色或只修浅色
8. 如果用户明确说“和某个页面保持一致”，Claude 必须把那个页面当作唯一基准，而不是“风格接近即可”。

## Codex 审查 Claude 结果流程

当用户让 Codex 审查 Claude 修改，或 Claude 已完成实现后，Codex 应：

1. 查看 `git diff` 和相关文件。
2. 根据 `AGENTS.md`、任务包和实际代码做 code review。
3. 优先指出 bug、回归风险、遗漏验收项、测试缺口。
4. 如果需要返工，在 `.ai/reviews/` 下创建审查修复包。

审查包文件名格式：

```text
.ai/reviews/YYYY-MM-DD-short-task-name-review.md
```

审查包必须包含：

- 审查目标。
- 需要修复的问题。
- 修复范围。
- 禁止事项。
- 验证方式。
- Claude 输出要求。

## 给用户的默认回复

生成任务包后，Codex 应告诉用户：

```text
已生成任务包：
.ai/tasks/YYYY-MM-DD-short-task-name.md

请在 Claude Code 中执行：
/codex-task .ai/tasks/YYYY-MM-DD-short-task-name.md
```

生成审查包后，Codex 应告诉用户：

```text
已生成审查修复包：
.ai/reviews/YYYY-MM-DD-short-task-name-review.md

请在 Claude Code 中执行：
/codex-review-fix .ai/reviews/YYYY-MM-DD-short-task-name-review.md
```

## 重要约束

- 不要把模糊需求直接交给 Claude。
- 不要让 Claude 自己猜修改范围。
- 不要在任务包中要求 Claude 做无边界重构。
- 不要让 Claude 同时处理多个无关需求。
- 每个任务包应尽量小而完整，便于实现和验收。
- Codex 对用户可见输出默认使用中文。
