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
      <div class="input-row">
        <el-input
          v-model.number="caseId"
          type="number"
          placeholder="输入用例ID"
          class="input-case-id"
          @keyup.enter="handleGenerate"
        />
        <span class="divider-text">或</span>
        <el-input
          v-model="responseJson"
          type="textarea"
          :rows="4"
          placeholder="粘贴响应 JSON body"
          class="input-json"
          @keyup.enter="handleGenerate"
        />
      </div>
      <div class="input-actions">
        <el-button type="primary" :loading="aiStore.loading" @click="handleGenerate">生成断言</el-button>
      </div>
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
.assertion-generator__header {
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

html:not(.dark) .assertion-generator__input {
  background: rgba(255, 255, 255, 0.86);
}

.input-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex-wrap: wrap;
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
  padding: 40px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: rgba(20, 22, 27, 0.7);
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
</style>
