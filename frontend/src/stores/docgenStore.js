import { ref } from 'vue'
import { defineStore } from 'pinia'
import { docgenApi } from '@/api/docgen'

export const useDocgenStore = defineStore('docgen', () => {
  // ── State: Tasks ───────────────────────────────────────────────
  const tasks = ref([])
  const taskTotal = ref(0)
  const taskPage = ref(1)
  const taskPageSize = ref(20)
  const currentTask = ref(null)

  // ── State: Rules ───────────────────────────────────────────────
  const rules = ref([])
  const ruleTotal = ref(0)
  const rulePage = ref(1)
  const rulePageSize = ref(20)

  // ── State: Templates ───────────────────────────────────────────
  const templates = ref([])
  const templateTotal = ref(0)
  const templatePage = ref(1)
  const templatePageSize = ref(20)

  // ── State: Generation ──────────────────────────────────────────
  const previewData = ref(null)
  const generationLoading = ref(false)

  // ── Shared ────────────────────────────────────────────────────
  const loading = ref(false)
  const error = ref('')

  // ── Actions: Tasks ───────────────────────────────────────────

  async function fetchTasks(params = {}) {
    loading.value = true
    error.value = ''
    try {
      const response = await docgenApi.listTasks({
        page: params.page || taskPage.value,
        page_size: params.page_size || taskPageSize.value,
        ...(params.task_type && { task_type: params.task_type }),
        ...(params.status && { status: params.status }),
        ...(params.keyword && { keyword: params.keyword }),
      })
      tasks.value = response.data.items
      taskTotal.value = response.data.total
      taskPage.value = response.data.page
      taskPageSize.value = response.data.page_size
      return tasks.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取任务列表失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchTask(id) {
    loading.value = true
    error.value = ''
    try {
      const response = await docgenApi.getTask(id)
      currentTask.value = response.data
      return currentTask.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取任务详情失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function downloadTaskFile(taskId, filename) {
    try {
      const response = await docgenApi.downloadTaskFile(taskId)
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', filename || 'output.docx')
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '下载文件失败'
      throw err
    }
  }

  // ── Actions: Rules ───────────────────────────────────────────

  async function fetchRules(params = {}) {
    loading.value = true
    error.value = ''
    try {
      const response = await docgenApi.listRules({
        page: params.page || rulePage.value,
        page_size: params.page_size || rulePageSize.value,
        ...(params.doc_type && { doc_type: params.doc_type }),
        ...(params.enabled !== undefined && { enabled: params.enabled }),
        ...(params.keyword && { keyword: params.keyword }),
      })
      rules.value = response.data.items
      ruleTotal.value = response.data.total
      rulePage.value = response.data.page
      rulePageSize.value = response.data.page_size
      return rules.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取规则列表失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createRule(data) {
    loading.value = true
    error.value = ''
    try {
      const response = await docgenApi.createRule(data)
      rules.value.unshift(response.data)
      ruleTotal.value += 1
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '创建规则失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateRule(id, data) {
    loading.value = true
    error.value = ''
    try {
      const response = await docgenApi.updateRule(id, data)
      const idx = rules.value.findIndex(r => r.id === id)
      if (idx !== -1) rules.value[idx] = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '更新规则失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteRule(id) {
    loading.value = true
    error.value = ''
    try {
      await docgenApi.deleteRule(id)
      rules.value = rules.value.filter(r => r.id !== id)
      ruleTotal.value = Math.max(0, ruleTotal.value - 1)
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '删除规则失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // ── Actions: Templates ─────────────────────────────────────────

  async function fetchTemplates(params = {}) {
    loading.value = true
    error.value = ''
    try {
      const response = await docgenApi.listTemplates({
        page: params.page || templatePage.value,
        page_size: params.page_size || templatePageSize.value,
        ...(params.keyword && { keyword: params.keyword }),
      })
      templates.value = response.data.items
      templateTotal.value = response.data.total
      templatePage.value = response.data.page
      templatePageSize.value = response.data.page_size
      return templates.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取模板列表失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function uploadTemplate(file) {
    loading.value = true
    error.value = ''
    try {
      const response = await docgenApi.uploadTemplate(file)
      templates.value.unshift(response.data)
      templateTotal.value += 1
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '上传模板失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteTemplate(id) {
    loading.value = true
    error.value = ''
    try {
      await docgenApi.deleteTemplate(id)
      templates.value = templates.value.filter(t => t.id !== id)
      templateTotal.value = Math.max(0, templateTotal.value - 1)
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '删除模板失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // ── Actions: Requirement Doc ──────────────────────────────────

  async function previewRequirement(data) {
    generationLoading.value = true
    error.value = ''
    try {
      const response = await docgenApi.previewRequirement(data)
      previewData.value = response.data
      return previewData.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '预览失败'
      throw err
    } finally {
      generationLoading.value = false
    }
  }

  async function generateRequirement(data) {
    generationLoading.value = true
    error.value = ''
    try {
      const response = await docgenApi.generateRequirement(data)
      tasks.value.unshift(response.data)
      taskTotal.value += 1
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '生成失败'
      throw err
    } finally {
      generationLoading.value = false
    }
  }

  async function generateRequirementAsync(data) {
    generationLoading.value = true
    error.value = ''
    try {
      const response = await docgenApi.generateRequirementAsync(data)
      tasks.value.unshift(response.data)
      taskTotal.value += 1
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '生成失败'
      throw err
    } finally {
      generationLoading.value = false
    }
  }

  // ── Actions: Database Doc ─────────────────────────────────────

  async function previewDatabase(data) {
    generationLoading.value = true
    error.value = ''
    try {
      const response = await docgenApi.previewDatabase(data)
      previewData.value = response.data
      return previewData.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '预览失败'
      throw err
    } finally {
      generationLoading.value = false
    }
  }

  async function generateDatabase(data) {
    generationLoading.value = true
    error.value = ''
    try {
      const response = await docgenApi.generateDatabase(data)
      tasks.value.unshift(response.data)
      taskTotal.value += 1
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '生成失败'
      throw err
    } finally {
      generationLoading.value = false
    }
  }

  async function generateDatabaseAsync(data) {
    generationLoading.value = true
    error.value = ''
    try {
      const response = await docgenApi.generateDatabaseAsync(data)
      tasks.value.unshift(response.data)
      taskTotal.value += 1
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '生成失败'
      throw err
    } finally {
      generationLoading.value = false
    }
  }

  // ── Actions: API Doc ───────────────────────────────────────────

  async function previewApi(data) {
    generationLoading.value = true
    error.value = ''
    try {
      const response = await docgenApi.previewApi(data)
      previewData.value = response.data
      return previewData.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '预览失败'
      throw err
    } finally {
      generationLoading.value = false
    }
  }

  async function generateApi(data) {
    generationLoading.value = true
    error.value = ''
    try {
      const response = await docgenApi.generateApi(data)
      tasks.value.unshift(response.data)
      taskTotal.value += 1
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '生成失败'
      throw err
    } finally {
      generationLoading.value = false
    }
  }

  async function generateApiAsync(data) {
    generationLoading.value = true
    error.value = ''
    try {
      const response = await docgenApi.generateApiAsync(data)
      tasks.value.unshift(response.data)
      taskTotal.value += 1
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '生成失败'
      throw err
    } finally {
      generationLoading.value = false
    }
  }

  // ── Poll task status ──────────────────────────────────────────

  async function pollTaskUntilDone(taskId, interval = 2000, timeout = 120000) {
    const start = Date.now()
    while (Date.now() - start < timeout) {
      const task = await fetchTask(taskId)
      if (task.status === 'success' || task.status === 'failed') {
        return task
      }
      await new Promise(r => setTimeout(r, interval))
    }
    throw new Error('任务超时')
  }

  return {
    // State: Tasks
    tasks,
    taskTotal,
    taskPage,
    taskPageSize,
    currentTask,
    // State: Rules
    rules,
    ruleTotal,
    rulePage,
    rulePageSize,
    // State: Templates
    templates,
    templateTotal,
    templatePage,
    templatePageSize,
    // State: Generation
    previewData,
    generationLoading,
    // Shared
    loading,
    error,
    // Actions: Tasks
    fetchTasks,
    fetchTask,
    downloadTaskFile,
    // Actions: Rules
    fetchRules,
    createRule,
    updateRule,
    deleteRule,
    // Actions: Templates
    fetchTemplates,
    uploadTemplate,
    deleteTemplate,
    // Actions: Requirement
    previewRequirement,
    generateRequirement,
    generateRequirementAsync,
    // Actions: Database
    previewDatabase,
    generateDatabase,
    generateDatabaseAsync,
    // Actions: API
    previewApi,
    generateApi,
    generateApiAsync,
    // Utilities
    pollTaskUntilDone,
  }
})