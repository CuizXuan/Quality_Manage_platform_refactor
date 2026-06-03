<template>
  <div class="ai-workbench-page scenario-workbench-page">
    <header class="ai-workbench-page__header scenario-workbench-page__header">
      <div>
        <h1>AI 总控台</h1>
        <p>统一编排资产理解、需求分析、测试设计、失败分析、发布建议五类代理，并查看建议采纳状态。</p>
      </div>
    </header>

    <section class="ai-workbench-page__board">
      <div class="agent-panel scenario-workbench-page__panel">
        <div class="agent-panel__title">代理矩阵</div>
        <div class="agent-grid">
          <button
            v-for="item in agents"
            :key="item.key"
            class="agent-card"
            type="button"
            @click="selectAgent(item.key)"
          >
            <strong>{{ item.title }}</strong>
            <span>{{ item.desc }}</span>
          </button>
        </div>
      </div>

      <div class="agent-panel scenario-workbench-page__panel">
        <div class="agent-panel__title">运行面板</div>
        <el-form label-width="90px" class="agent-form">
          <el-form-item label="当前代理">
            <el-input :model-value="currentAgentLabel" disabled />
          </el-form-item>
          <el-form-item label="目标 ID">
            <el-input v-model="payload.target_id" placeholder="输入关联目标 ID" />
          </el-form-item>
          <el-form-item label="来源说明">
            <el-input v-model="payload.source_name" placeholder="例如：API 资产中心手动触发" />
          </el-form-item>
          <template v-if="currentAgent === 'requirement'">
            <el-form-item label="来源类型">
              <el-select v-model="payload.source_type" placeholder="请选择来源类型">
                <el-option v-for="item in sourceTypes" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="需求内容">
              <el-input
                v-model="payload.content"
                type="textarea"
                :rows="8"
                maxlength="60000"
                show-word-limit
                placeholder="粘贴 PRD、SRS、用户故事、原型说明、OCR 结果、流程图或接口文档内容"
              />
            </el-form-item>
          </template>
          <el-form-item>
            <div class="agent-actions">
              <el-button type="primary" :loading="aiStore.loading" @click="runAgent">运行代理</el-button>
              <el-button
                v-if="currentAgent === 'requirement'"
                type="success"
                :loading="aiStore.workflowLoading"
                @click="runRequirementWorkflow"
              >运行需求到测试设计流程</el-button>
              <el-button @click="loadSuggestions">刷新建议</el-button>
            </div>
          </el-form-item>
        </el-form>

        <div v-if="latestResult" class="result-panel">
          <div class="agent-panel__title">最新结果</div>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="建议 ID">{{ latestResult.suggestion_id }}</el-descriptions-item>
            <el-descriptions-item label="代理类型">{{ latestResult.agent_type }}</el-descriptions-item>
            <el-descriptions-item label="状态">{{ latestResult.status }}</el-descriptions-item>
            <el-descriptions-item v-if="isRequirementResult" label="需求分析摘要">
              <div class="requirement-result">
                <strong>{{ latestPayload.summary }}</strong>
                <div>需求条目：{{ latestPayload.requirements?.length || 0 }} 个</div>
                <ul v-if="latestPayload.requirements?.length">
                  <li v-for="item in latestPayload.requirements" :key="item.source_key || item.title">
                    {{ item.source_key || 'REQ' }} - {{ item.title }}
                  </li>
                </ul>
                <div v-if="latestPayload.ambiguities?.length">歧义点：{{ formatList(latestPayload.ambiguities) }}</div>
                <div v-if="latestPayload.risks?.length">风险：{{ formatList(latestPayload.risks) }}</div>
                <div v-if="latestPayload.test_suggestions?.length">测试建议：{{ formatList(latestPayload.test_suggestions) }}</div>
              </div>
            </el-descriptions-item>
            <el-descriptions-item label="Trace Meta">
              <pre class="trace-block">{{ JSON.stringify(latestResult.trace_meta, null, 2) }}</pre>
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <div v-if="aiStore.workflowRun" class="result-panel workflow-panel">
          <div class="agent-panel__title">需求到测试设计工作流</div>
          <el-alert
            v-if="isWorkflowInProgress"
            :title="workflowProgressTitle"
            type="info"
            :closable="false"
            show-icon
            class="workflow-progress-alert"
          />
          <el-descriptions :column="1" border>
            <el-descriptions-item label="运行 ID">#{{ aiStore.workflowRun.id }}</el-descriptions-item>
            <el-descriptions-item label="工作流类型">{{ workflowTypeLabel }}</el-descriptions-item>
            <el-descriptions-item label="运行状态">
              <el-tag :type="workflowStatusTagType" size="small">{{ workflowStatusLabel }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="步骤">
              <div class="workflow-step-list">
                <div
                  v-for="step in aiStore.workflowRun.steps"
                  :key="step.id"
                  class="workflow-step-item"
                >
                  <span class="workflow-step-order">步骤 {{ step.step_order }}</span>
                  <span class="workflow-step-agent">{{ step.agent_type }}</span>
                  <el-tag :type="stepStatusTagType(step.status)" size="small">{{ stepStatusLabel(step.status) }}</el-tag>
                  <span v-if="step.suggestion_id" class="workflow-step-suggestion">建议 #{{ step.suggestion_id }}</span>
                  <span v-if="step.error_message" class="workflow-step-error">{{ step.error_message }}</span>
                </div>
              </div>
            </el-descriptions-item>
            <el-descriptions-item v-if="workflowRequirementSummary" label="需求分析摘要">
              <div class="requirement-result">
                <strong>{{ workflowRequirementSummary }}</strong>
                <div>需求条目：{{ workflowRequirementPayload.requirements?.length || 0 }} 个</div>
                <ul v-if="workflowRequirementPayload.requirements?.length">
                  <li v-for="item in workflowRequirementPayload.requirements" :key="item.source_key || item.title">
                    {{ item.source_key || 'REQ' }} - {{ item.title }}
                  </li>
                </ul>
              </div>
            </el-descriptions-item>
            <el-descriptions-item v-if="workflowDesignSummary" label="测试设计摘要">
              <div class="design-result">
                <strong>{{ workflowDesignSummary }}</strong>
                <div>测试点：{{ workflowDesignPayload.test_points?.length || 0 }} 个</div>
                <div>功能用例：{{ workflowDesignPayload.functional_cases?.length || 0 }} 个</div>
                <div>接口用例：{{ workflowDesignPayload.api_cases?.length || 0 }} 个</div>
                <div>场景草稿：{{ workflowDesignPayload.scenario_drafts?.length || 0 }} 个</div>
                <ul v-if="workflowDesignPayload.test_points?.length">
                  <li v-for="(point, idx) in workflowDesignPayload.test_points.slice(0, 5)" :key="idx">{{ point }}</li>
                </ul>
              </div>
            </el-descriptions-item>
            <el-descriptions-item v-if="workflowScenarioSummary" label="场景设计摘要">
              <div class="design-result">
                <strong>{{ workflowScenarioSummary }}</strong>
                <div>场景草稿：{{ workflowScenarioPayload.scenario_drafts?.length || 0 }} 个</div>
                <ul v-if="workflowScenarioPayload.scenario_drafts?.length">
                  <li v-for="(draft, idx) in workflowScenarioPayload.scenario_drafts.slice(0, 5)" :key="idx">
                    {{ draft.name || `场景草稿 ${idx + 1}` }}（{{ (draft.steps || []).length }} 步）
                  </li>
                </ul>
                <div v-if="!workflowScenarioPayload.scenario_drafts?.length && workflowDesignPayload.scenario_drafts?.length" class="adopt-hint">
                  场景草稿来自测试设计兼容结构。
                </div>
              </div>
            </el-descriptions-item>
            <el-descriptions-item v-if="aiStore.workflowRun.error" label="错误信息">
              <el-alert :title="aiStore.workflowRun.error" type="error" :closable="false" />
            </el-descriptions-item>
            <el-descriptions-item v-if="aiStore.workflowRun.status === 'completed'" label="人工采纳">
              <div v-if="workflowAdoption" class="adopt-summary">
                <el-alert
                  :title="`已采纳：需求 ${workflowAdoption.requirements_created || 0} 条，用例 ${workflowAdoption.cases_created || 0} 条，场景 ${workflowAdoption.scenarios_created || 0} 个${workflowAdoption.adopted_at ? ` · ${formatAdoptionTime(workflowAdoption.adopted_at)}` : ''}${workflowAdoption.force ? ' · 强制采纳' : ''}${(workflowAdoption.force_adoption_count || 0) > 0 ? `（含 ${workflowAdoption.force_adoption_count} 次强制采纳）` : ''}`"
                  :type="workflowAdoption.error_count ? 'warning' : 'success'"
                  :closable="false"
                />
                <div v-if="(workflowAdoption.cumulative_requirement_ids?.length || workflowAdoption.cumulative_case_ids?.length || workflowAdoption.cumulative_scenario_ids?.length)" class="adopt-ids">
                  <span v-if="workflowAdoption.cumulative_requirement_ids?.length">累计需求 ID：{{ workflowAdoption.cumulative_requirement_ids.join(', ') }}</span>
                  <span v-if="workflowAdoption.cumulative_case_ids?.length">累计用例 ID：{{ workflowAdoption.cumulative_case_ids.join(', ') }}</span>
                  <span v-if="workflowAdoption.cumulative_scenario_ids?.length">累计场景 ID：{{ workflowAdoption.cumulative_scenario_ids.join(', ') }}</span>
                </div>
              </div>

              <div class="adopt-row">
                <el-button
                  type="success"
                  :loading="aiStore.workflowAdoptLoading"
                  :disabled="workflowAdoptionCompleted && !adoptForm.force"
                  @click="showAdoptDialog = true"
                >{{ workflowAdoptionCompleted ? '再次采纳' : '采纳工作流结果' }}</el-button>
                <el-popover v-if="!showAdoptDialog" placement="right" :width="320" trigger="hover">
                  <template #reference>
                    <el-button text type="info" size="small">采纳说明</el-button>
                  </template>
                  <div class="adopt-hint">
                    将 workflow 草稿写入 requirement_items 和 test_cases，可选关联 requirement_id。需要填写 project_id。已采纳后默认阻止重复创建，勾选“强制重新采纳”可覆盖。
                  </div>
                </el-popover>
              </div>

              <div v-if="showAdoptDialog" class="adopt-panel">
                <el-alert
                  v-if="workflowAdoptionCompleted"
                  title="该工作流已采纳，默认不再创建重复数据；如需重新创建请勾选“强制重新采纳”。"
                  type="warning"
                  :closable="false"
                  class="adopt-warning"
                />
                <el-form label-width="120px" size="small">
                  <el-form-item label="项目 ID" required>
                    <el-input-number v-model="adoptForm.project_id" :min="1" :step="1" controls-position="right" />
                  </el-form-item>
                  <el-form-item label="版本 ID">
                    <el-input-number v-model="adoptForm.version_id" :min="0" :step="1" controls-position="right" />
                  </el-form-item>
                  <el-form-item label="迭代 ID">
                    <el-input-number v-model="adoptForm.iteration_id" :min="0" :step="1" controls-position="right" />
                  </el-form-item>
                  <el-form-item label="采纳范围">
                    <el-checkbox-group v-model="adoptForm.types">
                      <el-checkbox value="requirements">采纳需求</el-checkbox>
                      <el-checkbox value="functional">采纳功能用例</el-checkbox>
                      <el-checkbox value="api">采纳接口用例</el-checkbox>
                      <el-checkbox value="scenarios">采纳场景草稿</el-checkbox>
                    </el-checkbox-group>
                  </el-form-item>
                  <el-form-item label="关联到需求">
                    <el-switch v-model="adoptForm.link_cases_to_requirements" />
                  </el-form-item>
                  <el-form-item v-if="adoptForm.types.includes('scenarios')" label="关联步骤到用例">
                    <div class="adopt-force-row">
                      <el-switch v-model="adoptForm.link_scenario_steps_to_cases" />
                      <span class="adopt-force-hint">关闭后将跳过场景草稿，避免写入无法关联的步骤</span>
                    </div>
                  </el-form-item>
                  <el-form-item v-if="workflowAdoptionCompleted" label="强制重新采纳">
                    <div class="adopt-force-row">
                      <el-switch v-model="adoptForm.force" />
                      <span class="adopt-force-hint">强制采纳会重复创建数据，请谨慎使用</span>
                    </div>
                  </el-form-item>
                  <el-form-item>
                    <el-button
                      type="primary"
                      :loading="aiStore.workflowAdoptLoading"
                      :disabled="!adoptForm.project_id || (workflowAdoptionCompleted && !adoptForm.force)"
                      @click="submitAdopt"
                    >{{ workflowAdoptionCompleted && adoptForm.force ? '确认强制采纳' : '确认采纳' }}</el-button>
                    <el-button @click="cancelAdopt">取消</el-button>
                  </el-form-item>
                </el-form>
              </div>

              <div v-if="aiStore.workflowAdoptResult" class="adopt-result">
                <el-alert
                  :title="`采纳完成：新增需求 ${adoptSummary.requirements_created || 0} 条，新增用例 ${adoptSummary.cases_created || 0} 条，新增场景 ${adoptSummary.scenarios_created || 0} 个，跳过 ${adoptSummary.skipped_count || 0}，错误 ${adoptSummary.error_count || 0}`"
                  :type="adoptSummary.error_count ? 'warning' : 'success'"
                  :closable="false"
                />
                <div v-if="aiStore.workflowAdoptResult.created_requirements?.length" class="adopt-list">
                  <div class="adopt-list__title">已创建需求</div>
                  <ul>
                    <li v-for="item in aiStore.workflowAdoptResult.created_requirements" :key="`req-${item.index}`">
                      #{{ item.requirement_id }} - {{ item.title }}
                    </li>
                  </ul>
                </div>
                <div v-if="aiStore.workflowAdoptResult.created_cases?.length" class="adopt-list">
                  <div class="adopt-list__title">已创建用例</div>
                  <ul>
                    <li v-for="item in aiStore.workflowAdoptResult.created_cases" :key="`case-${item.index}`">
                      #{{ item.case_id }} - {{ item.name }}（{{ item.case_type }}）{{ item.requirement_id ? `→ 需求 #${item.requirement_id}` : '' }}
                    </li>
                  </ul>
                </div>
                <div v-if="aiStore.workflowAdoptResult.created_scenarios?.length" class="adopt-list">
                  <div class="adopt-list__title">已创建场景</div>
                  <ul>
                    <li v-for="item in aiStore.workflowAdoptResult.created_scenarios" :key="`scenario-${item.index}`">
                      #{{ item.scenario_id }} - {{ item.name }}（{{ item.step_count }} 步）
                    </li>
                  </ul>
                </div>
                <div v-if="aiStore.workflowAdoptResult.errors?.length" class="adopt-list adopt-list--error">
                  <div class="adopt-list__title">错误</div>
                  <ul>
                    <li v-for="(err, idx) in aiStore.workflowAdoptResult.errors" :key="`err-${idx}`">
                      {{ err.type }} #{{ err.index }} - {{ err.code }}：{{ err.message }}
                    </li>
                  </ul>
                </div>
              </div>

              <div v-if="canShowExecutionPlan" class="execution-plan-block">
                <div class="agent-panel__title">执行计划（五期）</div>
                <div class="adopt-row">
                  <el-button
                    v-if="!workflowExecutionPlanEntry"
                    type="primary"
                    :loading="aiStore.workflowExecutionLoading"
                    @click="generateExecutionPlan"
                  >生成执行计划</el-button>
                  <el-button
                    v-if="workflowExecutionPlanEntry"
                    :loading="aiStore.workflowExecutionLoading"
                    @click="generateExecutionPlan"
                  >重新生成执行计划</el-button>
                  <el-popover v-if="!workflowExecutionPlanEntry" placement="right" :width="320" trigger="hover">
                    <template #reference>
                      <el-button text type="info" size="small">计划说明</el-button>
                    </template>
                    <div class="adopt-hint">
                      基于本 workflow 累计采纳的场景生成执行批次与前置检查，<strong>不会启动执行</strong>，需要人工二次确认后才调用场景执行入口。
                    </div>
                  </el-popover>
                </div>
                <div v-if="workflowExecutionPlanEntry" class="execution-plan-result">
                  <el-alert
                    :title="executionPlanSummary"
                    type="info"
                    :closable="false"
                  />
                  <div v-if="executionPlanBatches.length" class="adopt-list">
                    <div class="adopt-list__title">执行批次</div>
                    <ul>
                      <li v-for="(batch, idx) in executionPlanBatches" :key="`batch-${idx}`">
                        {{ batch.name || `批次 ${idx + 1}` }} · 优先级 {{ batch.priority || 'P2' }} · 模式 {{ batch.run_mode === 'parallel' ? '并行' : '顺序' }} · 场景数 {{ (batch.scenario_ids || []).length }}（{{ (batch.scenario_ids || []).join(', ') }}）{{ batch.environment_id ? ` · 环境 ${batch.environment_id}` : '' }}
                        <div v-if="batch.rationale" class="adopt-hint">{{ batch.rationale }}</div>
                      </li>
                    </ul>
                  </div>
                  <div v-if="executionPlanPreChecks.length" class="adopt-list">
                    <div class="adopt-list__title">前置检查</div>
                    <ul>
                      <li v-for="(item, idx) in executionPlanPreChecks" :key="`precheck-${idx}`">
                        <el-tag size="small" :type="item.status === 'passed' ? 'success' : 'warning'">{{ item.status || 'pending' }}</el-tag>
                        {{ item.name }}：{{ item.description }}
                      </li>
                    </ul>
                  </div>
                  <div v-if="executionPlanRisks.length" class="adopt-list">
                    <div class="adopt-list__title">风险</div>
                    <ul>
                      <li v-for="(risk, idx) in executionPlanRisks" :key="`risk-${idx}`">{{ risk }}</li>
                    </ul>
                  </div>
                  <div v-if="executionPlanWarnings.length" class="adopt-list">
                    <div class="adopt-list__title">警告</div>
                    <ul>
                      <li v-for="(warn, idx) in executionPlanWarnings" :key="`warn-${idx}`">{{ warn }}</li>
                    </ul>
                  </div>
                  <div v-if="!workflowExecutionConfirmation" class="adopt-row" style="margin-top: 8px;">
                    <el-button
                      type="danger"
                      :loading="aiStore.workflowExecutionConfirmLoading"
                      @click="confirmExecutionPlan"
                    >确认执行计划</el-button>
                  </div>
                  <div v-if="workflowExecutionConfirmation" class="adopt-result">
                    <el-alert
                      :title="`已启动执行：场景 ${workflowExecutionConfirmation.scenario_ids?.length || 0} 个，execution_run_ids：${(workflowExecutionConfirmation.execution_run_ids || []).join(', ') || '—'}`"
                      type="success"
                      :closable="false"
                    />
                    <div class="adopt-hint">可在执行中心查看本次启动的 run 状态。</div>
                  </div>

                  <div v-if="canShowExecutionAnalysis" class="execution-analysis-block">
                    <div class="agent-panel__title">执行结果分析（六期）</div>
                    <div class="adopt-row">
                      <el-button
                        v-if="!workflowExecutionAnalysisEntry"
                        type="primary"
                        :loading="aiStore.workflowExecutionAnalysisLoading"
                        @click="analyzeExecutionResults"
                      >分析执行结果</el-button>
                      <el-button
                        v-if="workflowExecutionAnalysisEntry"
                        :loading="aiStore.workflowExecutionAnalysisLoading"
                        @click="analyzeExecutionResults"
                      >重新分析</el-button>
                      <el-popover v-if="!workflowExecutionAnalysisEntry" placement="right" :width="320" trigger="hover">
                        <template #reference>
                          <el-button text type="info" size="small">分析说明</el-button>
                        </template>
                        <div class="adopt-hint">
                          基于本 workflow 启动的 execution_runs 做质量闭环分析：<strong>不会自动创建缺陷、不会修改业务状态、不会自动重跑</strong>。仅给出结论、风险等级、失败归因与下一步建议。
                        </div>
                      </el-popover>
                    </div>
                    <div v-if="workflowExecutionAnalysisEntry" class="execution-analysis-result">
                      <el-alert
                        :title="`质量结论：${executionAnalysisOverallStatusLabel} · 风险等级 ${executionAnalysisRiskLabel} · 通过率 ${executionAnalysisPassRateLabel}`"
                        :type="executionAnalysisAlertType"
                        :closable="false"
                      />
                      <div v-if="executionAnalysisSummary" class="analysis-summary">
                        {{ executionAnalysisSummary }}
                      </div>
                      <div v-if="executionAnalysisFailedScenarios.length" class="adopt-list">
                        <div class="adopt-list__title">失败场景</div>
                        <ul>
                          <li v-for="(fs, idx) in executionAnalysisFailedScenarios" :key="`fs-${idx}`">
                            场景 #{{ fs.scenario_id || '?' }}{{ fs.scenario_name ? ` · ${fs.scenario_name}` : '' }}
                            {{ fs.execution_run_id ? `（execution_run #${fs.execution_run_id}）` : '' }}
                            <div v-if="fs.reason" class="adopt-hint">原因：{{ fs.reason }}</div>
                            <ul v-if="fs.evidence?.length" class="adopt-list__sub">
                              <li v-for="(evi, eIdx) in fs.evidence" :key="`evi-${idx}-${eIdx}`">{{ evi }}</li>
                            </ul>
                          </li>
                        </ul>
                      </div>
                      <div v-if="executionAnalysisRecommendedActions.length" class="adopt-list">
                        <div class="adopt-list__title">建议行动</div>
                        <ul>
                          <li v-for="(act, idx) in executionAnalysisRecommendedActions" :key="`act-${idx}`">
                            <el-tag size="small" :type="actionTagType(act.priority)">{{ act.priority || 'P2' }}</el-tag>
                            <el-tag size="small" effect="plain">{{ actionTypeLabel(act.type) }}</el-tag>
                            {{ act.description }}
                          </li>
                        </ul>
                      </div>
                      <div v-if="executionAnalysisWarnings.length" class="adopt-list">
                        <div class="adopt-list__title">警告</div>
                        <ul>
                          <li v-for="(warn, idx) in executionAnalysisWarnings" :key="`analysis-warn-${idx}`">{{ warn }}</li>
                        </ul>
                      </div>
                      <div v-if="executionAnalysisReportIds.length" class="adopt-list">
                        <div class="adopt-list__title">关联报告</div>
                        <div class="adopt-hint">report_ids：{{ executionAnalysisReportIds.join(', ') }}</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
    </section>

    <section class="ai-workbench-page__table scenario-workbench-page__panel">
      <div class="table-header">
        <div>
          <h3>建议流转</h3>
          <p>这里集中查看 AI 建议的待审核、已采纳和已拒绝状态。</p>
        </div>
      </div>
      <el-table :data="aiStore.suggestions" v-loading="aiStore.loading" height="100%">
        <el-table-column prop="id" label="建议 ID" width="90" />
        <el-table-column prop="suggestion_type" label="类型" width="160" />
        <el-table-column prop="accepted" label="采纳状态" width="110">
          <template #default="{ row }">
            <el-tag :type="row.accepted ? 'success' : 'info'" size="small">
              {{ row.accepted ? '已采纳' : '待处理' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="accepted_comment" label="备注" min-width="220" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <div class="actions-cell">
              <el-button v-if="!row.accepted" text type="primary" size="small" @click="accept(row.id)">采纳</el-button>
              <el-button v-if="!row.accepted" text type="danger" size="small" @click="reject(row.id)">拒绝</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAiStore } from '@/stores/aiStore'

const aiStore = useAiStore()
const route = useRoute()
const currentAgent = ref('asset')
const latestResult = ref(null)
const payload = reactive({
  target_id: '',
  source_name: 'AI 总控台触发',
  source_type: 'prd',
  content: '',
})

// ── 采纳工作流结果 ────────────────────────────────────────
const showAdoptDialog = ref(false)
const adoptForm = reactive({
  project_id: 1,
  version_id: 0,
  iteration_id: 0,
  types: ['requirements', 'functional', 'api'],
  link_cases_to_requirements: true,
  link_scenario_steps_to_cases: true,
  force: false,
})
const adoptSummary = computed(() => aiStore.workflowAdoptResult?.summary || {})

const workflowAdoption = computed(() => {
  return aiStore.workflowRun?.result_payload?.adoption || null
})

const workflowAdoptionCompleted = computed(() => workflowAdoption.value?.status === 'completed')

// 五期：执行计划（必须基于已采纳的累计场景 ID）
const canShowExecutionPlan = computed(() => {
  return (
    aiStore.workflowRun?.status === 'completed' &&
    (workflowAdoption.value?.cumulative_scenario_ids?.length || 0) > 0
  )
})

// 优先取 store 最新结果（生成/确认后清空前），回落到 run.result_payload
// 以便刷新页面或重新拉取 workflow run 后，已存在的计划仍能展示/确认
// 修复跨 workflow 泄漏：store 临时态必须校验 run_id 等于当前 workflowRun.id，
// 否则只采用 result_payload 兜底值（该值天然只属于当前 run）。
const currentWorkflowRunId = computed(() => aiStore.workflowRun?.id ?? null)
const workflowExecutionPlanEntry = computed(() => {
  const storeEntry = aiStore.workflowExecutionPlan
  if (
    storeEntry &&
    storeEntry.run_id !== undefined &&
    storeEntry.run_id !== null &&
    currentWorkflowRunId.value !== null &&
    storeEntry.run_id !== currentWorkflowRunId.value
  ) {
    // 旧 run 的临时态，丢弃
  } else if (storeEntry) {
    return storeEntry
  }
  return aiStore.workflowRun?.result_payload?.execution_plan || null
})

const workflowExecutionConfirmation = computed(() => {
  const storeEntry = aiStore.workflowExecutionConfirmResult
  if (
    storeEntry &&
    storeEntry.run_id !== undefined &&
    storeEntry.run_id !== null &&
    currentWorkflowRunId.value !== null &&
    storeEntry.run_id !== currentWorkflowRunId.value
  ) {
    // 旧 run 的临时态，丢弃
  } else if (storeEntry) {
    return storeEntry
  }
  return aiStore.workflowRun?.result_payload?.execution_confirmation || null
})

// 六期：执行结果分析（基于本 workflow 启动的 execution_runs）
const canShowExecutionAnalysis = computed(() => {
  return (
    Boolean(workflowExecutionConfirmation.value?.execution_run_ids?.length) &&
    aiStore.workflowRun?.status === 'completed'
  )
})

// 优先取 store 最新结果（点击分析后清空前），回落到 run.result_payload
const workflowExecutionAnalysisEntry = computed(() => {
  const storeEntry = aiStore.workflowExecutionAnalysis
  if (
    storeEntry &&
    storeEntry.run_id !== undefined &&
    storeEntry.run_id !== null &&
    currentWorkflowRunId.value !== null &&
    storeEntry.run_id !== currentWorkflowRunId.value
  ) {
    // 旧 run 的临时态，丢弃
  } else if (storeEntry) {
    return storeEntry
  }
  return aiStore.workflowRun?.result_payload?.execution_analysis || null
})

const executionAnalysisPayload = computed(() => {
  return workflowExecutionAnalysisEntry.value?.payload || {}
})

const executionAnalysisSummary = computed(() => executionAnalysisPayload.value?.summary || '')

const executionAnalysisOverallStatus = computed(() => executionAnalysisPayload.value?.overall_status || 'unknown')
const executionAnalysisRiskLevel = computed(() => executionAnalysisPayload.value?.risk_level || 'low')
const executionAnalysisPassRate = computed(() => {
  const rate = Number(executionAnalysisPayload.value?.pass_rate)
  return Number.isFinite(rate) ? Math.max(0, Math.min(1, rate)) : 0
})

const executionAnalysisOverallStatusLabel = computed(() => {
  const map = {
    passed: '通过',
    failed: '失败',
    running: '执行中',
    partial: '部分完成',
    unknown: '未知',
  }
  return map[executionAnalysisOverallStatus.value] || executionAnalysisOverallStatus.value
})

const executionAnalysisRiskLabel = computed(() => {
  const map = {
    low: '低',
    medium: '中',
    high: '高',
    critical: '严重',
  }
  return map[executionAnalysisRiskLevel.value] || executionAnalysisRiskLevel.value
})

const executionAnalysisPassRateLabel = computed(() => `${(executionAnalysisPassRate.value * 100).toFixed(1)}%`)

const executionAnalysisAlertType = computed(() => {
  if (executionAnalysisOverallStatus.value === 'failed' || executionAnalysisRiskLevel.value === 'critical') {
    return 'error'
  }
  if (executionAnalysisOverallStatus.value === 'partial' || executionAnalysisRiskLevel.value === 'high') {
    return 'warning'
  }
  if (executionAnalysisOverallStatus.value === 'passed' && executionAnalysisRiskLevel.value === 'low') {
    return 'success'
  }
  return 'info'
})

const executionAnalysisFailedScenarios = computed(() => executionAnalysisPayload.value?.failed_scenarios || [])

const executionAnalysisRecommendedActions = computed(() => executionAnalysisPayload.value?.recommended_actions || [])

const executionAnalysisWarnings = computed(() => executionAnalysisPayload.value?.warnings || [])

const executionAnalysisReportIds = computed(() => executionAnalysisPayload.value?.report_ids || [])

function actionTypeLabel(type) {
  const map = {
    rerun: '重跑',
    fix_case: '修复用例',
    fix_env: '修复环境',
    create_defect: '登记缺陷',
    review_requirement: '复核需求',
    manual_check: '人工复核',
  }
  return map[type] || type || 'manual_check'
}

function actionTagType(priority) {
  const map = { P0: 'danger', P1: 'warning', P2: 'info', P3: 'success' }
  return map[priority] || 'info'
}

async function analyzeExecutionResults() {
  if (!aiStore.workflowRun?.id) {
    ElMessage.warning('请先运行需求到测试设计流程')
    return
  }
  if (!workflowExecutionConfirmation.value?.execution_run_ids?.length) {
    ElMessage.warning('请先确认执行计划')
    return
  }
  try {
    await aiStore.analyzeWorkflowExecution(aiStore.workflowRun.id, {
      include_running: true,
    })
    ElMessage.success('执行结果分析已生成')
    await aiStore.fetchWorkflowRun(aiStore.workflowRun.id)
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || err?.message || '执行结果分析失败')
  }
}

const executionPlanPayload = computed(() => {
  return workflowExecutionPlanEntry.value?.payload || {}
})

const executionPlanSummary = computed(() => executionPlanPayload.value?.summary || '执行计划已生成。')
const executionPlanBatches = computed(() => executionPlanPayload.value?.execution_batches || [])
const executionPlanPreChecks = computed(() => executionPlanPayload.value?.pre_checks || [])
const executionPlanRisks = computed(() => executionPlanPayload.value?.risks || [])
const executionPlanWarnings = computed(() => executionPlanPayload.value?.warnings || [])

async function generateExecutionPlan() {
  if (!aiStore.workflowRun?.id) {
    ElMessage.warning('请先运行需求到测试设计流程')
    return
  }
  try {
    await aiStore.planWorkflowExecution(aiStore.workflowRun.id, {
      include_draft_scenarios: true,
    })
    ElMessage.success('执行计划已生成，请确认后再启动')
    await aiStore.fetchWorkflowRun(aiStore.workflowRun.id)
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || err?.message || '生成执行计划失败')
  }
}

