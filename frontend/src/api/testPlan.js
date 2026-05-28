import client from './client'

export const testPlanApi = {
  // Plans
  listPlans(params) {
    return client.get('/api/test-plans', { params })
  },
  getPlan(id) {
    return client.get(`/api/test-plans/${id}`)
  },
  createPlan(data) {
    return client.post('/api/test-plans', data)
  },
  updatePlan(id, data) {
    return client.put(`/api/test-plans/${id}`, data)
  },
  deletePlan(id) {
    return client.delete(`/api/test-plans/${id}`)
  },

  // Suites
  listSuites(planId) {
    return client.get(`/api/test-plans/${planId}/suites`)
  },
  createSuite(planId, data) {
    return client.post(`/api/test-plans/${planId}/suites`, data)
  },
  updateSuite(suiteId, data) {
    return client.put(`/api/test-plans/suites/${suiteId}`, data)
  },
  deleteSuite(suiteId) {
    return client.delete(`/api/test-plans/suites/${suiteId}`)
  },

  // Suite Items
  addSuiteItem(data) {
    return client.post('/api/test-plans/suites/items', data)
  },
  removeSuiteItem(itemId) {
    return client.delete(`/api/test-plans/suites/items/${itemId}`)
  },

  // Runs
  runPlan(planId) {
    return client.post(`/api/test-plans/${planId}/run`)
  },
  listRuns(params) {
    return client.get('/api/test-plans/runs', { params })
  },
  getRun(runId) {
    return client.get(`/api/test-plans/runs/${runId}`)
  },
}