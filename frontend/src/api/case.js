import axios from 'axios'

const authInterceptor = config => {
  const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
  if (token) config.headers.Authorization = 'Bearer ' + token
  return config
}

const client = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

client.interceptors.request.use(authInterceptor)

export const casesApi = {
  list: (params = {}) => client.get('/cases', { params }),
  get: (id) => client.get('/cases/' + id),
  create: (data) => client.post('/cases', data),
  update: (id, data) => client.put('/cases/' + id, data),
  delete: (id) => client.delete('/cases/' + id),
  duplicate: (id) => client.post('/cases/' + id + '/duplicate'),
  batchDelete: (ids) => client.post('/cases/batch-delete', ids),
  run: (id, data) => client.post('/cases/' + id + '/run', data),
}

export default client
