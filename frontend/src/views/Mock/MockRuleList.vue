<template>
  <div class="mock-list">
    <div class="toolbar">
      <h2 class="page-title">
        <span class="prompt">&gt;</span> Mock 规则
      </h2>
      <button class="btn primary" @click="openCreateModal">
        <span>+</span> 新建规则
      </button>
    </div>

    <div v-if="mockStore.loading" class="loading">
      <span class="loading-spinner">⟳</span> 加载中...
    </div>
    <div v-else-if="mockStore.rules.length === 0" class="empty">
      <span class="glitch">// 暂无 Mock 规则</span>
    </div>
    <div v-else class="rule-list">
      <div v-for="r in mockStore.rules" :key="r.id" class="rule-card panel">
        <div class="rule-header">
          <div class="rule-info">
            <span class="method-badge" :class="'method-' + (r.method || 'get').toLowerCase()">
              {{ r.method || 'GET' }}
            </span>
            <span class="rule-path">{{ r.path }}</span>
          </div>
          <div class="rule-actions">
            <button class="icon-btn toggle" :class="{ enabled: r.enabled }" @click="toggleRule(r)">
              {{ r.enabled ? '◉' : '○' }}
            </button>
            <button class="icon-btn" @click="openEditModal(r)">✏️</button>
            <button class="icon-btn danger" @click="removeRule(r.id)">🗑</button>
          </div>
        </div>
        <div class="rule-body">
          <div v-if="r.description" class="rule-desc">{{ r.description }}</div>
          <div class="rule-meta">
            <span v-if="r.delay_ms" class="meta-item">延迟: {{ r.delay_ms }}ms</span>
            <span v-if="r.match_type" class="meta-item">匹配: {{ r.match_type }}</span>
            <span :class="'status-badge ' + (r.enabled ? 'success' : 'pending')">
              {{ r.enabled ? '启用' : '禁用' }}
            </span>
          </div>
          <div v-if="r.response_status" class="rule-response">
            <span class="res-label">响应:</span>
            <span class="res-status" :style="{ color: r.response_status >= 400 ? 'var(--neon-pink)' : 'var(--neon-green)' }">
              {{ r.response_status }}
            </span>
            <span v-if="r.response_body && r.response_body.length > 50" class="res-preview">
              {{ r.response_body.substring(0, 50) }}...
            </span>
            <span v-else-if="r.response_body" class="res-preview">{{ r.response_body }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 新建/编辑弹窗 -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ editing ? '// 编辑规则' : '// 新建规则' }}</h3>
          <button class="btn-close" @click="showModal = false">×</button>
        </div>
        <div class="form-body">
          <div class="form-group">
            <label>规则名称</label>
            <input v-model="form.name" placeholder="用户详情Mock" />
          </div>
          <div class="form-row">
            <div class="form-group" style="flex:1">
              <label>请求方法</label>
              <select v-model="form.method">
                <option>GET</option>
                <option>POST</option>
                <option>PUT</option>
                <option>DELETE</option>
                <option>PATCH</option>
              </select>
            </div>
            <div class="form-group" style="flex:2">
              <label>请求路径</label>
              <input v-model="form.path" placeholder="/api/users/:id" />
            </div>
          </div>
          <div class="form-group">
            <label>匹配方式</label>
            <select v-model="form.match_type">
              <option value="exact">精确匹配</option>
              <option value="contains">包含</option>
              <option value="regex">正则</option>
            </select>
          </div>
          <div class="form-row">
            <div class="form-group" style="flex:1">
              <label>响应状态码</label>
              <input v-model="form.response_status" type="number" placeholder="200" />
            </div>
            <div class="form-group" style="flex:1">
              <label>延迟 (ms)</label>
              <input v-model="form.delay_ms" type="number" placeholder="0" />
            </div>
          </div>
          <div class="form-group">
            <label>响应体</label>
            <textarea v-model="form.response_body" rows="6" placeholder='{"message": "mocked response"}'></textarea>
          </div>
          <div class="form-group">
            <label>描述</label>
            <input v-model="form.description" placeholder="模拟用户详情接口" />
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
          <button class="btn primary" @click="saveRule" :disabled="saving">
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useMockStore } from '../../stores/mockStore'

