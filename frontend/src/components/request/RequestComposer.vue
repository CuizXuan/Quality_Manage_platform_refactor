<template>
  <div class="request-composer floating-card">
    <div class="composer-header">
      <span class="composer-icon">⬡</span>
      <span class="composer-title">Request Composer</span>
      <div class="composer-actions">
        <button class="action-btn" @click="toggleCollapse" :title="collapsed ? '展开' : '收起'">
          <svg v-if="!collapsed" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="18 15 12 9 6 15"></polyline>
          </svg>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </button>
      </div>
    </div>

    <div v-show="!collapsed" class="composer-body">
      <!-- Compact Request Bar -->
      <div class="compact-request-bar">
        <select v-model="method" class="method-select" :class="'method-' + method.toLowerCase()">
          <option v-for="m in methods" :key="m" :value="m">{{ m }}</option>
        </select>

        <input
          v-model="url"
          class="url-input"
          placeholder="输入请求地址或粘贴 cURL..."
          @keydown.meta.enter="send"
          @keydown.ctrl.enter="send"
        />

        <button
          class="send-btn"
          @click="send"
          :disabled="loading || !url.trim()"
          :class="{ loading: loading }"
        >
          <span v-if="loading" class="loading-icon">⟳</span>
          <span v-else>▶</span>
        </button>
      </div>

      <!-- Parse Area -->
      <div class="parse-area">
        <div class="parse-header">
          <span class="parse-label">📋 粘贴 cURL / Fetch 自动解析</span>
          <button v-if="rawInput" class="parse-btn" @click="clearParse">清空</button>
        </div>
        <textarea
          v-model="rawInput"
          class="parse-textarea"
          placeholder="粘贴 cURL 或 Fetch 命令，自动解析请求体、请求头等..."
          rows="3"
          @keydown.meta.enter="handleParse"
          @keydown.ctrl.enter="handleParse"
        ></textarea>
        <div class="parse-actions">
          <button class="btn-parse" @click="handleParse" :disabled="!rawInput.trim()">
            ✨ 智能解析
          </button>
        </div>
        <div v-if="parseError" class="parse-error">{{ parseError }}</div>
      </div>

      <!-- AI Suggestions -->
      <div v-if="url" class="ai-suggestions">
        <div class="suggestion-item" v-for="(s, idx) in aiSuggestions" :key="idx">
          <span class="suggestion-icon">{{ s.icon }}</span>
          <span class="suggestion-text">{{ s.text }}</span>
        </div>
      </div>

      <!-- Compact Tabs -->
      <div class="compact-tabs">
        <button
          v-for="tab in compactTabs"
          :key="tab.value"
          :class="{ active: activeTab === tab.value }"
          @click="activeTab = tab.value"
        >
          {{ tab.label }}
          <span v-if="tab.count > 0" class="tab-count">{{ tab.count }}</span>
        </button>
      </div>

      <!-- Tab Content -->
      <div class="compact-tab-content">
        <div v-show="activeTab === 'headers'" class="tab-pane">
          <KeyValueTable
            :modelValue="headers"
            @update:modelValue="val => requestStore.headers = val"
          />
        </div>
        <div v-show="activeTab === 'params'" class="tab-pane">
          <KeyValueTable
            :modelValue="params"
            @update:modelValue="val => requestStore.params = val"
          />
        </div>
        <div v-show="activeTab === 'body'" class="tab-pane">
          <BodyEditor
            :modelValue="body"
            @update:modelValue="val => requestStore.body = val"
            @update:type="t => requestStore.bodyType = t"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useRequestStore } from '@/stores/request'
import KeyValueTable from './KeyValueTable.vue'
import BodyEditor from './BodyEditor.vue'
import { proxyApi } from '@/api/client'
import { parseRequest, detectFormat } from '@/utils/parser'

const requestStore = useRequestStore()

const method = computed({
  get: () => requestStore.method,
  set: (v) => { requestStore.method = v }
})

