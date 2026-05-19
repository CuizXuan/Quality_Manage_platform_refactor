import { defineStore } from 'pinia'
import { ref } from 'vue'
import { casesApi } from '../api/case'
import { getCaseFolders } from '../api/caseFolders'
import { useToastStore } from './toast'

export const useCaseStore = defineStore('case', () => {
  const cases = ref([])
  const folders = ref([])
  const loading = ref(false)
  const fetchError = ref(null)
  const currentCase = ref(null)

  async function fetchCases(params = {}) {
    loading.value = true
    fetchError.value = null
    try {
      const res = await casesApi.list(params)
      cases.value = res.data
    } catch (e) {
      fetchError.value = e?.response?.data?.detail || e.message || '加载失败'
    } finally {
      loading.value = false
    }
  }

  async function fetchFolders() {
    try {
      const res = await getCaseFolders()
      folders.value = res.data
    } catch (e) {
      // silent fail for folders
    }
  }

  async function createCase(data) {
    const res = await casesApi.create(data)
    cases.value.push(res.data)
    const toast = useToastStore()
    toast.addToast({
      id: Date.now(),
      type: 'success',
      title: '创建成功',
      message: `用例"${data.name}"已创建`,
      duration: 3000
    })
    return res.data
  }

  async function updateCase(id, data) {
    const res = await casesApi.update(id, data)
    const idx = cases.value.findIndex(c => c.id === id)
    if (idx !== -1) cases.value[idx] = res.data
    const toast = useToastStore()
    toast.addToast({
      id: Date.now(),
      type: 'success',
      title: '更新成功',
      message: '用例信息已保存',
      duration: 3000
    })
    return res.data
  }

  async function deleteCase(id) {
    await casesApi.delete(id)
    cases.value = cases.value.filter(c => c.id !== id)
    const toast = useToastStore()
    toast.addToast({
      id: Date.now(),
      type: 'success',
      title: '删除成功',
      message: '用例已删除',
      duration: 3000
    })
  }

  async function duplicateCase(id) {
    const res = await casesApi.duplicate(id)
    cases.value.push(res.data)
    return res.data
  }

  async function runCase(id, data = {}) {
    const res = await casesApi.run(id, data)
    return res.data
  }

  function setCurrentCase(caseData) {
    currentCase.value = caseData
  }

  return {
    cases, folders, loading, fetchError, currentCase,
    fetchCases, fetchFolders, createCase, updateCase, deleteCase, duplicateCase, runCase, setCurrentCase,
  }
})
