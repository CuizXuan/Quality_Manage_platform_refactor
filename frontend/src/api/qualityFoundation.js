/**
 * Quality Foundation API - 质量基础接口封装
 */
import client from './client'

export const qualityFoundationApi = {
  // ── Projects ──────────────────────────────────────────────────

  listProjects(params) {
    return client.get('/api/foundation/projects', { params })
  },
  getProject(id) {
    return client.get(`/api/foundation/projects/${id}`)
  },
  createProject(data) {
    return client.post('/api/foundation/projects', data)
  },
  updateProject(id, data) {
    return client.put(`/api/foundation/projects/${id}`, data)
  },
  deleteProject(id) {
    return client.delete(`/api/foundation/projects/${id}`)
  },

  // ── Versions ───────────────────────────────────────────────────

  listVersions(params) {
    return client.get('/api/foundation/versions', { params })
  },
  getVersion(id) {
    return client.get(`/api/foundation/versions/${id}`)
  },
  createVersion(data) {
    return client.post('/api/foundation/versions', data)
  },
  updateVersion(id, data) {
    return client.put(`/api/foundation/versions/${id}`, data)
  },
  deleteVersion(id) {
    return client.delete(`/api/foundation/versions/${id}`)
  },

  // ── Iterations ────────────────────────────────────────────────

  listIterations(params) {
    return client.get('/api/foundation/iterations', { params })
  },
  getIteration(id) {
    return client.get(`/api/foundation/iterations/${id}`)
  },
  createIteration(data) {
    return client.post('/api/foundation/iterations', data)
  },
  updateIteration(id, data) {
    return client.put(`/api/foundation/iterations/${id}`, data)
  },
  deleteIteration(id) {
    return client.delete(`/api/foundation/iterations/${id}`)
  },

  // ── Requirements ───────────────────────────────────────────────

  listRequirements(params) {
    return client.get('/api/foundation/requirements', { params })
  },
  getRequirement(id) {
    return client.get(`/api/foundation/requirements/${id}`)
  },
  createRequirement(data) {
    return client.post('/api/foundation/requirements', data)
  },
  updateRequirement(id, data) {
    return client.put(`/api/foundation/requirements/${id}`, data)
  },
  deleteRequirement(id) {
    return client.delete(`/api/foundation/requirements/${id}`)
  },
  getRequirementCoverage(params) {
    return client.get('/api/foundation/requirements/coverage', { params })
  },
}