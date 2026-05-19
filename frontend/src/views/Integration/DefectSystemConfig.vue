<template>
  <div class="defect-system-config">
    <div class="toolbar">
      <h2 class="page-title">
        <span class="prompt">&gt;</span> 缺陷系统配置
      </h2>
      <button class="btn primary" @click="openCreateModal">
        <span>+</span> 新建配置
      </button>
    </div>

    <div v-if="loading" class="loading">
      <span class="loading-spinner">⟳</span> 加载中...
    </div>
    <div v-else-if="systems.length === 0" class="empty">
      <span class="glitch">// 暂无缺陷系统配置</span>
    </div>
    <div v-else class="system-list">
      <div v-for="sys in systems" :key="sys.id" class="system-card panel">
        <div class="sys-header">
          <div class="sys-info">
            <span class="sys-icon">{{ systemIcon(sys.type) }}</span>
            <div class="sys-name-block">
              <span class="sys-name">{{ sys.name }}</span>
              <span class="sys-type-badge">{{ systemTypeLabel(sys.type) }}</span>
            </div>
          </div>
          <div class="sys-status" :class="sys.enabled ? 'enabled' : 'disabled'">
            {{ sys.enabled ? '◉ 已连接' : '○ 未连接' }}
          </div>
        </div>

        <div class="sys-fields">
          <div class="sys-field" v-for="(val, key) in visibleFields(sys)" :key="key">
            <span class="sf-label">{{ fieldLabel(key) }}</span>
            <span class="sf-value mono">{{ val }}</span>
          </div>
        </div>

        <div class="sys-actions">
          <button class="btn" @click="testConnection(sys)" :disabled="testing === sys.id">
            {{ testing === sys.id ? '测试中...' : '🔗 测试连接' }}
          </button>
          <button class="icon-btn" @click="openEditModal(sys)">✏️</button>
          <button class="icon-btn danger" @click="deleteSystem(sys.id)">🗑</button>
        </div>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ editing ? '// 编辑配置' : '// 新建缺陷系统' }}</h3>
          <button class="btn-close" @click="showModal = false">×</button>
        </div>
        <div class="form-body">
          <div class="form-group">
            <label>名称 *</label>
            <input v-model="form.name" placeholder="配置名称" />
          </div>
          <div class="form-group">
            <label>类型 *</label>
            <select v-model="form.type" @change="onTypeChange">
              <option value="jira">Jira</option>
              <option value="tapd">TAPD</option>
              <option value="zentao">禅道</option>
            </select>
          </div>

          <!-- Common fields -->
          <div class="form-group">
            <label>URL</label>
            <input v-model="form.url" placeholder="https://xxx.atlassian.net" />
          </div>
          <div class="form-group">
            <label>用户名 / 邮箱</label>
            <input v-model="form.username" placeholder="用户名或邮箱" />
          </div>
          <div class="form-group">
            <label>API Token</label>
            <input v-model="form.api_token" type="password" placeholder="API Token" />
          </div>

          <!-- Jira specific -->
          <template v-if="form.type === 'jira'">
            <div class="form-group">
              <label>项目 Key</label>
              <input v-model="form.project_key" placeholder="PROJECT" />
            </div>
          </template>

          <!-- TAPD specific -->
          <template v-if="form.type === 'tapd'">
            <div class="form-group">
              <label>公司 ID</label>
              <input v-model="form.company_id" placeholder="公司 ID" />
            </div>
            <div class="form-group">
              <label>Workspace ID</label>
              <input v-model="form.workspace_id" placeholder="Workspace ID" />
            </div>
          </template>

          <!-- 禅道 specific -->
          <template v-if="form.type === 'zentao'">
            <div class="form-group">
              <label>禅道版本</label>
              <select v-model="form.zentao_version">
                <option value="old">旧版 (开源版)</option>
                <option value="pro">企业版</option>
              </select>
            </div>
          </template>

          <div class="form-group">
            <label>启用状态</label>
            <label class="switch-label">
              <input type="checkbox" v-model="form.enabled" />
              <span>{{ form.enabled ? '启用' : '禁用' }}</span>
            </label>
          </div>
        </div>
        <div class="form-actions">
          <button class="btn" @click="showModal = false">取消</button>
          <button class="btn primary" @click="saveSystem" :disabled="saving || !form.name || !form.type">
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { integrationApi } from '../../api/integration'

const systems = ref([])
const loading = ref(true)
const showModal = ref(false)
const editing = ref(null)
const saving = ref(false)
const testing = ref(null)

const form = ref(defaultForm())
function defaultForm() {
  return {
    name: '', type: 'jira', url: '', username: '', api_token: '',
    project_key: '', company_id: '', workspace_id: '', zentao_version: 'old', enabled: true,
  }
}

async function fetchSystems() {
  loading.value = true
  try {
    const res = await integrationApi.listDefectSystems()
    systems.value = res.data.data || []
  } catch {
    systems.value = []
  } finally {
    loading.value = false
  }
}

function onTypeChange() {
  // Reset type-specific fields
  form.value.project_key = ''
  form.value.company_id = ''
  form.value.workspace_id = ''
}

