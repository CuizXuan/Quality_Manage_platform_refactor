<template>
  <div class="variant-generator">
    <!-- 页面标题区 -->
    <header class="variant-generator__header">
      <div>
        <h1>用例变体生成</h1>
        <p>基于原始用例批量生成语义等价变体，提升测试覆盖率。</p>
      </div>
    </header>

    <!-- 输入区 -->
    <section class="variant-generator__input">
      <el-form :model="{}" inline label-position="left" class="filter-form">
        <el-form-item label="原始用例" class="filter-item">
          <el-select
            v-model="sourceCaseId"
            placeholder="选择或搜索用例"
            filterable
            remote
            :remote-method="searchCases"
            class="case-select"
          >
            <el-option
              v-for="c in caseOptions"
              :key="c.id"
              :label="c.name"
              :value="c.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="变体数量" class="filter-item">
          <el-input-number v-model="variantCount" :min="1" :max="20" />
        </el-form-item>
        <el-form-item label="变异策略" class="filter-item">
          <el-checkbox-group v-model="strategies" class="strategy-group">
            <el-checkbox value="boundary">边界值</el-checkbox>
            <el-checkbox value="equivalence">等价类</el-checkbox>
            <el-checkbox value="negative">逆向思维</el-checkbox>
            <el-checkbox value="noise">噪声注入</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item class="filter-item filter-actions">
          <el-button type="primary" :loading="aiStore.loading" @click="handleGenerate">生成变体</el-button>
        </el-form-item>
      </el-form>
    </section>

    <!-- 加载状态 -->
    <section v-if="aiStore.loading && !variants.length" class="variant-generator__loading">
      <div class="loading-content">
        <el-icon class="is-loading" :size="24"><Loading /></el-icon>
        <span>正在生成变体...</span>
      </div>
    </section>

    <!-- 空状态 -->
    <section v-if="!aiStore.loading && !variants.length" class="variant-generator__empty">
      <el-empty description="暂无变体结果，请选择用例并设置参数开始生成" />
    </section>

    <!-- 变体结果 -->
    <section v-if="variants.length" class="variant-generator__result">
      <div class="result-header">
        <span class="card-title">生成的变体 ({{ variants.length }})</span>
      </div>
      <el-table :data="variants" stripe>
        <el-table-column type="index" label="#" width="60" align="center" />
        <el-table-column label="变体类型" width="120" align="center">
          <template #default="{ row }">
            <el-tag size="small">{{ row.variant_type || 'standard' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="变体描述" prop="description" min-width="200" show-overflow-tooltip />
        <el-table-column label="变异策略" prop="strategy" min-width="120" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="text-secondary">{{ row.strategy || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" align="center">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="handleAdopt(row)">采纳</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import feedback from '@/utils/feedback'
import { useAiStore } from '@/stores/aiStore'
import { caseApi } from '@/api/case'

const aiStore = useAiStore()

const sourceCaseId = ref(null)
const variantCount = ref(3)
const strategies = ref(['boundary', 'equivalence'])
const caseOptions = ref([])

const variants = computed(() => aiStore.variantResult?.variants || [])

async function searchCases(query) {
  if (!query) return
  try {
    const res = await caseApi.list({ keyword: query, page: 1, page_size: 20 })
    caseOptions.value = res.data.items || res.data || []
  } catch {
    caseOptions.value = []
  }
}

async function handleGenerate() {
  if (!sourceCaseId.value) {
    feedback.warning('请选择原始用例')
    return
  }
  try {
    await aiStore.generateVariants({
      case_id: sourceCaseId.value,
      count: variantCount.value,
      strategies: strategies.value,
    })
  } catch {
    // error handled in store
  }
}

async function handleAdopt(variant) {
  try {
    await aiStore.acceptSuggestion(variant.id)
    feedback.success('变体已采纳')
  } catch {
    // error handled in store
  }
}
</script>

<style scoped>
/* ── 页面容器 ── */
.variant-generator {
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

.variant-generator::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 24%, rgba(56, 189, 248, 0.16) 44%, transparent 62%),
    repeating-linear-gradient(90deg, transparent 0 92px, rgba(56, 189, 248, 0.075) 92px 93px);
  content: "";
  animation: case-scan 14s linear infinite;
}

.variant-generator::after {
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
  .variant-generator::before,
  .variant-generator::after {
    animation: none;
  }
}

/* ── 标题区 ── */
.variant-generator__header {
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-height: 56px;
  padding: 12px 16px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background:
    linear-gradient(rgba(56, 189, 248, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.045) 1px, transparent 1px);
  background-size: 32px 32px;
  backdrop-filter: blur(10px);
}

.variant-generator__header::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(56, 189, 248, 0.12) 50%, transparent 66%);
  opacity: 0.6;
  content: "";
  animation: case-form-scan 10s linear infinite;
}

html:not(.dark) .variant-generator__header {
  background: rgba(255, 255, 255, 0.86);
}

.variant-generator__header h1,
.variant-generator__header p {
  margin: 0;
}

.variant-generator__header h1 {
  color: var(--text-strong);
  font-size: 24px;
  line-height: 1.25;
}

.variant-generator__header p {
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 13px;
}

/* ── 输入区 ── */
.variant-generator__input {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 14px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background:
    linear-gradient(rgba(56, 189, 248, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.045) 1px, transparent 1px);
  background-size: 32px 32px;
  backdrop-filter: blur(10px);
}

.variant-generator__input::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(56, 189, 248, 0.12) 50%, transparent 66%);
  opacity: 0.6;
  content: "";
  animation: case-form-scan 10s linear infinite;
}

html:not(.dark) .variant-generator__input {
  background: rgba(255, 255, 255, 0.86);
}

.input-group {
  display: flex;
  align-items: center;
  gap: 16px;
}

.input-label {
  min-width: 80px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 16px;
  align-items: center;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.filter-form :deep(.el-form-item__label) {
  color: var(--text-secondary);
  font-size: 13px;
}

.filter-item {
  display: inline-flex;
  align-items: center;
}

.filter-actions {
  margin-left: auto;
}

.case-select {
  width: 360px;
}

.strategy-group {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.input-actions {
  display: flex;
  justify-content: flex-start;
  padding-top: 4px;
}

/* ── 加载/空状态 ── */
.variant-generator__loading,
.variant-generator__empty {
  position: relative;
  padding: 40px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background:
    linear-gradient(rgba(56, 189, 248, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.045) 1px, transparent 1px);
  background-size: 32px 32px;
  backdrop-filter: blur(10px);
  text-align: center;
}

html:not(.dark) .variant-generator__loading,
html:not(.dark) .variant-generator__empty {
  background: rgba(255, 255, 255, 0.86);
}

.loading-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-secondary);
}

/* ── 结果表格 ── */
.variant-generator__result {
  position: relative;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background:
    linear-gradient(rgba(56, 189, 248, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.045) 1px, transparent 1px);
  background-size: 32px 32px;
  backdrop-filter: blur(10px);
  overflow: hidden;
}

.variant-generator__result::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(56, 189, 248, 0.12) 50%, transparent 66%);
  opacity: 0.6;
  content: "";
  animation: case-form-scan 10s linear infinite;
}

html:not(.dark) .variant-generator__result {
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

.variant-generator__result :deep(.el-table) {
  flex: 1;
}

.text-secondary {
  color: var(--text-secondary);
  font-size: 13px;
}
</style>
