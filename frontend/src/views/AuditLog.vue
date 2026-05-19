<template>
  <div class="audit-page">
    <div class="page-header">
      <h1 class="page-title">企业审计</h1>
      <div class="header-actions">
        <button class="btn-secondary" @click="exportLogs">
          📥 导出日志
        </button>
      </div>
    </div>

    <!-- 统计概览 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">📋</div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.totalLogs || 0 }}</span>
          <span class="stat-label">日志总数</span>
        </div>
      </div>
      <div class="stat-card warning">
        <div class="stat-icon">⚠️</div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.sensitiveOps || 0 }}</span>
          <span class="stat-label">敏感操作</span>
        </div>
      </div>
      <div class="stat-card danger">
        <div class="stat-icon">🚨</div>
        <div class="stat-info">
          <span class="stat-value">{{ securityStats.unresolved || 0 }}</span>
          <span class="stat-label">待处理安全事件</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📊</div>
        <div class="stat-info">
          <span class="stat-value">{{ periodDays }}</span>
          <span class="stat-label">统计周期(天)</span>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="tabs">
      <button :class="{ active: currentTab === 'logs' }" @click="currentTab = 'logs'">
        操作日志
      </button>
      <button :class="{ active: currentTab === 'security' }" @click="currentTab = 'security'; loadSecurityEvents()">
        安全事件
      </button>
      <button :class="{ active: currentTab === 'stats' }" @click="currentTab = 'stats'; loadStats()">
        统计分析
      </button>
    </div>

    <!-- 操作日志 -->
    <div v-if="currentTab === 'logs'" class="tab-content">
      <!-- 筛选器 -->
      <div class="filter-bar">
        <select v-model="filterOperation" @change="loadLogs" class="filter-select">
          <option value="">全部操作</option>
          <option value="user_login">用户登录</option>
          <option value="user_create">创建用户</option>
          <option value="user_delete">删除用户</option>
          <option value="project_create">创建项目</option>
          <option value="project_update">更新项目</option>
          <option value="plugin_publish">发布插件</option>
          <option value="plugin_install">安装插件</option>
          <option value="cli_key_create">创建CLI Key</option>
        </select>
        <input
          v-model="filterDate"
          type="date"
          class="filter-input"
          @change="loadLogs"
        />
        <label class="checkbox-item">
          <input type="checkbox" v-model="filterSensitive" @change="loadLogs" />
          <span>仅敏感操作</span>
        </label>
        <button class="btn-refresh" @click="loadLogs">🔄 刷新</button>
      </div>

      <!-- 日志列表 -->
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="!logs.length" class="empty-state">
        <p>暂无日志记录</p>
      </div>
      <div v-else class="log-table-wrapper">
        <table class="log-table">
          <thead>
            <tr>
              <th>时间</th>
              <th>操作</th>
              <th>路径</th>
              <th>方法</th>
              <th>用户</th>
              <th>IP</th>
              <th>状态</th>
              <th>耗时</th>
              <th>敏感</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="log in logs"
              :key="log.id"
              :class="{ 'sensitive-row': log.is_sensitive }"
            >
              <td>{{ formatTime(log.created_at) }}</td>
              <td>
                <span class="operation-badge" :class="'op-' + log.operation">
                  {{ log.operation }}
                </span>
              </td>
              <td class="path-cell" :title="log.path">{{ log.path }}</td>
              <td>
                <span class="method-badge" :class="'method-' + log.method">
                  {{ log.method }}
                </span>
              </td>
              <td>{{ log.user_id || '-' }}</td>
              <td>{{ log.client_ip || '-' }}</td>
              <td>
                <span class="status-badge" :class="getStatusClass(log.status_code)">
                  {{ log.status_code }}
                </span>
              </td>
              <td>{{ log.duration_ms }}ms</td>
              <td>
                <span v-if="log.is_sensitive" class="sensitive-badge">⚠️</span>
                <span v-else>-</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 分页 -->
      <div v-if="totalCount > pageSize" class="pagination">
        <button :disabled="page <= 1" @click="page--; loadLogs()">上一页</button>
        <span>{{ page }} / {{ Math.ceil(totalCount / pageSize) }}</span>
        <button :disabled="page >= Math.ceil(totalCount / pageSize)" @click="page++; loadLogs()">下一页</button>
      </div>
    </div>

    <!-- 安全事件 -->
    <div v-if="currentTab === 'security'" class="tab-content">
      <div v-if="securityLoading" class="loading">加载中...</div>
      <div v-else-if="!securityEvents.length" class="empty-state">
        <p>暂无安全事件</p>
      </div>
      <div v-else class="event-list">
        <div
          v-for="event in securityEvents"
          :key="event.id"
          class="event-card"
          :class="'severity-' + event.severity"
        >
          <div class="event-header">
            <span class="event-type">{{ event.event_type }}</span>
            <span class="severity-badge" :class="'sev-' + event.severity">
              {{ event.severity }}
            </span>
            <span v-if="event.resolved" class="resolved-badge">已处理</span>
            <span v-else class="unresolved-badge">待处理</span>
          </div>
          <div class="event-details">
            <span>IP: {{ event.client_ip }}</span>
            <span>时间: {{ formatTime(event.created_at) }}</span>
            <span>用户: {{ event.user_id || 'N/A' }}</span>
          </div>
          <div v-if="event.details" class="event-json">
            <pre>{{ JSON.stringify(event.details, null, 2) }}</pre>
          </div>
          <div v-if="!event.resolved" class="event-actions">
            <button class="btn-primary btn-small" @click="resolveEvent(event.id)">
              标记已处理
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 统计分析 -->
    <div v-if="currentTab === 'stats'" class="tab-content">
      <div class="stats-section">
        <h3>操作类型分布</h3>
        <div class="stats-chart">
          <div
            v-for="item in statsData.operation_stats"
            :key="item.operation"
            class="stat-bar-row"
          >
            <span class="stat-bar-label">{{ item.operation }}</span>
            <div class="stat-bar-wrapper">
              <div
                class="stat-bar"
                :style="{ width: getBarWidth(item.count) + '%' }"
              ></div>
            </div>
            <span class="stat-bar-count">{{ item.count }}</span>
          </div>
        </div>
      </div>

      <div class="stats-section">
        <h3>每日请求趋势 (最近 {{ periodDays }} 天)</h3>
        <div class="trend-chart">
          <div
            v-for="item in statsData.daily_trend"
            :key="item.date"
            class="trend-bar-wrapper"
            :title="item.date + ': ' + item.count"
          >
            <div
              class="trend-bar"
              :style="{ height: getTrendHeight(item.count) + 'px' }"
            ></div>
            <span class="trend-date">{{ formatShortDate(item.date) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'

const API_BASE = '/api'

const currentTab = ref('logs')
const loading = ref(false)
const securityLoading = ref(false)
const logs = ref([])
const securityEvents = ref([])
const totalCount = ref(0)
const page = ref(1)
const pageSize = 50
const periodDays = ref(7)

const filterOperation = ref('')
const filterDate = ref('')
const filterSensitive = ref(false)

const stats = ref({ totalLogs: 0, sensitiveOps: 0 })
const securityStats = ref({ unresolved: 0 })
const statsData = ref({ operation_stats: [], daily_trend: [] })

async function loadLogs() {
  loading.value = true
  try {
    const params = new URLSearchParams({
      page: page.value,
      page_size: pageSize,
    })
    if (filterOperation.value) params.set('operation', filterOperation.value)
    if (filterDate.value) params.set('start_date', filterDate.value)
    if (filterSensitive.value) params.set('is_sensitive', 'true')

    const res = await fetch(`${API_BASE}/audit/logs?${params}`)
    const data = await res.json()
    logs.value = data.items || []
    totalCount.value = data.total || 0
    stats.value.totalLogs = data.total || 0
  } catch (e) {
    console.error('Load logs failed:', e)
  } finally {
    loading.value = false
  }
}

async function loadSecurityEvents() {
  securityLoading.value = true
  try {
    const res = await fetch(`${API_BASE}/audit/security/events`)
    const data = await res.json()
    securityEvents.value = data.items || []
    securityStats.value.unresolved = data.items?.filter(e => !e.resolved).length || 0
  } catch (e) {
    console.error('Load security events failed:', e)
  } finally {
    securityLoading.value = false
  }
}

async function loadStats() {
  try {
    const res = await fetch(`${API_BASE}/audit/stats/overview?days=${periodDays.value}`)
    const data = await res.json()
    statsData.value = data
    stats.value.sensitiveOps = data.sensitive_operations || 0
  } catch (e) {
    console.error('Load stats failed:', e)
  }
}

async function resolveEvent(eventId) {
  const notes = prompt('处理说明（可选）:')
  try {
    await fetch(`${API_BASE}/audit/security/events/${eventId}/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ notes: notes || '' }),
    })
    loadSecurityEvents()
    alert('已标记为处理')
  } catch (e) {
    alert('操作失败')
  }
}

function exportLogs() {
  const csv = [
    ['ID', '时间', '操作', '路径', '方法', '用户', 'IP', '状态', '耗时', '敏感'],
    ...logs.value.map(l => [
      l.id,
      l.created_at,
      l.operation,
      l.path,
      l.method,
      l.user_id,
      l.client_ip,
      l.status_code,
      l.duration_ms,
      l.is_sensitive ? '是' : '否',
    ]),
  ]
    .map(row => row.map(cell => `"${cell || ''}"`).join(','))
    .join('\n')

  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `audit_logs_${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

function formatTime(t) {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN')
}

function formatShortDate(d) {
  if (!d) return ''
  return d.slice(5)  // MM-DD
}

function getStatusClass(code) {
  if (!code) return ''
  if (code >= 500) return 'error'
  if (code >= 400) return 'warning'
  if (code >= 200) return 'success'
  return ''
}

function getBarWidth(count) {
  const max = Math.max(...(statsData.value.operation_stats || []).map(s => s.count), 1)
  return (count / max) * 100
}

function getTrendHeight(count) {
  const max = Math.max(...(statsData.value.daily_trend || []).map(s => s.count), 1)
  return Math.max(10, (count / max) * 120)
}

onMounted(() => {
  loadLogs()
})
</script>

<style scoped>
.audit-page {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.stat-icon { font-size: 32px; }

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #888;
}

.stat-card.warning .stat-value { color: #f59e0b; }
.stat-card.danger .stat-value { color: #ef4444; }

.tabs {
  display: flex;
  gap: 4px;
  border-bottom: 2px solid #f0f0f0;
  margin-bottom: 20px;
}

.tabs button {
  padding: 10px 20px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 14px;
  color: #666;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
}

.tabs button.active {
  color: #667eea;
  border-bottom-color: #667eea;
  font-weight: 500;
}

.filter-bar {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.filter-select, .filter-input {
  padding: 8px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
}

.btn-refresh {
  padding: 8px 16px;
  background: #f5f5f5;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  margin-left: auto;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  cursor: pointer;
}

.log-table-wrapper {
  overflow-x: auto;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.log-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.log-table th {
  text-align: left;
  padding: 12px 16px;
  background: #f9f9f9;
  font-weight: 500;
  color: #666;
  border-bottom: 1px solid #e0e0e0;
}

.log-table td {
  padding: 10px 16px;
  border-bottom: 1px solid #f0f0f0;
  color: #333;
}

.log-table tr:last-child td {
  border-bottom: none;
}

.sensitive-row {
  background: #fff9f0;
}

.path-cell {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.operation-badge {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  background: #f0f0f0;
  color: #666;
}

.method-badge {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 600;
}

.method-GET { background: #e8f5e9; color: #2e7d32; }
.method-POST { background: #e3f2fd; color: #1565c0; }
.method-PUT { background: #fff3e0; color: #e65100; }
.method-DELETE { background: #ffebee; color: #c62828; }

.status-badge { font-size: 12px; padding: 2px 8px; border-radius: 4px; }
.status-badge.success { background: #e8f5e9; color: #2e7d32; }
.status-badge.warning { background: #fff3e0; color: #e65100; }
.status-badge.error { background: #ffebee; color: #c62828; }

.sensitive-badge { font-size: 16px; }

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 20px;
}

.pagination button {
  padding: 8px 16px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
}

.pagination button:disabled { opacity: 0.5; cursor: not-allowed; }

.event-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.event-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  border-left: 4px solid;
}

.event-card.severity-low { border-left-color: #3b82f6; }
.event-card.severity-medium { border-left-color: #f59e0b; }
.event-card.severity-high { border-left-color: #ef4444; }
.event-card.severity-critical { border-left-color: #7c3aed; }

.event-header {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}

.event-type {
  font-weight: 600;
  font-size: 15px;
  flex: 1;
}

.severity-badge {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.sev-low { background: #dbeafe; color: #1d4ed8; }
.sev-medium { background: #fef3c7; color: #d97706; }
.sev-high { background: #fee2e2; color: #dc2626; }
.sev-critical { background: #ede9fe; color: #6d28d9; }

.resolved-badge {
  background: #e8f5e9;
  color: #2e7d32;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
}

.unresolved-badge {
  background: #fee2e2;
  color: #dc2626;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
}

.event-details {
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: #666;
  flex-wrap: wrap;
}

.event-json {
  margin-top: 8px;
}

.event-json pre {
  background: #f5f5f5;
  padding: 8px;
  border-radius: 6px;
  font-size: 12px;
  overflow-x: auto;
  max-height: 150px;
}

.event-actions {
  margin-top: 12px;
}

.stats-section {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.stats-section h3 {
  margin: 0 0 16px;
  font-size: 16px;
  font-weight: 600;
}

.stat-bar-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}

.stat-bar-label {
  width: 120px;
  font-size: 13px;
  color: #666;
  flex-shrink: 0;
}

.stat-bar-wrapper {
  flex: 1;
  height: 20px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.stat-bar {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.stat-bar-count {
  width: 50px;
  text-align: right;
  font-size: 13px;
  font-weight: 500;
  color: #333;
}

.trend-chart {
  display: flex;
  align-items: flex-end;
  gap: 4px;
  height: 150px;
  padding-top: 20px;
}

.trend-bar-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  height: 100%;
  justify-content: flex-end;
}

.trend-bar {
  width: 100%;
  background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
  border-radius: 4px 4px 0 0;
  min-height: 4px;
  cursor: pointer;
  transition: opacity 0.2s;
}

.trend-bar:hover { opacity: 0.8; }

.trend-date {
  font-size: 10px;
  color: #888;
  transform: rotate(-45deg);
  transform-origin: top left;
}

.loading, .empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #888;
}

.btn-primary {
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}

.btn-secondary {
  padding: 10px 20px;
  background: #fff;
  color: #667eea;
  border: 1px solid #667eea;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}

.btn-small {
  padding: 6px 12px;
  font-size: 13px;
}
</style>
