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

export const coverageApi = {
  upload: (formData, extra = {}) => client.post('/coverage/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    params: extra,
  }),
  summary: (params) => client.get('/coverage/summary', { params }),
  fileList: (repositoryId) => client.get('/coverage/files', {
    params: { repository_id: repositoryId },
  }),
}

export default client