async function confirmExecutionPlan() {
  if (!aiStore.workflowRun?.id) {
    ElMessage.warning('请先运行需求到测试设计流程')
    return
  }
  try {
    await ElMessageBox.confirm(
      '确认后将启动场景执行，是否继续？',
      '确认执行',
      { confirmButtonText: '确认执行', cancelButtonText: '取消', type: 'warning' },
    )
  } catch (_) {
    return
  }
  try {
    await aiStore.confirmWorkflowExecution(aiStore.workflowRun.id, {})
    ElMessage.success('执行计划已确认，execution_runs 已创建')
    await aiStore.fetchWorkflowRun(aiStore.workflowRun.id)
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || err?.message || '确认执行计划失败')
  }
}

const agents = [
  { key: 'asset', title: '资产理解代理', desc: '识别来源资产、风险点和冷启动问题' },
  { key: 'requirement', title: '需求分析 Agent', desc: '解析 PRD、原型、流程和接口文档，生成结构化需求建议' },
  { key: 'design', title: '测试设计代理', desc: '批量生成基础用例、断言模板和场景草稿' },
  { key: 'failure', title: '失败分析代理', desc: '结合执行日志与历史缺陷做归因建议' },
  { key: 'release', title: '发布建议代理', desc: '基于质量指标输出放行/警告/阻断建议' },
]

