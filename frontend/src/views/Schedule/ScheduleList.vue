<template>
  <div class="schedule-list">
    <div class="toolbar">
      <h2 class="page-title">
        <span class="prompt">&gt;</span> 定时任务
      </h2>
      <button class="btn primary" @click="openCreateModal">
        <span>+</span> 新建任务
      </button>
    </div>

    <div v-if="schedStore.loading" class="loading">
      <span class="loading-spinner">⟳</span> 加载中...
    </div>
    <div v-else-if="schedStore.schedules.length === 0" class="empty">
      <span class="glitch">// 暂无定时任务</span>
    </div>
    <div v-else class="schedule-grid">
      <div v-for="s in schedStore.schedules" :key="s.id" class="schedule-card panel">
        <div class="sch-header">
          <div class="sch-name">
            <span class="sch-icon">⏱</span>
            {{ s.name }}
          </div>
          <div class="sch-actions">
            <button class="icon-btn" :class="{ active: s.enabled }" @click="toggleSchedule(s)" title="Toggle">
              {{ s.enabled ? '⏸' : '▶' }}
            </button>
            <button class="icon-btn" @click="openEditModal(s)">✏️</button>
            <button class="icon-btn" danger @click="removeSchedule(s.id)">🗑</button>
          </div>
        </div>
        <div class="sch-body">
          <div class="sch-row">
            <span class="sch-label">Cron</span>
            <span class="sch-value mono">{{ s.cron_expression }}</span>
          </div>
          <div class="sch-row">
            <span class="sch-label">STATUS</span>
            <span :class="'status-badge ' + (s.enabled ? 'success' : 'pending')">
              {{ s.enabled ? '已启用' : '已暂停' }}
            </span>
          </div>
          <div class="sch-row">
            <span class="sch-label">下次执行</span>
            <span class="sch-value mono">{{ formatTime(s.next_run_at) }}</span>
          </div>
          <div v-if="s.environment" class="sch-row">
            <span class="sch-label">环境</span>
            <span class="sch-value">{{ s.environment }}</span>
          </div>
          <div v-if="s.notify_channels?.length" class="sch-row">
            <span class="sch-label">通知</span>
            <span class="sch-value">{{ s.notify_channels.join(', ') }}</span>
          </div>
        </div>
        <div class="sch-footer">
          <button class="btn" @click="runNow(s.id)">▶ 立即执行</button>
        </div>
      </div>
    </div>

    <!-- 新建/编辑弹窗 -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ editing ? '// 编辑任务' : '// 新建任务' }}</h3>
          <button class="btn-close" @click="showModal = false">×</button>
        </div>
        <div class="form-body">
          <div class="form-group">
            <label>任务名称</label>
            <input v-model="form.name" placeholder="每日冒烟测试" />
          </div>
          <div class="form-group">
            <label>Cron 表达式</label>
            <input v-model="form.cron_expression" placeholder="0 8 * * *" />
            <div class="cron-hint">格式: 分 时 日 月 周</div>
          </div>
          <div class="form-group">
            <label>执行对象</label>
            <select v-model="form.target_type">
              <option value="case">单个用例</option>
              <option value="scenario">场景</option>
            </select>
          </div>
          <div class="form-group">
            <label>{{ form.target_type === 'case' ? '用例 ID' : '场景 ID' }}</label>
            <input v-model="form.target_id" type="number" placeholder="1" />
          </div>
          <div class="form-group">
            <label>执行环境</label>
            <input v-model="form.environment" placeholder="test" />
          </div>
          <div class="form-group">
            <label>通知渠道（逗号分隔）</label>
            <input v-model="form.notify_channels" placeholder="email, dingtalk" />
          </div>
          <div class="form-group">
            <label>启用状态</label>
            <label class="switch-label">
              <input type="checkbox" v-model="form.enabled" />
              <span>{{ form.enabled ? '是' : '否' }}</span>
            </label>
          </div>
        </div>
        <div class="form-actions">
          <button class="btn" @click="showModal = false">取消</button>
          <button class="btn primary" @click="saveSchedule" :disabled="saving">
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useScheduleStore } from '../../stores/scheduleStore'

