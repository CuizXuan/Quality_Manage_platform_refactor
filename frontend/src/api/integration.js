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

export const integrationApi = {
  listDefectSystems: () => client.get('/integrations/defect-systems'),
  createDefectSystem: (data) => client.post('/integrations/defect-systems', data),
  updateDefectSystem: (id, data) => client.put('/integrations/defect-systems/' + id, data),
  deleteDefectSystem: (id) => client.delete('/integrations/defect-systems/' + id),
  testConnection: (id) => client.post('/integrations/defect-systems/' + id + '/test'),
  getTypes: () => client.get('/integrations/types'),
}

export default client