const sourceTypes = [
  { label: 'PRD', value: 'prd' },
  { label: 'SRS', value: 'srs' },
  { label: '用户故事', value: 'user_story' },
  { label: 'Axure', value: 'axure' },
  { label: 'Figma', value: 'figma' },
  { label: 'OCR', value: 'ocr' },
  { label: '流程图', value: 'flowchart' },
  { label: '接口文档', value: 'api_doc' },
  { label: '混合', value: 'mixed' },
  { label: '其他', value: 'other' },
]

const currentAgentLabel = computed(() => agents.find((item) => item.key === currentAgent.value)?.title || '—')
const latestPayload = computed(() => latestResult.value?.payload || {})
const isRequirementResult = computed(() => latestResult.value?.agent_type === 'requirement-analyst')

const workflowTypeLabel = computed(() => {
  const type = aiStore.workflowRun?.workflow_type
  if (type === 'requirement_to_test_design') return '需求到测试设计'
  return type || '—'
})

const workflowStatusLabel = computed(() => {
  const map = {
    pending: '等待中',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
  }
  return map[aiStore.workflowRun?.status] || aiStore.workflowRun?.status || '—'
})

const workflowStatusTagType = computed(() => {
  const map = { pending: 'info', running: 'warning', completed: 'success', failed: 'danger' }
  return map[aiStore.workflowRun?.status] || 'info'
})

