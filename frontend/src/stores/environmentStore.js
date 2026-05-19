import { defineStore } from 'pinia'
import { ref } from 'vue'
import { environmentsApi } from '../api/environment'
import { useToastStore } from './toast'

export const useEnvironmentStore = defineStore('environment', () => {
  const environments = ref([])
  const loading = ref(false)

  async function fetchEnvironments() {
    loading.value = true
    try {
      const res = await environmentsApi.list()
      environments.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function createEnvironment(data) {
    const res = await environmentsApi.create(data)
    environments.value.push(res.data)
    const toast = useToastStore()
    toast.addToast({
      id: Date.now(),
      type: 'success',
      title: '创建成功',
      message: `环境"${data.name}"已创建`,
      duration: 3000
    })
    return res.data
  }

  async function updateEnvironment(id, data) {
    const res = await environmentsApi.update(id, data)
    const idx = environments.value.findIndex(e => e.id === id)
    if (idx !== -1) environments.value[idx] = res.data
    const toast = useToastStore()
    toast.addToast({
      id: Date.now(),
      type: 'success',
      title: '更新成功',
      message: '环境信息已保存',
      duration: 3000
    })
    return res.data
  }

  async function deleteEnvironment(id) {
    await environmentsApi.delete(id)
    environments.value = environments.value.filter(e => e.id !== id)
    const toast = useToastStore()
    toast.addToast({
      id: Date.now(),
      type: 'success',
      title: '删除成功',
      message: '环境已删除',
      duration: 3000
    })
  }

  async function setDefault(id) {
    await environmentsApi.setDefault(id)
    environments.value.forEach(e => {
      e.is_default = e.id === id
    })
    const toast = useToastStore()
    toast.addToast({
      id: Date.now(),
      type: 'success',
      title: '设置成功',
      message: '已设为默认环境',
      duration: 3000
    })
  }

  function getDefault() {
    return environments.value.find(e => e.is_default)
  }

  return {
    environments, loading,
    fetchEnvironments, createEnvironment, updateEnvironment, deleteEnvironment, setDefault, getDefault,
  }
})
