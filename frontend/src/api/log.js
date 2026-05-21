import client from './client'

export const logApi = {
  list: (params = {}) => client.get('/api/logs', { params }),
}