// 五/七期：异步 workflow 启动后，run 处于 pending/running 时持续轮询并显示进度。
const isWorkflowInProgress = computed(() => {
  const status = aiStore.workflowRun?.status
  return status === 'pending' || status === 'running'
})

const workflowProgressTitle = computed(() => {
  const status = aiStore.workflowRun?.status
  const step = aiStore.workflowRun?.current_step
  if (status === 'pending') {
    return 'AI 工作流已加入后台队列,正在准备开始,预计 1-3 分钟完成。'
  }
  if (status === 'running') {
    return step
      ? `AI 正在执行（${step}），预计还需 1-2 分钟,请勿关闭页面。`
      : 'AI 正在执行,预计还需 1-2 分钟,请勿关闭页面。'
  }
  return ''
})

const workflowRequirementPayload = computed(() => {
  return aiStore.workflowRun?.result_payload?.requirement_analysis?.payload || {}
})

const workflowDesignPayload = computed(() => {
  return aiStore.workflowRun?.result_payload?.test_design?.payload || {}
})

// 四期：scenario-designer 输出；旧结构回落到 test_design.payload.scenario_drafts
const workflowScenarioPayload = computed(() => {
  const scenarioDesign = aiStore.workflowRun?.result_payload?.scenario_design?.payload
  if (scenarioDesign && scenarioDesign.scenario_drafts?.length) {
    return scenarioDesign
  }
  return workflowDesignPayload.value
})

