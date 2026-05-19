<template>
  <div class="ai-insight-grid">
    <!-- Risk Analysis Card -->
    <AIInsightCard
      type="risk"
      icon="⚠"
      title="风险分析"
      :badge="riskLevel"
      :badgeClass="riskBadgeClass"
      :isLoading="isAnalyzing"
      loadingText="分析中..."
    >
      <div class="risk-content">
        <div class="risk-item" v-if="riskAnalysis.length === 0 && !isAnalyzing">
          <span class="risk-status safe">✓ 无风险</span>
          <span class="risk-desc">未检测到敏感字段或危险 Header</span>
        </div>
        <div v-else class="risk-list">
          <div v-for="(risk, idx) in riskAnalysis" :key="idx" class="risk-item">
            <span class="risk-status" :class="risk.level">{{ risk.level === 'high' ? '高' : risk.level === 'medium' ? '中' : '低' }}</span>
            <span class="risk-desc">{{ risk.message }}</span>
          </div>
        </div>
      </div>
    </AIInsightCard>

    <!-- Quality Score Card -->
    <AIInsightCard
      type="quality"
      icon="📊"
      title="AI 质量评分"
      :isLoading="isAnalyzing"
      loadingText="计算中..."
    >
      <div class="quality-content">
        <div class="quality-score" :class="{ animating: isAnalyzing }">
          <span class="score-value">{{ qualityScore }}</span>
          <span class="score-max">/ 100</span>
        </div>
        <div class="quality-tags">
          <span class="quality-tag" :class="{ active: qualityFactors.includes('structure') }">结构完整</span>
          <span class="quality-tag" :class="{ active: qualityFactors.includes('rest') }">RESTful</span>
          <span class="quality-tag" :class="{ active: qualityFactors.includes('doc') }">文档良好</span>
        </div>
      </div>
    </AIInsightCard>

    <!-- API Health Card -->
    <AIInsightCard
      type="health"
      icon="💚"
      title="接口健康度"
      :isLoading="isAnalyzing"
      loadingText="检测中..."
    >
      <div class="health-content">
        <div class="health-metrics">
          <div class="metric">
            <span class="metric-label">响应时间</span>
            <span class="metric-value" :class="responseTimeClass">{{ responseTime }}</span>
          </div>
          <div class="metric">
            <span class="metric-label">成功率</span>
            <span class="metric-value" :class="successRateClass">{{ successRate }}%</span>
          </div>
          <div class="metric">
            <span class="metric-label">字段稳定</span>
            <span class="metric-value">{{ fieldStability }}</span>
          </div>
        </div>
      </div>
    </AIInsightCard>

    <!-- Smart Suggestions Card -->
    <AIInsightCard
      type="suggestion"
      icon="💡"
      title="智能建议"
      :isLoading="isAnalyzing"
      loadingText="生成建议中..."
    >
      <div class="suggestion-content">
        <div v-if="suggestions.length === 0 && !isAnalyzing" class="suggestion-empty">
          <span>暂无建议</span>
        </div>
        <div v-else class="suggestion-list">
          <div v-for="(suggestion, idx) in suggestions" :key="idx" class="suggestion-item">
            <span class="suggestion-icon">{{ suggestion.icon || '→' }}</span>
            <span class="suggestion-text">{{ suggestion.text }}</span>
          </div>
        </div>
      </div>
    </AIInsightCard>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRequestStore } from '@/stores/request'
import AIInsightCard from './AIInsightCard.vue'

const requestStore = useRequestStore()

// AI 分析状态
const isAnalyzing = ref(false)

