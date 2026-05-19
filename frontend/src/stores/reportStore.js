import { ref } from 'vue'
import { defineStore } from 'pinia'
import { reportApi } from '@/api/report'

export const useReportStore = defineStore('report', () => {
  // ── State: Report ─────────────────────────────────────────────
  const reports = ref([])
  const reportTotal = ref(0)
  const reportPage = ref(1)
  const reportPageSize = ref(20)
  const currentReport = ref(null)

  // ── State: Defect ─────────────────────────────────────────────
  const defects = ref([])
  const defectTotal = ref(0)
  const defectPage = ref(1)
  const defectPageSize = ref(20)
  const currentDefect = ref(null)
  const defectStats = ref(null)

  // ── State: QualityGate ────────────────────────────────────────
  const qualityGates = ref([])
  const gateTotal = ref(0)
  const gatePage = ref(1)
  const gatePageSize = ref(20)
  const currentGate = ref(null)

  // ── Shared ────────────────────────────────────────────────────
  const loading = ref(false)
  const error = ref('')

  // ── Actions: Report ───────────────────────────────────────────

  async function fetchReports(params = {}) {
    loading.value = true
    error.value = ''
    try {
      const response = await reportApi.list({
        page: params.page || reportPage.value,
        page_size: params.page_size || reportPageSize.value,
        ...(params.keyword && { keyword: params.keyword }),
        ...(params.report_type && { report_type: params.report_type }),
        ...(params.environment && { environment: params.environment }),
      })
      reports.value = response.data.items
      reportTotal.value = response.data.total
      reportPage.value = response.data.page
      reportPageSize.value = response.data.page_size
      return reports.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取报告列表失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchReport(id) {
    loading.value = true
    error.value = ''
    try {
      const response = await reportApi.get(id)
      currentReport.value = response.data
      return currentReport.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取报告详情失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createReport(data) {
    loading.value = true
    error.value = ''
    try {
      const response = await reportApi.create(data)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '创建报告失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteReport(id) {
    loading.value = true
    error.value = ''
    try {
      await reportApi.delete(id)
      reports.value = reports.value.filter(r => r.id !== id)
      reportTotal.value = Math.max(0, reportTotal.value - 1)
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '删除报告失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // ── Actions: Defect ───────────────────────────────────────────

  async function fetchDefects(params = {}) {
    loading.value = true
    error.value = ''
    try {
      const response = await reportApi.listDefects({
        page: params.page || defectPage.value,
        page_size: params.page_size || defectPageSize.value,
        ...(params.keyword && { keyword: params.keyword }),
        ...(params.status && { status: params.status }),
        ...(params.severity && { severity: params.severity }),
        ...(params.priority && { priority: params.priority }),
        ...(params.defect_type && { defect_type: params.defect_type }),
        ...(params.assigned_to && { assigned_to: params.assigned_to }),
        ...(params.project_id && { project_id: params.project_id }),
      })
      defects.value = response.data.items
      defectTotal.value = response.data.total
      defectPage.value = response.data.page
      defectPageSize.value = response.data.page_size
      return defects.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取缺陷列表失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchDefect(id) {
    loading.value = true
    error.value = ''
    try {
      const response = await reportApi.getDefect(id)
      currentDefect.value = response.data
      return currentDefect.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取缺陷详情失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createDefect(data) {
    loading.value = true
    error.value = ''
    try {
      const response = await reportApi.createDefect(data)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '创建缺陷失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateDefect(id, data) {
    loading.value = true
    error.value = ''
    try {
      const response = await reportApi.updateDefect(id, data)
      const idx = defects.value.findIndex(d => d.id === id)
      if (idx !== -1) defects.value[idx] = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '更新缺陷失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteDefect(id) {
    loading.value = true
    error.value = ''
    try {
      await reportApi.deleteDefect(id)
      defects.value = defects.value.filter(d => d.id !== id)
      defectTotal.value = Math.max(0, defectTotal.value - 1)
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '删除缺陷失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function transitionDefect(id, status, comment) {
    loading.value = true
    error.value = ''
    try {
      const response = await reportApi.transitionDefect(id, { status, comment })
      const idx = defects.value.findIndex(d => d.id === id)
      if (idx !== -1) defects.value[idx] = response.data
      if (currentDefect.value?.id === id) currentDefect.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '状态流转失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchDefectStats(projectId) {
    loading.value = true
    error.value = ''
    try {
      const response = await reportApi.getDefectStats({ project_id: projectId })
      defectStats.value = response.data
      return defectStats.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取统计失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // ── Actions: QualityGate ──────────────────────────────────────

  async function fetchQualityGates(params = {}) {
    loading.value = true
    error.value = ''
    try {
      const response = await reportApi.listQualityGates({
        page: params.page || gatePage.value,
        page_size: params.page_size || gatePageSize.value,
        ...(params.keyword && { keyword: params.keyword }),
        ...(params.gate_type && { gate_type: params.gate_type }),
        ...(params.enabled !== undefined && { enabled: params.enabled }),
      })
      qualityGates.value = response.data.items
      gateTotal.value = response.data.total
      gatePage.value = response.data.page
      gatePageSize.value = response.data.page_size
      return qualityGates.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取门禁列表失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchQualityGate(id) {
    loading.value = true
    error.value = ''
    try {
      const response = await reportApi.getQualityGate(id)
      currentGate.value = response.data
      return currentGate.value
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '获取门禁详情失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createQualityGate(data) {
    loading.value = true
    error.value = ''
    try {
      const response = await reportApi.createQualityGate(data)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '创建门禁失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateQualityGate(id, data) {
    loading.value = true
    error.value = ''
    try {
      const response = await reportApi.updateQualityGate(id, data)
      const idx = qualityGates.value.findIndex(g => g.id === id)
      if (idx !== -1) qualityGates.value[idx] = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '更新门禁失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteQualityGate(id) {
    loading.value = true
    error.value = ''
    try {
      await reportApi.deleteQualityGate(id)
      qualityGates.value = qualityGates.value.filter(g => g.id !== id)
      gateTotal.value = Math.max(0, gateTotal.value - 1)
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '删除门禁失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function evaluateQualityGate(id, params) {
    loading.value = true
    error.value = ''
    try {
      const response = await reportApi.evaluateQualityGate(id, params)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message || '门禁评估失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    // State
    reports,
    reportTotal,
    reportPage,
    reportPageSize,
    currentReport,
    defects,
    defectTotal,
    defectPage,
    defectPageSize,
    currentDefect,
    defectStats,
    qualityGates,
    gateTotal,
    gatePage,
    gatePageSize,
    currentGate,
    loading,
    error,
    // Actions: Report
    fetchReports,
    fetchReport,
    createReport,
    deleteReport,
    // Actions: Defect
    fetchDefects,
    fetchDefect,
    createDefect,
    updateDefect,
    deleteDefect,
    transitionDefect,
    fetchDefectStats,
    // Actions: QualityGate
    fetchQualityGates,
    fetchQualityGate,
    createQualityGate,
    updateQualityGate,
    deleteQualityGate,
    evaluateQualityGate,
  }
})
