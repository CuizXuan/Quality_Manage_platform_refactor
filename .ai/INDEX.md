# AI 协作目录索引

本目录用于存放 Codex 与 Claude Code 协作过程中的交接文件。

## 目录说明

- `.ai/tasks/`：Codex 编写的实现任务包，交给 Claude 执行。
- `.ai/reviews/`：Codex 编写的审查修复包，交给 Claude 返工。
- `.ai/results/`：可选的 Claude 执行结果记录。

## Claude 执行规则

Claude 必须把 `.ai/tasks/` 和 `.ai/reviews/` 中的指定文件视为当前任务范围的唯一事实来源。

修改代码前：
1. 读取 `CLAUDE.md`。
2. 读取 `AGENTS.md`。
3. 读取本索引。
4. 读取用户指定的任务文件或审查文件。

实现过程中：
- 修改范围必须严格限定在指定任务包或审查包内。
- 遵循 `AGENTS.md` 中的后端、前端、测试和 Git 规范。
- 不做无关重构。
- 除非用户明确要求，否则不要修改任务包或审查包文件。

结束前：
- 运行相关测试；如果无法运行，必须说明原因。
- 汇报变更文件。
- 汇报验证结果。
- 汇报剩余风险。
- 对用户可见的输出必须使用中文。

## 文件命名

使用日期前缀命名：

```text
.ai/tasks/2026-05-22-feature-name.md
.ai/reviews/2026-05-22-feature-name-review.md
.ai/results/2026-05-22-feature-name-result.md
```
