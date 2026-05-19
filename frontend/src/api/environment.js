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

export const environmentsApi = {
  list: () => client.get('/environments'),
  get: (id) => client.get('/environments/' + id),
  create: (data) => client.post('/environments', data),
  update: (id, data) => client.put('/environments/' + id, data),
  delete: (id) => client.delete('/environments/' + id),
  setDefault: (id) => client.post('/environments/' + id + '/set-default'),
}

export default client
