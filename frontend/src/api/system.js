import client from './client'

export const systemApi = {
  users: {
    list: () => client.get('/api/system/users'),
    create: (data) => client.post('/api/system/users', data),
    update: (id, data) => client.put(`/api/system/users/${id}`, data),
    delete: (id) => client.delete(`/api/system/users/${id}`),
  },
  roles: {
    list: () => client.get('/api/system/roles'),
    create: (data) => client.post('/api/system/roles', data),
    update: (id, data) => client.put(`/api/system/roles/${id}`, data),
    delete: (id) => client.delete(`/api/system/roles/${id}`),
  },
  organizations: {
    list: () => client.get('/api/system/organizations'),
    create: (data) => client.post('/api/system/organizations', data),
    update: (id, data) => client.put(`/api/system/organizations/${id}`, data),
    delete: (id) => client.delete(`/api/system/organizations/${id}`),
  },
  menus: {
    list: () => client.get('/api/system/menus'),
    create: (data) => client.post('/api/system/menus', data),
    update: (id, data) => client.put(`/api/system/menus/${id}`, data),
    delete: (id) => client.delete(`/api/system/menus/${id}`),
  },
}

