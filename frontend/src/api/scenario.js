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

export const scenariosApi = {
  list: () => client.get('/scenarios'),
  get: (id) => client.get('/scenarios/' + id),
  create: (data) => client.post('/scenarios', data),
  update: (id, data) => client.put('/scenarios/' + id, data),
  delete: (id) => client.delete('/scenarios/' + id),
  run: (id, data) => client.post('/scenarios/' + id + '/run', data),
  addStep: (scenarioId, data) => client.post('/scenarios/' + scenarioId + '/steps', data),
  updateStep: (scenarioId, stepId, data) => client.put('/scenarios/' + scenarioId + '/steps/' + stepId, data),
  deleteStep: (scenarioId, stepId) => client.delete('/scenarios/' + scenarioId + '/steps/' + stepId),
  reorderSteps: (scenarioId, stepIds) => client.put('/scenarios/' + scenarioId + '/steps/reorder', stepIds),
}

export default client