const workflowRequirementSummary = computed(() => {
  return workflowRequirementPayload.value?.summary || ''
})

const workflowDesignSummary = computed(() => {
  return workflowDesignPayload.value?.summary || ''
})

const workflowScenarioSummary = computed(() => {
  return workflowScenarioPayload.value?.summary || ''
})

function stepStatusTagType(status) {
  const map = { pending: 'info', running: 'warning', completed: 'success', failed: 'danger' }
  return map[status] || 'info'
}

function stepStatusLabel(status) {
  const map = { pending: '等待中', running: '运行中', completed: '已完成', failed: '失败' }
  return map[status] || status
}

function selectAgent(key) {
  currentAgent.value = key
}

async function runAgent() {
  const data = {
    target_id: Number(payload.target_id || 0),
    source_name: payload.source_name,
  }
  if (currentAgent.value === 'requirement') {
    if (!payload.content.trim()) {
      ElMessage.warning('请先输入需求内容')
      return
    }
    latestResult.value = await aiStore.runRequirementAnalysis({
      ...data,
      source_type: payload.source_type,
      content: payload.content,
    })
  } else if (currentAgent.value === 'design') latestResult.value = await aiStore.runDesignTests(data)
  else if (currentAgent.value === 'failure') latestResult.value = await aiStore.runFailureAgent(data)
  else if (currentAgent.value === 'release') latestResult.value = await aiStore.runReleaseAdvice(data)
  else latestResult.value = await aiStore.runAssetUnderstand(data)
  ElMessage.success('AI 代理已生成建议')
  await loadSuggestions()
}

