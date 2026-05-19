import { defineStore } from 'pinia'
import { ref } from 'vue'
import { datasetApi } from '../api/dataset'
import { useToastStore } from './toast'

export const useDatasetStore = defineStore('dataset', () => {
  const datasets = ref([])
  const loading = ref(false)
  const currentDataset = ref(null)
  const previewData = ref({ headers: [], rows: [] })

  async function fetchDatasets(params = {}) {
    loading.value = true
    try {
      const res = await datasetApi.list(params)
      datasets.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function createDataset(data) {
    const res = await datasetApi.create(data)
    datasets.value.push(res.data)
    const toast = useToastStore()
    toast.addToast({
      id: Date.now(),
      type: 'success',
      title: '创建成功',
      message: `数据集"${data.name}"已创建`,
      duration: 3000
    })
    return res.data
  }

  async function updateDataset(id, data) {
    const res = await datasetApi.update(id, data)
    const idx = datasets.value.findIndex(d => d.id === id)
    if (idx !== -1) datasets.value[idx] = res.data
    const toast = useToastStore()
    toast.addToast({
      id: Date.now(),
      type: 'success',
      title: '更新成功',
      message: '数据集信息已保存',
      duration: 3000
    })
    return res.data
  }

  async function deleteDataset(id) {
    await datasetApi.delete(id)
    datasets.value = datasets.value.filter(d => d.id !== id)
    const toast = useToastStore()
    toast.addToast({
      id: Date.now(),
      type: 'success',
      title: '删除成功',
      message: '数据集已删除',
      duration: 3000
    })
  }

  async function fetchPreview(id, params = {}) {
    try {
      const res = await datasetApi.getPreview(id, params)
      previewData.value = res.data
    } catch (e) {
      console.error('fetchPreview failed', e)
    }
  }

  function setCurrentDataset(ds) {
    currentDataset.value = ds
  }

  return {
    datasets, loading, currentDataset, previewData,
    fetchDatasets, createDataset, updateDataset, deleteDataset, fetchPreview, setCurrentDataset,
  }
})
