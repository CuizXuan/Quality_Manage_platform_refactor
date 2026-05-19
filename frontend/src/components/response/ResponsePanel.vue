<template>
  <div class="response-panel panel">
    <div class="panel-header">
      <span class="panel-title">
        <span class="prompt">&gt;</span> 响应
      </span>
      <div v-if="response" class="response-actions">
        <button class="action-btn" @click="copyResponse" title="复制">📋 COPY</button>
        <button class="action-btn" @click="downloadResponse" title="下载">⬇ DOWNLOAD</button>
        <button class="action-btn" @click="$emit('convert-to-case')" title="转用例">⚡ 转用例</button>
      </div>
    </div>

    <!-- Loading 状态 -->
    <div v-if="loading" class="response-loading">
      <div class="loading-spinner">⟳</div>
      <span class="loading-text">等待响应...</span>
      <div class="loading-bar">
        <div class="loading-progress"></div>
      </div>
    </div>

    <!-- Error 状态 -->
    <div v-else-if="error" class="response-error">
      <div class="error-title">
        <span class="error-icon">⚠</span>
        连接失败
      </div>
      <div class="error-detail error-state">{{ error }}</div>
    </div>

    <!-- 响应内容 -->
    <div v-else-if="response" class="response-content">
      <!-- 概览栏 -->
      <div class="response-overview">
        <span class="status-badge" :class="getStatusClass(response.status_code)">
          {{ response.status_code }} {{ response.status_text }}
        </span>
        <span class="overview-item">
          <span class="item-icon">⏱</span>
          {{ response.duration_ms }}ms
        </span>
        <span class="overview-item">
          <span class="item-icon">📦</span>
          {{ formatSize(response.content_size) }}
        </span>
      </div>

      <!-- Tab 切换 -->
      <div class="response-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- 响应体 Tab -->
      <div v-show="activeTab === 'body'" class="tab-content">
        <div class="section-header" @click="bodyExpanded = !bodyExpanded">
          <span>响应体</span>
          <span>{{ bodyExpanded ? '▼' : '▶' }}</span>
        </div>
        <div v-show="bodyExpanded" class="response-body">
          <div class="body-toolbar">
            <button @click="toggleFormat" :class="{ active: formatted }">
              {{ formatted ? '📐 原始' : '📄 格式化' }}
            </button>
          </div>
          <pre class="body-content" :class="{ 'body-formatted': formatted }">{{ displayContent }}</pre>
        </div>

        <div class="section-header" @click="headersExpanded = !headersExpanded">
          <span>响应头 ({{ responseHeadersCount }})</span>
          <span>{{ headersExpanded ? '▼' : '▶' }}</span>
        </div>
        <div v-show="headersExpanded" class="response-headers">
          <div v-for="(value, key) in response.headers" :key="key" class="header-row">
            <span class="header-key">{{ key }}</span>
            <span class="header-value">{{ value }}</span>
          </div>
        </div>
      </div>

      <!-- 请求参数 Tab -->
      <div v-show="activeTab === 'request'" class="tab-content">
        <div class="section-header" @click="reqUrlExpanded = !reqUrlExpanded">
          <span>请求 URL</span>
          <span>{{ reqUrlExpanded ? '▼' : '▶' }}</span>
        </div>
        <div v-show="reqUrlExpanded" class="request-url">
          <div class="url-row">
            <span class="method-badge" :class="'method-' + method.toLowerCase()">{{ method }}</span>
            <span class="url-text">{{ fullUrl || requestStore.url }}</span>
          </div>
        </div>

        <div class="section-header" @click="reqHeadersExpanded = !reqHeadersExpanded">
          <span>请求头 ({{ requestHeadersCount }})</span>
          <span>{{ reqHeadersExpanded ? '▼' : '▶' }}</span>
        </div>
        <div v-show="reqHeadersExpanded" class="request-headers">
          <div v-for="(item, index) in enabledHeaders" :key="index" class="header-row">
            <span class="header-key">{{ item.key }}</span>
            <span class="header-value">{{ item.value }}</span>
          </div>
          <div v-if="enabledHeaders.length === 0" class="empty-hint">-- 暂无数据 --</div>
        </div>

        <div class="section-header" @click="reqParamsExpanded = !reqParamsExpanded">
          <span>查询参数 ({{ queryParamsCount }})</span>
          <span>{{ reqParamsExpanded ? '▼' : '▶' }}</span>
        </div>
        <div v-show="reqParamsExpanded" class="request-headers">
          <div v-for="(item, index) in enabledParams" :key="index" class="header-row">
            <span class="header-key">{{ item.key }}</span>
            <span class="header-value">{{ item.value }}</span>
          </div>
          <div v-if="enabledParams.length === 0" class="empty-hint">-- 暂无数据 --</div>
        </div>

        <div class="section-header" @click="reqBodyExpanded = !reqBodyExpanded">
          <span>请求体</span>
          <span>{{ reqBodyExpanded ? '▼' : '▶' }}</span>
        </div>
        <div v-show="reqBodyExpanded" class="request-body">
          <pre v-if="requestStore.body" class="body-content">{{ requestStore.body }}</pre>
          <div v-else class="empty-hint">-- 暂无数据 --</div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="response-empty">
      <div class="empty-icon">◌</div>
      <div class="empty-text">等待输入</div>
      <div class="empty-hint">// 发送请求以查看响应</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRequestStore } from '../../stores/request'

