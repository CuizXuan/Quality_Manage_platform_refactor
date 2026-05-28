/**
 * Quality Analytics Store - 质量分析状态管理
 */
import { defineStore } from "pinia"
import { qualityAnalyticsApi } from "@/api/qualityAnalytics"

export const useQualityAnalyticsStore = defineStore("qualityAnalytics", {
  state: () => ({
    overview: null,
    trends: [],
    defectDistribution: [],
    requirementCoverage: [],
    releaseGate: null,
    coverageRate: 0,
    gatesChecked: 0,
    scopeNote: null,
    loading: false,
    filters: {
      project_id: null,
      version_id: null,
      iteration_id: null,
      start_date: null,
      end_date: null,
      days: 30,
    },
  }),

  actions: {
    async fetchOverview() {
      this.loading = true
      try {
        const res = await qualityAnalyticsApi.overview(this.filters)
        const data = res.data
        this.overview = data?.metrics || null
        this.scopeNote = data?.scope_note || null
      } finally {
        this.loading = false
      }
    },

    async fetchTrends() {
      this.loading = true
      try {
        const res = await qualityAnalyticsApi.trends(this.filters)
        this.trends = res.data?.points || []
        if (res.data?.scope_note) this.scopeNote = res.data.scope_note
      } finally {
        this.loading = false
      }
    },

    async fetchDefectDistribution() {
      this.loading = true
      try {
        const res = await qualityAnalyticsApi.defectDistribution(this.filters)
        this.defectDistribution = res.data?.items || []
        if (res.data?.scope_note) this.scopeNote = res.data.scope_note
      } finally {
        this.loading = false
      }
    },

    async fetchRequirementCoverage() {
      this.loading = true
      try {
        const res = await qualityAnalyticsApi.requirementCoverage({
          project_id: this.filters.project_id,
          version_id: this.filters.version_id,
          iteration_id: this.filters.iteration_id,
        })
        this.requirementCoverage = res.data?.items || []
        this.coverageRate = res.data?.coverage_rate || 0
        if (res.data?.scope_note) this.scopeNote = res.data.scope_note
      } finally {
        this.loading = false
      }
    },

    async fetchReleaseGate() {
      this.loading = true
      try {
        const res = await qualityAnalyticsApi.releaseGate(this.filters)
        this.releaseGate = res.data?.result || null
        this.gatesChecked = res.data?.gates_checked || 0
        if (res.data?.scope_note) this.scopeNote = res.data.scope_note
      } finally {
        this.loading = false
      }
    },

    async loadAll() {
      await Promise.all([
        this.fetchOverview(),
        this.fetchTrends(),
        this.fetchDefectDistribution(),
        this.fetchRequirementCoverage(),
        this.fetchReleaseGate(),
      ])
    },

    resetFilters() {
      this.filters = {
        project_id: null,
        version_id: null,
        iteration_id: null,
        start_date: null,
        end_date: null,
        days: 30,
      }
    },

    setFilters(nextFilters) {
      const known = ['project_id', 'version_id', 'iteration_id', 'start_date', 'end_date', 'days']
      for (const key of known) {
        if (key in nextFilters) {
          this.filters[key] = nextFilters[key]
        }
      }
    },
  },
})