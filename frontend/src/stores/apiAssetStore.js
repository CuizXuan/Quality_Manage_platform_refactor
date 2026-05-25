import { ref } from 'vue'
import { defineStore } from 'pinia'
import { apiAssetApi } from '@/api/apiAsset'

export const useApiAssetStore = defineStore('apiAsset', () => {
  // State
  const groups = ref([])
  const apis = ref([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const loading = ref(false)
  const error = ref('')
  const currentApi = ref(null)
  const selectedGroupId = ref(null)

  // Actions: Groups
  async function fetchGroups(params = {}) {
    loading.value = true
    error.value = ''
    try {
      const response = await apiAssetApi.listGroups(params)
      groups.value = response.data?.items || response.data || []
      return groups.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取分组失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createGroup(data) {
    loading.value = true
    error.value = ''
    try {
      const response = await apiAssetApi.createGroup(data)
      groups.value.push(response.data)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '创建分组失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteGroup(id) {
    loading.value = true
    error.value = ''
    try {
      await apiAssetApi.deleteGroup(id)
      groups.value = groups.value.filter(g => g.id !== id)
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '删除分组失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // Actions: APIs
  async function fetchApis(params = {}) {
    loading.value = true
    error.value = ''
    try {
      const response = await apiAssetApi.listApis({
        page: params.page || page.value,
        page_size: params.page_size || pageSize.value,
        project_id: params.project_id || undefined,
        group_id: params.group_id || undefined,
        keyword: params.keyword || undefined,
        method: params.method || undefined,
        status: params.status || undefined,
      })
      apis.value = response.data?.items || []
      total.value = response.data?.total || 0
      page.value = response.data?.page || 1
      pageSize.value = response.data?.page_size || 20
      return apis.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取 API 列表失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function getDebugPayload(apiId) {
    const response = await apiAssetApi.getDebugPayload(apiId)
    return response.data || response
  }

  async function generateCase(apiId) {
    loading.value = true
    error.value = ''
    try {
      const response = await apiAssetApi.generateCase(apiId)
      return response.data || response
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '生成用例失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function importOpenapi(data) {
    loading.value = true
    error.value = ''
    try {
      const response = await apiAssetApi.importOpenapi(data)
      return response.data || response
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '导入失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createApi(data) {
    loading.value = true
    error.value = ''
    try {
      const response = await apiAssetApi.createApi(data)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '创建 API 失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateApi(id, data) {
    loading.value = true
    error.value = ''
    try {
      const response = await apiAssetApi.updateApi(id, data)
      const idx = apis.value.findIndex(a => a.id === id)
      if (idx !== -1) apis.value[idx] = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '更新 API 失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteApi(id) {
    loading.value = true
    error.value = ''
    try {
      await apiAssetApi.deleteApi(id)
      apis.value = apis.value.filter(a => a.id !== id)
      total.value = Math.max(0, total.value - 1)
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '删除 API 失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  function setSelectedGroup(groupId) {
    selectedGroupId.value = groupId
    if (groupId) {
      fetchApis({ group_id: groupId })
    } else {
      fetchApis({})
    }
  }

  return {
    groups,
    apis,
    total,
    page,
    pageSize,
    loading,
    error,
    currentApi,
    selectedGroupId,
    fetchGroups,
    createGroup,
    deleteGroup,
    fetchApis,
    getDebugPayload,
    generateCase,
    importOpenapi,
    createApi,
    updateApi,
    deleteApi,
    setSelectedGroup,
  }
})