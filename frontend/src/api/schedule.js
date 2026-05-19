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

export const scheduleApi = {
  list: (params = {}) => client.get('/schedules', { params }),
  get: (id) => client.get('/schedules/' + id),
  create: (data) => client.post('/schedules', data),
  update: (id, data) => client.put('/schedules/' + id, data),
  delete: (id) => client.delete('/schedules/' + id),
  toggle: (id, enabled) => client.post('/schedules/' + id + '/toggle', { enabled }),
  run: (id) => client.post('/schedules/' + id + '/run'),
}

export default client
