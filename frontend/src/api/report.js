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

export const reportApi = {
  list: (params = {}) => client.get('/reports', { params }),
  get: (id) => client.get('/reports/' + id),
  generate: (data) => client.post('/reports/generate', data),
  download: (id) => client.get('/reports/' + id + '/download', { responseType: 'blob' }),
  delete: (id) => client.delete('/reports/' + id),
}

export default client
