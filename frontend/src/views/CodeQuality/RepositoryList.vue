<template>
  <div class="repository-list">
    <div class="toolbar">
      <h2 class="page-title">
        <span class="prompt">&gt;</span> 代码仓库管理
      </h2>
      <button class="btn primary" @click="openCreateModal">
        <span>+</span> 新建仓库
      </button>
    </div>

    <div v-if="loading" class="loading">
      <span class="loading-spinner">⟳</span> 加载中...
    </div>
    <div v-else-if="repos.length === 0" class="empty">
      <span class="glitch">// 暂无代码仓库</span>
    </div>
    <div v-else class="repo-table-wrap panel">
      <table class="repo-table">
        <thead>
          <tr>
            <th style="width:160px">名称</th>
            <th style="width:auto">URL</th>
            <th style="width:80px">分支</th>
            <th style="width:90px">提供商</th>
            <th style="width:150px">最后同步</th>
            <th style="width:110px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="repo in repos" :key="repo.id" class="repo-row">
            <td>
              <span class="repo-icon">⚡</span>
              {{ repo.name }}
            </td>
            <td>
              <span class="mono repo-url-text">{{ repo.url }}</span>
            </td>
            <td>
              <span class="method-badge">{{ repo.branch || 'main' }}</span>
            </td>
            <td>
              <span class="provider-badge" :class="'provider-' + (repo.provider || 'local')">
                {{ providerLabel(repo.provider) }}
              </span>
            </td>
            <td class="mono">{{ formatTime(repo.last_sync_at) }}</td>
            <td>
                <button class="icon-btn" @click="syncRepo(repo)" title="同步">⟳</button>
              <button class="icon-btn" @click="openEditModal(repo)" title="编辑">✏️</button>
              <button class="icon-btn danger" @click="deleteRepo(repo.id)" title="删除">🗑</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 新建/编辑弹窗 -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ editing ? '// 编辑仓库' : '// 新建仓库' }}</h3>
          <button class="btn-close" @click="showModal = false">×</button>
        </div>
        <div class="form-body">
          <div class="form-group">
            <label>名称</label>
            <input v-model="form.name" placeholder="仓库名称" />
          </div>
          <div class="form-group">
            <label>URL</label>
            <input v-model="form.url" placeholder="https://github.com/owner/repo" />
          </div>
          <div class="form-group">
            <label>分支</label>
            <input v-model="form.branch" placeholder="main" />
          </div>
          <div class="form-group">
            <label>提供商</label>
            <select v-model="form.provider">
              <option value="github">GitHub</option>
              <option value="gitlab">GitLab</option>
              <option value="gitee">Gitee</option>
              <option value="local">Local</option>
            </select>
          </div>
          <div class="form-group">
            <label>访问令牌</label>
            <input v-model="form.access_token" type="password" placeholder="可选，用于私有仓库" />
          </div>
        </div>
        <div class="form-actions">
          <button class="btn" @click="showModal = false">取消</button>
          <button class="btn primary" @click="saveRepo" :disabled="saving">
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { repositoryApi } from '../../api/repository'

const repos = ref([])
const loading = ref(true)
const showModal = ref(false)
const editing = ref(null)
const saving = ref(false)
const form = ref(defaultForm())

function defaultForm() {
  return { name: '', url: '', branch: 'main', provider: 'github', access_token: '' }
}

function providerLabel(p) {
  const map = { github: 'GitHub', gitlab: 'GitLab', gitee: 'Gitee', local: 'Local' }
  return map[p] || p
}

function formatTime(ts) {
  if (!ts) return '--'
  return new Date(ts).toLocaleString('zh-CN', { hour12: false })
}

async function fetchRepos() {
  loading.value = true
  try {
    const res = await repositoryApi.list()
    repos.value = res.data.data || []
  } catch {
    repos.value = []
  } finally {
    loading.value = false
  }
}

function openCreateModal() {
  editing.value = null
  form.value = defaultForm()
  showModal.value = true
}

function openEditModal(repo) {
  editing.value = repo
  form.value = {
    name: repo.name,
    url: repo.url,
    branch: repo.branch || 'main',
    provider: repo.provider || 'github',
    access_token: '',
  }
  showModal.value = true
}

async function saveRepo() {
  if (!form.value.name || !form.value.url) return
  saving.value = true
  try {
    const data = { ...form.value }
    if (!data.access_token) delete data.access_token
    if (editing.value) {
      await repositoryApi.update(editing.value.id, data)
    } else {
      await repositoryApi.create(data)
    }
    showModal.value = false
    await fetchRepos()
  } finally {
    saving.value = false
  }
}

async function syncRepo(repo) {
  try {
    await repositoryApi.sync(repo.id)
    await fetchRepos()
  } catch {}
}

async function deleteRepo(id) {
  if (!confirm('确定要删除吗？')) return
  await repositoryApi.delete(id)
  await fetchRepos()
}

onMounted(() => fetchRepos())
</script>

<style scoped>
.repository-list { padding: 16px; }

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
.empty { padding: 40px; text-align: center; color: var(--text-secondary); }
.glitch { font-family: var(--font-mono); animation: glitch 0.5s infinite; }

.repo-table-wrap {
  padding: 0; overflow: auto;
  border: 1px solid var(--border-default);
  border-radius: 4px;
}
.repo-table {
  width: 100%; border-collapse: collapse;
  table-layout: fixed;
}
.repo-table th {
  background: rgba(0,255,255,0.05); color: var(--neon-cyan);
  padding: 12px 16px; text-align: left;
  font-family: var(--font-title); font-size: 10px; letter-spacing: 1px;
  border-bottom: 1px solid var(--border-default); white-space: nowrap;
  font-weight: 600;
}
.repo-table td {
  padding: 10px 16px; border-bottom: 1px solid var(--border-default);
  font-family: var(--font-mono); font-size: 12px; color: var(--text-primary);
  vertical-align: middle;
}
.repo-table tr:last-child td { border-bottom: none; }
.repo-table th:first-child { border-left: none; }
.repo-table th:last-child { border-right: none; }
.repo-table td:first-child { border-left: none; }
.repo-table td:last-child { border-right: none; }
.repo-row:hover td { background: rgba(0,255,255,0.03); }
.repo-icon { color: var(--neon-magenta); margin-right: 8px; }
.repo-url-text { color: var(--text-secondary); }
.mono { font-family: var(--font-mono); font-size: 11px; }

.provider-badge {
  font-family: var(--font-title); font-size: 9px; font-weight: 700;
  padding: 2px 8px; border-radius: 3px; letter-spacing: 1px; text-transform: uppercase;
}
.provider-github { background: rgba(0,255,0,0.15); color: var(--neon-green); border: 1px solid var(--neon-green); }
.provider-gitlab { background: rgba(255,170,0,0.15); color: var(--neon-orange); border: 1px solid var(--neon-orange); }
.provider-gitee { background: rgba(255,0,0,0.15); color: var(--neon-red); border: 1px solid var(--neon-red); }
.provider-local { background: rgba(0,255,255,0.15); color: var(--neon-cyan); border: 1px solid var(--neon-cyan); }

.action-btns { display: inline-flex; gap: 4px; }

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
  color: var(--text-secondary); margin-bottom: 6px;
}
.form-group input, .form-group select {
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
