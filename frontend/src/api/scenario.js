/**
 * Scenario API — 场景编排前端接口封装
 */
import client from './client'

export const scenarioApi = {
  // ── Scenario CRUD ────────────────────────────────────────────

  list(params) {
    return client.get('/api/scenario', { params })
  },
  get(id) {
    return client.get(`/api/scenario/${id}`)
  },
  create(data) {
    return client.post('/api/scenario', data)
  },
  update(id, data) {
    return client.put(`/api/scenario/${id}`, data)
  },
  delete(id) {
    return client.delete(`/api/scenario/${id}`)
  },

  // ── Steps ───────────────────────────────────────────────────

  addStep(scenarioId, data) {
    return client.post(`/api/scenario/${scenarioId}/steps`, data)
  },
  updateStep(stepId, data) {
    return client.put(`/api/scenario/steps/${stepId}`, data)
  },
  deleteStep(stepId) {
    return client.delete(`/api/scenario/steps/${stepId}`)
  },
  reorderSteps(scenarioId, stepIds) {
    return client.post(`/api/scenario/${scenarioId}/steps/reorder`, stepIds)
  },

  // ── Execution ────────────────────────────────────────────────

  startExecution(scenarioId, params = {}) {
    return client.post(`/api/scenario/${scenarioId}/run`, null, { params })
  },
  getExecution(runId) {
    return client.get(`/api/scenario/runs/${runId}`)
  },
  listExecutions(params) {
    return client.get('/api/scenario/runs', { params })
  },
}
