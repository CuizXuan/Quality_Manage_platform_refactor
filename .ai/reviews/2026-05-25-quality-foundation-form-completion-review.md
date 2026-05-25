# Codex 审查修复包

## 审查目标

补充复审 `.ai/results/2026-05-25-quality-platform-foundation-project-version-requirement-result.md` 中未准确描述的表单缺口，确保“项目/版本/迭代/需求”不仅能筛选，还能在核心业务表单里被真实维护。

## 需要修复的问题

1. `frontend/src/views/case/CaseEditDialog.vue`
   - 当前用例创建/编辑表单仍未暴露 `project_id / version_id / iteration_id / requirement_id`。
   - 这意味着虽然列表已支持筛选、后端也支持字段，但用户在新建/编辑用例时仍无法建立需求归属。
   - 需要补齐项目、版本、迭代、需求字段，并实现级联加载：
     - 选项目 -> 加载版本、需求
     - 选版本 -> 加载迭代
     - 需求列表按当前项目过滤，必要时按版本/迭代进一步约束

2. `frontend/src/views/report/DefectForm.vue`
   - 当前缺陷创建/编辑表单只有标题、描述、严重程度、优先级、类型、标签，没有 `project_id / version_id / iteration_id / requirement_id`。
   - 缺陷列表虽然已经能按这些字段筛选，但表单无法维护归属，链路仍然不闭环。
   - 需要补齐项目、版本、迭代、需求字段，并实现与查询栏一致的级联逻辑。

3. `frontend/src/views/scenario/ScenarioDetailDialog.vue` 与 `frontend/src/views/scenario/ScenarioList.vue`
   - Claude 当前结论“场景创建/编辑表单未接入项目/版本/迭代”是成立的。
   - 需要在“新建场景”弹窗和“编辑场景”弹窗中补齐 `project_id / version_id / iteration_id`，并实现级联加载。
   - 场景详情卡片中也建议展示当前项目/版本/迭代归属，避免保存后无法确认归属结果。

4. `frontend/src/views/report/ReportList.vue` 及相关报告前端
   - 当前不是“手动创建报告时归属字段未暴露”这么简单，而是前端根本没有“新建报告”入口和手动创建报告表单。
   - 如果产品预期支持手动创建报告，则需要明确补一套最小可用入口与表单，并暴露 `project_id / version_id / iteration_id`。
   - 如果当前版本不打算支持手动创建报告，结果文档必须明确写成：
     - “前端暂无手动创建报告能力，仅支持执行生成报告”
     - 不要写成“手动创建时字段未暴露”，以免误导验收判断。

5. `.ai/results/2026-05-25-quality-platform-foundation-project-version-requirement-result.md`
   - 需要同步修正剩余风险描述：
     - 加入“用例表单未接入归属字段”
     - 加入“缺陷表单未接入归属字段”
     - 报告模块要么补手动创建能力，要么把“无手动创建入口”写清楚
   - 保持结论与当前代码一致，不要用模糊表述弱化未完成项。

## 修复范围

允许修改：

- `frontend/src/views/case/CaseEditDialog.vue`
- `frontend/src/views/report/DefectForm.vue`
- `frontend/src/views/scenario/ScenarioList.vue`
- `frontend/src/views/scenario/ScenarioDetailDialog.vue`
- `frontend/src/views/report/**`
- `frontend/src/stores/qualityFoundationStore.js`
- `frontend/src/stores/reportStore.js`
- `frontend/src/api/**`
- `.ai/results/2026-05-25-quality-platform-foundation-project-version-requirement-result.md`

## 禁止事项

- 不重写页面整体视觉风格。
- 不为了补字段引入新的复杂状态体系。
- 不把“没有手动创建报告入口”包装成“只是少几个字段”。
- 不改动与本次表单补齐无关的业务逻辑。

## 验证方式

修复后至少完成：

```bash
cd frontend
npm run build
```

并人工验证：

- 新建/编辑用例时可以设置项目、版本、迭代、需求
- 新建/编辑缺陷时可以设置项目、版本、迭代、需求
- 新建/编辑场景时可以设置项目、版本、迭代
- 报告模块的“手动创建能力是否存在”在页面与结果文档中表述一致

## Claude 输出要求

结束时必须用中文汇报：

- 已补齐哪些表单字段。
- 是否新增了手动创建报告入口；如果没有，为什么，并在结果文档中如何表述。
- 变更文件。
- 已运行的验证。
- 剩余风险。
