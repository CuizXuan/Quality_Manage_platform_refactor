import client from './client'

export const terminalApi = {
  /** Send a debug request */
  debug(data) {
    return client.post('/api/terminal/debug', data)
  },

  /** Get debug history */
  getHistory(params) {
    return client.get('/api/terminal/history', { params })
  },

  /** Get a specific request with result */
  getRequest(id) {
    return client.get(`/api/terminal/history/${id}`)
  },

  /** Toggle favorite */
  toggleFavorite(id) {
    return client.post(`/api/terminal/history/${id}/favorite`)
  },

  /** Delete a request */
  deleteRequest(id) {
    return client.delete(`/api/terminal/history/${id}`)
  },
}