const url = computed({
  get: () => requestStore.url,
  set: (v) => { requestStore.url = v }
})

const headers = computed({
  get: () => requestStore.headers,
  set: (v) => { requestStore.headers = v }
})

const params = computed({
  get: () => requestStore.params,
  set: (v) => { requestStore.params = v }
})

const body = computed({
  get: () => requestStore.body,
  set: (v) => { requestStore.body = v }
})

const methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
const loading = ref(false)
const collapsed = ref(false)
const activeTab = ref('params')

// Parse state
const rawInput = ref('')
const parseError = ref('')

function clearParse() {
  rawInput.value = ''
  parseError.value = ''
}

function handleParse() {
  parseError.value = ''
  const input = rawInput.value.trim()
  if (!input) {
    parseError.value = '请先输入 cURL 或 Fetch 命令'
    return
  }
  const format = detectFormat(input)
  if (format === 'unknown') {
    parseError.value = '不支持的格式，请输入 cURL 或 Fetch 格式'
    return
  }
  try {
    const result = parseRequest(input)
    requestStore.setRequest(result)
    ElMessage.success('解析成功')
  } catch (e) {
    parseError.value = e.message
  }
}

// AI Suggestions
const aiSuggestions = computed(() => {
  const suggestions = []
  const currentUrl = url.value

  if (!currentUrl) return suggestions

  // 检测 API 类型
  if (currentUrl.includes('/api/')) {
    suggestions.push({ icon: '🔗', text: '检测到 RESTful API 路径' })
  }
  if (currentUrl.includes('localhost') || currentUrl.includes('127.0.0.1')) {
    suggestions.push({ icon: '💻', text: '本地开发环境' })
  }
  if (currentUrl.startsWith('https://')) {
    suggestions.push({ icon: '🔒', text: 'HTTPS 安全连接' })
  } else if (currentUrl.startsWith('http://')) {
    suggestions.push({ icon: '⚠', text: 'HTTP 连接可能存在安全风险' })
  }

  // 方法相关建议
  if (['POST', 'PUT', 'PATCH'].includes(method.value) && !body.value) {
    suggestions.push({ icon: '📝', text: `${method.value} 请求建议携带 body` })
  }

  // Header 建议
  const headerKeys = headers.value.filter(h => h.enabled && h.key).map(h => h.key.toLowerCase())
  if (!headerKeys.some(k => k.includes('content-type'))) {
    suggestions.push({ icon: '📋', text: '建议添加 Content-Type' })
  }
  if (!headerKeys.some(k => k.includes('authorization'))) {
    suggestions.push({ icon: '🔐', text: '建议添加认证信息' })
  }

  return suggestions.slice(0, 4)
})

const compactTabs = computed(() => [
  { label: '参数', value: 'params', count: params.value.filter(p => p.key.trim()).length },
  { label: '请求头', value: 'headers', count: headers.value.filter(h => h.key.trim()).length },
  { label: '请求体', value: 'body', count: body.value ? 1 : 0 },
])

function toggleCollapse() {
  collapsed.value = !collapsed.value
}

async function send() {
  if (!url.value?.trim() || loading.value) return

  loading.value = true
  requestStore.loading = true
  requestStore.error = null

  window.dispatchEvent(new CustomEvent('request-sent'))

  const headersObj = {}
  requestStore.headers.forEach(h => {
    if (h.key.trim() && h.enabled !== false) {
      headersObj[h.key] = h.value
    }
  })

  const paramsObj = {}
  requestStore.params.forEach(p => {
    if (p.key.trim() && p.enabled !== false) {
      paramsObj[p.key] = p.value
    }
  })

  let fullUrl = url.value.trim()
  try {
    const urlObj = new URL(fullUrl.startsWith('http') ? fullUrl : 'http://' + fullUrl)
    Object.entries(paramsObj).forEach(([k, v]) => urlObj.searchParams.set(k, v))
    fullUrl = urlObj.toString()
  } catch (e) {}

  requestStore.fullUrl = fullUrl

  try {
    const response = await proxyApi.send({
      method: requestStore.method,
      url: fullUrl,
      headers: headersObj,
      params: {},
      body: ['POST', 'PUT', 'PATCH'].includes(requestStore.method) ? requestStore.body : undefined,
      timeout: 30,
    })
    requestStore.response = response.data
  } catch (e) {
    requestStore.error = e.response?.data?.detail || e.message
  } finally {
    loading.value = false
    requestStore.loading = false
  }
}
</script>

