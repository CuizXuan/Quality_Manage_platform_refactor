import client from './client'

// ========== 管理 API（需鉴权）==========

export const dictTypeApi = {
  list: (params = {}) => client.get('/api/system/dict-types', { params }),
  create: (data) => client.post('/api/system/dict-types', data),
  update: (id, data) => client.put(`/api/system/dict-types/${id}`, data),
  delete: (id) => client.delete(`/api/system/dict-types/${id}`),
  getItems: (typeId, params = {}) => client.get(`/api/system/dict-types/${typeId}/items`, { params }),
}

export const dictItemApi = {
  list: (params = {}) => client.get('/api/system/dict-items', { params }),
  create: (data) => client.post('/api/system/dict-items', data),
  update: (id, data) => client.put(`/api/system/dict-items/${id}`, data),
  delete: (id) => client.delete(`/api/system/dict-items/${id}`),
  toggleStatus: (id) => client.put(`/api/system/dict-items/${id}/toggle-status`),
  reorder: (data) => client.put('/api/system/dict-items/reorder', data),
}

// ========== 公开查询 API（无需鉴权，使用无拦截器的 client）==========

import axios from 'axios'

const publicClient = axios.create({
  baseURL: '',
  timeout: 30000,
})

export const dictPublicApi = {
  getByType: (typeCode) => publicClient.get(`/api/dicts/${typeCode}`),
  getAll: () => publicClient.get('/api/dicts'),
}