import client from './client'

export const caseApi = {
  list(params) {
    return client.get('/api/case', {
      params,
      paramsSerializer: {
        serialize: serializeParams,
      },
    })
  },
  get(id) {
    return client.get(`/api/case/${id}`)
  },
  create(data) {
    return client.post('/api/case', data)
  },
  update(id, data) {
    return client.put(`/api/case/${id}`, data)
  },
  delete(id) {
    return client.delete(`/api/case/${id}`)
  },
  copy(id) {
    return client.post(`/api/case/${id}/copy`)
  },
  batchUpdate(data) {
    return client.put('/api/case/batch', data)
  },
  batchDelete(ids) {
    return client.post('/api/case/batch-delete', { ids })
  },
  listVariants(id, params) {
    return client.get(`/api/case/${id}/variant`, { params })
  },
  createVariant(id, data) {
    return client.post(`/api/case/${id}/variant`, data)
  },
  listFolders(params) {
    return client.get('/api/case/folders', { params })
  },
  createFolder(data) {
    return client.post('/api/case/folders', data)
  },
  updateFolder(id, data) {
    return client.put(`/api/case/folders/${id}`, data)
  },
  deleteFolder(id) {
    return client.delete(`/api/case/folders/${id}`)
  },
}

function serializeParams(params = {}) {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return
    if (Array.isArray(value)) {
      value.forEach((item) => search.append(key, item))
      return
    }
    search.append(key, value)
  })
  return search.toString()
}