<style scoped>
.request-composer {
  padding: 16px 20px;
}

.composer-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.composer-icon {
  font-size: 18px;
  color: var(--primary);
}

.composer-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  flex: 1;
}

.composer-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.action-btn:hover {
  background: var(--bg-card-hover);
  color: var(--text-primary);
}

.action-btn svg {
  width: 14px;
  height: 14px;
}

.composer-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Compact Request Bar */
.compact-request-bar {
  display: flex;
  gap: 8px;
}

.method-select {
  width: 100px;
  padding: 10px 12px;
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  outline: none;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.method-select:focus {
  border-color: var(--primary);
}

.method-select.method-get { color: var(--method-get); }
.method-select.method-post { color: var(--method-post); }
.method-select.method-put { color: var(--method-put); }
.method-select.method-delete { color: var(--method-delete); }
.method-select.method-patch { color: var(--method-patch); }

.url-input {
  flex: 1;
  padding: 10px 14px;
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--text-primary);
  outline: none;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.url-input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-muted);
}

.url-input::placeholder {
  color: var(--text-tertiary);
}

.send-btn {
  width: 48px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--primary);
  border: none;
  color: white;
  font-size: 16px;
  cursor: pointer;
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.send-btn:hover:not(:disabled) {
  background: var(--primary-hover);
  transform: translateY(-1px);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.send-btn.loading {
  background: var(--secondary);
}

.loading-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* AI Suggestions */
.ai-suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bg-card);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-default);
}

.suggestion-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--text-secondary);
}

.suggestion-icon {
  font-size: 12px;
}

/* Compact Tabs */
.compact-tabs {
  display: flex;
  gap: 4px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-default);
}

.compact-tabs button {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-size: 12px;
  font-family: var(--font-body);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.compact-tabs button:hover {
  background: var(--bg-card);
  color: var(--text-primary);
}

.compact-tabs button.active {
  background: var(--primary-muted);
  color: var(--primary);
}

.tab-count {
  font-size: 10px;
  padding: 1px 5px;
  border-radius: 8px;
  background: var(--bg-card);
  color: var(--text-tertiary);
}

.compact-tabs button.active .tab-count {
  background: var(--primary);
  color: white;
}

/* Tab Content */
.compact-tab-content {
  min-height: 80px;
}

.tab-pane {
  animation: fade-in 0.2s ease;
}

@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Parse Area */
.parse-area {
  margin-top: 12px;
  padding: 12px;
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
}

.parse-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.parse-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
}

.parse-btn {
  padding: 2px 8px;
  background: transparent;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xs);
  color: var(--text-tertiary);
  font-size: 11px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.parse-btn:hover {
  background: var(--bg-card-hover);
  color: var(--text-secondary);
}

.parse-textarea {
  width: 100%;
  padding: 10px 12px;
  background: var(--bg-primary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: 12px;
  line-height: 1.5;
  resize: vertical;
  box-sizing: border-box;
}

.parse-textarea:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-muted);
}

.parse-textarea::placeholder {
  color: var(--text-tertiary);
}

.parse-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}

.btn-parse {
  padding: 6px 14px;
  background: var(--primary);
  border: none;
  border-radius: var(--radius-sm);
  color: white;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-parse:hover:not(:disabled) {
  background: var(--primary-hover);
}

.btn-parse:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.parse-error {
  margin-top: 8px;
  padding: 6px 10px;
  background: var(--error-muted);
  border-radius: var(--radius-sm);
  color: var(--error);
  font-size: 12px;
}
</style>