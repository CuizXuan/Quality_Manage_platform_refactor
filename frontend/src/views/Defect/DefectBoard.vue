<template>
  <div class="defect-board">
    <div class="toolbar">
      <h2 class="page-title">
        <span class="prompt">&gt;</span> 缺陷看板
      </h2>
      <button class="btn primary" @click="openCreateForm">
        <span>+</span> 新建缺陷
      </button>
    </div>

    <!-- Stats Bar -->
    <div v-if="stats" class="stats-bar">
      <div class="stat-item">
        <span class="stat-label">总计</span>
        <span class="stat-value text-cyan">{{ stats.total || 0 }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">待处理</span>
        <span class="stat-value text-yellow">{{ stats.open || 0 }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">处理中</span>
        <span class="stat-value text-blue">{{ stats.in_progress || 0 }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">已解决</span>
        <span class="stat-value text-green">{{ stats.resolved || 0 }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">已关闭</span>
        <span class="stat-value text-muted">{{ stats.closed || 0 }}</span>
      </div>
    </div>

    <!-- Filters -->
    <div class="filter-bar">
      <div class="filter-group">
        <label>状态</label>
        <select v-model="filters.status">
          <option value="">全部</option>
          <option value="open">待处理</option>
          <option value="in_progress">处理中</option>
          <option value="resolved">已解决</option>
          <option value="closed">已关闭</option>
        </select>
      </div>
      <div class="filter-group">
        <label>严重程度</label>
        <select v-model="filters.severity">
          <option value="">全部</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>
      <div class="filter-group">
        <label>指派人</label>
        <input v-model="filters.assignee" placeholder="指派人" />
      </div>
      <button class="btn" @click="resetFilters">重置</button>
    </div>

    <div v-if="loading" class="loading">
      <span class="loading-spinner">⟳</span> 加载中...
    </div>
    <div v-else class="kanban-board">
      <div
        v-for="column in columns"
        :key="column.key"
        class="kanban-column"
        :class="'col-' + column.key"
      >
        <div class="col-header">
          <span class="col-title">{{ column.label }}</span>
          <span class="col-count">{{ column.items.length }}</span>
        </div>
        <div class="col-body">
          <div
            v-for="defect in column.items"
            :key="defect.id"
            class="defect-card"
            @click="openDetail(defect)"
          >
            <div class="defect-header">
              <span class="defect-id mono">#{{ defect.id }}</span>
              <span class="severity-badge" :class="'sev-' + (defect.severity || 'low')">
                {{ severityIcon(defect.severity) }} {{ severityLabel(defect.severity) }}
              </span>
            </div>
            <div class="defect-title">{{ defect.title }}</div>
            <div class="defect-meta">
              <span v-if="defect.assignee" class="meta-item">👤 {{ defect.assignee }}</span>
              <span v-if="defect.priority" class="meta-item priority">⭐ {{ defect.priority }}</span>
            </div>
          </div>
          <div v-if="column.items.length === 0" class="col-empty">
            <span class="glitch">// 空</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Create/Edit Inline Form -->
    <div v-if="showForm" class="modal-overlay" @click.self="showForm = false">
      <div class="modal form-modal">
        <div class="modal-header">
          <h3>// 新建缺陷</h3>
          <button class="btn-close" @click="showForm = false">×</button>
        </div>
        <div class="form-body">
          <div class="form-group">
            <label>标题 *</label>
            <input v-model="defectForm.title" placeholder="缺陷标题" />
          </div>
          <div class="form-group">
            <label>描述</label>
            <textarea v-model="defectForm.description" rows="3" placeholder="详细描述..."></textarea>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>严重程度</label>
              <select v-model="defectForm.severity">
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
            <div class="form-group">
              <label>优先级</label>
              <select v-model="defectForm.priority">
                <option value="P0">P0</option>
                <option value="P1">P1</option>
                <option value="P2">P2</option>
                <option value="P3">P3</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>指派人</label>
              <input v-model="defectForm.assignee" placeholder="指派人" />
            </div>
            <div class="form-group">
              <label>环境</label>
              <input v-model="defectForm.environment" placeholder="环境" />
            </div>
          </div>
          <div class="form-group">
            <label>复现步骤</label>
            <textarea v-model="defectForm.steps_to_reproduce" rows="2" placeholder="1. ... 2. ..."></textarea>
          </div>
          <div class="form-group">
            <label>期望结果</label>
            <input v-model="defectForm.expected_result" placeholder="期望结果" />
          </div>
          <div class="form-group">
            <label>实际结果</label>
            <input v-model="defectForm.actual_result" placeholder="实际结果" />
          </div>
        </div>
        <div class="form-actions">
          <button class="btn" @click="showForm = false">取消</button>
          <button class="btn primary" @click="submitDefect" :disabled="submitting">
            {{ submitting ? '提交中...' : '提交' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Defect Detail Panel -->
    <div v-if="showDetail" class="modal-overlay" @click.self="showDetail = false">
      <div class="modal detail-modal">
        <div class="modal-header">
          <h3>// 缺陷详情 #{{ currentDefect?.id }}</h3>
          <button class="btn-close" @click="showDetail = false">×</button>
        </div>
        <div class="detail-body" v-if="currentDefect">
          <div class="detail-title">{{ currentDefect.title }}</div>

          <div class="detail-meta-row">
            <span class="severity-badge" :class="'sev-' + (currentDefect.severity || 'low')">
              {{ severityIcon(currentDefect.severity) }} {{ severityLabel(currentDefect.severity) }}
            </span>
            <span class="priority-badge">{{ currentDefect.priority || 'P2' }}</span>
            <span class="status-badge" :class="'status-' + currentDefect.status">
              {{ statusLabel(currentDefect.status) }}
            </span>
          </div>

          <div class="detail-grid">
            <div class="detail-item">
              <label>指派人</label>
              <span>{{ currentDefect.assignee || '--' }}</span>
            </div>
            <div class="detail-item">
              <label>报告人</label>
              <span>{{ currentDefect.reporter || '--' }}</span>
            </div>
            <div class="detail-item">
              <label>环境</label>
              <span>{{ currentDefect.environment || '--' }}</span>
            </div>
            <div class="detail-item">
              <label>创建时间</label>
              <span class="mono">{{ formatTime(currentDefect.created_at) }}</span>
            </div>
          </div>

          <div class="detail-section">
            <label>描述</label>
            <p>{{ currentDefect.description || '--' }}</p>
          </div>

          <div class="detail-section">
            <label>复现步骤</label>
            <p class="mono">{{ currentDefect.steps_to_reproduce || '--' }}</p>
          </div>

          <div class="detail-row-2">
            <div class="detail-section">
              <label>期望结果</label>
              <p>{{ currentDefect.expected_result || '--' }}</p>
            </div>
            <div class="detail-section">
              <label>实际结果</label>
              <p>{{ currentDefect.actual_result || '--' }}</p>
            </div>
          </div>

          <!-- Status Transitions -->
          <div class="detail-section">
            <label>流转状态</label>
            <div class="status-actions">
              <button v-for="s in nextStatuses(currentDefect.status)" :key="s" class="btn" @click="changeStatus(currentDefect.id, s)">
                → {{ statusLabel(s) }}
              </button>
            </div>
          </div>

          <!-- Comments -->
          <div class="detail-section">
            <label>评论 ({{ (currentDefect.comments || []).length }})</label>
            <div class="comments-list">
              <div v-for="c in currentDefect.comments || []" :key="c.id" class="comment-item">
                <span class="comment-author">{{ c.author || '未知' }}</span>
                <span class="comment-time mono">{{ formatTime(c.created_at) }}</span>
                <p class="comment-text">{{ c.content }}</p>
              </div>
              <div v-if="!currentDefect.comments?.length" class="col-empty">
                <span class="glitch">// 暂无评论</span>
              </div>
            </div>
            <div class="comment-form">
              <textarea v-model="newComment" rows="2" placeholder="添加评论..."></textarea>
              <button class="btn" @click="addComment" :disabled="!newComment.trim()">发送</button>
            </div>
          </div>

          <!-- Actions -->
          <div class="detail-actions">
            <button class="btn" @click="openEditFromDetail">编辑</button>
            <button class="btn danger" @click="deleteDefect(currentDefect.id)">删除</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { defectApi } from '../../api/defect'

const defects = ref([])
const stats = ref(null)
const loading = ref(true)
const showForm = ref(false)
const showDetail = ref(false)
const currentDefect = ref(null)
const submitting = ref(false)
const newComment = ref('')

const filters = ref({ status: '', severity: '', assignee: '' })

const columns = computed(() => {
  const list = defects.value
  const filtered = list.filter(d => {
    if (filters.value.status && d.status !== filters.value.status) return false
    if (filters.value.severity && d.severity !== filters.value.severity) return false
    if (filters.value.assignee && !d.assignee?.toLowerCase().includes(filters.value.assignee.toLowerCase())) return false
    return true
  })
  return [
    { key: 'open', label: '待处理', items: filtered.filter(d => d.status === 'open') },
    { key: 'in_progress', label: '处理中', items: filtered.filter(d => d.status === 'in_progress') },
    { key: 'resolved', label: '已解决', items: filtered.filter(d => d.status === 'resolved') },
    { key: 'closed', label: '已关闭', items: filtered.filter(d => d.status === 'closed') },
  ]
})

const defectForm = ref(defaultForm())
function defaultForm() {
  return {
    title: '', description: '', severity: 'medium', priority: 'P2',
    assignee: '', environment: '', steps_to_reproduce: '',
    expected_result: '', actual_result: '',
  }
}

async function fetchDefects() {
  loading.value = true
  try {
    const res = await defectApi.list()
    defects.value = res.data.data || []
  } catch {
    defects.value = []
  } finally {
    loading.value = false
  }
}

async function fetchStats() {
  try {
    const res = await defectApi.stats()
    stats.value = res.data.data
  } catch {}
}

function openCreateForm() {
  defectForm.value = defaultForm()
  showForm.value = true
}

async function submitDefect() {
  if (!defectForm.value.title) return
  submitting.value = true
  try {
    await defectApi.create(defectForm.value)
    showForm.value = false
    await fetchDefects()
    await fetchStats()
  } finally {
    submitting.value = false
  }
}

async function openDetail(defect) {
  try {
    const res = await defectApi.get(defect.id)
    currentDefect.value = res.data.data
    showDetail.value = true
  } catch {}
}

function openEditFromDetail() {
  if (!currentDefect.value) return
  defectForm.value = {
    title: currentDefect.value.title,
    description: currentDefect.value.description,
    severity: currentDefect.value.severity || 'medium',
    priority: currentDefect.value.priority || 'P2',
    assignee: currentDefect.value.assignee || '',
    environment: currentDefect.value.environment || '',
    steps_to_reproduce: currentDefect.value.steps_to_reproduce || '',
    expected_result: currentDefect.value.expected_result || '',
    actual_result: currentDefect.value.actual_result || '',
  }
  showDetail.value = false
  showForm.value = true
}

async function changeStatus(id, status) {
  await defectApi.update(id, { status })
  await openDetail({ id })
  await fetchDefects()
  await fetchStats()
}

async function addComment() {
  if (!newComment.value.trim() || !currentDefect.value) return
  await defectApi.addComment(currentDefect.value.id, { content: newComment.value })
  newComment.value = ''
  await openDetail({ id: currentDefect.value.id })
}

async function deleteDefect(id) {
  if (!confirm('确定要删除吗？')) return
  await defectApi.delete(id)
  showDetail.value = false
  await fetchDefects()
  await fetchStats()
}

function resetFilters() {
  filters.value = { status: '', severity: '', assignee: '' }
}

function severityIcon(s) {
  const m = { critical: '🔴', high: '🟠', medium: '🟡', low: '🟢' }
  return m[s] || '🟢'
}

function severityLabel(s) {
  const m = { critical: 'Critical', high: 'High', medium: 'Medium', low: 'Low' }
  return m[s] || 'Low'
}

function statusLabel(s) {
  const m = { open: '待处理', in_progress: '处理中', resolved: '已解决', closed: '已关闭' }
  return m[s] || s
}

function nextStatuses(current) {
  const flow = { open: ['in_progress'], in_progress: ['resolved'], resolved: ['closed'], closed: [] }
  return flow[current] || []
}

function formatTime(ts) {
  if (!ts) return '--'
  return new Date(ts).toLocaleString('zh-CN', { hour12: false })
}

onMounted(() => {
  fetchDefects()
  fetchStats()
})
</script>

<style scoped>
.defect-board { padding: 16px; display: flex; flex-direction: column; height: calc(100vh - var(--header-height)); }

.toolbar {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-shrink: 0;
}
.page-title {
  font-family: var(--font-title); font-size: 16px; font-weight: 700;
  letter-spacing: 3px; color: var(--neon-cyan); margin: 0; text-shadow: 0 0 10px var(--neon-cyan);
}
.prompt { color: var(--neon-magenta); }

.stats-bar {
  display: flex; gap: 24px; margin-bottom: 16px; padding: 12px 16px;
  background: var(--bg-panel); border: 1px solid var(--border-default);
  border-radius: 8px; flex-shrink: 0;
}
.stat-item { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.stat-label { font-family: var(--font-title); font-size: 9px; letter-spacing: 2px; color: var(--text-secondary); text-transform: uppercase; }
.stat-value { font-family: var(--font-title); font-size: 20px; font-weight: 700; }
.text-cyan { color: var(--neon-cyan); }
.text-yellow { color: var(--neon-yellow); }
.text-blue { color: var(--neon-cyan); }
.text-green { color: var(--neon-green); }
.text-muted { color: var(--text-secondary); }

.filter-bar {
  display: flex; gap: 16px; margin-bottom: 16px; align-items: flex-end; flex-shrink: 0;
}
.filter-group { display: flex; flex-direction: column; gap: 4px; }
.filter-group label {
  font-family: var(--font-title); font-size: 9px; letter-spacing: 1px; color: var(--text-secondary); text-transform: uppercase;
}
.filter-group select, .filter-group input {
  padding: 6px 10px; background: var(--bg-secondary); border: 1px solid var(--border-default);
  color: var(--neon-cyan); font-family: var(--font-mono); font-size: 12px; outline: none;
}

.loading { padding: 40px; text-align: center; color: var(--neon-cyan); }
.loading-spinner { display: inline-block; animation: spin 1s linear infinite; margin-right: 10px; }

.kanban-board {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; flex: 1; overflow: hidden; min-height: 0;
}

.kanban-column {
  display: flex; flex-direction: column; border: 1px solid var(--border-default);
  border-radius: 8px; overflow: hidden; min-height: 0;
}
.col-open { border-color: rgba(255,255,0,0.3); background: rgba(255,255,0,0.02); }
.col-in_progress { border-color: rgba(0,255,255,0.3); background: rgba(0,255,255,0.02); }
.col-resolved { border-color: rgba(0,255,0,0.3); background: rgba(0,255,0,0.02); }
.col-closed { border-color: rgba(136,136,136,0.3); background: rgba(136,136,136,0.02); }

.col-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 12px; border-bottom: 1px solid var(--border-default); flex-shrink: 0;
}
.col-title { font-family: var(--font-title); font-size: 11px; letter-spacing: 2px; text-transform: uppercase; }
.col-open .col-title { color: var(--neon-yellow); }
.col-in_progress .col-title { color: var(--neon-cyan); }
.col-resolved .col-title { color: var(--neon-green); }
.col-closed .col-title { color: var(--text-secondary); }
.col-count { font-family: var(--font-mono); font-size: 12px; color: var(--text-secondary); }

.col-body { flex: 1; overflow-y: auto; padding: 8px; display: flex; flex-direction: column; gap: 8px; }

.defect-card {
  padding: 10px 12px; background: var(--bg-panel); border: 1px solid var(--border-default);
  border-radius: 6px; cursor: pointer; transition: all var(--transition-fast);
}
.defect-card:hover { border-color: var(--neon-cyan); box-shadow: 0 0 10px rgba(0,255,255,0.2); }

.defect-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.defect-id { font-family: var(--font-mono); font-size: 10px; color: var(--text-secondary); }
.defect-title {
  font-family: var(--font-title); font-size: 11px; letter-spacing: 1px;
  color: var(--text-primary); margin-bottom: 6px; line-height: 1.4;
}
.defect-meta { display: flex; gap: 8px; flex-wrap: wrap; }
.meta-item { font-family: var(--font-mono); font-size: 10px; color: var(--text-secondary); }
.meta-item.priority { color: var(--neon-yellow); }

.severity-badge {
  font-family: var(--font-title); font-size: 9px; font-weight: 700; letter-spacing: 1px;
  padding: 2px 6px; border-radius: 3px; text-transform: uppercase;
}
.sev-critical { background: rgba(255,0,0,0.2); color: var(--neon-red); border: 1px solid var(--neon-red); }
.sev-high { background: rgba(255,136,0,0.2); color: var(--neon-orange); border: 1px solid var(--neon-orange); }
.sev-medium { background: rgba(255,255,0,0.2); color: var(--neon-yellow); border: 1px solid var(--neon-yellow); }
.sev-low { background: rgba(0,255,0,0.2); color: var(--neon-green); border: 1px solid var(--neon-green); }

.col-empty { padding: 20px; text-align: center; }
.glitch { font-family: var(--font-mono); font-size: 11px; animation: glitch 0.5s infinite; color: var(--text-secondary); }

.mono { font-family: var(--font-mono); }

/* Modal Styles */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.85); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}
.modal {
  background: var(--bg-panel); border: 1px solid var(--neon-cyan);
  box-shadow: 0 0 30px rgba(0,255,255,0.3);
}
.modal::before, .modal::after { display: none; }
.form-modal { width: 600px; max-height: 85vh; overflow-y: auto; }
.detail-modal { width: 720px; max-height: 85vh; overflow-y: auto; }
.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px; border-bottom: 1px solid var(--border-default); position: sticky; top: 0;
  background: var(--bg-panel); z-index: 1;
}
.modal-header h3 {
  font-family: var(--font-title); font-size: 14px; font-weight: 600; letter-spacing: 2px;
  color: var(--neon-cyan); margin: 0;
}
.btn-close { background: none; border: none; font-size: 20px; color: var(--text-secondary); cursor: pointer; }
.form-body { padding: 20px; }
.form-group { margin-bottom: 16px; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.form-group label {
  display: block; font-family: var(--font-title); font-size: 10px; letter-spacing: 1px;
  color: var(--text-secondary); margin-bottom: 6px; text-transform: uppercase;
}
.form-group input, .form-group textarea, .form-group select {
  width: 100%; padding: 10px 12px; background: var(--bg-secondary);
  border: 1px solid var(--border-default); color: var(--neon-cyan);
  font-family: var(--font-mono); font-size: 12px; outline: none; box-sizing: border-box;
}
.form-actions {
  display: flex; gap: 12px; justify-content: flex-end;
  padding: 16px 20px; border-top: 1px solid var(--border-default);
}

.detail-body { padding: 20px; }
.detail-title {
  font-family: var(--font-title); font-size: 16px; letter-spacing: 1px;
  color: var(--neon-cyan); margin-bottom: 12px;
}
.detail-meta-row { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
.priority-badge {
  font-family: var(--font-title); font-size: 10px; font-weight: 700; letter-spacing: 1px;
  padding: 2px 8px; border-radius: 3px; background: rgba(255,255,0,0.2);
  color: var(--neon-yellow); border: 1px solid var(--neon-yellow);
}
.status-badge {
  font-family: var(--font-title); font-size: 10px; font-weight: 600; letter-spacing: 1px;
  padding: 2px 8px; border-radius: 3px;
}
.status-open { background: rgba(255,255,0,0.2); color: var(--neon-yellow); border: 1px solid var(--neon-yellow); }
.status-in_progress { background: rgba(0,255,255,0.2); color: var(--neon-cyan); border: 1px solid var(--neon-cyan); }
.status-resolved { background: rgba(0,255,0,0.2); color: var(--neon-green); border: 1px solid var(--neon-green); }
.status-closed { background: rgba(136,136,136,0.2); color: var(--text-secondary); border: 1px solid var(--text-secondary); }

.detail-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
.detail-item { display: flex; flex-direction: column; gap: 4px; }
.detail-item label { font-family: var(--font-title); font-size: 9px; letter-spacing: 1px; color: var(--text-secondary); text-transform: uppercase; }
.detail-item span { font-family: var(--font-mono); font-size: 12px; color: var(--neon-cyan); }

.detail-section { margin-bottom: 16px; }
.detail-section > label {
  display: block; font-family: var(--font-title); font-size: 10px; letter-spacing: 1px;
  color: var(--text-secondary); text-transform: uppercase; margin-bottom: 6px;
}
.detail-section p { font-size: 13px; color: var(--text-primary); margin: 0; }
.detail-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }

.status-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.status-actions .btn { padding: 6px 12px; font-size: 10px; }

.comments-list { margin-bottom: 12px; }
.comment-item { padding: 10px; border: 1px solid var(--border-default); border-radius: 4px; margin-bottom: 8px; }
.comment-author { font-family: var(--font-title); font-size: 10px; color: var(--neon-cyan); margin-right: 8px; }
.comment-time { font-family: var(--font-mono); font-size: 10px; color: var(--text-secondary); }
.comment-text { font-size: 12px; color: var(--text-primary); margin: 6px 0 0; }
.comment-form { display: flex; gap: 8px; }
.comment-form textarea { flex: 1; }

.detail-actions { display: flex; gap: 12px; padding-top: 12px; border-top: 1px solid var(--border-default); }

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
