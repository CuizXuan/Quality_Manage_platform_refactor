import { defineStore } from 'pinia'
import { ref } from 'vue'
import { scenariosApi } from '../api/scenario'
import { useToastStore } from './toast'

export const useScenarioStore = defineStore('scenario', () => {
  const scenarios = ref([])
  const loading = ref(false)

  async function fetchScenarios() {
    loading.value = true
    try {
      const res = await scenariosApi.list()
      scenarios.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function createScenario(data) {
    const res = await scenariosApi.create(data)
    scenarios.value.push(res.data)
    const toast = useToastStore()
    toast.addToast({
      id: Date.now(),
      type: 'success',
      title: '创建成功',
      message: `场景"${data.name}"已创建`,
      duration: 3000
    })
    return res.data
  }

  async function updateScenario(id, data) {
    const res = await scenariosApi.update(id, data)
    const idx = scenarios.value.findIndex(s => s.id === id)
    if (idx !== -1) scenarios.value[idx] = res.data
    const toast = useToastStore()
    toast.addToast({
      id: Date.now(),
      type: 'success',
      title: '更新成功',
      message: '场景信息已保存',
      duration: 3000
    })
    return res.data
  }

  async function deleteScenario(id) {
    await scenariosApi.delete(id)
    scenarios.value = scenarios.value.filter(s => s.id !== id)
    const toast = useToastStore()
    toast.addToast({
      id: Date.now(),
      type: 'success',
      title: '删除成功',
      message: '场景已删除',
      duration: 3000
    })
  }

  async function addStep(scenarioId, data) {
    const res = await scenariosApi.addStep(scenarioId, data)
    return res.data
  }

  async function updateStep(scenarioId, stepId, data) {
    const res = await scenariosApi.updateStep(scenarioId, stepId, data)
    return res.data
  }

  async function deleteStep(scenarioId, stepId) {
    await scenariosApi.deleteStep(scenarioId, stepId)
  }

  async function runScenario(id, data = {}) {
    const res = await scenariosApi.run(id, data)
    return res.data
  }

  return {
    scenarios, loading,
    fetchScenarios, createScenario, updateScenario, deleteScenario,
    addStep, updateStep, deleteStep, runScenario,
  }
})
