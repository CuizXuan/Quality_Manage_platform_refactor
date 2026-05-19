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

export const datasetApi = {
  list: (params = {}) => client.get('/datasets', { params }),
  get: (id) => client.get('/datasets/' + id),
  getPreview: (id, params = {}) => client.get('/datasets/' + id + '/preview', { params }),
  create: (data) => client.post('/datasets', data),
  update: (id, data) => client.put('/datasets/' + id, data),
  delete: (id) => client.delete('/datasets/' + id),
}

export default client
