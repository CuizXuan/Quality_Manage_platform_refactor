<template>
  <div class="execution-history">
    <div class="toolbar">
      <h2 class="page-title">
        <span class="prompt">&gt;</span> 执行日志
      </h2>
      <div class="filters">
        <select v-model="filterStatus" @change="fetchLogs" class="cyber-select">
          <option value="">全部状态</option>
          <option value="success">成功</option>
          <option value="failure">失败</option>
          <option value="error">错误</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="loading">
      <span class="loading-spinner">⟳</span>
      加载中...
    </div>
    <div v-else-if="logs.length === 0" class="empty">
      <span class="glitch">// 暂无日志</span>
    </div>
    <div v-else class="log-list">
      <div v-for="log in logs" :key="log.id" class="log-card panel" @click="openLog(log)">
        <div class="log-header">
          <span :class="'status-badge ' + log.status">{{ statusLabel(log.status) }}</span>
          <span class="log-time">{{ formatTime(log.created_at) }}</span>
        </div>
        <div class="log-url">
          <span class="method-badge" :class="'method-' + (log.request_method || 'get').toLowerCase()">
            {{ log.request_method }}
          </span>
          {{ log.request_url }}
        </div>
        <div class="log-meta">
          <span v-if="log.response_status">状态: {{ log.response_status }}</span>
          <span v-if="log.response_time_ms">耗时: {{ log.response_time_ms }}ms</span>
          <span v-if="log.case_id">用例 #{{ log.case_id }}</span>
        </div>
      </div>
    </div>

    <!-- 详情 Drawer -->
    <CyberDrawer
      v-model="showDetail"
      :title="selectedLog ? `执行详情 #${selectedLog.id}` : '执行详情'"
      :status="selectedLog?.status"
      :status-text="statusLabel(selectedLog?.status)"
      width="800px"
    >
      <div class="detail-grid">
        <div class="detail-section">
          <h4>// REQUEST</h4>
          <div class="detail-row">
            <span class="detail-label">URL:</span>
            <span class="detail-value">{{ selectedLog?.request_url }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">METHOD:</span>
            <span class="method-badge" :class="'method-' + (selectedLog?.request_method || 'get').toLowerCase()">
              {{ selectedLog?.request_method }}
            </span>
          </div>
          <div class="detail-block">
            <span class="detail-label">HEADERS:</span>
            <pre>{{ JSON.stringify(selectedLog?.request_headers, null, 2) }}</pre>
          </div>
          <div class="detail-block" v-if="selectedLog?.request_body">
            <span class="detail-label">BODY:</span>
            <pre>{{ selectedLog?.request_body }}</pre>
          </div>
        </div>

        <div class="detail-section">
          <h4>// RESPONSE</h4>
          <div class="detail-row">
            <span class="detail-label">STATUS:</span>
            <span :class="'status-badge ' + selectedLog?.status">{{ selectedLog?.response_status }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">TIME:</span>
            <span class="detail-value text-cyan">{{ selectedLog?.response_time_ms }}ms</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">SIZE:</span>
            <span class="detail-value">{{ selectedLog?.response_size }} bytes</span>
          </div>
          <div class="detail-block">
            <span class="detail-label">BODY:</span>
            <pre class="response-body">{{ formatBody(selectedLog?.response_body) }}</pre>
          </div>
        </div>
      </div>

      <div v-if="selectedLog?.assertion_results?.length" class="assertions">
        <h4>// ASSERTIONS</h4>
        <div v-for="a in selectedLog.assertion_results" :key="a.id" class="assertion-item">
          <span :class="a.passed ? 'pass' : 'fail'">{{ a.passed ? '✅' : '❌' }}</span>
          <span class="assertion-type">{{ a.type }}:</span>
          <span class="assertion-msg">{{ a.message }}</span>
        </div>
      </div>

      <div v-if="selectedLog?.error_message" class="error-msg">
        <strong>ERROR:</strong> {{ selectedLog.error_message }}
      </div>

      <template #footer>
        <button class="btn" @click="showDetail = false">关闭</button>
      </template>
    </CyberDrawer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { logsApi } from '../api/log'
import CyberDrawer from '@/components/common/modal/CyberDrawer.vue'

const logs = ref([])
const loading = ref(false)
const filterStatus = ref('')
const showDetail = ref(false)
const selectedLog = ref(null)

async function fetchLogs() {
  loading.value = true
  try {
    const params = filterStatus.value ? { status: filterStatus.value } : {}
    const res = await logsApi.list(params)
    logs.value = res.data
  } finally {
    loading.value = false
  }
}

async function openLog(log) {
  const res = await logsApi.get(log.id)
  selectedLog.value = res.data
  showDetail.value = true
}

function statusLabel(s) {
  const labels = { success: 'SUCCESS', failure: 'FAILURE', error: 'ERROR', pending: 'PENDING', running: 'RUNNING', skipped: 'SKIPPED' }
  return labels[s] || s
}

function formatTime(ts) {
  if (!ts) return ''
  return new Date(ts).toLocaleString('en-US', { hour12: false })
}

function formatBody(body) {
  if (!body) return ''
  try { return JSON.stringify(JSON.parse(body), null, 2) } catch { return body }
}

onMounted(fetchLogs)
</script>

<style scoped>
.execution-history {
  padding: 16px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-title {
  font-family: var(--font-title);
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 3px;
  color: var(--neon-cyan);
  margin: 0;
  text-shadow: 0 0 10px var(--neon-cyan);
}

.prompt {
  color: var(--neon-magenta);
}

.cyber-select {
  font-family: var(--font-title);
  font-size: 11px;
  letter-spacing: 1px;
  padding: 8px 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--neon-cyan);
  color: var(--neon-cyan);
  cursor: pointer;
  outline: none;
}

.loading, .empty {
  padding: 40px;
  text-align: center;
}

.loading {
  color: var(--neon-cyan);
  font-family: var(--font-mono);
}

.loading-spinner {
  display: inline-block;
  animation: spin 1s linear infinite;
  margin-right: 10px;
}

.glitch {
  color: var(--text-secondary);
  font-family: var(--font-mono);
  animation: glitch 0.5s infinite;
}

.log-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.log-card {
  padding: 12px 16px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.log-card:hover {
  border-color: var(--neon-cyan);
  box-shadow: 0 0 15px rgba(0, 255, 255, 0.2);
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.log-time {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-secondary);
  letter-spacing: 1px;
}

.log-url {
  font-family: var(--font-mono);
  font-size: 12px;
  margin-bottom: 6px;
  word-break: break-all;
  display: flex;
  align-items: center;
  gap: 8px;
}

.method-badge {
  flex-shrink: 0;
}

.log-meta {
  display: flex;
  gap: 20px;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-secondary);
}

/* Detail Styles */
.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.detail-section {
  background: var(--bg-secondary);
  border: 1px solid var(--border-default);
  border-radius: 4px;
  padding: 16px;
}

.detail-section h4 {
  font-family: var(--font-title);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 2px;
  color: var(--neon-magenta);
  margin: 0 0 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-default);
}

.detail-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
  font-family: var(--font-mono);
  font-size: 12px;
}

