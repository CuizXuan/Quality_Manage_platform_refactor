import client from './client'

export const caseApi = {
  /** List test cases with pagination */
  list(params) {
    return client.get('/api/testcase', { params })
  },

  /** Get a test case by ID */
  get(id) {
    return client.get(`/api/testcase/${id}`)
  },

  /** Create a test case */
  create(data) {
    return client.post('/api/testcase', data)
  },

  /** Update a test case */
  update(id, data) {
    return client.put(`/api/testcase/${id}`, data)
  },

  /** Delete a test case */
  delete(id) {
    return client.delete(`/api/testcase/${id}`)
  },

  /** List variants for a test case */
  listVariants(id, params) {
    return client.get(`/api/testcase/${id}/variant`, { params })
  },

  /** Create a variant for a test case */
  createVariant(id, data) {
    return client.post(`/api/testcase/${id}/variant`, data)
  },

  /** List folders */
  listFolders(params) {
    return client.get('/api/case/folders', { params })
  },

  /** Create a folder */
  createFolder(data) {
    return client.post('/api/case/folders', data)
  },

  /** Update a folder */
  updateFolder(id, data) {
    return client.put(`/api/case/folders/${id}`, data)
  },

  /** Delete a folder */
  deleteFolder(id) {
    return client.delete(`/api/case/folders/${id}`)
  },
}
