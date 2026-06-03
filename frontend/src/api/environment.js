import client from './client'

export const environmentApi = {
  list(params = {}) {
    return client.get('/api/environments', { params })
  },
  create(data) {
    return client.post('/api/environments', data)
  },
  render(data) {
    return client.post('/api/environments/render', data)
  },
}
