import { ref } from 'vue'
import { defineStore } from 'pinia'
import { qualityFoundationApi } from '@/api/qualityFoundation'

export const useQualityFoundationStore = defineStore('foundation', () => {
  // ── State: Project ────────────────────────────────────────────
  const projects = ref([])
  const projectTotal = ref(0)
  const projectPage = ref(1)
  const projectPageSize = ref(20)
  const currentProject = ref(null)

  // ── State: Version ──────────────────────────────────────────────
  const versions = ref([])
  const versionTotal = ref(0)

  // ── State: Iteration ────────────────────────────────────────────
  const iterations = ref([])
  const iterationTotal = ref(0)

  // ── State: Requirement ────────────────────────────────────────
  const requirements = ref([])
  const requirementTotal = ref(0)
  const requirementPage = ref(1)
  const requirementPageSize = ref(20)
  const currentRequirement = ref(null)
  const requirementCoverage = ref(null)

  // ── Shared ──────────────────────────────────────────────────────
  const loading = ref(false)
  const error = ref('')

  // ── Actions: Project ──────────────────────────────────────────

  async function fetchProjects(params = {}) {
    loading.value = true
    error.value = ''
    try {
      const response = await qualityFoundationApi.listProjects({
        page: params.page || 1,
        page_size: params.page_size || 15,
        keyword: params.keyword || '',
        status: params.status || '',
      })
      projects.value = response.data || []
      projectTotal.value = response.total || response.data?.length || 0
      return projects.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取项目列表失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchProject(id) {
    loading.value = true
    error.value = ''
    try {
      const response = await qualityFoundationApi.getProject(id)
      currentProject.value = response.data
      return currentProject.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取项目详情失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createProject(data) {
    loading.value = true
    error.value = ''
    try {
      const response = await qualityFoundationApi.createProject(data)
      projects.value.push(response.data)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '创建项目失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateProject(id, data) {
    loading.value = true
    error.value = ''
    try {
      const response = await qualityFoundationApi.updateProject(id, data)
      const idx = projects.value.findIndex(p => p.id === id)
      if (idx !== -1) projects.value[idx] = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '更新项目失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteProject(id) {
    loading.value = true
    error.value = ''
    try {
      await qualityFoundationApi.deleteProject(id)
      projects.value = projects.value.filter(p => p.id !== id)
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '删除项目失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // ── Actions: Version ───────────────────────────────────────────

  async function fetchVersions(params = {}) {
    loading.value = true
    error.value = ''
    try {
      const response = await qualityFoundationApi.listVersions({
        project_id: params.project_id,
      })
      versions.value = response.data
      return versions.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取版本列表失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createVersion(data) {
    loading.value = true
    error.value = ''
    try {
      const response = await qualityFoundationApi.createVersion(data)
      versions.value.push(response.data)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '创建版本失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateVersion(id, data) {
    loading.value = true
    error.value = ''
    try {
      const response = await qualityFoundationApi.updateVersion(id, data)
      const idx = versions.value.findIndex(v => v.id === id)
      if (idx !== -1) versions.value[idx] = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '更新版本失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteVersion(id) {
    loading.value = true
    error.value = ''
    try {
      await qualityFoundationApi.deleteVersion(id)
      versions.value = versions.value.filter(v => v.id !== id)
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '删除版本失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // ── Actions: Iteration ────────────────────────────────────────

  async function fetchIterations(params = {}) {
    loading.value = true
    error.value = ''
    try {
      const response = await qualityFoundationApi.listIterations({
        project_id: params.project_id,
        version_id: params.version_id,
      })
      iterations.value = response.data
      return iterations.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取迭代列表失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createIteration(data) {
    loading.value = true
    error.value = ''
    try {
      const response = await qualityFoundationApi.createIteration(data)
      iterations.value.push(response.data)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '创建迭代失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateIteration(id, data) {
    loading.value = true
    error.value = ''
    try {
      const response = await qualityFoundationApi.updateIteration(id, data)
      const idx = iterations.value.findIndex(i => i.id === id)
      if (idx !== -1) iterations.value[idx] = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '更新迭代失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteIteration(id) {
    loading.value = true
    error.value = ''
    try {
      await qualityFoundationApi.deleteIteration(id)
      iterations.value = iterations.value.filter(i => i.id !== id)
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '删除迭代失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  function clearVersions() {
    versions.value = []
    versionTotal.value = 0
  }

  function clearIterations() {
    iterations.value = []
    iterationTotal.value = 0
  }

  function clearRequirements() {
    requirements.value = []
    requirementTotal.value = 0
  }

  // ── Actions: Requirement ──────────────────────────────────────

  async function fetchRequirements(params = {}) {
    loading.value = true
    error.value = ''
    try {
      const response = await qualityFoundationApi.listRequirements({
        project_id: params.project_id || undefined,
        version_id: params.version_id || undefined,
        iteration_id: params.iteration_id || undefined,
        keyword: params.keyword || '',
        status: params.status || '',
        page: params.page || 1,
        page_size: params.page_size || 15,
      })
      requirements.value = response.data
      requirementTotal.value = response.total || response.data.length
      return requirements.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取需求列表失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchRequirement(id) {
    loading.value = true
    error.value = ''
    try {
      const response = await qualityFoundationApi.getRequirement(id)
      currentRequirement.value = response.data
      return currentRequirement.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取需求详情失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createRequirement(data) {
    loading.value = true
    error.value = ''
    try {
      const response = await qualityFoundationApi.createRequirement(data)
      requirements.value.push(response.data)
      requirementTotal.value++
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '创建需求失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateRequirement(id, data) {
    loading.value = true
    error.value = ''
    try {
      const response = await qualityFoundationApi.updateRequirement(id, data)
      const idx = requirements.value.findIndex(r => r.id === id)
      if (idx !== -1) requirements.value[idx] = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '更新需求失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteRequirement(id) {
    loading.value = true
    error.value = ''
    try {
      await qualityFoundationApi.deleteRequirement(id)
      requirements.value = requirements.value.filter(r => r.id !== id)
      requirementTotal.value = Math.max(0, requirementTotal.value - 1)
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '删除需求失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchRequirementCoverage(params = {}) {
    loading.value = true
    error.value = ''
    try {
      const response = await qualityFoundationApi.getRequirementCoverage({
        project_id: params.project_id,
      })
      requirementCoverage.value = response.data
      return requirementCoverage.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取需求覆盖率失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    // State
    projects,
    projectTotal,
    projectPage,
    projectPageSize,
    currentProject,
    versions,
    versionTotal,
    iterations,
    iterationTotal,
    requirements,
    requirementTotal,
    requirementPage,
    requirementPageSize,
    currentRequirement,
    requirementCoverage,
    loading,
    error,
    // Actions: Project
    fetchProjects,
    fetchProject,
    createProject,
    updateProject,
    deleteProject,
    // Actions: Version
    fetchVersions,
    createVersion,
    updateVersion,
    deleteVersion,
    clearVersions,
    // Actions: Iteration
    fetchIterations,
    createIteration,
    updateIteration,
    deleteIteration,
    clearIterations,
    // Actions: Requirement
    fetchRequirements,
    fetchRequirement,
    createRequirement,
    updateRequirement,
    deleteRequirement,
    clearRequirements,
    fetchRequirementCoverage,
  }
})