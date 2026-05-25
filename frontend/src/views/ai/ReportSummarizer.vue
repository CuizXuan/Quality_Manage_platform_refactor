<template>
  <div class="report-summarizer">
    <!-- 页面标题区 -->
    <header class="report-summarizer__header">
      <div>
        <h1>报告智能总结</h1>
        <p>AI 自动分析测试报告，输出风险评分与改进建议。</p>
      </div>
    </header>

    <!-- 查询区 -->
    <section class="report-summarizer__query">
      <el-form :model="queryForm" label-position="left" class="filter-form">
        <div class="filter-form__row">
          <el-form-item label="报告ID：" class="filter-item">
            <el-input-number
              v-model="queryForm.report_id"
              :min="1"
              placeholder="输入报告ID"
              class="input-report-id"
            />
          </el-form-item>
          <div class="filter-actions">
            <el-button type="primary" :loading="aiStore.loading" @click="handleSummarize">生成总结</el-button>
            <el-button @click="handleReset">重置</el-button>
          </div>
        </div>
      </el-form>
    </section>

    <!-- 错误提示 -->
    <section v-if="aiStore.error" class="report-summarizer__error">
      <el-alert :title="aiStore.error" type="error" show-icon :closable="false" />
    </section>

    <!-- 加载状态 -->
    <section v-if="aiStore.loading && !summaryResult" class="report-summarizer__loading">
      <div class="loading-content">
        <el-icon class="is-loading" :size="24"><Loading /></el-icon>
        <span>正在生成报告总结，请稍候...</span>
      </div>
    </section>

    <!-- 空状态 -->
    <section v-if="!aiStore.loading && !summaryResult" class="report-summarizer__empty">
      <el-empty description="请输入报告ID并点击「生成总结」" />
    </section>

    <!-- 总结结果 -->
    <template v-if="summaryResult">
      <!-- 风险评分 -->
      <section class="report-summarizer__risk">
        <div class="result-header">
          <span class="card-title">风险评估</span>
        </div>
        <div class="risk-section">
          <div class="risk-score-row">
            <span class="risk-label">风险评分</span>
            <span class="risk-value" :class="riskLevelClass">{{ summaryResult.risk_score }}</span>
          </div>
          <el-progress
            :percentage="summaryResult.risk_score"
            :color="riskProgressColor"
            :show-text="false"
            class="risk-progress"
          />
          <div class="risk-hint">
            <span v-if="summaryResult.risk_score >= 80" class="risk-high">高风险 — 建议优先处理</span>
            <span v-else-if="summaryResult.risk_score >= 60" class="risk-medium">中风险 — 需要关注</span>
            <span v-else class="risk-low">低风险 — 整体状况良好</span>
          </div>
        </div>
      </section>

      <!-- 风险因素 -->
      <section v-if="summaryResult.risk_factors?.length" class="report-summarizer__factors">
        <div class="result-header">
          <span class="card-title">风险因素</span>
        </div>
        <div class="risk-factors">
          <el-tag
            v-for="(factor, index) in summaryResult.risk_factors"
            :key="index"
            type="warning"
            effect="plain"
            size="small"
          >
            {{ factor }}
          </el-tag>
        </div>
      </section>

      <!-- 总结内容 -->
      <section class="report-summarizer__summary">
        <div class="result-header">
          <span class="card-title">总结报告</span>
        </div>
        <pre class="summary-content">{{ summaryResult.summary_md }}</pre>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { useAiStore } from '@/stores/aiStore'

const aiStore = useAiStore()

const queryForm = ref({ report_id: null })

const summaryResult = computed(() => aiStore.summaryResult)

const riskLevelClass = computed(() => {
  const score = summaryResult.value?.risk_score ?? 0
  if (score >= 80) return 'risk-high'
  if (score >= 60) return 'risk-medium'
  return 'risk-low'
})

const riskProgressColor = computed(() => {
  const score = summaryResult.value?.risk_score ?? 0
  if (score >= 80) return '#67C23A'
  if (score >= 60) return '#E6A23C'
  return '#F56C6C'
})

async function handleSummarize() {
  if (!queryForm.value.report_id) return
  await aiStore.summarizeReport({ report_id: queryForm.value.report_id })
}

function handleReset() {
  queryForm.value.report_id = null
  aiStore.summaryResult = null
  aiStore.error = ''
}
</script>

<style scoped>
/* ── 页面容器 ── */
.report-summarizer {
  position: relative;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-height: 0;
  min-width: 0;
  gap: 10px;
  padding: 12px;
  background:
    linear-gradient(rgba(56, 189, 248, 0.095) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.085) 1px, transparent 1px),
    linear-gradient(145deg, rgba(34, 211, 166, 0.18), transparent 30%),
    linear-gradient(225deg, rgba(56, 189, 248, 0.22), transparent 36%),
    linear-gradient(0deg, rgba(22, 119, 255, 0.12), transparent 50%),
    var(--bg-page);
  background-size: 28px 28px, 28px 28px, auto, auto, auto, auto;
  overflow: hidden;
}