const emit = defineEmits(['convert-to-case'])
const requestStore = useRequestStore()

const loading = computed(() => requestStore.loading)
const error = computed(() => requestStore.error)
const response = computed(() => requestStore.response)
const method = computed(() => requestStore.method)
const fullUrl = computed(() => requestStore.fullUrl)

const tabs = [
  { key: 'body', label: '响应体' },
  { key: 'request', label: '请求信息' }
]
const activeTab = ref('body')

const bodyExpanded = ref(true)
const headersExpanded = ref(false)
const formatted = ref(true)

const reqUrlExpanded = ref(true)
const reqHeadersExpanded = ref(true)
const reqParamsExpanded = ref(true)
const reqBodyExpanded = ref(true)

const enabledHeaders = computed(() => {
  return requestStore.headers.filter(h => h.key.trim() && h.enabled !== false)
})

const enabledParams = computed(() => {
  return requestStore.params.filter(p => p.key.trim() && p.enabled !== false)
})

const requestHeadersCount = computed(() => enabledHeaders.value.length)
const queryParamsCount = computed(() => enabledParams.value.length)

const displayContent = computed(() => {
  if (!response.value?.content) return ''
  if (formatted.value) {
    try {
      const parsed = JSON.parse(response.value.content)
      return JSON.stringify(parsed, null, 2)
    } catch (e) {
      return response.value.content
    }
  }
  return response.value.content
})

const responseHeadersCount = computed(() => {
  if (!response.value?.headers) return 0
  return Object.keys(response.value.headers).length
})

function getStatusClass(code) {
  if (code >= 200 && code < 300) return 'status-2xx'
  if (code >= 300 && code < 400) return 'status-3xx'
  if (code >= 400 && code < 500) return 'status-4xx'
  if (code >= 500) return 'status-5xx'
  return ''
}

function formatSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(1) + ' MB'
}

function toggleFormat() {
  formatted.value = !formatted.value
}

function copyResponse() {
  if (response.value?.content) {
    navigator.clipboard.writeText(displayContent.value)
  }
}

