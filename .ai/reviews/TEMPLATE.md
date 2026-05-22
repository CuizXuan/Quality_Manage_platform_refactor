# Codex 审查修复包

## 审查目标

描述被审查的分支、提交、diff 或任务结果。

## 需要修复的问题

只列出 Claude 需要修复的可执行问题。

示例：

1. `backend/app/routers/example.py`: route handler contains business logic. Move it to a service.
2. `frontend/src/views/Example.vue`: API call should be moved to `frontend/src/api/example.js`.
3. Missing test coverage for the 404 path.

## 修复范围

Claude 只能修改解决上述问题所必需的文件。

## 禁止事项

- 不添加无关清理。
- 不为了风格重写已经正常工作的代码。
- 不改变审查问题范围之外的行为。
- 除非明确要求，不修改本审查包。

## 验证方式

修复后运行最相关的测试或检查。

## Claude 输出要求

结束时必须用中文汇报：
- 已修复哪些问题。
- 变更文件。
- 已运行的测试或检查。
- 剩余风险。
