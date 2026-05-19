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

export const mockApi = {
  list: (params = {}) => client.get('/mocks', { params }),
  get: (id) => client.get('/mocks/' + id),
  create: (data) => client.post('/mocks', data),
  update: (id, data) => client.put('/mocks/' + id, data),
  delete: (id) => client.delete('/mocks/' + id),
  toggle: (id, enabled) => client.post('/mocks/' + id + '/toggle', { enabled }),
}

export default client
