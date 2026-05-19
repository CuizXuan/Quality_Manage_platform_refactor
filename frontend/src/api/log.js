import axios from 'axios'

const authInterceptor = config => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = 'Bearer ' + token
  return config
}

const client = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

client.interceptors.request.use(authInterceptor)

export const logsApi = {
  list: (params = {}) => client.get('/logs', { params }),
  get: (id) => client.get('/logs/' + id),
  delete: (id) => client.delete('/logs/' + id),
  batchDelete: (ids) => client.post('/logs/batch-delete', ids),
}

export default client
