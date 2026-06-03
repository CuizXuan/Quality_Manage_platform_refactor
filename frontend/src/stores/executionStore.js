import { ref } from 'vue'
import { defineStore } from 'pinia'
import { executionApi } from '@/api/execution'

export const useExecutionStore = defineStore('execution', () => {
  const runs = ref([])
  const total = ref(0)
  const currentRun = ref(null)
  const artifacts = ref([])
  const loading = ref(false)
  const error = ref('')

  async function fetchRuns(params = {}) {
    loading.value = true
    error.value = ''
    try {
      const response = await executionApi.listRuns(params)
      runs.value = response.data.items || []
      total.value = response.data.total || 0
      return runs.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取执行列表失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createRun(data) {
    loading.value = true
    error.value = ''
    try {
      const response = await executionApi.createRun(data)
      currentRun.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '创建执行失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchRun(id) {
    loading.value = true
    error.value = ''
    try {
      const response = await executionApi.getRun(id)
      currentRun.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取执行详情失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchArtifacts(id) {
    loading.value = true
    error.value = ''
    try {
      const response = await executionApi.listArtifacts(id)
      artifacts.value = response.data || []
      return artifacts.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取执行产物失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function cancelRun(id) {
    const response = await executionApi.cancelRun(id)
    currentRun.value = response.data
    return response.data
  }

  async function rerunFailed(id) {
    const response = await executionApi.rerunFailed(id)
    currentRun.value = response.data
    return response.data
  }

  return {
    runs,
    total,
    currentRun,
    artifacts,
    loading,
    error,
    fetchRuns,
    createRun,
    fetchRun,
    fetchArtifacts,
    cancelRun,
    rerunFailed,
  }
})