.detail-label {
  color: var(--text-secondary);
  min-width: 60px;
}

.detail-value {
  color: var(--text-primary);
  word-break: break-all;
}

.detail-block {
  margin-top: 12px;
}

.detail-block .detail-label {
  display: block;
  margin-bottom: 6px;
}

.detail-block pre {
  background: var(--bg-primary);
  border: 1px solid var(--border-default);
  padding: 10px;
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--neon-green);
  max-height: 150px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.response-body {
  color: var(--neon-cyan) !important;
}

.assertions {
  background: var(--bg-secondary);
  border: 1px solid var(--border-default);
  border-radius: 4px;
  padding: 16px;
  margin-bottom: 16px;
}

.assertions h4 {
  font-family: var(--font-title);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 2px;
  color: var(--neon-magenta);
  margin: 0 0 12px;
}

.assertion-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 0;
  font-family: var(--font-mono);
  font-size: 12px;
  border-bottom: 1px solid var(--border-default);
}

.assertion-item:last-child {
  border-bottom: none;
}

.pass {
  color: var(--neon-green);
}

.fail {
  color: #f00;
  animation: alert-flash 0.5s infinite;
}

.assertion-type {
  color: var(--neon-cyan);
}

.assertion-msg {
  color: var(--text-secondary);
}

.error-msg {
  padding: 12px;
  background: rgba(255, 0, 0, 0.1);
  border: 1px solid rgba(255, 0, 0, 0.3);
  border-radius: 4px;
  color: #f00;
  font-family: var(--font-mono);
  font-size: 12px;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes glitch {
  0% { transform: translate(0); opacity: 0.7; }
  20% { transform: translate(-2px, 2px); opacity: 0.8; }
  40% { transform: translate(-2px, -2px); opacity: 0.7; }
  60% { transform: translate(2px, 2px); opacity: 0.8; }
  80% { transform: translate(2px, -2px); opacity: 0.7; }
  100% { transform: translate(0); opacity: 0.7; }
}

@keyframes alert-flash {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>