.report-summarizer::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 24%, rgba(56, 189, 248, 0.16) 44%, transparent 62%),
    repeating-linear-gradient(90deg, transparent 0 92px, rgba(56, 189, 248, 0.075) 92px 93px);
  content: "";
  animation: case-scan 14s linear infinite;
}

.report-summarizer::after {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background-image:
    radial-gradient(circle, rgba(125, 211, 252, 0.72) 0 1.2px, transparent 1.8px),
    radial-gradient(circle, rgba(45, 212, 191, 0.52) 0 1.1px, transparent 1.7px);
  background-position: 8% 16%, 80% 42%;
  background-size: 180px 160px, 240px 220px;
  opacity: 0.48;
  content: "";
  animation: case-particles 18s ease-in-out infinite alternate;
}

/* ── 标题区 ── */
.report-summarizer__header {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-height: 56px;
  padding: 12px 16px;
  border: 1px solid rgba(56, 189, 248, 0.22);
  border-radius: var(--border-radius-base);
  background:
    linear-gradient(135deg, rgba(15, 23, 42, 0.68), rgba(15, 23, 42, 0.42)),
    rgba(20, 22, 27, 0.48);
  box-shadow: 0 18px 48px rgba(2, 8, 23, 0.24), inset 0 1px 0 rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(18px) saturate(1.25);
  overflow: hidden;
}

.report-summarizer__header::after {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(90deg, rgba(56, 189, 248, 0.22), transparent 18% 82%, rgba(34, 211, 166, 0.18)),
    repeating-linear-gradient(90deg, transparent 0 42px, rgba(56, 189, 248, 0.06) 42px 43px);
  opacity: 0.65;
  content: "";
}

html:not(.dark) .report-summarizer__header {
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.86), rgba(245, 250, 255, 0.68)),
    rgba(255, 255, 255, 0.72);
  box-shadow: 0 18px 46px rgba(20, 42, 76, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.82);
}

.report-summarizer__header h1,
.report-summarizer__header p {
  margin: 0;
  position: relative;
  z-index: 1;
}

/* ── 查询区 ── */
.report-summarizer__query {
  position: relative;
  z-index: 1;
  padding: 14px;
  border: 1px solid rgba(56, 189, 248, 0.18);
  border-radius: var(--border-radius-base);
  background:
    linear-gradient(135deg, rgba(15, 23, 42, 0.54), rgba(15, 23, 42, 0.34)),
    rgba(20, 22, 27, 0.48);
  box-shadow: 0 14px 36px rgba(2, 8, 23, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(16px) saturate(1.2);
  overflow: hidden;
}

.report-summarizer__query::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(56, 189, 248, 0.1) 50%, transparent 66%),
    radial-gradient(circle at 88% 16%, rgba(34, 211, 166, 0.12), transparent 26%);
  opacity: 0.8;
  content: "";
  animation: case-form-scan 12s linear infinite;
}

html:not(.dark) .report-summarizer__query {
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.76), rgba(245, 250, 255, 0.58)),
    rgba(255, 255, 255, 0.72);
  box-shadow: 0 14px 34px rgba(20, 42, 76, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.86);
}

html:not(.dark) .report-summarizer__query::before {
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(22, 119, 255, 0.08) 50%, transparent 66%),
    radial-gradient(circle at 88% 16%, rgba(22, 119, 255, 0.1), transparent 26%);
}

html:not(.dark) .report-summarizer__header {
  background: rgba(255, 255, 255, 0.86);
}

.report-summarizer__header h1,
.report-summarizer__header p {
  margin: 0;
}

.report-summarizer__header h1 {
  color: var(--text-strong);
  font-size: 24px;
  line-height: 1.25;
}

.report-summarizer__header p {
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 13px;
}

