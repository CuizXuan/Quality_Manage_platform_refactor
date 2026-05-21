<template>
  <div class="failure-analyzer">
    <!-- 页面标题区 -->
    <header class="failure-analyzer__header">
      <div>
        <h1>失败归因分析</h1>
        <p>智能分析执行失败根因，自动推荐修复方案。</p>
      </div>
    </header>

    <!-- 分析输入 -->
    <section class="failure-analyzer__input">
      <div class="input-row">
        <el-input
          v-model.number="executionStepId"
          type="number"
          placeholder="输入执行步骤ID"
          class="input-id"
          @keyup.enter="handleAnalyze"
        />
        <el-button type="primary" :loading="aiStore.loading" @click="handleAnalyze">开始分析</el-button>
      </div>
      <div v-if="aiStore.error" class="error-tip">{{ aiStore.error }}</div>
    </section>

    <!-- 加载状态 -->
    <section v-if="aiStore.loading && !analysisResult" class="failure-analyzer__loading">
      <div class="loading-content">
        <el-icon class="is-loading" :size="24"><Loading /></el-icon>
        <span>正在分析失败原因...</span>
      </div>
    </section>

    <!-- 空状态 -->
    <section v-if="!aiStore.loading && !analysisResult" class="failure-analyzer__empty">
      <el-empty description="暂无分析结果，请输入执行步骤ID开始分析" />
    </section>

    <!-- 分析结果 -->
    <template v-if="analysisResult">
      <!-- 根因与严重度 -->
      <section class="failure-analyzer__result">
        <div class="result-header">
          <span class="card-title">分析结果</span>
        </div>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="根因">{{ analysisResult.root_cause || '—' }}</el-descriptions-item>
          <el-descriptions-item label="严重度">
            <el-tag :type="severityType" size="small">{{ analysisResult.severity || 'unknown' }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </section>

      <!-- 建议列表 -->
      <section v-if="analysisResult.suggestions?.length" class="failure-analyzer__suggestions">
        <div class="result-header">
          <span class="card-title">修复建议</span>
        </div>
        <div class="suggestion-list">
          <div
            v-for="suggestion in analysisResult.suggestions"
            :key="suggestion.id"
            class="suggestion-item"
          >
            <div class="suggestion-info">
              <div class="suggestion-type">
                <el-tag size="small" type="info">{{ suggestion.type }}</el-tag>
              </div>
              <div class="suggestion-desc">{{ suggestion.description }}</div>
              <div class="suggestion-effort">
                <el-tag size="small" :type="effortType(suggestion.effort)">{{ suggestion.effort || 'medium' }}</el-tag>
              </div>
            </div>
            <div class="suggestion-action">
              <el-button size="small" type="primary" @click="handleAccept(suggestion.id)">采纳</el-button>
            </div>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import feedback from '@/utils/feedback'
import { useAiStore } from '@/stores/aiStore'

const aiStore = useAiStore()

const executionStepId = ref(null)

const analysisResult = computed(() => aiStore.failureResult)

const severityType = computed(() => {
  const map = { critical: 'danger', high: 'warning', medium: 'info', low: 'success' }
  return map[analysisResult.value?.severity] || 'info'
})

function effortType(effort) {
  const map = { low: 'success', medium: 'warning', high: 'danger' }
  return map[effort] || 'info'
}

async function handleAnalyze() {
  if (!executionStepId.value) {
    feedback.warning('请输入执行步骤ID')
    return
  }
  try {
    await aiStore.analyzeFailure({ execution_step_id: executionStepId.value })
  } catch {
    // error handled in store
  }
}

async function handleAccept(id) {
  try {
    await aiStore.acceptSuggestion(id)
    feedback.success('建议已采纳')
  } catch {
    // error handled in store
  }
}
</script>

<style scoped>
/* ── 页面容器 ── */
.failure-analyzer {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-height: 0;
  min-width: 0;
  gap: 10px;
  padding: 12px;
  background:
    radial-gradient(circle at top right, rgba(56, 189, 248, 0.13), transparent 30%),
    var(--bg-page);
  overflow: hidden;
}

/* ── 标题区 ── */
.failure-analyzer__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-height: 56px;
  padding: 12px 16px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: rgba(20, 22, 27, 0.7);
  box-shadow: var(--box-shadow-light);
  backdrop-filter: blur(10px);
}

html:not(.dark) .failure-analyzer__header {
  background: rgba(255, 255, 255, 0.86);
}

.failure-analyzer__header h1,
.failure-analyzer__header p {
  margin: 0;
}

.failure-analyzer__header h1 {
  color: var(--text-strong);
  font-size: 24px;
  line-height: 1.25;
}

.failure-analyzer__header p {
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 13px;
}

/* ── 输入区 ── */
.failure-analyzer__input {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 14px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: rgba(20, 22, 27, 0.7);
  box-shadow: var(--box-shadow-light);
  backdrop-filter: blur(10px);
}

html:not(.dark) .failure-analyzer__input {
  background: rgba(255, 255, 255, 0.86);
}

.input-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.input-id {
  width: 280px;
}

.error-tip {
  color: var(--color-danger);
  font-size: 14px;
}

/* ── 加载/空状态 ── */
.failure-analyzer__loading,
.failure-analyzer__empty {
  padding: 40px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: rgba(20, 22, 27, 0.7);
  backdrop-filter: blur(10px);
  text-align: center;
}

html:not(.dark) .failure-analyzer__loading,
html:not(.dark) .failure-analyzer__empty {
  background: rgba(255, 255, 255, 0.86);
}

.loading-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-secondary);
}

/* ── 结果/建议 ── */
.failure-analyzer__result,
.failure-analyzer__suggestions {
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: rgba(20, 22, 27, 0.7);
  box-shadow: var(--box-shadow-light);
  backdrop-filter: blur(10px);
  overflow: hidden;
}

html:not(.dark) .failure-analyzer__result,
html:not(.dark) .failure-analyzer__suggestions {
  background: rgba(255, 255, 255, 0.86);
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

/* ── 建议列表 ── */
.suggestion-list {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.suggestion-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 12px;
  background: var(--bg-page);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  gap: 12px;
}

.suggestion-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  flex: 1;
  min-width: 0;
}

.suggestion-type {
  flex-shrink: 0;
}

.suggestion-desc {
  flex: 1;
  min-width: 200px;
  color: var(--text-primary);
}

.suggestion-effort {
  flex-shrink: 0;
}

.suggestion-action {
  flex-shrink: 0;
}
</style>
