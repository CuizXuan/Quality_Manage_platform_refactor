<template>
  <div class="ai-workspace">
    <!-- AI Canvas - Main Content Area -->
    <div class="ai-canvas">
      <!-- Layer 1: Request Composer (compact, floating) -->
      <RequestComposer class="floating-card" />

      <!-- Layer 2: AI Insight Grid (MAIN FOCUS) -->
      <AIInsightGrid class="floating-card" />

      <!-- Layer 3: Response Intelligence -->
      <div class="response-section floating-card">
        <div class="section-header">
          <span class="section-icon">📡</span>
          <span class="section-title">Response Intelligence</span>
          <div v-if="requestStore.response" class="response-meta">
            <span class="status-badge" :class="statusClass">{{ requestStore.response.status_code }}</span>
            <span class="duration-badge">{{ requestStore.response.duration_ms }}ms</span>
          </div>
        </div>
        <ResponsePanel />
      </div>

      <!-- Layer 4: AI Activity Stream -->
      <AIActivityStream />
    </div>

    <!-- Case Modal -->
    <CyberModal
      v-model="showCaseModal"
      title="新建用例"
      subtitle="从 API 终端快速创建测试用例"
      size="large"
      confirm-text="创建"
      :loading="saving"
      @confirm="saveCaseFromModal"
      @cancel="closeCaseModal"
    >
      <div class="form-row">
        <div class="form-group form-group--shrink">
          <label class="form-label">请求方法</label>
          <select v-model="caseModalForm.method" class="form-select">
            <option v-for="m in ['GET','POST','PUT','DELETE','PATCH']" :key="m" :value="m">{{ m }}</option>
          </select>
        </div>
        <div class="form-group flex-1">
          <label class="form-label">请求地址</label>
          <input
            v-model="caseModalForm.url"
            class="form-input"
            placeholder="https://api.example.com/path"
          />
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">用例名称</label>
        <input
          v-model="caseModalForm.name"
          class="form-input"
          placeholder="用例名称"
        />
      </div>

      <div class="form-group">
        <label class="form-label">所属分类</label>
        <input
          v-model="caseModalForm.folder_path"
          class="form-input"
          placeholder="/用户模块/登录"
        />
      </div>

      <div class="form-group">
        <label class="form-label">描述</label>
        <textarea
          v-model="caseModalForm.description"
          class="form-textarea"
          rows="2"
          placeholder="用例描述..."
        ></textarea>
      </div>
    </CyberModal>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useRequestStore } from '@/stores/request'
import { useCaseStore } from '@/stores/caseStore'
import RequestComposer from '@/components/request/RequestComposer.vue'
import AIInsightGrid from '@/components/ai/AIInsightGrid.vue'
import ResponsePanel from '@/components/response/ResponsePanel.vue'
import AIActivityStream from '@/components/ai/AIActivityStream.vue'
import CyberModal from '@/components/common/modal/CyberModal.vue'

const requestStore = useRequestStore()
const caseStore = useCaseStore()

const showCaseModal = ref(false)
const saving = ref(false)
const caseModalForm = ref(defaultCaseForm())

const statusClass = computed(() => {
  const code = requestStore.response?.status_code
  if (!code) return ''
  return code >= 200 && code < 300 ? 'success' : code >= 400 && code < 500 ? 'warning' : 'error'
})

function defaultCaseForm() {
  return {
    name: '',
    method: 'GET',
    url: '',
    folder_path: '/终端导入',
    description: '',
    headers: {},
    body: '',
    request_body: '',
  }
}

function openCaseModal() {
  const method = requestStore.method || 'GET'
  const url = requestStore.url || ''
  const headersObj = {}
  requestStore.headers.forEach(h => {
    if (h.key && h.enabled !== false) {
      headersObj[h.key] = h.value
    }
  })
  caseModalForm.value = {
    name: `${method} ${url}`,
    method,
    url,
    folder_path: '/终端导入',
    description: `从终端调试创建 - ${new Date().toLocaleString()}`,
    headers: headersObj,
    body: requestStore.body || '',
    request_body: requestStore.body || '',
  }
  showCaseModal.value = true
}

function closeCaseModal() {
  showCaseModal.value = false
}

async function saveCaseFromModal() {
  if (!caseModalForm.value.name?.trim()) {
    ElMessage.warning('请填写用例名称')
    return
  }
  if (!caseModalForm.value.url?.trim()) {
    ElMessage.warning('请填写请求地址')
    return
  }
  saving.value = true
  try {
    const caseData = {
      name: caseModalForm.value.name.trim(),
      method: caseModalForm.value.method || 'GET',
      url: caseModalForm.value.url.trim(),
      folder_path: caseModalForm.value.folder_path || '/终端导入',
      description: caseModalForm.value.description || '',
      headers: caseModalForm.value.headers || {},
      body: caseModalForm.value.request_body || '',
      request_body: caseModalForm.value.request_body || '',
      body_type: 'json',
    }
    await caseStore.createCase(caseData)
    ElMessage.success('用例创建成功')
    closeCaseModal()
  } catch (err) {
    ElMessage.error('用例创建失败: ' + (err.message || err))
  } finally {
    saving.value = false
  }
}

// 暴露给外部调用
defineExpose({ openCaseModal })
</script>

<style scoped>
.ai-workspace {
  height: calc(100vh - var(--header-height) - 28px - 32px);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
}

.ai-canvas {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Floating Card Base */
.floating-card {
  background: var(--glass-bg);
  backdrop-filter: blur(20px);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xl);
  transition: all var(--transition-normal);
}

.floating-card:hover {
  box-shadow: var(--shadow-card-hover);
}

/* Response Section */
.response-section {
  padding: 16px 20px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.section-icon {
  font-size: 18px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  flex: 1;
}

.response-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--bg-card-hover);
}

.status-badge.success {
  background: var(--success-muted);
  color: var(--success);
}

.status-badge.warning {
  background: var(--warning-muted);
  color: var(--warning);
}

.status-badge.error {
  background: var(--error-muted);
  color: var(--error);
}

.duration-badge {
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--text-tertiary);
}

/* Form Styles for CyberModal */
.form-row {
  display: flex;
  gap: 12px;
  margin-bottom: 18px;
}

.form-row:last-child {
  margin-bottom: 0;
}

.form-group {
  margin-bottom: 18px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group--shrink {
  flex-shrink: 0;
}

.flex-1 {
  flex: 1;
  min-width: 0;
}

.form-label {
  display: block;
  font-family: var(--font-title, 'Orbitron', sans-serif);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: var(--modal-text-secondary, #888);
  margin-bottom: 8px;
}

.form-input,
.form-select,
.form-textarea {
  width: 100%;
  padding: 10px 14px;
  background: var(--bg-secondary, #0a0a0f);
  border: 1px solid var(--modal-border, rgba(0, 255, 255, 0.22));
  border-radius: 4px;
  color: var(--modal-text-primary, #e0e0e0);
  font-family: var(--font-mono, 'Fira Code', monospace);
  font-size: 13px;
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
  box-sizing: border-box;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  border-color: var(--modal-ai-accent, #00f0ff);
  box-shadow: 0 0 0 2px rgba(0, 240, 255, 0.15);
}

.form-input::placeholder,
.form-textarea::placeholder {
  color: var(--modal-text-muted, #666);
}

.form-select {
  cursor: pointer;
  min-width: 100px;
}

.form-textarea {
  resize: vertical;
  min-height: 60px;
}
</style>