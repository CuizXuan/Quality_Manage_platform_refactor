import client from './client'

export const importAssetApi = {
  importOpenapi(data) {
    return client.post('/api/import/openapi', data)
  },
  importPostman(data) {
    return client.post('/api/import/postman', data)
  },
  importApifox(data) {
    return client.post('/api/import/apifox', data)
  },
  listJobs() {
    return client.get('/api/import/jobs')
  },
}
