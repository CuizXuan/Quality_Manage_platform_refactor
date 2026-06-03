import { ref } from 'vue'
import { defineStore } from 'pinia'
import { environmentApi } from '@/api/environment'

export const useEnvironmentStore = defineStore('environment', () => {
  const environments = ref([])
  const renderedRequest = ref(null)
  const loading = ref(false)
  const error = ref('')

  async function fetchEnvironments(params = {}) {
    loading.value = true
    error.value = ''
    try {
      const response = await environmentApi.list(params)
      environments.value = response.data || []
      return environments.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取环境列表失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createEnvironment(data) {
    loading.value = true
    error.value = ''
    try {
      const response = await environmentApi.create(data)
      environments.value.push(response.data)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '创建环境失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function renderRequest(data) {
    loading.value = true
    error.value = ''
    try {
      const response = await environmentApi.render(data)
      renderedRequest.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '渲染请求失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    environments,
    renderedRequest,
    loading,
    error,
    fetchEnvironments,
    createEnvironment,
    renderRequest,
  }
})