// Risk Analysis
const riskAnalysis = ref([])
const riskLevel = computed(() => {
  if (riskAnalysis.value.length === 0) return '安全'
  const hasHigh = riskAnalysis.value.some(r => r.level === 'high')
  const hasMedium = riskAnalysis.value.some(r => r.level === 'medium')
  return hasHigh ? '高风险' : hasMedium ? '中风险' : '低风险'
})
const riskBadgeClass = computed(() => {
  if (riskAnalysis.value.length === 0) return 'success'
  const hasHigh = riskAnalysis.value.some(r => r.level === 'high')
  const hasMedium = riskAnalysis.value.some(r => r.level === 'medium')
  return hasHigh ? 'error' : hasMedium ? 'warning' : 'success'
})

// Quality Score
const qualityScore = ref(0)
const qualityFactors = ref([])

// API Health
const responseTime = ref('--')
const successRate = ref(100)
const fieldStability = ref('--')
const responseTimeClass = computed(() => {
  const ms = parseInt(responseTime.value)
  if (isNaN(ms)) return ''
  return ms < 200 ? 'fast' : ms < 500 ? 'normal' : 'slow'
})
const successRateClass = computed(() => {
  return successRate.value >= 99 ? 'success' : successRate.value >= 95 ? 'normal' : 'error'
})

// Suggestions
const suggestions = ref([])

// 分析请求
function analyzeRequest() {
  if (!requestStore.url) return

  isAnalyzing.value = true

  // 模拟 AI 分析
  setTimeout(() => {
    analyzeURL(requestStore.url, requestStore.method)
    isAnalyzing.value = false
  }, 800)
}

// 分析 URL
function analyzeURL(url, method) {
  // Risk Analysis
  riskAnalysis.value = []
  const lowRiskItems = []
  const mediumRiskItems = []
  const highRiskItems = []

  // 检查 URL 安全
  if (url.startsWith('http://')) {
    mediumRiskItems.push({ level: 'medium', message: '使用 HTTP 而非 HTTPS，可能存在安全风险' })
  }
  if (url.includes('localhost') || url.includes('127.0.0.1')) {
    lowRiskItems.push({ level: 'low', message: '本地开发环境地址' })
  }

  // 检查敏感路径
  const sensitivePaths = ['/admin', '/login', '/password', '/secret', '/api/key']
  if (sensitivePaths.some(p => url.toLowerCase().includes(p))) {
    highRiskItems.push({ level: 'high', message: '检测到敏感路径，建议加强认证' })
  }

  // 检查 Header
  const headers = requestStore.headers.filter(h => h.enabled && h.key)
  const sensitiveHeaders = ['authorization', 'x-api-key', 'cookie']
  const hasSensitiveHeader = headers.some(h =>
    sensitiveHeaders.some(s => h.key.toLowerCase().includes(s))
  )
  if (hasSensitiveHeader) {
    mediumRiskItems.push({ level: 'medium', message: '请求包含认证信息，请注意安全传输' })
  }

  riskAnalysis.value = [...highRiskItems, ...mediumRiskItems, ...lowRiskItems]

  // Quality Score
  let score = 75
  qualityFactors.value = []

  if (url.includes('?')) {
    score += 5
    qualityFactors.value.push('structure')
  }
  if (['GET', 'POST', 'PUT', 'DELETE'].includes(method)) {
    score += 5
    qualityFactors.value.push('rest')
  }
  if (headers.length > 2) {
    score += 5
    qualityFactors.value.push('doc')
  }
  if (requestStore.body) {
    score += 10
  }

  qualityScore.value = Math.min(100, score)

  // API Health
  if (requestStore.response) {
    const duration = requestStore.response.duration_ms
    responseTime.value = duration < 1000 ? `${duration}ms` : `${(duration / 1000).toFixed(1)}s`
    successRate.value = requestStore.response.status_code >= 200 && requestStore.response.status_code < 400 ? 100 : 0
    fieldStability.value = '良好'
  } else {
    responseTime.value = '--'
    successRate.value = 100
    fieldStability.value = '--'
  }

  // Suggestions
  suggestions.value = []

  if (!headers.find(h => h.key.toLowerCase().includes('content-type'))) {
    suggestions.value.push({ icon: '📝', text: '建议添加 Content-Type header' })
  }
  if (!headers.find(h => h.key.toLowerCase().includes('authorization'))) {
    suggestions.value.push({ icon: '🔐', text: '建议添加认证信息' })
  }
  if (method === 'GET' && requestStore.body) {
    suggestions.value.push({ icon: '⚠', text: 'GET 请求不建议携带 body' })
  }
  if (url.includes('?')) {
    suggestions.value.push({ icon: '📋', text: '建议使用 RESTful 路径参数设计' })
  }
  if (suggestions.value.length === 0) {
    suggestions.value.push({ icon: '✓', text: '请求配置良好，无需额外建议' })
  }
}

