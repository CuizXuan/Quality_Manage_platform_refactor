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

export const notifyApi = {
  list: (params = {}) => client.get('/notify-channels', { params }),
  get: (id) => client.get('/notify-channels/' + id),
  create: (data) => client.post('/notify-channels', data),
  update: (id, data) => client.put('/notify-channels/' + id, data),
  delete: (id) => client.delete('/notify-channels/' + id),
  test: (id) => client.post('/notify-channels/' + id + '/test'),
}

export default client
