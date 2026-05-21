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
      <div class="input-group">
        <label class="input-label">原始用例</label>
        <el-select
          v-model="sourceCaseId"
          placeholder="选择或搜索用例"
          filterable
          remote
          :remote-method="searchCases"
          class="case-select"
          @keyup.enter="handleGenerate"
        >
          <el-option
            v-for="c in caseOptions"
            :key="c.id"
            :label="c.name"
            :value="c.id"
          />
        </el-select>
      </div>

      <div class="input-group">
        <label class="input-label">变体数量</label>
        <el-input-number v-model="variantCount" :min="1" :max="20" />
      </div>

      <div class="input-group">
        <label class="input-label">变异策略</label>
        <el-checkbox-group v-model="strategies" class="strategy-group">
          <el-checkbox value="boundary">边界值</el-checkbox>
          <el-checkbox value="equivalence">等价类</el-checkbox>
          <el-checkbox value="negative">逆向思维</el-checkbox>
          <el-checkbox value="noise">噪声注入</el-checkbox>
        </el-checkbox-group>
      </div>

      <div class="input-actions">
        <el-button type="primary" :loading="aiStore.loading" @click="handleGenerate">生成变体</el-button>
      </div>
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
.variant-generator__header {
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
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 14px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: rgba(20, 22, 27, 0.7);
  box-shadow: var(--box-shadow-light);
  backdrop-filter: blur(10px);
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
  padding: 40px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: rgba(20, 22, 27, 0.7);
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
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: rgba(20, 22, 27, 0.7);
  box-shadow: var(--box-shadow-light);
  backdrop-filter: blur(10px);
  overflow: hidden;
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
