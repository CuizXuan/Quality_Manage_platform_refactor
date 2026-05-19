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

export const defectApi = {
  list: (params) => client.get('/defects', { params }),
  get: (id) => client.get('/defects/' + id),
  create: (data) => client.post('/defects', data),
  update: (id, data) => client.put('/defects/' + id, data),
  delete: (id) => client.delete('/defects/' + id),
  addComment: (id, data) => client.post('/defects/' + id + '/comments', data),
  uploadAttachment: (id, formData) => client.post('/defects/' + id + '/attachments', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  fromExecution: (data) => client.post('/defects/from-execution', data),
  stats: () => client.get('/defects/stats/summary'),
}

export default client
