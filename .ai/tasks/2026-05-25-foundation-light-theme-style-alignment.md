# Codex 任务包

## 任务目标

修复“质量基础”下两个页面在**浅色主题**中的视觉不适配问题：

- `frontend/src/views/foundation/ProjectManagement.vue`
- `frontend/src/views/foundation/RequirementManagement.vue`

目标不是简单“改个颜色”，而是让这两个页面在浅色主题下的**页面背景、标题区、查询区、表格区、透明度、层级感、网格流动感**，都与 `frontend/src/views/scenario/ScenarioList.vue` 保持一致的设计语言。

## 现象描述

当前问题：

1. 在浅色主题下，这两个页面整体发灰、发闷，像覆盖了一层灰色蒙版。
2. 页面背景没有正确切换到和“场景管理”一致的浅色蓝绿流动网格感。
3. 标题区、查询区、表格区在浅色模式下仍然保留了过重的深色半透明底，导致层级不通透。
4. 用户感知上不像“场景管理”的浅色版本，而更像“深色样式硬套到浅色模式”。

## 对照基准

以 `frontend/src/views/scenario/ScenarioList.vue` 为**唯一视觉基准**，尤其对齐其浅色主题下的以下处理：

1. 页面容器浅色背景：
   - 不是纯白，也不是大面积灰蒙层
   - 保留蓝绿网格和轻微流动感
   - 整体明亮、轻透

2. 标题区浅色样式：
   - `html:not(.dark)` 下应切到明亮的白蓝渐变玻璃质感
   - 阴影更轻，边框更干净
   - 不能出现沉重灰底

3. 查询区浅色样式：
   - 背景为浅色半透明层
   - 网格纹理和扫描感仍保留，但更轻
   - 不应出现“深灰板块”感

4. 表格区浅色样式：
   - 表格容器、表头、行背景都应切换到浅色版本
   - 不应出现大面积灰蓝蒙层
   - 表格透明度、奇偶行、hover 层次与 `ScenarioList.vue` 一致

## 明确要求

请直接对照 `ScenarioList.vue` 的浅色主题实现，修复以下页面：

### 1. `ProjectManagement.vue`

- 页面根容器浅色背景与 `ScenarioList.vue` 一致
- 标题区、查询区、表格区都补齐 `html:not(.dark)` 的浅色适配
- 表格容器不能再是当前截图中的整块灰蓝底
- 版本弹窗、迭代弹窗内部表单区域如沿用本页样式，也需要检查浅色下是否偏灰过重

### 2. `RequirementManagement.vue`

- 当前页面整体比 `ProjectManagement.vue` 更接近未完成态，需要完整补齐：
  - 页面背景层
  - 覆盖率卡片浅色样式
  - 标题区浅色样式
  - 查询区浅色样式
  - 表格区浅色样式
- 最终视觉必须与 `ScenarioList.vue` 属于同一套风格，而不是另一套“质量基础专属灰色板块”

## 实现方式要求

1. 优先复用 `ScenarioList.vue` 已验证有效的浅色主题写法。
2. 不要只改少量颜色变量后草草结束。
3. 需要补齐：
   - 容器背景
   - `::before / ::after` 装饰层在浅色模式下的表现
   - header / filters / table 的 `html:not(.dark)` 分支
   - 表格内部 `:deep(.el-table)`、表头、奇偶行、hover 的浅色分支
4. 如果两个页面已有自定义 `background: rgba(15, 23, 42, ...)` 等深色半透明底，请在浅色主题下显式覆盖，不要依赖默认变量碰运气。

## 禁止事项

- 不改动页面结构和业务逻辑。
- 不引入新的视觉风格。
- 不把页面改成纯白平板式 UI。
- 不只修一个页面。
- 不只修 header，不修 table / filters / coverage cards。

## 验收标准

完成后，浅色主题下必须满足：

1. `ProjectManagement.vue` 与 `RequirementManagement.vue` 的整体明度、背景层次、透明度明显接近 `ScenarioList.vue`
2. 页面不再呈现整片灰色压暗效果
3. 表格区域不再是截图中的“灰蓝大底板”
4. 查询区和标题区在浅色主题下具备通透感，不发闷
5. 两个页面属于同一设计系统，而不是孤立样式

## 验证方式

至少执行：

```bash
cd frontend
npm run build
```

并在浅色主题下人工确认：

- `/foundation/projects`
- `/foundation/requirements`
- 对照 `/scenario`

## Claude 输出要求

结束时必须用中文说明：

- 具体对齐了哪些浅色主题样式点
- 哪些 `html:not(.dark)` 分支是新增或修复的
- 变更文件
- 已运行的验证
- 是否已与 `ScenarioList.vue` 对齐