async function runRequirementWorkflow() {
  if (!payload.content.trim()) {
    ElMessage.warning('请先输入需求内容')
    return
  }
  if (!payload.source_name.trim()) {
    ElMessage.warning('请先输入来源说明')
    return
  }
  const workflowPayload = {
    target_id: Number(payload.target_id || 0),
    source_name: payload.source_name,
    source_type: payload.source_type,
    content: payload.content,
    auto_continue: true,
  }
  const result = await aiStore.startRequirementWorkflow(workflowPayload)
  if (result?.status === 'completed') {
    ElMessage.success('需求到测试设计流程已完成')
  } else if (result?.status === 'failed') {
    ElMessage.error('工作流执行失败，请查看步骤详情')
  } else {
    ElMessage.info(`工作流状态：${result?.status || 'unknown'}`)
  }
  await loadSuggestions()
}

function formatList(items) {
  return items.map((item) => (typeof item === 'string' ? item : item.risk || item.criteria || item.description || JSON.stringify(item))).join('；')
}

async function loadSuggestions() {
  await aiStore.fetchSuggestions({ page: 1, page_size: 20 })
}

async function submitAdopt() {
  if (!adoptForm.project_id) {
    ElMessage.warning('请先填写项目 ID')
    return
  }
  if (!aiStore.workflowRun?.id) {
    ElMessage.warning('请先运行需求到测试设计流程')
    return
  }
  // force 重新采纳走二次确认，避免误触重复入库
  if (workflowAdoptionCompleted.value && adoptForm.force) {
    try {
      await ElMessageBox.confirm(
        '强制重新采纳会重复创建需求/用例，请确认是否继续？',
        '强制重新采纳',
        { confirmButtonText: '确认强制', cancelButtonText: '取消', type: 'warning' },
      )
    } catch (_) {
      return
    }
  }
  const requestBody = {
    project_id: adoptForm.project_id,
    version_id: adoptForm.version_id || null,
    iteration_id: adoptForm.iteration_id || null,
    adopt_requirements: adoptForm.types.includes('requirements'),
    adopt_functional_cases: adoptForm.types.includes('functional'),
    adopt_api_cases: adoptForm.types.includes('api'),
    adopt_scenario_drafts: adoptForm.types.includes('scenarios'),
    link_cases_to_requirements: adoptForm.link_cases_to_requirements,
    link_scenario_steps_to_cases: adoptForm.link_scenario_steps_to_cases,
    force: adoptForm.force,
  }
  try {
    await aiStore.adoptWorkflowRun(aiStore.workflowRun.id, requestBody)
    const summary = aiStore.workflowAdoptResult?.summary || {}
    if (summary.error_count) {
      ElMessage.warning(
        `采纳完成：${summary.requirements_created || 0} 需求 / ${summary.cases_created || 0} 用例 / ${summary.scenarios_created || 0} 场景，${summary.error_count || 0} 条错误`,
      )
    } else {
      ElMessage.success(
        `采纳完成：${summary.requirements_created || 0} 需求 / ${summary.cases_created || 0} 用例 / ${summary.scenarios_created || 0} 场景`,
      )
    }
    // 重新拉取 run 状态，使面板展示最新的 adoption 摘要
    await aiStore.fetchWorkflowRun(aiStore.workflowRun.id)
    await loadSuggestions()
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || err?.message || '采纳失败')
  }
}

