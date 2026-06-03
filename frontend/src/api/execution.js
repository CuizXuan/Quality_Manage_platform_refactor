import client from './client'

export const executionApi = {
  listRuns(params = {}) {
    return client.get('/api/executions/runs', { params })
  },
  createRun(data) {
    return client.post('/api/executions/runs', data)
  },
  getRun(id) {
    return client.get(`/api/executions/runs/${id}`)
  },
  cancelRun(id) {
    return client.post(`/api/executions/runs/${id}/cancel`)
  },
  rerunFailed(id) {
    return client.post(`/api/executions/runs/${id}/rerun-failed`)
  },
  streamRun(id) {
    return client.get(`/api/executions/runs/${id}/stream`)
  },
  listArtifacts(id) {
    return client.get(`/api/executions/runs/${id}/artifacts`)
  },
}
