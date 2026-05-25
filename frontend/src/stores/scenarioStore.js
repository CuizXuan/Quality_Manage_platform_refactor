import { ref } from 'vue'
import { defineStore } from 'pinia'
import { scenarioApi } from '@/api/scenario'

export const useScenarioStore = defineStore('scenario', () => {
  // ── State ────────────────────────────────────────────────────
  const scenarios = ref([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const currentScenario = ref(null)
  const currentSteps = ref([])
  const loading = ref(false)
  const error = ref('')

  // ── Executions ───────────────────────────────────────────────
  const executions = ref([])
  const executionTotal = ref(0)
  const executionPage = ref(1)
  const executionPageSize = ref(20)
  const currentExecution = ref(null)

  // ── Actions: Scenario CRUD ───────────────────────────────────

  async function fetchScenarios(params = {}) {
    loading.value = true
    error.value = ''
    try {
      const response = await scenarioApi.list({
        page: params.page || page.value,
        page_size: params.page_size || pageSize.value,
        keyword: params.keyword || undefined,
        status: params.status || undefined,
        project_id: params.project_id || undefined,
        version_id: params.version_id || undefined,
        iteration_id: params.iteration_id || undefined,
      })
      scenarios.value = response.data.items
      total.value = response.data.total
      page.value = response.data.page
      pageSize.value = response.data.page_size
      return scenarios.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取场景列表失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchScenario(id) {
    loading.value = true
    error.value = ''
    try {
      const response = await scenarioApi.get(id)
      currentScenario.value = response.data
      currentSteps.value = response.data.steps || []
      return currentScenario.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取场景详情失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createScenario(data) {
    loading.value = true
    error.value = ''
    try {
      const response = await scenarioApi.create(data)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '创建场景失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateScenario(id, data) {
    loading.value = true
    error.value = ''
    try {
      const response = await scenarioApi.update(id, data)
      currentScenario.value = response.data
      return currentScenario.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '更新场景失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteScenario(id) {
    loading.value = true
    error.value = ''
    try {
      await scenarioApi.delete(id)
      scenarios.value = scenarios.value.filter(s => s.id !== id)
      if (currentScenario.value?.id === id) {
        currentScenario.value = null
        currentSteps.value = []
      }
      total.value = Math.max(0, total.value - 1)
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '删除场景失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // ── Actions: Steps ───────────────────────────────────────────

  async function addStep(scenarioId, data) {
    loading.value = true
    error.value = ''
    try {
      const response = await scenarioApi.addStep(scenarioId, data)
      currentSteps.value.push(response.data)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '添加步骤失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateStep(stepId, data) {
    loading.value = true
    error.value = ''
    try {
      const response = await scenarioApi.updateStep(stepId, data)
      const idx = currentSteps.value.findIndex(s => s.id === stepId)
      if (idx !== -1) currentSteps.value[idx] = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '更新步骤失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteStep(stepId) {
    loading.value = true
    error.value = ''
    try {
      await scenarioApi.deleteStep(stepId)
      currentSteps.value = currentSteps.value.filter(s => s.id !== stepId)
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '删除步骤失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function reorderSteps(scenarioId, stepIds) {
    loading.value = true
    error.value = ''
    try {
      await scenarioApi.reorderSteps(scenarioId, stepIds)
      // 重新按 stepIds 顺序排列本地步骤
      const stepMap = Object.fromEntries(currentSteps.value.map(s => [s.id, s]))
      currentSteps.value = stepIds.map(id => stepMap[id]).filter(Boolean)
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '重排步骤失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // ── Actions: Execution ───────────────────────────────────────

  async function startExecution(scenarioId, params = {}) {
    loading.value = true
    error.value = ''
    try {
      const response = await scenarioApi.startExecution(scenarioId, params)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '启动执行失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchExecution(runId) {
    loading.value = true
    error.value = ''
    try {
      const response = await scenarioApi.getExecution(runId)
      currentExecution.value = response.data
      return currentExecution.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取执行详情失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchExecutions(params = {}) {
    loading.value = true
    error.value = ''
    try {
      const response = await scenarioApi.listExecutions({
        page: params.page || executionPage.value,
        page_size: params.page_size || executionPageSize.value,
        ...(params.scenario_id && { scenario_id: params.scenario_id }),
        ...(params.status && { status: params.status }),
      })
      executions.value = response.data.items
      executionTotal.value = response.data.total
      executionPage.value = response.data.page
      executionPageSize.value = response.data.page_size
      return executions.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取执行历史失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  function clearCurrentScenario() {
    currentScenario.value = null
    currentSteps.value = []
    currentExecution.value = null
  }

  return {
    // State
    scenarios,
    total,
    page,
    pageSize,
    currentScenario,
    currentSteps,
    loading,
    error,
    executions,
    executionTotal,
    executionPage,
    executionPageSize,
    currentExecution,
    // Actions
    fetchScenarios,
    fetchScenario,
    createScenario,
    updateScenario,
    deleteScenario,
    addStep,
    updateStep,
    deleteStep,
    reorderSteps,
    startExecution,
    fetchExecution,
    fetchExecutions,
    clearCurrentScenario,
  }
})
