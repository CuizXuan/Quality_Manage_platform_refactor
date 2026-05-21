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

  async function acceptSuggestion(id, comment) {
    try {
      await aiApi.acceptSuggestion(id, { accepted_comment: comment })
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '采纳建议失败'
      throw err
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
    currentAnalysis,
    suggestions,
    suggestionTotal,
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
    acceptSuggestion,
  }
})
