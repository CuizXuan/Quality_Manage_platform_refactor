import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { caseApi } from '@/api/case'

export const useCaseStore = defineStore('case', () => {
  // State
  const cases = ref([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const currentCase = ref(null)
  const variants = ref([])
  const variantTotal = ref(0)
  const variantPage = ref(1)
  const variantPageSize = ref(20)
  const loading = ref(false)
  const error = ref('')
  const caseType = ref('api') // 'functional' | 'api'
  const folders = ref([])

  // Getters
  const hasCases = computed(() => cases.value.length > 0)

  // Actions
  async function fetchCases(params = {}) {
    loading.value = true
    error.value = ''
    try {
      const queryParams = {
        case_type: params.case_type || caseType.value,
        page: params.page || page.value,
        page_size: params.page_size || pageSize.value,
        ...(params.folder_id && { folder_id: params.folder_id }),
        ...(params.keyword && { keyword: params.keyword }),
      }
      const response = await caseApi.list(queryParams)
      cases.value = response.data.items
      total.value = response.data.total
      page.value = response.data.page
      pageSize.value = response.data.page_size
      return cases.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取用例列表失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchFolders() {
    try {
      const response = await caseApi.listFolders({ case_type: caseType.value })
      folders.value = response.data.items
      return folders.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取分类失败'
      throw err
    }
  }

  async function fetchCase(id) {
    loading.value = true
    error.value = ''
    try {
      const response = await caseApi.get(id)
      currentCase.value = response.data
      return currentCase.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取用例详情失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createCase(data) {
    loading.value = true
    error.value = ''
    try {
      const response = await caseApi.create(data)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '创建用例失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateCase(id, data) {
    loading.value = true
    error.value = ''
    try {
      const response = await caseApi.update(id, data)
      currentCase.value = response.data
      return currentCase.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '更新用例失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteCase(id) {
    loading.value = true
    error.value = ''
    try {
      await caseApi.delete(id)
      cases.value = cases.value.filter(c => c.id !== id)
      if (currentCase.value?.id === id) {
        currentCase.value = null
      }
      total.value = Math.max(0, total.value - 1)
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '删除用例失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchVariants(caseId, params = {}) {
    loading.value = true
    error.value = ''
    try {
      const queryParams = {
        page: params.page || variantPage.value,
        page_size: params.page_size || variantPageSize.value,
        ...(params.variant_type && { variant_type: params.variant_type }),
      }
      const response = await caseApi.listVariants(caseId, queryParams)
      variants.value = response.data.items
      variantTotal.value = response.data.total
      variantPage.value = response.data.page
      variantPageSize.value = response.data.page_size
      return variants.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取变体列表失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createVariant(caseId, data) {
    loading.value = true
    error.value = ''
    try {
      const response = await caseApi.createVariant(caseId, data)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '创建变体失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  function clearCurrentCase() {
    currentCase.value = null
    variants.value = []
    variantTotal.value = 0
  }

  return {
    // State
    cases,
    total,
    page,
    pageSize,
    currentCase,
    variants,
    variantTotal,
    variantPage,
    variantPageSize,
    loading,
    error,
    caseType,
    folders,
    // Getters
    hasCases,
    // Actions
    fetchCases,
    fetchFolders,
    fetchCase,
    createCase,
    updateCase,
    deleteCase,
    fetchVariants,
    createVariant,
    clearCurrentCase,
  }
})
