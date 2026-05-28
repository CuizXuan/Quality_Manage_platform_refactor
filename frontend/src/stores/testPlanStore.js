import { ref } from 'vue'
import { defineStore } from 'pinia'
import { testPlanApi } from '@/api/testPlan'

export const useTestPlanStore = defineStore('testPlan', () => {
  // State
  const plans = ref([])
  const currentPlan = ref(null)
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const loading = ref(false)
  const error = ref('')

  // Runs state
  const runs = ref([])
  const currentRun = ref(null)
  const runsTotal = ref(0)

  // Actions: Plans
  async function fetchPlans(params = {}) {
    loading.value = true
    error.value = ''
    try {
      const response = await testPlanApi.listPlans({
        page: params.page || page.value,
        page_size: params.page_size || pageSize.value,
        project_id: params.project_id || undefined,
        status: params.status || undefined,
        keyword: params.keyword || undefined,
      })
      plans.value = response.data?.items || []
      total.value = response.data?.total || 0
      page.value = response.data?.page || 1
      pageSize.value = response.data?.page_size || 20
      return plans.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取测试计划失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchPlan(id) {
    loading.value = true
    error.value = ''
    try {
      const response = await testPlanApi.getPlan(id)
      currentPlan.value = response.data || response
      return currentPlan.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取测试计划失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createPlan(data) {
    loading.value = true
    error.value = ''
    try {
      const response = await testPlanApi.createPlan(data)
      return response.data || response
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '创建测试计划失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updatePlan(id, data) {
    loading.value = true
    error.value = ''
    try {
      const response = await testPlanApi.updatePlan(id, data)
      return response.data || response
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '更新测试计划失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deletePlan(id) {
    loading.value = true
    error.value = ''
    try {
      await testPlanApi.deletePlan(id)
      plans.value = plans.value.filter(p => p.id !== id)
      total.value = Math.max(0, total.value - 1)
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '删除测试计划失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // Actions: Runs
  async function runPlan(planId) {
    loading.value = true
    error.value = ''
    try {
      const response = await testPlanApi.runPlan(planId)
      return response.data || response
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '执行测试计划失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchRuns(params = {}) {
    loading.value = true
    error.value = ''
    try {
      const response = await testPlanApi.listRuns({
        plan_id: params.plan_id || undefined,
        status: params.status || undefined,
        page: params.page || 1,
        page_size: params.page_size || 20,
      })
      runs.value = response.data?.items || []
      runsTotal.value = response.data?.total || 0
      return runs.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取执行记录失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchRun(runId) {
    loading.value = true
    error.value = ''
    try {
      const response = await testPlanApi.getRun(runId)
      currentRun.value = response.data || response
      return currentRun.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取执行记录失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // Actions: Suites
  async function createSuite(planId, data) {
    const response = await testPlanApi.createSuite(planId, data)
    return response.data || response
  }

  async function deleteSuite(suiteId) {
    await testPlanApi.deleteSuite(suiteId)
  }

  // Actions: Suite Items
  async function addSuiteItem(data) {
    const response = await testPlanApi.addSuiteItem(data)
    return response.data || response
  }

  async function removeSuiteItem(itemId) {
    await testPlanApi.removeSuiteItem(itemId)
  }

  return {
    plans,
    currentPlan,
    total,
    page,
    pageSize,
    loading,
    error,
    runs,
    currentRun,
    runsTotal,
    fetchPlans,
    fetchPlan,
    createPlan,
    updatePlan,
    deletePlan,
    runPlan,
    fetchRuns,
    fetchRun,
    createSuite,
    deleteSuite,
    addSuiteItem,
    removeSuiteItem,
  }
})