// 监听请求变化
watch(() => requestStore.url, (newUrl) => {
  if (newUrl) {
    analyzeRequest()
  } else {
    // 重置状态
    riskAnalysis.value = []
    qualityScore.value = 0
    qualityFactors.value = []
    responseTime.value = '--'
    successRate.value = 100
    fieldStability.value = '--'
    suggestions.value = []
  }
})

// 监听响应变化
watch(() => requestStore.response, (newResponse) => {
  if (newResponse) {
    const duration = newResponse.duration_ms
    responseTime.value = duration < 1000 ? `${duration}ms` : `${(duration / 1000).toFixed(1)}s`
    successRate.value = newResponse.status_code >= 200 && newResponse.status_code < 400 ? 100 :
                       newResponse.status_code >= 400 && newResponse.status_code < 500 ? 80 : 0
    fieldStability.value = '良好'

    // 响应后重新计算分数
    if (requestStore.url) {
      analyzeRequest()
    }
  }
})
</script>

<style scoped>
.ai-insight-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  animation: card-enter 0.4s ease-out;
}

@keyframes card-enter {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.ai-insight-grid > :nth-child(1) { animation-delay: 0ms; }
.ai-insight-grid > :nth-child(2) { animation-delay: 50ms; }
.ai-insight-grid > :nth-child(3) { animation-delay: 100ms; }
.ai-insight-grid > :nth-child(4) { animation-delay: 150ms; }

/* Risk Content */
.risk-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.risk-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.risk-status {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  flex-shrink: 0;
}

.risk-status.safe,
.risk-status.low {
  background: var(--success-muted);
  color: var(--success);
}

.risk-status.medium {
  background: var(--warning-muted);
  color: var(--warning);
}

.risk-status.high {
  background: var(--error-muted);
  color: var(--error);
}

.risk-desc {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.4;
}

/* Quality Content */
.quality-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.quality-score {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.score-value {
  font-size: 36px;
  font-weight: 700;
  color: var(--primary);
  line-height: 1;
  transition: all 0.3s ease;
}

.quality-score.animating .score-value {
  animation: score-pulse 0.6s ease-in-out infinite;
}

@keyframes score-pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.05); opacity: 0.8; }
}

.score-max {
  font-size: 16px;
  color: var(--text-tertiary);
}

.quality-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.quality-tag {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 4px;
  background: var(--bg-card-hover);
  color: var(--text-tertiary);
  transition: all 0.2s ease;
}

.quality-tag.active {
  background: var(--primary-muted);
  color: var(--primary);
}

/* Health Content */
.health-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.health-metrics {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.metric {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.metric-label {
  font-size: 12px;
  color: var(--text-tertiary);
}

.metric-value {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.metric-value.fast { color: var(--success); }
.metric-value.normal { color: var(--warning); }
.metric-value.slow { color: var(--error); }

/* Suggestion Content */
.suggestion-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.suggestion-empty {
  font-size: 12px;
  color: var(--text-tertiary);
  text-align: center;
  padding: 8px 0;
}

.suggestion-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.suggestion-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-secondary);
}

.suggestion-icon {
  font-size: 12px;
  flex-shrink: 0;
}

.suggestion-text {
  line-height: 1.4;
}
</style>
