<template>
  <div class="report-list">
    <div class="toolbar">
      <h2 class="page-title">
        <span class="prompt">&gt;</span> 报告中心
      </h2>
      <button class="btn primary" @click="showGenerateModal = true">
        <span>+</span> 生成报告
      </button>
    </div>

    <div v-if="loading" class="loading">
      <span class="loading-spinner">⟳</span> 加载中...
    </div>
    <div v-else-if="reports.length === 0" class="empty">
      <span class="glitch">// 暂无报告</span>
    </div>
    <div v-else class="report-grid">
      <div v-for="r in reports" :key="r.id" class="report-card panel">
        <div class="report-header">
          <div class="report-icon">📊</div>
          <div class="report-name">{{ r.name }}</div>
          <span :class="'status-badge ' + (r.type || 'summary').toLowerCase()">
            {{ (r.type || 'SUMMARY').toUpperCase() }}
          </span>
        </div>
        <div class="report-meta">
          <div class="meta-row">
            <span class="meta-label">创建时间</span>
            <span class="meta-value">{{ formatTime(r.created_at) }}</span>
          </div>
          <div v-if="r.time_range" class="meta-row">
            <span class="meta-label">时间范围</span>
            <span class="meta-value">{{ r.time_range }}</span>
          </div>
          <div v-if="r.total_cases != null" class="meta-row">
            <span class="meta-label">用例数</span>
            <span class="meta-value">{{ r.total_cases }}</span>
          </div>
          <div v-if="r.pass_rate != null" class="meta-row">
            <span class="meta-label">通过率</span>
            <span class="meta-value" :style="{ color: r.pass_rate >= 80 ? 'var(--neon-green)' : 'var(--neon-pink)' }">
              {{ r.pass_rate }}%
            </span>
          </div>
        </div>
        <div class="report-actions">
          <button class="btn" @click="downloadReport(r)">⬇ 下载</button>
          <button class="icon-btn danger" @click="removeReport(r.id)">🗑</button>
        </div>
      </div>
    </div>

    <!-- 生成报告弹窗 -->
    <div v-if="showGenerateModal" class="modal-overlay" @click.self="showGenerateModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>// 生成报告</h3>
          <button class="btn-close" @click="showGenerateModal = false">×</button>
        </div>
        <div class="form-body">
          <div class="form-group">
            <label>报告名称</label>
            <input v-model="genForm.name" placeholder="Daily Smoke Test Report" />
          </div>
          <div class="form-group">
            <label>报告类型</label>
            <select v-model="genForm.type">
              <option value="summary">概览</option>
              <option value="detailed">详情</option>
              <option value="trend">趋势</option>
            </select>
          </div>
          <div class="form-row">
            <div class="form-group" style="flex:1">
              <label>开始时间</label>
              <input v-model="genForm.start_time" type="datetime-local" />
            </div>
            <div class="form-group" style="flex:1">
              <label>结束时间</label>
              <input v-model="genForm.end_time" type="datetime-local" />
            </div>
          </div>
        </div>
        <div class="form-actions">
          <button class="btn" @click="showGenerateModal = false">取消</button>
          <button class="btn primary" @click="generateReport" :disabled="generating">
            {{ generating ? '生成中...' : '生成' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { reportApi } from '../../api/report'

const reports = ref([])
const loading = ref(false)
const showGenerateModal = ref(false)
const generating = ref(false)
const genForm = ref({
  name: '', type: 'summary',
  start_time: '', end_time: '',
})

async function fetchReports() {
  loading.value = true
  try {
    const res = await reportApi.list()
    reports.value = res.data.data || []
  } finally {
    loading.value = false
  }
}

async function generateReport() {
  if (!genForm.value.name) return
  generating.value = true
  try {
    const data = {
      name: genForm.value.name,
      start_time: genForm.value.start_time ? new Date(genForm.value.start_time).toISOString() : undefined,
      end_time: genForm.value.end_time ? new Date(genForm.value.end_time).toISOString() : undefined,
    }
    const res = await reportApi.generate(data)
    reports.value.unshift(res.data.data)
    showGenerateModal.value = false
  } finally {
    generating.value = false
  }
}

async function downloadReport(r) {
  try {
    const res = await reportApi.download(r.id)
    const blob = new Blob([res], { type: 'text/html' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${r.name || 'report'}.html`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    alert('下载失败: ' + e.message)
  }
}

async function removeReport(id) {
  if (!confirm('确定要删除吗？')) return
  await reportApi.delete(id)
  reports.value = reports.value.filter(r => r.id !== id)
}

function formatTime(ts) {
  if (!ts) return '--'
  return new Date(ts).toLocaleString('en-US', { hour12: false })
}

onMounted(fetchReports)
</script>

<style scoped>
.report-list { padding: 16px; }

.toolbar {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;
}
.page-title {
  font-family: var(--font-title); font-size: 16px; font-weight: 700;
  letter-spacing: 3px; color: var(--neon-cyan); margin: 0; text-shadow: 0 0 10px var(--neon-cyan);
}
.prompt { color: var(--neon-magenta); }

.loading { padding: 40px; text-align: center; color: var(--neon-cyan); }
.loading-spinner { display: inline-block; animation: spin 1s linear infinite; margin-right: 10px; }
.empty { padding: 40px; text-align: center; }
.glitch { color: var(--text-secondary); font-family: var(--font-mono); animation: glitch 0.5s infinite; }

.report-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px;
}

.report-card { padding: 16px; }
.report-header {
  display: flex; align-items: center; gap: 10px; margin-bottom: 12px;
}
.report-icon { font-size: 20px; }
.report-name {
  flex: 1; font-family: var(--font-title); font-size: 13px; font-weight: 600;
  letter-spacing: 1px; color: var(--neon-cyan); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}

.report-meta { margin-bottom: 12px; }
.meta-row {
  display: flex; justify-content: space-between; padding: 3px 0;
  font-family: var(--font-mono); font-size: 12px;
}
.meta-label { color: var(--text-secondary); }
.meta-value { color: var(--neon-cyan); }

.report-actions {
  display: flex; gap: 8px; align-items: center; padding-top: 8px; border-top: 1px solid var(--border-default);
}

.icon-btn {
  background: transparent; border: 1px solid var(--border-default); cursor: pointer;
  padding: 4px 8px; font-size: 12px; color: var(--text-secondary); transition: all var(--transition-fast);
}
.icon-btn.danger:hover { border-color: var(--neon-pink); color: var(--neon-pink); }

.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.85); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}
.modal {
  background: var(--bg-panel); border: 1px solid var(--neon-cyan);
  box-shadow: 0 0 30px rgba(0,255,255,0.3); width: 480px; max-height: 80vh; overflow-y: auto;
}
.modal::before, .modal::after { display: none; }
.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px; border-bottom: 1px solid var(--border-default);
}
.modal-header h3 {
  font-family: var(--font-title); font-size: 14px; font-weight: 600; letter-spacing: 2px;
  color: var(--neon-cyan); margin: 0;
}
.btn-close { background: none; border: none; font-size: 20px; color: var(--text-secondary); cursor: pointer; }
.form-body { padding: 20px; }
.form-row { display: flex; gap: 12px; }
.form-group { margin-bottom: 16px; flex: 1; }
.form-group label {
  display: block; font-family: var(--font-title); font-size: 10px; letter-spacing: 1px;
  color: var(--text-secondary); margin-bottom: 6px;
}
.form-group input[type="text"], .form-group select, .form-group input[type="datetime-local"] {
  width: 100%; padding: 10px 12px; background: var(--bg-secondary);
  border: 1px solid var(--border-default); color: var(--neon-cyan);
  font-family: var(--font-mono); font-size: 12px; outline: none; box-sizing: border-box;
}
.form-actions {
  display: flex; gap: 12px; justify-content: flex-end;
  padding: 16px 20px; border-top: 1px solid var(--border-default);
}

@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
@keyframes glitch {
  0% { transform: translate(0); opacity: 0.7; }
  20% { transform: translate(-2px, 2px); opacity: 0.8; }
  40% { transform: translate(-2px, -2px); opacity: 0.7; }
  60% { transform: translate(2px, 2px); opacity: 0.8; }
  80% { transform: translate(2px, -2px); opacity: 0.7; }
  100% { transform: translate(0); opacity: 0.7; }
}
</style>