.filter-form {
  position: relative;
  z-index: 1;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.filter-form__row {
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 12px 16px;
  align-items: center;
  width: 100%;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.filter-form :deep(.el-form-item__label) {
  display: flex;
  align-items: center;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 700;
  line-height: 34px;
}

.filter-item {
  display: inline-flex;
  align-items: center;
}

.filter-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: flex-end;
  margin-left: auto;
}

.filter-actions :deep(.el-button),
.filter-actions .el-button {
  min-width: 76px;
  height: 34px;
  margin-left: 0;
}

.input-report-id {
  width: 220px;
}

.query-actions {
  display: flex;
  gap: 12px;
}

/* ── 错误提示 ── */
.report-summarizer__error {
  position: relative;
  padding: 0;
}

/* ── 加载/空状态 ── */
.report-summarizer__loading,
.report-summarizer__empty {
  position: relative;
  z-index: 1;
  padding: 40px;
  border: 1px solid rgba(56, 189, 248, 0.18);
  border-radius: var(--border-radius-base);
  background:
    linear-gradient(135deg, rgba(15, 23, 42, 0.54), rgba(15, 23, 42, 0.34)),
    rgba(20, 22, 27, 0.48);
  box-shadow: 0 14px 36px rgba(2, 8, 23, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(16px) saturate(1.2);
  text-align: center;
}

.report-summarizer__loading::before,
.report-summarizer__empty::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(56, 189, 248, 0.1) 50%, transparent 66%),
    radial-gradient(circle at 88% 16%, rgba(34, 211, 166, 0.12), transparent 26%);
  opacity: 0.8;
  content: "";
  animation: case-form-scan 12s linear infinite;
}

html:not(.dark) .report-summarizer__loading,
html:not(.dark) .report-summarizer__empty {
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.76), rgba(245, 250, 255, 0.58)),
    rgba(255, 255, 255, 0.72);
  box-shadow: 0 14px 34px rgba(20, 42, 76, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.86);
}

html:not(.dark) .report-summarizer__loading::before,
html:not(.dark) .report-summarizer__empty::before {
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(22, 119, 255, 0.08) 50%, transparent 66%),
    radial-gradient(circle at 88% 16%, rgba(22, 119, 255, 0.1), transparent 26%);
}

/* ── 结果区 ── */
.report-summarizer__risk,
.report-summarizer__factors,
.report-summarizer__summary {
  position: relative;
  z-index: 1;
  border: 1px solid rgba(56, 189, 248, 0.18);
  border-radius: var(--border-radius-base);
  background:
    linear-gradient(135deg, rgba(15, 23, 42, 0.54), rgba(15, 23, 42, 0.34)),
    rgba(20, 22, 27, 0.48);
  box-shadow: 0 14px 36px rgba(2, 8, 23, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(16px) saturate(1.2);
  overflow: hidden;
}

.report-summarizer__risk::before,
.report-summarizer__factors::before,
.report-summarizer__summary::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(56, 189, 248, 0.1) 50%, transparent 66%),
    radial-gradient(circle at 88% 16%, rgba(34, 211, 166, 0.12), transparent 26%);
  opacity: 0.8;
  content: "";
  animation: case-form-scan 12s linear infinite;
}

html:not(.dark) .report-summarizer__risk,
html:not(.dark) .report-summarizer__factors,
html:not(.dark) .report-summarizer__summary {
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.76), rgba(245, 250, 255, 0.58)),
    rgba(255, 255, 255, 0.72);
  box-shadow: 0 14px 34px rgba(20, 42, 76, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.86);
}

html:not(.dark) .report-summarizer__risk::before,
html:not(.dark) .report-summarizer__factors::before,
html:not(.dark) .report-summarizer__summary::before {
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(22, 119, 255, 0.08) 50%, transparent 66%),
    radial-gradient(circle at 88% 16%, rgba(22, 119, 255, 0.1), transparent 26%);
}

.result-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-strong);
}

/* ── 风险评分 ── */
.risk-section {
  padding: 16px;
}

.risk-score-row {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.risk-label {
  font-size: 14px;
  color: var(--text-secondary);
}

.risk-value {
  font-size: 32px;
  font-weight: 700;
  line-height: 1;
}

.risk-value.risk-high { color: #67C23A; }
.risk-value.risk-medium { color: #E6A23C; }
.risk-value.risk-low { color: #F56C6C; }

.risk-progress {
  margin-top: 12px;
}

.risk-hint {
  margin-top: 8px;
  font-size: 13px;
}

.risk-hint .risk-high { color: #67C23A; }
.risk-hint .risk-medium { color: #E6A23C; }
.risk-hint .risk-low { color: #F56C6C; }

/* ── 风险因素 ── */
.risk-factors {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 16px;
}

/* ── 总结内容 ── */
.summary-content {
  background: var(--bg-page);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  padding: 16px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-primary);
  white-space: pre-wrap;
  word-break: break-word;
  overflow-x: auto;
  margin: 0;
}

@keyframes case-scan {
  from { transform: translateX(-24%); }
  to { transform: translateX(24%); }
}

@keyframes case-particles {
  from { transform: translate3d(0, 0, 0); }
  to { transform: translate3d(26px, -18px, 0); }
}

@keyframes case-form-scan {
  from { transform: translateX(-22%); }
  to { transform: translateX(22%); }
}

@media (prefers-reduced-motion: reduce) {
  .report-summarizer::before,
  .report-summarizer::after {
    animation: none;
  }
}
</style>
