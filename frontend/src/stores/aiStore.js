import { ref } from 'vue'
import { defineStore } from 'pinia'
import { aiApi } from '@/api/ai'

export const useAiStore = defineStore('ai', () => {
  // ── State: Config ───────────────────────────────────────────
  const aiConfig = ref(null)
  const configLoading = ref(false)

  // ── State: Templates ─────────────────────────────────────────
  const templates = ref([])
  const templateTotal = ref(0)
  const templatePage = ref(1)
  const templatePageSize = ref(20)
  const currentTemplate = ref(null)

  // ── State: Generation Results ────────────────────────────────
  const variantResult = ref(null)
  const assertionResult = ref(null)
  const failureResult = ref(null)
  const summaryResult = ref(null)
  const requirementAnalysisResult = ref(null)

  // ── State: Multi-Agent Workflow ─────────────────────────────
  const workflowRun = ref(null)
  const workflowLoading = ref(false)
  const workflowAdoptResult = ref(null)
  const workflowAdoptLoading = ref(false)
  const workflowExecutionPlan = ref(null)
  const workflowExecutionLoading = ref(false)
  const workflowExecutionConfirmResult = ref(null)
  const workflowExecutionConfirmLoading = ref(false)
  const workflowExecutionAnalysis = ref(null)
  const workflowExecutionAnalysisLoading = ref(false)

  // ── 七期 A：按业务来源 trace ────────────────────────────────
  const workflowTraceItems = ref([])
  const workflowTraceTotal = ref(0)
  const workflowTraceLoading = ref(false)

  // ── State: Analysis ─────────────────────────────────────────
  const currentAnalysis = ref(null)

  // ── State: Suggestions ──────────────────────────────────────
  const suggestions = ref([])
  const suggestionTotal = ref(0)

  // ── State: Common ───────────────────────────────────────────
  const loading = ref(false)
  const error = ref('')

  // ── Actions: Config ─────────────────────────────────────────

  async function fetchConfig() {
    configLoading.value = true
    try {
      const response = await aiApi.getConfig()
      aiConfig.value = response.data
      return aiConfig.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取AI配置失败'
      throw err
    } finally {
      configLoading.value = false
    }
  }

  async function saveConfig(data) {
    configLoading.value = true
    try {
      const response = await aiApi.updateConfig(data)
      aiConfig.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '保存AI配置失败'
      throw err
    } finally {
      configLoading.value = false
    }
  }

  async function testConnection(data) {
    configLoading.value = true
    try {
      const response = await aiApi.testConnection(data)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '连接测试失败'
      throw err
    } finally {
      configLoading.value = false
    }
  }

  // ── Actions: Templates ───────────────────────────────────────

  async function fetchTemplates(params = {}) {
    loading.value = true
    error.value = ''
    try {
      const response = await aiApi.listTemplates({
        page: params.page || templatePage.value,
        page_size: params.page_size || templatePageSize.value,
        ...(params.keyword && { keyword: params.keyword }),
        ...(params.template_type && { template_type: params.template_type }),
      })
      templates.value = response.data.items
      templateTotal.value = response.data.total
      templatePage.value = response.data.page
      templatePageSize.value = response.data.page_size
      return templates.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取模板列表失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createTemplate(data) {
    loading.value = true
    try {
      const response = await aiApi.createTemplate(data)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '创建模板失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateTemplate(id, data) {
    loading.value = true
    try {
      const response = await aiApi.updateTemplate(id, data)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '更新模板失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteTemplate(id) {
    loading.value = true
    try {
      await aiApi.deleteTemplate(id)
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '删除模板失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // ── Actions: Generation ──────────────────────────────────────

  async function generateVariants(data) {
    loading.value = true
    error.value = ''
    try {
      const response = await aiApi.generateVariants(data)
      variantResult.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '生成变体失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function generateAssertions(data) {
    loading.value = true
    error.value = ''
    try {
      const response = await aiApi.generateAssertions(data)
      assertionResult.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '生成断言失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function analyzeFailure(data) {
    loading.value = true
    error.value = ''
    try {
      const response = await aiApi.analyzeFailure(data)
      failureResult.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '失败归因分析失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function summarizeReport(data) {
    loading.value = true
    error.value = ''
    try {
      const response = await aiApi.summarizeReport(data)
      summaryResult.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '报告总结失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // ── Actions: Analysis ────────────────────────────────────────

  async function fetchAnalysis(id) {
    loading.value = true
    error.value = ''
    try {
      const response = await aiApi.getAnalysis(id)
      currentAnalysis.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取分析结果失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchSuggestions(params = {}) {
    loading.value = true
    error.value = ''
    try {
      const response = await aiApi.listSuggestions(params)
      suggestions.value = response.data?.items || []
      suggestionTotal.value = response.data?.total || 0
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取建议列表失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function acceptSuggestion(id, comment) {
    try {
      await aiApi.acceptSuggestion(id, { accepted_comment: comment })
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '采纳建议失败'
      throw err
    }
  }

  async function rejectSuggestion(id, comment) {
    try {
      await aiApi.rejectSuggestion(id, { comment })
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '拒绝建议失败'
      throw err
    }
  }

  async function runRequirementAnalysis(data) {
    loading.value = true
    error.value = ''
    try {
      const response = await aiApi.runRequirementAnalysis(data)
      requirementAnalysisResult.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '需求分析失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function runAssetUnderstand(data) {
    loading.value = true
    try {
      const response = await aiApi.runAssetUnderstand(data)
      return response.data
    } finally {
      loading.value = false
    }
  }

  async function runDesignTests(data) {
    loading.value = true
    try {
      const response = await aiApi.runDesignTests(data)
      return response.data
    } finally {
      loading.value = false
    }
  }

  async function runFailureAgent(data) {
    loading.value = true
    try {
      const response = await aiApi.runFailureAgent(data)
      return response.data
    } finally {
      loading.value = false
    }
  }

  async function runReleaseAdvice(data) {
    loading.value = true
    try {
      const response = await aiApi.runReleaseAdvice(data)
      return response.data
    } finally {
      loading.value = false
    }
  }

  // ── Actions: Multi-Agent Workflow ────────────────────────────

  /** 清理工作流派生态（采纳/计划/确认/分析），切换 run 时避免泄漏旧数据。 */
  function clearWorkflowDerivedState() {
    workflowAdoptResult.value = null
    workflowExecutionPlan.value = null
    workflowExecutionConfirmResult.value = null
    workflowExecutionAnalysis.value = null
  }

  async function startRequirementWorkflow(data) {
    workflowLoading.value = true
    error.value = ''
    try {
      const response = await aiApi.startRequirementWorkflow(data)
      // 切换到新 run：先清理派生态，再覆盖 workflowRun
      // 避免旧 run 的 plan/confirm/analysis 在新 run 渲染时被读到
      clearWorkflowDerivedState()
      workflowRun.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '启动工作流失败'
      throw err
    } finally {
      workflowLoading.value = false
    }
  }

  async function fetchWorkflowRun(id) {
    workflowLoading.value = true
    error.value = ''
    try {
      const response = await aiApi.getWorkflowRun(id)
      // 切换 run（与当前 workflowRun.id 不同）时清理派生态
      if (!workflowRun.value || workflowRun.value.id !== response.data?.id) {
        clearWorkflowDerivedState()
      }
      workflowRun.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '查询工作流失败'
      throw err
    } finally {
      workflowLoading.value = false
    }
  }

  async function adoptWorkflowRun(id, data) {
    workflowAdoptLoading.value = true
    error.value = ''
    try {
      const response = await aiApi.adoptWorkflowRun(id, data)
      workflowAdoptResult.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '采纳工作流失败'
      throw err
    } finally {
      workflowAdoptLoading.value = false
    }
  }

  async function planWorkflowExecution(id, data) {
    workflowExecutionLoading.value = true
    error.value = ''
    try {
      const response = await aiApi.planWorkflowExecution(id, data)
      workflowExecutionPlan.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '生成执行计划失败'
      throw err
    } finally {
      workflowExecutionLoading.value = false
    }
  }

  async function confirmWorkflowExecution(id, data) {
    workflowExecutionConfirmLoading.value = true
    error.value = ''
    try {
      const response = await aiApi.confirmWorkflowExecution(id, data)
      workflowExecutionConfirmResult.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '确认执行计划失败'
      throw err
    } finally {
      workflowExecutionConfirmLoading.value = false
    }
  }

  async function analyzeWorkflowExecution(id, data) {
    workflowExecutionAnalysisLoading.value = true
    error.value = ''
    try {
      const response = await aiApi.analyzeWorkflowExecution(id, data)
      workflowExecutionAnalysis.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '执行结果分析失败'
      throw err
    } finally {
      workflowExecutionAnalysisLoading.value = false
    }
  }

  // ── 七期 A：按业务来源查询 / 从需求启动 ──────────────────────

  async function fetchWorkflowTrace(params = {}) {
    if (!params || !params.origin_module || !params.origin_type || !params.origin_id) {
      workflowTraceItems.value = []
      workflowTraceTotal.value = 0
      return { items: [], total: 0 }
    }
    workflowTraceLoading.value = true
    error.value = ''
    try {
      const response = await aiApi.listWorkflowsBySource({
        origin_module: params.origin_module,
        origin_type: params.origin_type,
        origin_id: params.origin_id,
        limit: params.limit || 5,
      })
      workflowTraceItems.value = response.data?.items || []
      workflowTraceTotal.value = response.data?.total || 0
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '查询 workflow trace 失败'
      throw err
    } finally {
      workflowTraceLoading.value = false
    }
  }

  async function startWorkflowFromRequirements(data) {
    workflowLoading.value = true
    error.value = ''
    try {
      const response = await aiApi.startWorkflowFromRequirements(data)
      // 与 startRequirementWorkflow 行为对齐：先清理派生态再覆盖 workflowRun
      clearWorkflowDerivedState()
      workflowRun.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '从需求启动 workflow 失败'
      throw err
    } finally {
      workflowLoading.value = false
    }
  }

  return {
    // State
    aiConfig,
    configLoading,
    templates,
    templateTotal,
    templatePage,
    templatePageSize,
    currentTemplate,
    variantResult,
    assertionResult,
    failureResult,
    summaryResult,
    requirementAnalysisResult,
    currentAnalysis,
    suggestions,
    suggestionTotal,
    workflowRun,
    workflowLoading,
    workflowAdoptResult,
    workflowAdoptLoading,
    workflowExecutionPlan,
    workflowExecutionLoading,
    workflowExecutionConfirmResult,
    workflowExecutionConfirmLoading,
    workflowExecutionAnalysis,
    workflowExecutionAnalysisLoading,
    workflowTraceItems,
    workflowTraceTotal,
    workflowTraceLoading,
    loading,
    error,
    // Actions: Config
    fetchConfig,
    saveConfig,
    testConnection,
    // Actions: Templates
    fetchTemplates,
    createTemplate,
    updateTemplate,
    deleteTemplate,
    // Actions: Generation
    generateVariants,
    generateAssertions,
    analyzeFailure,
    summarizeReport,
    // Actions: Analysis
    fetchAnalysis,
    fetchSuggestions,
    acceptSuggestion,
    rejectSuggestion,
    runRequirementAnalysis,
    runAssetUnderstand,
    runDesignTests,
    runFailureAgent,
    runReleaseAdvice,
    // Actions: Workflow
    startRequirementWorkflow,
    fetchWorkflowRun,
    clearWorkflowDerivedState,
    adoptWorkflowRun,
    planWorkflowExecution,
    confirmWorkflowExecution,
    analyzeWorkflowExecution,
    // 七期 A
    fetchWorkflowTrace,
    startWorkflowFromRequirements,
  }
})
