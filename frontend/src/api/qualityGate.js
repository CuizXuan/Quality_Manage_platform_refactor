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

export const qualityGateApi = {
  list: () => client.get('/quality-gates'),
  get: (id) => client.get('/quality-gates/' + id),
  create: (data) => client.post('/quality-gates', data),
  update: (id, data) => client.put('/quality-gates/' + id, data),
  delete: (id) => client.delete('/quality-gates/' + id),
  evaluate: (id, extra = {}) => client.post('/quality-gates/' + id + '/evaluate', null, { params: extra }),
  results: (id) => client.get('/quality-gates/' + id + '/results'),
}

export default client
