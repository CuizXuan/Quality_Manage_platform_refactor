<template>
  <div class="assertion-generator">
    <!-- 页面标题区 -->
    <header class="assertion-generator__header">
      <div>
        <h1>断言生成</h1>
        <p>基于接口响应自动生成断言规则，降低用例编写成本。</p>
      </div>
    </header>

    <!-- 输入区域 -->
    <section class="assertion-generator__input">
      <el-form :model="{}" inline label-position="left" class="filter-form">
        <el-form-item label="用例ID" class="filter-item">
          <el-input
            v-model.number="caseId"
            type="number"
            placeholder="输入用例ID"
            class="input-case-id"
          />
        </el-form-item>
        <el-form-item label="响应JSON" class="filter-item filter-json">
          <el-input
            v-model="responseJson"
            type="textarea"
            :rows="4"
            placeholder="粘贴响应 JSON body"
            class="input-json"
          />
        </el-form-item>
        <el-form-item class="filter-item filter-actions">
          <el-button type="primary" :loading="aiStore.loading" @click="handleGenerate">生成断言</el-button>
        </el-form-item>
      </el-form>
      <div v-if="aiStore.error" class="error-tip">{{ aiStore.error }}</div>
    </section>

    <!-- 加载状态 -->
    <section v-if="aiStore.loading && !assertions.length" class="assertion-generator__loading">
      <div class="loading-content">
        <el-icon class="is-loading" :size="24"><Loading /></el-icon>
        <span>正在生成断言...</span>
      </div>
    </section>

    <!-- 空状态 -->
    <section v-if="!aiStore.loading && !assertions.length" class="assertion-generator__empty">
      <el-empty description="暂无断言结果，请输入用例ID或粘贴响应JSON开始生成" />
    </section>

    <!-- 断言结果表格 -->
    <section v-if="assertions.length" class="assertion-generator__result">
      <div class="result-header">
        <span class="card-title">生成的断言 ({{ assertions.length }})</span>
      </div>
      <el-table :data="assertions" stripe>
        <el-table-column label="断言类型" width="150">
          <template #default="{ row }">
            <el-tag :type="assertionTypeTag(row.assertion_type)" size="small">{{ row.assertion_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="字段 (JSONPath)" prop="field" min-width="180" show-overflow-tooltip />
        <el-table-column label="期望值" prop="expected_value" min-width="140" show-overflow-tooltip />
        <el-table-column label="描述" prop="description" min-width="200" show-overflow-tooltip />
        <el-table-column label="操作" width="100" align="center">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="handleAccept(row.id)">采纳</el-button>
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

const aiStore = useAiStore()

const caseId = ref(null)
const responseJson = ref('')

const assertions = computed(() => aiStore.assertionResult?.assertions || [])

function assertionTypeTag(type) {
  const map = {
    status_code: 'success',
    response_time: 'warning',
    json_exists: 'info',
    json_equals: 'primary',
    json_contains: 'danger',
  }
  return map[type] || 'info'
}

async function handleGenerate() {
  if (!caseId.value && !responseJson.value.trim()) {
    feedback.warning('请输入用例ID或粘贴响应JSON')
    return
  }

  const data = {}
  if (caseId.value) data.case_id = caseId.value
  if (responseJson.value.trim()) {
    try {
      data.response_body = JSON.parse(responseJson.value)
    } catch {
      feedback.error('JSON 格式错误，请检查')
      return
    }
  }

  try {
    await aiStore.generateAssertions(data)
  } catch {
    // error handled in store
  }
}

async function handleAccept(id) {
  try {
    await aiStore.acceptSuggestion(id)
    feedback.success('断言已采纳')
  } catch {
    // error handled in store
  }
}
</script>

<style scoped>
/* ── 页面容器 ── */
.assertion-generator {
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

.assertion-generator::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 24%, rgba(56, 189, 248, 0.16) 44%, transparent 62%),
    repeating-linear-gradient(90deg, transparent 0 92px, rgba(56, 189, 248, 0.075) 92px 93px);
  content: "";
  animation: case-scan 14s linear infinite;
}

.assertion-generator::after {
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
.assertion-generator__header {
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

.assertion-generator__header::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(56, 189, 248, 0.12) 50%, transparent 66%);
  opacity: 0.6;
  content: "";
  animation: case-form-scan 10s linear infinite;
}

html:not(.dark) .assertion-generator__header {
  background: rgba(255, 255, 255, 0.86);
}

.assertion-generator__header h1,
.assertion-generator__header p {
  margin: 0;
}

.assertion-generator__header h1 {
  color: var(--text-strong);
  font-size: 24px;
  line-height: 1.25;
}

.assertion-generator__header p {
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 13px;
}

/* ── 输入区 ── */
.assertion-generator__input {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 14px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background:
    linear-gradient(rgba(56, 189, 248, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.045) 1px, transparent 1px);
  background-size: 32px 32px;
  backdrop-filter: blur(10px);
}

.assertion-generator__input::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(56, 189, 248, 0.12) 50%, transparent 66%);
  opacity: 0.6;
  content: "";
  animation: case-form-scan 10s linear infinite;
}

html:not(.dark) .assertion-generator__input {
  background: rgba(255, 255, 255, 0.86);
}

.input-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex-wrap: wrap;
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

.filter-json {
  flex: 1;
  min-width: 300px;
}

.filter-actions {
  margin-left: auto;
}

.input-case-id {
  width: 220px;
  flex-shrink: 0;
}

.input-json {
  flex: 1;
  min-width: 300px;
}

.divider-text {
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 32px;
  flex-shrink: 0;
}

.input-actions {
  display: flex;
  justify-content: flex-start;
}

.error-tip {
  color: var(--color-danger);
  font-size: 14px;
}

/* ── 加载/空状态 ── */
.assertion-generator__loading,
.assertion-generator__empty {
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

html:not(.dark) .assertion-generator__loading,
html:not(.dark) .assertion-generator__empty {
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
.assertion-generator__result {
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

.assertion-generator__result::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(56, 189, 248, 0.12) 50%, transparent 66%);
  opacity: 0.6;
  content: "";
  animation: case-form-scan 10s linear infinite;
}

html:not(.dark) .assertion-generator__result {
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

.assertion-generator__result :deep(.el-table) {
  flex: 1;
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
  .assertion-generator::before,
  .assertion-generator::after,
  .assertion-generator__header::before,
  .assertion-generator__input::before,
  .assertion-generator__result::before {
    animation: none;
  }
}
</style>
