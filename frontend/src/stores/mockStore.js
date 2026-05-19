import { defineStore } from 'pinia'
import { ref } from 'vue'
import { mockApi } from '../api/mock'
import { useToastStore } from './toast'

export const useMockStore = defineStore('mock', () => {
  const rules = ref([])
  const loading = ref(false)

  async function fetchRules(params = {}) {
    loading.value = true
    try {
      const res = await mockApi.list(params)
      rules.value = res.data.data || []
    } finally {
      loading.value = false
    }
  }

  async function createRule(data) {
    const res = await mockApi.create(data)
    rules.value.push(res.data.data)
    const toast = useToastStore()
    toast.addToast({
      id: Date.now(),
      type: 'success',
      title: '创建成功',
      message: 'Mock规则已创建',
      duration: 3000
    })
    return res.data.data
  }

  async function updateRule(id, data) {
    const res = await mockApi.update(id, data)
    const idx = rules.value.findIndex(r => r.id === id)
    if (idx !== -1) rules.value[idx] = res.data.data
    const toast = useToastStore()
    toast.addToast({
      id: Date.now(),
      type: 'success',
      title: '更新成功',
      message: 'Mock规则已保存',
      duration: 3000
    })
    return res.data.data
  }

  async function deleteRule(id) {
    await mockApi.delete(id)
    rules.value = rules.value.filter(r => r.id !== id)
    const toast = useToastStore()
    toast.addToast({
      id: Date.now(),
      type: 'success',
      title: '删除成功',
      message: 'Mock规则已删除',
      duration: 3000
    })
  }

  async function toggleRule(id, enabled) {
    const res = await mockApi.toggle(id, enabled)
    const idx = rules.value.findIndex(r => r.id === id)
    if (idx !== -1) rules.value[idx] = res.data.data
    return res.data.data
  }

  return {
    rules, loading,
    fetchRules, createRule, updateRule, deleteRule, toggleRule,
  }
})