const schedStore = useScheduleStore()

const showModal = ref(false)
const editing = ref(null)
const saving = ref(false)
const form = ref(defaultForm())

function defaultForm() {
  return {
    name: '', cron_expression: '0 8 * * *',
    target_type: 'case', target_id: null,
    environment: '', notify_channels: '', enabled: true,
  }
}

function openCreateModal() {
  editing.value = null
  form.value = defaultForm()
  showModal.value = true
}

function openEditModal(s) {
  editing.value = s
  form.value = {
    name: s.name,
    cron_expression: s.cron_expression,
    target_type: s.target_type || 'case',
    target_id: s.target_id,
    environment: s.environment || '',
    notify_channels: (s.notify_channels || []).join(', '),
    enabled: s.enabled,
  }
  showModal.value = true
}

async function saveSchedule() {
  if (!form.value.name || !form.value.cron_expression) return
  saving.value = true
  try {
    const data = {
      ...form.value,
      target_id: form.value.target_id ? Number(form.value.target_id) : null,
      notify_channels: form.value.notify_channels ? form.value.notify_channels.split(',').map(s => s.trim()) : [],
    }
    if (editing.value) {
      await schedStore.updateSchedule(editing.value.id, data)
    } else {
      await schedStore.createSchedule(data)
    }
    showModal.value = false
  } finally {
    saving.value = false
  }
}

async function toggleSchedule(s) {
  await schedStore.toggleSchedule(s.id, !s.enabled)
}

async function runNow(id) {
  await schedStore.runSchedule(id)
}

async function removeSchedule(id) {
  if (!confirm('确定要删除吗？')) return
  await schedStore.deleteSchedule(id)
}

function formatTime(ts) {
  if (!ts) return '--'
  return new Date(ts).toLocaleString('en-US', { hour12: false })
}

onMounted(() => schedStore.fetchSchedules())
</script>

<style scoped>
.schedule-list { padding: 16px; }

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

.schedule-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px;
}

.schedule-card { padding: 16px; }
.sch-header {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;
}
.sch-name {
  font-family: var(--font-title); font-size: 13px; font-weight: 600; letter-spacing: 1px;
  color: var(--neon-cyan); display: flex; align-items: center; gap: 8px;
}
.sch-icon { color: var(--neon-magenta); }
.sch-actions { display: flex; gap: 4px; }

.sch-body { margin-bottom: 12px; }
.sch-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 4px 0; font-family: var(--font-mono); font-size: 12px;
}
.sch-label { color: var(--text-secondary); letter-spacing: 1px; }
.sch-value { color: var(--neon-cyan); }
.mono { font-family: var(--font-mono); }

.sch-footer { padding-top: 8px; border-top: 1px solid var(--border-default); }

.icon-btn {
  background: transparent; border: 1px solid var(--border-default); cursor: pointer;
  padding: 4px 8px; font-size: 12px; color: var(--text-secondary); transition: all var(--transition-fast);
}
.icon-btn:hover { border-color: var(--neon-cyan); color: var(--neon-cyan); }
.icon-btn.active { color: var(--neon-green); border-color: var(--neon-green); }
.icon-btn[danger]:hover { border-color: var(--neon-pink); color: var(--neon-pink); }

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
.form-group { margin-bottom: 16px; }
.form-group label {
  display: block; font-family: var(--font-title); font-size: 10px; letter-spacing: 1px;
  color: var(--text-secondary); margin-bottom: 6px;
}
.form-group input[type="text"], .form-group input[type="number"], .form-group select {
  width: 100%; padding: 10px 12px; background: var(--bg-secondary);
  border: 1px solid var(--border-default); color: var(--neon-cyan);
  font-family: var(--font-mono); font-size: 12px; outline: none; box-sizing: border-box;
}
.cron-hint { font-family: var(--font-mono); font-size: 10px; color: var(--text-secondary); margin-top: 4px; }
.switch-label {
  display: flex; align-items: center; gap: 8px; cursor: pointer;
  color: var(--neon-cyan); font-family: var(--font-title); font-size: 11px; letter-spacing: 1px;
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
