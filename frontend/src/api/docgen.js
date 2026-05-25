/**
 * DocGen API — 文档生成中心前端接口封装
 */
import client from './client'

export const docgenApi = {
  // ── Task ───────────────────────────────────────────────────────

  listTasks(params) {
    return client.get('/api/docgen/tasks', { params })
  },
  getTask(id) {
    return client.get(`/api/docgen/tasks/${id}`)
  },
  downloadTaskFile(taskId) {
    return client.get(`/api/docgen/tasks/download/${taskId}`, { responseType: 'blob' })
  },

  // ── Rule ───────────────────────────────────────────────────────

  listRules(params) {
    return client.get('/api/docgen/rules', { params })
  },
  getRule(id) {
    return client.get(`/api/docgen/rules/${id}`)
  },
  createRule(data) {
    return client.post('/api/docgen/rules', data)
  },
  updateRule(id, data) {
    return client.put(`/api/docgen/rules/${id}`, data)
  },
  deleteRule(id) {
    return client.delete(`/api/docgen/rules/${id}`)
  },

  // ── Template ───────────────────────────────────────────────────

  listTemplates(params) {
    return client.get('/api/docgen/templates', { params })
  },
  uploadTemplate(file) {
    const formData = new FormData()
    formData.append('file', file)
    return client.post('/api/docgen/templates/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  deleteTemplate(id) {
    return client.delete(`/api/docgen/templates/${id}`)
  },

  // ── Uploaded Files ─────────────────────────────────────────────

  listUploads() {
    return client.get('/api/docgen/uploads')
  },
  uploadFile(file) {
    const formData = new FormData()
    formData.append('file', file)
    return client.post('/api/docgen/uploads/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  // ── Requirement Doc ─────────────────────────────────────────────

  previewRequirement(data) {
    return client.post('/api/docgen/requirement/preview', data)
  },
  generateRequirement(data) {
    return client.post('/api/docgen/requirement/generate', data)
  },
  generateRequirementAsync(data) {
    return client.post('/api/docgen/requirement/generate-async', data)
  },

  // ── Database Doc ───────────────────────────────────────────────

  previewDatabase(data) {
    return client.post('/api/docgen/database/preview', data)
  },
  generateDatabase(data) {
    return client.post('/api/docgen/database/generate', data)
  },
  generateDatabaseAsync(data) {
    return client.post('/api/docgen/database/generate-async', data)
  },

  // ── API Doc ─────────────────────────────────────────────────────

  previewApi(data) {
    return client.post('/api/docgen/api/preview', data)
  },
  generateApi(data) {
    return client.post('/api/docgen/api/generate', data)
  },
  generateApiAsync(data) {
    return client.post('/api/docgen/api/generate-async', data)
  },
}