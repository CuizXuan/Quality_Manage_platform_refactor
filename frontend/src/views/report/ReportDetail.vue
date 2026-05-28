<template>
  <div class="report-detail">
    <div class="detail-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" text @click="router.push('/report')">返回列表</el-button>
        <el-divider direction="vertical" />
        <span class="detail-title">{{ report?.name || '加载中…' }}</span>
      </div>
      <div class="header-right">
        <el-button type="primary" :loading="gateEvaluating" @click="evaluateQualityGates">
          评估门禁
        </el-button>
        <el-button type="primary" :icon="MagicStick" :loading="aiSummarizing" @click="handleAiSummarize">
          AI 总结报告
        </el-button>
      </div>
    </div>

    <!-- AI 总结结果 -->
    <el-dialog v-model="aiSummaryVisible" title="AI 报告总结" width="600px" destroy-on-close>
      <div v-if="aiSummaryResult" class="ai-summary-result">
        <el-alert v-if="aiSummaryResult?.summary_md" type="info" :title="aiSummaryResult.summary_md" :closable="false" show-icon />
        <div v-if="aiSummaryResult?.risk_score != null" class="summary-section">
          <h4>风险评分</h4>
          <p>
            <el-tag :type="aiSummaryResult.risk_score >= 80 ? 'danger' : aiSummaryResult.risk_score >= 60 ? 'warning' : 'success'" size="small">
              {{ aiSummaryResult.risk_score }}/100
            </el-tag>
          </p>
        </div>
        <div v-if="aiSummaryResult?.risk_factors?.length" class="summary-section">
          <h4>风险因素</h4>
          <ul>
            <li v-for="(f, i) in aiSummaryResult.risk_factors" :key="i">{{ f }}</li>
          </ul>
        </div>
        <div v-if="aiSummaryResult?.analysis_id" class="summary-section">
          <p class="saved-hint">分析记录已保存 (ID: {{ aiSummaryResult.analysis_id }})</p>
        </div>
      </div>
      <el-empty v-else description="暂无总结结果" />
    </el-dialog>

    <!-- 门禁评估结果 -->
    <el-card v-if="gateResult" class="gate-result-card" shadow="never">
      <template #header>
        <span class="card-title">质量门禁评估结果</span>
      </template>
      <el-alert
        v-if="gateResult.evaluations && gateResult.evaluations.length === 0"
        type="info"
        :closable="false"
        show-icon
        title="暂无启用的质量门禁规则"
      />
      <div v-else class="gate-list">
        <div v-for="ev in gateResult.evaluations" :key="ev.gate_id" class="gate-item">
          <div class="gate-header">
            <span class="gate-name">{{ ev.gate_name }}</span>
            <el-tag :type="getGateResultType(ev.overall_result)" size="small">
              {{ getGateResultText(ev.overall_result) }}
            </el-tag>
          </div>
          <div class="gate-details">
            <div v-for="(detail, idx) in ev.details" :key="idx" class="detail-row">
              <span class="detail-metric">{{ detail.metric }}</span>
              <span class="detail-expr">{{ detail.actual }} {{ detail.operator }} {{ detail.threshold }}</span>
              <el-tag :type="detail.result === 'pass' ? 'success' : detail.result === 'fail' ? 'danger' : 'info'" size="small">
                {{ detail.result }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 概览统计 -->
    <el-row :gutter="16" v-if="report">
      <el-col :span="6">
        <el-card class="stat-card" shadow="never">
          <div class="stat-label">通过率</div>
          <div class="stat-value" :style="{ color: getPassRateColor(report.summary?.pass_rate) }">
            {{ report.summary?.pass_rate != null ? report.summary.pass_rate + '%' : '—' }}
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="never">
          <div class="stat-label">用例总数</div>
          <div class="stat-value">{{ report.summary?.total ?? '—' }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="never">
          <div class="stat-label">通过 / 失败</div>
          <div class="stat-value">
            <span style="color: var(--el-color-success)">{{ report.summary?.passed ?? 0 }}</span>
            /
            <span style="color: var(--el-color-danger)">{{ report.summary?.failed ?? 0 }}</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="never">
          <div class="stat-label">执行耗时</div>
          <div class="stat-value">{{ report.duration_ms ? (report.duration_ms / 1000).toFixed(1) + 's' : '—' }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 基本信息 -->
    <el-card v-if="report" class="info-card" shadow="never">
      <el-descriptions :column="3" border>
        <el-descriptions-item label="报告ID">{{ report.id }}</el-descriptions-item>
        <el-descriptions-item label="报告类型">{{ formatType(report.report_type) }}</el-descriptions-item>
        <el-descriptions-item label="执行环境">{{ report.environment || '—' }}</el-descriptions-item>
        <el-descriptions-item label="目标名称">{{ report.target_name || '—' }}</el-descriptions-item>
        <el-descriptions-item label="触发者">{{ report.triggered_by || '—' }}</el-descriptions-item>
        <el-descriptions-item label="执行时间">{{ report.executed_at || '—' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 指标详情 -->
    <el-card v-if="report?.metrics && Object.keys(report.metrics).length > 0" class="metrics-card" shadow="never">
      <template #header>
        <span class="card-title">详细指标</span>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item
          v-for="(value, key) in report.metrics"
          :key="key"
          :label="key"
        >
          {{ formatMetricValue(value) }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 加载状态 -->
    <el-empty v-if="!report && !reportStore.loading" description="报告不存在或已删除" />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, MagicStick } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useReportStore } from '@/stores/reportStore'
import { useAiStore } from '@/stores/aiStore'

const route = useRoute()
const router = useRouter()
const reportStore = useReportStore()

const report = computed(() => reportStore.currentReport)
const gateEvaluating = computed(() => reportStore.gateEvaluating)
const gateResult = computed(() => reportStore.gateResult)

onMounted(async () => {
  const id = Number(route.params.id)
  try {
    await reportStore.fetchReport(id)
  } catch {
    /* error handled in store */
  }
})

async function evaluateQualityGates() {
  const id = Number(route.params.id)
  try {
    await reportStore.evaluateQualityGatesFromReport(id)
  } catch {
    /* error handled in store */
  }
}

function getGateResultType(result) {
  const map = { pass: 'success', fail: 'danger', skipped: 'info', warning: 'warning' }
  return map[result] || 'info'
}

function getGateResultText(result) {
  const map = { pass: '通过', fail: '未通过', skipped: '跳过', warning: '警告' }
  return map[result] || result
}

function formatType(type) {
  const map = { execution: '执行报告', scenario: '场景报告', suite: '套件报告' }
  return map[type] || type
}

function getPassRateColor(rate) {
  if (rate == null) return 'var(--text-secondary)'
  if (rate >= 95) return 'var(--el-color-success)'
  if (rate >= 80) return 'var(--el-color-warning)'
  return 'var(--el-color-danger)'
}

function formatMetricValue(value) {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

// ── AI 报告总结 ────────────────────────────────────────────

const aiStore = useAiStore()
const aiSummarizing = ref(false)
const aiSummaryResult = ref(null)
const aiSummaryVisible = ref(false)

async function handleAiSummarize() {
  if (!report.value?.id) return
  aiSummarizing.value = true
  aiSummaryResult.value = null
  try {
    const result = await aiStore.summarizeReport({ report_id: report.value.id })
    aiSummaryResult.value = result
    aiSummaryVisible.value = true
    if (result?.summary_md) {
      ElMessage.success('总结完成')
    }
  } catch (e) {
    ElMessage.error('AI 总结失败: ' + (e.response?.data?.detail || e.message || '请检查 AI 配置'))
  } finally {
    aiSummarizing.value = false
  }
}
</script>

<style scoped>
.report-detail {
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--bg-container);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--border-radius-base);
  border: 1px solid var(--border-color);
}

.header-left {
  display: flex;
  align-items: center;
}

.detail-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.stat-card {
  border-radius: var(--border-radius-base);
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}

.info-card,
.metrics-card {
  border-radius: var(--border-radius-base);
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.gate-result-card {
  border-radius: var(--border-radius-base);
}

.gate-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.gate-item {
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  padding: var(--spacing-sm);
}

.gate-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xs);
}

.gate-name {
  font-weight: 600;
  color: var(--text-primary);
}

.gate-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: 13px;
}

.detail-metric {
  color: var(--text-secondary);
  min-width: 120px;
}

.detail-expr {
  color: var(--text-primary);
  font-family: monospace;
}

.ai-summary-result {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ai-summary-result .summary-section h4 {
  margin: 0 0 8px;
  color: var(--text-secondary);
  font-size: 13px;
}

.ai-summary-result .summary-section ul {
  margin: 0;
  padding-left: 20px;
  color: var(--text-primary);
}
</style>
