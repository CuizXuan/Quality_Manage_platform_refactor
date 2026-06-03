import client from './client'

export const apiAssetApi = {
  // Groups
  listGroups(params) {
    return client.get('/api/assets/groups', { params })
  },
  createGroup(data) {
    return client.post('/api/assets/groups', data)
  },
  updateGroup(id, data) {
    return client.put(`/api/assets/groups/${id}`, data)
  },
  deleteGroup(id) {
    return client.delete(`/api/assets/groups/${id}`)
  },

  // APIs
  listApis(params) {
    return client.get('/api/assets/apis', { params })
  },
  getApi(id) {
    return client.get(`/api/assets/apis/${id}`)
  },
  listServices(params) {
    return client.get('/api/assets/services', { params })
  },
  createApi(data) {
    return client.post('/api/assets/apis', data)
  },
  updateApi(id, data) {
    return client.put(`/api/assets/apis/${id}`, data)
  },
  deleteApi(id) {
    return client.delete(`/api/assets/apis/${id}`)
  },
  getDebugPayload(id) {
    return client.get(`/api/assets/apis/${id}/debug-payload`)
  },
  getDiff(id) {
    return client.get(`/api/assets/apis/${id}/diff`)
  },
  generateCase(id) {
    return client.post(`/api/assets/apis/${id}/generate-case`)
  },
  generateBaseline(id) {
    return client.post(`/api/assets/apis/${id}/generate-baseline`)
  },

  // Import/Export
  importOpenapi(data) {
    return client.post('/api/assets/import/openapi', data)
  },
  exportOpenapi(params) {
    return client.get('/api/assets/export/openapi', { params })
  },
}
