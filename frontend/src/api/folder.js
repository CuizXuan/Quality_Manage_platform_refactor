import axios from 'axios'

const authInterceptor = config => {
  const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
  if (token) config.headers.Authorization = 'Bearer ' + token
  return config
}

const client = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

client.interceptors.request.use(authInterceptor)

export const foldersApi = {
  getTree: () => client.get('/folders'),
}

export default client