const mockStore = useMockStore()

const showModal = ref(false)
const editing = ref(null)
const saving = ref(false)
const form = ref(defaultForm())

function defaultForm() {
  return {
    name: '', method: 'GET', path: '/', match_type: 'exact',
    response_status: 200, response_body: '', delay_ms: 0,
    description: '', enabled: true,
  }
}

function openCreateModal() {
  editing.value = null
  form.value = defaultForm()
  showModal.value = true
}

function openEditModal(r) {
  editing.value = r
  form.value = {
    name: r.name,
    method: r.method || 'GET',
    path: r.path,
    match_type: r.match_type || 'exact',
    response_status: r.response_status || 200,
    response_body: r.response_body || '',
    delay_ms: r.delay_ms || 0,
    description: r.description || '',
    enabled: r.enabled,
  }
  showModal.value = true
}

async function saveRule() {
  if (!form.value.name || !form.value.path) return
  saving.value = true
  try {
    const data = {
      ...form.value,
      response_status: Number(form.value.response_status),
      delay_ms: Number(form.value.delay_ms) || 0,
    }
    if (editing.value) {
      await mockStore.updateRule(editing.value.id, data)
    } else {
      await mockStore.createRule(data)
    }
    showModal.value = false
  } finally {
    saving.value = false
  }
}

async function toggleRule(r) {
  await mockStore.toggleRule(r.id, !r.enabled)
}

async function removeRule(id) {
  if (!confirm('确定要删除吗？')) return
  await mockStore.deleteRule(id)
}

onMounted(() => mockStore.fetchRules())
</script>

<style scoped>
.mock-list { padding: 16px; }

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

.rule-list { display: flex; flex-direction: column; gap: 12px; }

.rule-card { padding: 14px 16px; }
.rule-header {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;
}
.rule-info { display: flex; align-items: center; gap: 10px; }
.rule-path {
  font-family: var(--font-mono); font-size: 13px; color: var(--neon-cyan);
}
.rule-actions { display: flex; gap: 4px; align-items: center; }

.rule-body {}
.rule-desc { font-size: 12px; color: var(--text-secondary); margin-bottom: 8px; }
.rule-meta {
  display: flex; align-items: center; gap: 12px; font-family: var(--font-mono); font-size: 11px;
}
.meta-item { color: var(--text-secondary); }
.rule-response {
  margin-top: 8px; display: flex; align-items: center; gap: 8px;
  font-family: var(--font-mono); font-size: 11px; padding: 6px 10px;
  background: var(--bg-secondary); border-radius: 4px;
}
.res-label { color: var(--text-secondary); }
.res-status { font-weight: 600; }
.res-preview { color: var(--neon-magenta); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.icon-btn {
  background: transparent; border: 1px solid var(--border-default); cursor: pointer;
  padding: 4px 8px; font-size: 12px; color: var(--text-secondary); transition: all var(--transition-fast);
}
.icon-btn:hover { border-color: var(--neon-cyan); color: var(--neon-cyan); }
.icon-btn.toggle { font-size: 14px; }
.icon-btn.toggle.enabled { color: var(--neon-green); border-color: var(--neon-green); }
.icon-btn.danger:hover { border-color: var(--neon-pink); color: var(--neon-pink); }

.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.85); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}
.modal {
  background: var(--bg-panel); border: 1px solid var(--neon-cyan);
  box-shadow: 0 0 30px rgba(0,255,255,0.3); width: 540px; max-height: 80vh; overflow-y: auto;
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
.form-group { margin-bottom: 16px; }
.form-group label {
  display: block; font-family: var(--font-title); font-size: 10px; letter-spacing: 1px;
  color: var(--text-secondary); margin-bottom: 6px;
}
.form-group input[type="text"], .form-group input[type="number"], .form-group select, .form-group textarea {
  width: 100%; padding: 10px 12px; background: var(--bg-secondary);
  border: 1px solid var(--border-default); color: var(--neon-cyan);
  font-family: var(--font-mono); font-size: 12px; outline: none; box-sizing: border-box;
}
.form-group textarea { resize: vertical; }
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