function cancelAdopt() {
  showAdoptDialog.value = false
  adoptForm.force = false
}

function formatAdoptionTime(value) {
  if (!value) return ''
  try {
    return new Date(value).toLocaleString()
  } catch (err) {
    return value
  }
}


async function accept(id) {
  await aiStore.acceptSuggestion(id, 'AI 总控台采纳')
  ElMessage.success('已采纳建议')
  await loadSuggestions()
}

async function reject(id) {
  await aiStore.rejectSuggestion(id, 'AI 总控台拒绝')
  ElMessage.success('已拒绝建议')
  await loadSuggestions()
}

// 七期 A 修复：异步 workflow 启动后 status=pending/running 时持续轮询。
// 真实模型三步约 1-3 分钟，前端 axios 30s 超时不会误判失败。
const POLL_INTERVAL_MS = 2500
let pollTimer = null
const watchedQueryRunId = computed(() => {
  const v = Number(route.query?.run_id)
  return Number.isInteger(v) && v > 0 ? v : 0
})

function startWorkflowPolling() {
  stopWorkflowPolling()
  const runId = watchedQueryRunId.value
  if (!runId) return
  pollTimer = setInterval(async () => {
    const status = aiStore.workflowRun?.status
    if (status !== 'pending' && status !== 'running') {
      stopWorkflowPolling()
      return
    }
    try {
      await aiStore.fetchWorkflowRun(runId)
    } catch (err) {
      // 单次网络抖动忽略,下次轮询继续
    }
  }, POLL_INTERVAL_MS)
}

function stopWorkflowPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

