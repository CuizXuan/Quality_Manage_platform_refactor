/**
 * AI API — AI中枢前端接口封装
 */
import client from './client'

export const aiApi = {
  // ── AI Config ─────────────────────────────────────────────────

  getConfig() {
    return client.get('/api/ai/config')
  },

  updateConfig(data) {
    return client.put('/api/ai/config', data)
  },

  testConnection() {
    return client.post('/api/ai/config/test')
  },

  // ── Prompt Templates ───────────────────────────────────────────

  listTemplates(params) {
    return client.get('/api/ai/templates', { params })
  },

  createTemplate(data) {
    return client.post('/api/ai/templates', data)
  },

  updateTemplate(id, data) {
    return client.put(`/api/ai/templates/${id}`, data)
  },

  deleteTemplate(id) {
    return client.delete(`/api/ai/templates/${id}`)
  },

  // ── AI Generation ──────────────────────────────────────────────

  generateVariants(data) {
    return client.post('/api/ai/generate-variants', data)
  },

  generateAssertions(data) {
    return client.post('/api/ai/generate-assertions', data)
  },

  analyzeFailure(data) {
    return client.post('/api/ai/analyze-failure', data)
  },

  runAssetUnderstand(data) {
    return client.post('/api/ai/agents/asset-understand', data)
  },

  runDesignTests(data) {
    return client.post('/api/ai/agents/design-tests', data)
  },

  runFailureAgent(data) {
    return client.post('/api/ai/agents/analyze-failure', data)
  },

  runReleaseAdvice(data) {
    return client.post('/api/ai/agents/release-advice', data)
  },

  runRequirementAnalysis(data) {
    return client.post('/api/ai/agents/analyze-requirements', data)
  },

  summarizeReport(data) {
    return client.post('/api/ai/summarize-report', data)
  },

  // ── Suggestions & Analysis ─────────────────────────────────────

  listSuggestions(params) {
    return client.get('/api/ai/suggestions', { params })
  },

  acceptSuggestion(id, data = {}) {
    return client.post(`/api/ai/suggestions/${id}/accept`, data)
  },

  rejectSuggestion(id, data = {}) {
    return client.post(`/api/ai/suggestions/${id}/reject`, data)
  },

  getAnalysis(id) {
    return client.get(`/api/ai/analysis/${id}`)
  },

  // ── Multi-Agent Workflow ─────────────────────────────────────

  startRequirementWorkflow(data) {
    return client.post('/api/ai/workflows/requirement-to-test-design', data)
  },

  getWorkflowRun(id) {
    return client.get(`/api/ai/workflows/${id}`)
  },

  adoptWorkflowRun(id, data) {
    return client.post(`/api/ai/workflows/${id}/adopt`, data)
  },

  planWorkflowExecution(id, data) {
    return client.post(`/api/ai/workflows/${id}/execution-plan`, data)
  },

  confirmWorkflowExecution(id, data) {
    return client.post(`/api/ai/workflows/${id}/execution-plan/confirm`, data)
  },

  analyzeWorkflowExecution(id, data) {
    return client.post(`/api/ai/workflows/${id}/execution-analysis`, data)
  },

  // ── 七期 A：按业务来源查询 / 从需求启动 workflow ──────────

  listWorkflowsBySource(params) {
    return client.get('/api/ai/workflows/by-source', { params })
  },

  startWorkflowFromRequirements(data) {
    return client.post('/api/ai/workflows/from-requirements', data)
  },
}
