import client from './client'

export const systemApi = {
  users: {
    list: (params = {}) => client.get('/api/system/users', { params }),
    create: (data) => client.post('/api/system/users', data),
    update: (id, data) => client.put(`/api/system/users/${id}`, data),
    delete: (id) => client.delete(`/api/system/users/${id}`),
  },
  roles: {
    list: (params = {}) => client.get('/api/system/roles', { params }),
    create: (data) => client.post('/api/system/roles', data),
    update: (id, data) => client.put(`/api/system/roles/${id}`, data),
    delete: (id) => client.delete(`/api/system/roles/${id}`),
  },
  organizations: {
    list: (params = {}) => client.get('/api/system/organizations', { params }),
    create: (data) => client.post('/api/system/organizations', data),
    update: (id, data) => client.put(`/api/system/organizations/${id}`, data),
    delete: (id) => client.delete(`/api/system/organizations/${id}`),
  },
  menus: {
    list: (params = {}) => client.get('/api/system/menus', { params }),
    create: (data) => client.post('/api/system/menus', data),
    update: (id, data) => client.put(`/api/system/menus/${id}`, data),
    delete: (id) => client.delete(`/api/system/menus/${id}`),
  },
  dictionaries: {
    list: (params = {}) => client.get('/api/system/dictionaries', { params }),
    create: (data) => client.post('/api/system/dictionaries', data),
    update: (id, data) => client.put(`/api/system/dictionaries/${id}`, data),
    delete: (id) => client.delete(`/api/system/dictionaries/${id}`),
  },
}

