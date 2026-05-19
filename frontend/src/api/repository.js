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

export const repositoryApi = {
  list: () => client.get('/repositories'),
  get: (id) => client.get('/repositories/' + id),
  create: (data) => client.post('/repositories', data),
  update: (id, data) => client.put('/repositories/' + id, data),
  delete: (id) => client.delete('/repositories/' + id),
  sync: (id) => client.post('/repositories/' + id + '/sync'),
}

export default client
