/**
 * Quality Analytics API - 质量分析 API 封装
 */
import client from './client'

export const qualityAnalyticsApi = {
  overview(params = {}) {
    return client.get("/api/quality-analytics/overview", { params })
  },

  trends(params = {}) {
    return client.get("/api/quality-analytics/trends", { params })
  },

  defectDistribution(params = {}) {
    return client.get("/api/quality-analytics/defect-distribution", { params })
  },

  requirementCoverage(params = {}) {
    return client.get("/api/quality-analytics/requirement-coverage", { params })
  },

  releaseGate(params = {}) {
    return client.get("/api/quality-analytics/release-gate", { params })
  },
}