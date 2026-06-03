import { ref } from 'vue'
import { defineStore } from 'pinia'
import { importAssetApi } from '@/api/importAsset'

export const useImportAssetStore = defineStore('importAsset', () => {
  const jobs = ref([])
  const loading = ref(false)
  const error = ref('')

  async function fetchJobs() {
    loading.value = true
    error.value = ''
    try {
      const response = await importAssetApi.listJobs()
      jobs.value = response.data || []
      return jobs.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取导入任务失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function importDocument(sourceType, data) {
    loading.value = true
    error.value = ''
    try {
      let response
      if (sourceType === 'postman') response = await importAssetApi.importPostman(data)
      else if (sourceType === 'apifox') response = await importAssetApi.importApifox(data)
      else response = await importAssetApi.importOpenapi(data)
      await fetchJobs()
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '导入失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    jobs,
    loading,
    error,
    fetchJobs,
    importDocument,
  }
})
