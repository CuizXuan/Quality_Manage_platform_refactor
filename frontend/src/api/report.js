/**
 * Report API — 报告 / 缺陷 / 质量门禁 前端接口封装
 */
import client from './client'

export const reportApi = {
  // ── Report ───────────────────────────────────────────────────

  list(params) {
    return client.get('/api/reports', { params })
  },
  get(id) {
    return client.get(`/api/reports/${id}`)
  },
  create(data) {
    return client.post('/api/reports', data)
  },
  update(id, data) {
    return client.put(`/api/reports/${id}`, data)
  },
  delete(id) {
    return client.delete(`/api/reports/${id}`)
  },

  // ── Defect ───────────────────────────────────────────────────

  listDefects(params) {
    return client.get('/api/reports/defects', { params })
  },
  getDefect(id) {
    return client.get(`/api/reports/defects/${id}`)
  },
  createDefect(data) {
    return client.post('/api/reports/defects', data)
  },
  updateDefect(id, data) {
    return client.put(`/api/reports/defects/${id}`, data)
  },
  deleteDefect(id) {
    return client.delete(`/api/reports/defects/${id}`)
  },
  transitionDefect(id, data) {
    return client.post(`/api/reports/defects/${id}/transition`, data)
  },
  getDefectStats(params) {
    return client.get('/api/reports/defects/stats/summary', { params })
  },

  // ── QualityGate ──────────────────────────────────────────────

  listQualityGates(params) {
    return client.get('/api/reports/quality-gates', { params })
  },
  getQualityGate(id) {
    return client.get(`/api/reports/quality-gates/${id}`)
  },
  createQualityGate(data) {
    return client.post('/api/reports/quality-gates', data)
  },
  updateQualityGate(id, data) {
    return client.put(`/api/reports/quality-gates/${id}`, data)
  },
  deleteQualityGate(id) {
    return client.delete(`/api/reports/quality-gates/${id}`)
  },
  evaluateQualityGate(id, data) {
    return client.post(`/api/reports/quality-gates/${id}/evaluate`, data)
  },
  evaluateAllQualityGates(params, data) {
    return client.post('/api/reports/quality-gates/evaluate-all', data, { params })
  },
}
