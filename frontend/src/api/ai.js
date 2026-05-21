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

  summarizeReport(data) {
    return client.post('/api/ai/summarize-report', data)
  },

  // ── Suggestions & Analysis ─────────────────────────────────────

  acceptSuggestion(id, data = {}) {
    return client.post(`/api/ai/suggestions/${id}/accept`, data)
  },

  getAnalysis(id) {
    return client.get(`/api/ai/analysis/${id}`)
  },
}