function downloadResponse() {
  if (response.value?.content) {
    const blob = new Blob([response.value.content], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `response-${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
  }
}
</script>

<style scoped>
.response-panel {
  min-height: 300px;
  display: flex;
  flex-direction: column;
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  overflow: hidden;
}

.response-panel::before,
.response-panel::after {
  display: none;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-default);
  background: var(--bg-tertiary);
}

.panel-title {
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.prompt {
  color: var(--secondary);
  margin-right: 8px;
}

.response-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 4px 10px;
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  color: var(--text-secondary);
  font-family: var(--font-body);
  font-size: 11px;
  cursor: pointer;
  transition: all var(--transition-fast);
  border-radius: var(--radius-sm);
}

.action-btn:hover {
  background: var(--bg-card-hover);
  color: var(--text-primary);
  border-color: var(--border-hover);
}

.response-loading {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 40px;
}

.loading-spinner {
  font-size: 32px;
  color: var(--primary);
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.loading-text {
  font-family: var(--font-body);
  font-size: 12px;
  color: var(--text-secondary);
}

.loading-bar {
  width: 200px;
  height: 4px;
  background: var(--bg-secondary);
  border-radius: 2px;
  overflow: hidden;
}

.loading-progress {
  height: 100%;
  background: linear-gradient(90deg, var(--primary), var(--secondary));
  animation: loading-progress 1.5s infinite;
}

@keyframes loading-progress {
  0% { width: 0%; margin-left: 0%; }
  50% { width: 70%; margin-left: 30%; }
  100% { width: 0%; margin-left: 100%; }
}

.response-error {
  padding: 20px;
}

.error-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 600;
  color: var(--error);
  margin-bottom: 12px;
}

.error-icon {
  font-size: 18px;
}

.error-detail {
  background: var(--bg-tertiary);
  padding: 12px;
  border: 1px solid var(--error-border);
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--error);
}

.response-overview {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-default);
  background: var(--bg-tertiary);
}

.status-badge {
  padding: 4px 12px;
  border-radius: var(--radius-sm);
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 600;
}

.status-badge.status-2xx {
  background: var(--success-muted);
  color: var(--success);
  border: 1px solid var(--success-border);
}

.status-badge.status-3xx {
  background: var(--warning-muted);
  color: var(--warning);
  border: 1px solid var(--warning-border);
}

.status-badge.status-4xx {
  background: var(--error-muted);
  color: var(--error);
  border: 1px solid var(--error-border);
}

.status-badge.status-5xx {
  background: var(--error-muted);
  color: var(--error);
  border: 1px solid var(--error-border);
}

.overview-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-secondary);
}

.item-icon {
  color: var(--text-tertiary);
}

.response-tabs {
  display: flex;
  gap: 4px;
  padding: 8px 16px;
  border-bottom: 1px solid var(--border-default);
}

.response-tabs button {
  padding: 6px 14px;
  background: transparent;
  border: 1px solid transparent;
  color: var(--text-secondary);
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  border-radius: var(--radius-sm);
}

.response-tabs button.active {
  background: var(--primary-muted);
  color: var(--primary);
}

.response-tabs button:hover:not(.active) {
  background: var(--bg-card);
  color: var(--text-primary);
}

.tab-content {
  flex: 1;
  overflow-y: auto;
}

.section-header {
  display: flex;
  justify-content: space-between;
  padding: 10px 16px;
  cursor: pointer;
  font-family: var(--font-body);
  font-size: 12px;
  color: var(--text-secondary);
  background: var(--bg-tertiary);
  border-bottom: 1px solid var(--border-default);
  transition: all var(--transition-fast);
}

.section-header:hover {
  background: var(--bg-card);
  color: var(--text-primary);
}

.response-body,
.response-headers {
  padding: 12px 16px;
}

.body-toolbar {
  margin-bottom: 10px;
}

.body-toolbar button {
  padding: 4px 10px;
  background: transparent;
  border: 1px solid var(--border-default);
  color: var(--text-secondary);
  font-family: var(--font-body);
  font-size: 11px;
  cursor: pointer;
  transition: all var(--transition-fast);
  border-radius: var(--radius-sm);
}

.body-toolbar button:hover,
.body-toolbar button.active {
  background: var(--bg-card);
  color: var(--text-primary);
  border-color: var(--border-hover);
}

.body-content {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  padding: 12px;
  font-family: var(--font-mono);
  font-size: 12px;
  line-height: 1.6;
  color: var(--text-primary);
  max-height: 300px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.response-headers {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 4px 16px;
}

.header-key {
  color: var(--primary);
  font-family: var(--font-mono);
  font-size: 12px;
}

.header-value {
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: 12px;
  word-break: break-all;
}

.request-url {
  padding: 12px 16px;
}

.url-row {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--bg-tertiary);
  padding: 10px 14px;
  border-radius: var(--radius-sm);
  overflow-x: auto;
}

.method-badge {
  padding: 3px 10px;
  border-radius: var(--radius-xs);
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  flex-shrink: 0;
}

.method-badge.method-get { background: rgba(34, 197, 94, 0.12); color: var(--method-get); }
.method-badge.method-post { background: rgba(59, 130, 246, 0.12); color: var(--method-post); }
.method-badge.method-put { background: rgba(245, 158, 11, 0.12); color: var(--method-put); }
.method-badge.method-delete { background: rgba(239, 68, 68, 0.12); color: var(--method-delete); }
.method-badge.method-patch { background: rgba(139, 92, 246, 0.12); color: var(--method-patch); }

.url-text {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-primary);
  word-break: break-all;
}

.request-headers {
  padding: 0 16px 12px;
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 4px 16px;
}

.request-body {
  padding: 0 16px 12px;
}

.empty-hint {
  color: var(--text-tertiary);
  font-family: var(--font-mono);
  font-size: 11px;
  padding: 8px 0;
}

.response-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  gap: 16px;
}

.empty-icon {
  font-size: 48px;
  color: var(--text-tertiary);
}

.empty-text {
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--text-secondary);
}

.empty-hint {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-tertiary);
}
</style>