// 七期 A 修复：路由 run_id 变化时, 先拉取新 run, 再根据状态决定是否轮询。
// 关键修复: 之前 watch 只调 startWorkflowPolling, 但 polling 内部第一 tick
// 看的是 store 中已有的旧 run 状态, 如果旧 run 已 completed 会直接停止, 不拉取新 run。
async function loadWorkflowRunFromRoute() {
  const runId = watchedQueryRunId.value
  // 任何路径都先 stop, 避免保留指向旧 run 的 timer
  stopWorkflowPolling()
  if (!runId) return
  try {
    // 先拉取新 run (覆盖 store.workflowRun), 再决定是否轮询
    await aiStore.fetchWorkflowRun(runId)
    startWorkflowPolling()
  } catch (err) {
    // 错误已写入 aiStore.error; 不启动轮询, 让用户能看到错误状态
  }
}

onMounted(async () => {
  await loadWorkflowRunFromRoute()
  await loadSuggestions()
})

onUnmounted(stopWorkflowPolling)
watch(watchedQueryRunId, () => {
  // 路由 run_id 变化时: 先 fetch 新 run, 再启动轮询
  loadWorkflowRunFromRoute()
})
</script>

<style scoped>
.ai-workbench-page {
  display: flex;
  flex-direction: column;
  gap: 10px;
  height: 100%;
  padding: 12px;
  position: relative;
}

.ai-workbench-page__header {
  min-height: 56px;
  padding: 12px 16px;
}

.ai-workbench-page__header h1,
.ai-workbench-page__header p {
  margin: 0;
}

.ai-workbench-page__header h1 {
  color: var(--text-strong);
  font-size: 24px;
}

.ai-workbench-page__header p {
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 13px;
}

.ai-workbench-page__board {
  display: grid;
  grid-template-columns: minmax(340px, 0.95fr) minmax(0, 1.05fr);
  gap: 10px;
}

.agent-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 14px;
}

.agent-panel__title {
  color: var(--text-strong);
  font-size: 15px;
  font-weight: 700;
}

.agent-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.agent-card {
  display: grid;
  gap: 6px;
  padding: 12px;
  border: 1px solid rgba(56, 189, 248, 0.12);
  border-radius: 10px;
  background: rgba(8, 18, 32, 0.26);
  text-align: left;
}

html:not(.dark) .agent-card {
  background: rgba(255, 255, 255, 0.6);
  border-color: rgba(22, 119, 255, 0.12);
}

.agent-card strong {
  color: var(--text-strong);
}

.agent-card span {
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.5;
}

.agent-form {
  width: 100%;
}

.agent-actions {
  display: flex;
  gap: 8px;
}

.result-panel {
  display: grid;
  gap: 10px;
}

.requirement-result {
  display: grid;
  gap: 6px;
  color: var(--text-primary);
}

.requirement-result ul {
  margin: 0;
  padding-left: 18px;
}

.design-result {
  display: grid;
  gap: 6px;
  color: var(--text-primary);
}

.design-result ul {
  margin: 0;
  padding-left: 18px;
}

.workflow-panel {
  border-top: 1px solid rgba(56, 189, 248, 0.18);
  padding-top: 12px;
}

html:not(.dark) .workflow-panel {
  border-top-color: rgba(22, 119, 255, 0.18);
}

.workflow-progress-alert {
  margin-bottom: 10px;
}

.workflow-step-list {
  display: grid;
  gap: 6px;
}

.workflow-step-item {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 6px;
  background: rgba(8, 18, 32, 0.18);
  color: var(--text-primary);
  font-size: 12px;
}

html:not(.dark) .workflow-step-item {
  background: rgba(22, 119, 255, 0.06);
}

.workflow-step-order {
  font-weight: 700;
  color: var(--text-strong);
}

.workflow-step-agent {
  font-family: monospace;
}

.workflow-step-suggestion {
  color: var(--text-secondary);
}

.workflow-step-error {
  color: var(--el-color-danger);
  width: 100%;
}

.adopt-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.adopt-summary {
  display: grid;
  gap: 6px;
  margin-bottom: 8px;
}

.adopt-ids {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  color: var(--text-secondary);
  font-size: 12px;
}

.adopt-warning {
  margin-bottom: 10px;
}

.adopt-force-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.adopt-force-hint {
  color: var(--el-color-warning);
  font-size: 12px;
}

.adopt-hint {
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.6;
}

.adopt-panel {
  margin-top: 10px;
  padding: 12px;
  border-radius: 8px;
  background: rgba(8, 18, 32, 0.18);
  border: 1px solid rgba(56, 189, 248, 0.18);
}

html:not(.dark) .adopt-panel {
  background: rgba(22, 119, 255, 0.04);
  border-color: rgba(22, 119, 255, 0.18);
}

.adopt-result {
  margin-top: 10px;
  display: grid;
  gap: 8px;
}

.adopt-list {
  display: grid;
  gap: 4px;
  font-size: 12px;
  color: var(--text-primary);
}

.adopt-list__title {
  font-weight: 700;
  color: var(--text-strong);
}

.adopt-list ul {
  margin: 0;
  padding-left: 18px;
}

.adopt-list--error ul {
  color: var(--el-color-danger);
}

.execution-plan-block {
  margin-top: 12px;
  display: grid;
  gap: 10px;
  padding-top: 10px;
  border-top: 1px dashed rgba(56, 189, 248, 0.18);
}

html:not(.dark) .execution-plan-block {
  border-top-color: rgba(22, 119, 255, 0.18);
}

.execution-plan-result {
  display: grid;
  gap: 8px;
}

.execution-analysis-block {
  margin-top: 12px;
  display: grid;
  gap: 10px;
  padding-top: 10px;
  border-top: 1px dashed rgba(56, 189, 248, 0.18);
}

html:not(.dark) .execution-analysis-block {
  border-top-color: rgba(22, 119, 255, 0.18);
}

.execution-analysis-result {
  display: grid;
  gap: 8px;
}

.analysis-summary {
  color: var(--text-primary);
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.adopt-list__sub {
  margin: 4px 0 0;
  padding-left: 18px;
  color: var(--text-secondary);
  font-size: 12px;
}

.trace-block {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}

.ai-workbench-page__table {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  padding: 14px;
}

.table-header {
  margin-bottom: 10px;
}

.table-header h3,
.table-header p {
  margin: 0;
}

.table-header h3 {
  color: var(--text-strong);
  font-size: 15px;
}

.table-header p {
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 12px;
}

.actions-cell {
  display: inline-flex;
  gap: 4px;
}
</style>