function openCreateModal() {
  editing.value = null
  form.value = defaultForm()
  showModal.value = true
}

function openEditModal(sys) {
  editing.value = sys
  form.value = {
    name: sys.name,
    type: sys.type || 'jira',
    url: sys.url || '',
    username: sys.username || '',
    api_token: '',
    project_key: sys.project_key || '',
    company_id: sys.company_id || '',
    workspace_id: sys.workspace_id || '',
    zentao_version: sys.zentao_version || 'old',
    enabled: sys.enabled,
  }
  showModal.value = true
}

async function saveSystem() {
  if (!form.value.name || !form.value.type) return
  saving.value = true
  try {
    const data = { ...form.value }
    if (!data.api_token) delete data.api_token
    if (editing.value) {
      await integrationApi.updateDefectSystem(editing.value.id, data)
    } else {
      await integrationApi.createDefectSystem(data)
    }
    showModal.value = false
    await fetchSystems()
  } finally {
    saving.value = false
  }
}

async function testConnection(sys) {
  testing.value = sys.id
  try {
    await integrationApi.testConnection(sys.id)
    alert('连接成功！')
  } catch {
    alert('连接失败，请检查配置。')
  } finally {
    testing.value = null
  }
}

async function deleteSystem(id) {
  if (!confirm('确定要删除吗？')) return
  await integrationApi.deleteDefectSystem(id)
  await fetchSystems()
}

function systemIcon(type) {
  const m = { jira: '📋', tapd: '📝', zentao: '🛠' }
  return m[type] || '⚙'
}

function systemTypeLabel(type) {
  const m = { jira: 'Jira', tapd: 'TAPD', zentao: '禅道' }
  return m[type] || type
}

function fieldLabel(key) {
  const m = {
    url: 'URL', username: '用户名', project_key: '项目Key',
    company_id: '公司ID', workspace_id: 'Workspace', zentao_version: '版本',
  }
  return m[key] || key
}

function visibleFields(sys) {
  const fields = {}
  if (sys.url) fields.url = sys.url
  if (sys.username) fields.username = sys.username
  if (sys.project_key) fields.project_key = sys.project_key
  if (sys.company_id) fields.company_id = sys.company_id
  if (sys.workspace_id) fields.workspace_id = sys.workspace_id
  if (sys.zentao_version) fields.zentao_version = sys.zentao_version === 'pro' ? '企业版' : '开源版'
  return fields
}

onMounted(() => fetchSystems())
</script>

<style scoped>
.defect-system-config { padding: 16px; }

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
.glitch { font-family: var(--font-mono); animation: glitch 0.5s infinite; }

.system-list {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); gap: 16px;
}

.system-card { padding: 16px; }
.sys-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.sys-info { display: flex; align-items: center; gap: 12px; }
.sys-icon { font-size: 28px; }
.sys-name-block { display: flex; flex-direction: column; gap: 4px; }
.sys-name { font-family: var(--font-title); font-size: 14px; font-weight: 600; letter-spacing: 1px; color: var(--neon-cyan); }
.sys-type-badge {
  font-family: var(--font-title); font-size: 9px; font-weight: 700;
  padding: 2px 8px; border-radius: 3px; letter-spacing: 1px;
  background: rgba(0,255,255,0.15); color: var(--neon-cyan); border: 1px solid var(--neon-cyan);
}
.sys-status { font-family: var(--font-title); font-size: 11px; letter-spacing: 1px; }
.sys-status.enabled { color: var(--neon-green); }
.sys-status.disabled { color: var(--text-secondary); }

.sys-fields { display: flex; flex-direction: column; gap: 6px; margin-bottom: 12px; padding: 10px; background: var(--bg-secondary); border-radius: 4px; }
.sys-field { display: flex; gap: 8px; }
.sf-label { font-family: var(--font-title); font-size: 9px; letter-spacing: 1px; color: var(--text-secondary); text-transform: uppercase; min-width: 80px; }
.sf-value { font-family: var(--font-mono); font-size: 11px; color: var(--neon-cyan); }
.mono { font-family: var(--font-mono); }

.sys-actions { display: flex; gap: 8px; align-items: center; padding-top: 12px; border-top: 1px solid var(--border-default); }

.icon-btn {
  background: transparent; border: 1px solid var(--border-default); cursor: pointer;
  padding: 4px 8px; font-size: 12px; color: var(--text-secondary); transition: all var(--transition-fast);
}
.icon-btn:hover { border-color: var(--neon-cyan); color: var(--neon-cyan); }
.icon-btn.danger:hover { border-color: var(--neon-pink); color: var(--neon-pink); }

.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.85); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}
.modal {
  background: var(--bg-panel); border: 1px solid var(--neon-cyan);
  box-shadow: 0 0 30px rgba(0,255,255,0.3); width: 520px; max-height: 80vh; overflow-y: auto;
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
  color: var(--text-secondary); margin-bottom: 6px; text-transform: uppercase;
}
.form-group input, .form-group select {
  width: 100%; padding: 10px 12px; background: var(--bg-secondary);
  border: 1px solid var(--border-default); color: var(--neon-cyan);
  font-family: var(--font-mono); font-size: 12px; outline: none; box-sizing: border-box;
}
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
