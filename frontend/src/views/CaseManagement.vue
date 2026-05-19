<template>
  <div class="case-management">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <h2 class="page-title">
          <span class="prompt">&gt;</span> 用例管理
        </h2>
      </div>
      <div class="toolbar-right">
        <input v-model="keyword" placeholder="搜索用例..." class="search-input" @input="debounceSearch" />
        <div style="display: flex; gap: 8px; align-items: center;">
          <el-select
            v-model="sortBy"
            style="width: 130px"
            popper-class="case-sort-select-popper"
            @change="debounceSearch"
          >
            <el-option label="按名称" value="name" />
            <el-option label="按创建时间" value="created_at" />
            <el-option label="按ID" value="id" />
          </el-select>
          <el-select
            v-model="sortOrder"
            style="width: 100px"
            popper-class="case-sort-select-popper"
            @change="debounceSearch"
          >
            <el-option label="↓ 降序" value="desc" />
            <el-option label="↑ 升序" value="asc" />
          </el-select>
        </div>
        <button class="btn primary" @click="openCreateModal">
          <span>+</span> 新建用例
        </button>
      </div>
    </div>

    <!-- Tab 切换：用例列表 / 分类管理 -->
    <el-tabs v-model="activeTab" class="content-tabs cyber-tabs">
      <el-tab-pane label="用例列表" name="cases">
        <div class="content">
          <!-- 左侧文件夹树 -->
          <div class="folder-tree panel">
            <div class="panel-header">
              <span class="panel-title">// 分类</span>
            </div>
            <div
              class="tree-item root"
              :class="{ active: selectedFolder === '/' }"
              @click="selectFolder('/')"
            >
              <span class="folder-icon">◈</span>
              全部用例 ({{ cases.length }})
            </div>
            <div v-for="folder in folderList" :key="folder.path"
              class="tree-item"
              :class="{ active: selectedFolder === folder.path }"
              @click="selectFolder(folder.path)"
            >
              <span class="folder-icon">▤</span>
              {{ folder.name }} ({{ folder.count }})
            </div>
          </div>

          <!-- 用例列表 -->
          <div class="case-list panel">
            <div class="panel-header">
              <span class="panel-title">// 用例列表</span>
            </div>
            <div v-if="loading" class="loading">
              <span class="loading-spinner">⟳</span>
              <span>加载中...</span>
            </div>
            <div v-else-if="fetchError" class="empty" style="color:#F43F5E;">
              <span>⚠ {{ fetchError }}</span>
            </div>
            <div v-else-if="filteredCases.length === 0" class="empty">
              <span class="glitch">// 暂无数据</span>
            </div>
            <div v-else class="case-table">
              <div class="table-header">
                <span class="col-method">方法</span>
                <span class="col-name">名称</span>
                <span class="col-path">路径</span>
                <span class="col-time">创建时间</span>
                <span class="col-actions">操作</span>
              </div>
              <div v-for="c in filteredCases" :key="c.id" class="table-row" @click="openCase(c)">
                <span class="col-method">
                  <span class="method-badge" :class="'method-' + c.method.toLowerCase()">{{ c.method }}</span>
                </span>
                <span class="col-name">{{ c.name }}</span>
                <span class="col-path">{{ c.folder_path }}</span>
                <span class="col-time">{{ formatDate(c.created_at) }}</span>
                <span class="col-actions" @click.stop>
                  <button class="icon-btn" :class="{ loading: runningCaseId === c.id }" :disabled="runningCaseId === c.id" title="执行" @click="runCase(c)">
                    <span v-if="runningCaseId === c.id" class="loading-spinner">⟳</span>
                    <span v-else>▶</span>
                  </button>
                  <button class="icon-btn" :class="{ loading: duplicatingCaseId === c.id }" :disabled="duplicatingCaseId === c.id" title="复制" @click="duplicateCase(c.id)">
                    <span v-if="duplicatingCaseId === c.id" class="loading-spinner">⟳</span>
                    <span v-else>📋</span>
                  </button>
                  <CyberConfirm
                    :ref="el => { if (el) cyberConfirmRefs[c.id] = el }"
                    title="确认删除这个用例？"
                    ok-text="删除"
                    cancel-text="取消"
                    danger
                    :loading="deletingCaseId === c.id"
                    @confirm="handleDelete(c.id)"
                  >
                    <template #trigger>
                      <button class="icon-btn danger" title="删除">🗑</button>
                    </template>
                  </CyberConfirm>
                </span>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>
      <el-tab-pane label="分类管理" name="folders">
        <CaseFolderManager />
      </el-tab-pane>
    </el-tabs>

    <!-- 新建/编辑弹窗 -->
    <CyberModal
      v-model="showCreateModal"
      :title="editingCase ? '编辑用例' : '新建用例'"
      :subtitle="editingCase ? `正在编辑: ${editingCase.name}` : '创建新的测试用例'"
      size="large"
      :confirm-text="editingCase ? '保存' : '创建'"
      :loading="saving"
      @confirm="saveCase"
    >
      <div class="form-row">
        <div class="form-group form-group--shrink">
          <label class="form-label">请求方法 *</label>
          <select v-model="form.method" class="form-select" :class="{ 'has-error': formErrors.method }">
            <option v-for="m in ['GET','POST','PUT','DELETE','PATCH']" :key="m" :value="m">{{ m }}</option>
          </select>
        </div>
        <div class="form-group flex-1">
          <label class="form-label">请求地址 *</label>
          <input
            v-model="form.url"
            class="form-input"
            placeholder="https://api.example.com/path"
            :class="{ 'has-error': formErrors.url }"
          />
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">用例名称 *</label>
        <input
          v-model="form.name"
          class="form-input"
          placeholder="用例名称"
          :class="{ 'has-error': formErrors.name }"
        />
      </div>

      <div class="form-group">
        <label class="form-label">所属分类</label>
        <input v-model="form.folder_path" class="form-input" placeholder="/用户模块/登录" />
      </div>

      <div class="form-group">
        <label class="form-label">描述</label>
        <textarea v-model="form.description" class="form-textarea" rows="2" placeholder="用例描述..."></textarea>
      </div>

      <div class="form-group">
        <label class="form-label">请求头 (JSON)</label>
        <textarea
          v-model="form.headers"
          class="form-textarea form-textarea--mono"
          rows="3"
          placeholder='{"Content-Type": "application/json"}'
        ></textarea>
      </div>

      <div class="form-group">
        <label class="form-label">请求体</label>
        <textarea v-model="form.request_body" class="form-textarea" rows="4" placeholder="请求体内容..."></textarea>
      </div>
    </CyberModal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onActivated, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { useCaseStore } from '@/stores/caseStore'
import { useRequestStore } from '@/stores/request'
import { storeToRefs } from 'pinia'
import CaseFolderManager from '@/components/CaseFolderManager.vue'
import CyberConfirm from '@/components/common/CyberConfirm.vue'
import CyberModal from '@/components/common/modal/CyberModal.vue'

const router = useRouter()

const caseStore = useCaseStore()
const requestStore = useRequestStore()

const { cases, folders, loading, fetchError } = storeToRefs(caseStore)

const keyword = ref('')
const activeTab = ref('cases')
const selectedFolder = ref('/')
const sortBy = ref('created_at')
const sortOrder = ref('desc')
const showCreateModal = ref(false)
const editingCase = ref(null)
const saving = ref(false)
const form = ref(defaultForm())
const formErrors = ref({ name: false, method: false, url: false })

watch(showCreateModal, (val) => {
  if (val) {
    formErrors.value = { name: false, method: false, url: false }
  } else {
    editingCase.value = null
    form.value = defaultForm()
  }
})

const runningCaseId = ref(null)
const duplicatingCaseId = ref(null)
const deletingCaseId = ref(null)

const cyberConfirmRefs = ref({})

const folderList = computed(() => {
  return folders.value.map(f => ({
    name: f.name,
    path: '/' + f.name,
    count: cases.value.filter(c => c.folder_path === '/' + f.name).length
  }))
})

const filteredCases = computed(() => {
  let list = cases.value
  if (selectedFolder.value !== '/') {
    list = list.filter(c => c.folder_path === selectedFolder.value)
  }
  if (keyword.value) {
    const kw = keyword.value.toLowerCase()
    list = list.filter(c => c.name.toLowerCase().includes(kw) || c.url.toLowerCase().includes(kw))
  }
  return list
})

function defaultForm() {
  return {
    name: '',
    method: 'GET',
    url: '',
    folder_path: '/',
    description: '',
    headers: {},
    params: {},
    body: '',
    body_type: 'json',
    request_body: '',
    response_body: '',
    auth_type: 'none',
    auth_config: {},
    assertions: [],
    pre_script: '',
    post_script: '',
    timeout: 30,
    follow_redirects: true,
    verify_ssl: true,
  }
}

function selectFolder(path) {
  selectedFolder.value = path
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit'
  })
}

let searchTimer = null
function debounceSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    caseStore.fetchCases({ keyword: keyword.value, sort_by: sortBy.value, order: sortOrder.value })
  }, 300)
}

function refreshWithDefaults() {
  clearTimeout(searchTimer)
  keyword.value = ''
  sortBy.value = 'created_at'
  sortOrder.value = 'desc'
  caseStore.fetchCases({ sort_by: 'created_at', order: 'desc' })
}

function openCreateModal() {
  editingCase.value = null
  form.value = defaultForm()
  showCreateModal.value = true
}

async function saveCase() {
  formErrors.value = { name: false, method: false, url: false }
  const missing = []
  if (!form.value.name?.trim()) {
    formErrors.value.name = true
    missing.push('名称')
  }
  if (!form.value.url?.trim()) {
    formErrors.value.url = true
    missing.push('URL')
  }
  if (missing.length > 0) {
    ElMessage.warning(`请填写必填项：${missing.join('、')}`)
    return
  }
  saving.value = true
  try {
    if (editingCase.value) {
      await caseStore.updateCase(editingCase.value.id, form.value)
      ElMessage.success('用例更新成功')
    } else {
      await caseStore.createCase(form.value)
      ElMessage.success('用例创建成功')
    }
    showCreateModal.value = false
    refreshWithDefaults()
  } catch (err) {
    ElMessage.error(editingCase.value ? '用例更新失败' : '用例创建失败')
    console.error('saveCase error:', err)
  } finally {
    saving.value = false
  }
}

function openCase(c) {
  editingCase.value = c
  form.value = { ...c }
  showCreateModal.value = true
}

async function runCase(c) {
  if (!c.url?.trim()) {
    ElMessage.warning('用例 URL 为空，无法执行')
    return
  }
  if (!c.method?.trim()) {
    ElMessage.warning('用例请求方法为空，无法执行')
    return
  }

  runningCaseId.value = c.id
  let result = {}
  let apiError = null
  try {
    result = await caseStore.runCase(c.id)
    console.log('[CaseManagement] 执行结果:', result)
  } catch (err) {
    apiError = err.message || '请求失败'
    console.error('[CaseManagement] 执行失败:', err)
    result = {}
  }

  const execData = result || {}
  const resp = execData?.response || {}
  const isSuccess = execData?.status === 'success'
  const error = apiError || execData?.error || resp.error || ''
  const reqBody = c.body || c.request_body || ''
  const reqHeaders = typeof c.headers === 'object' ? JSON.stringify(c.headers) : (c.headers || '')

  await ElMessageBox.alert(
    `<div class="run-result">
      <p><strong>方法:</strong> ${c.method}</p>
      <p><strong>URL:</strong> ${c.url}</p>
      ${reqHeaders ? `<p><strong>请求头:</strong></p><pre style="max-height:150px;overflow:auto;">${formatJson(reqHeaders)}</pre>` : ''}
      ${reqBody ? `<p><strong>请求体:</strong></p><pre style="max-height:150px;overflow:auto;">${formatJson(reqBody)}</pre>` : ''}
      <hr style="border-color:var(--border-default);margin:12px 0;">
      <p><strong>用例:</strong> ${c.name}</p>
      <p><strong>状态:</strong> ${isSuccess ? '✅ 成功' : '❌ 失败'}</p>
      ${resp.time_ms ? `<p><strong>响应时间:</strong> ${resp.time_ms}ms</p>` : ''}
      ${resp.status_code ? `<p><strong>状态码:</strong> ${resp.status_code}</p>` : ''}
      ${resp.body ? `<p><strong>响应体:</strong></p><pre style="max-height:200px;overflow:auto;">${formatJson(resp.body)}</pre>` : ''}
      ${error ? `<p style="color:#F43F5E;"><strong>错误:</strong> ${error}</p>` : ''}
    </div>`,
    '执行结果',
    {
      confirmButtonText: '确定',
      dangerouslyUseHTMLString: true,
      customClass: 'cyber-msgbox',
    }
  )
  runningCaseId.value = null

  if (isSuccess) {
    router.push('/history')
  }
}

function formatJson(val) {
  if (!val) return ''
  if (typeof val === 'object') return JSON.stringify(val, null, 2)
  try { return JSON.stringify(JSON.parse(val), null, 2) } catch { return val }
}

async function duplicateCase(id) {
  duplicatingCaseId.value = id
  try {
    const newCase = await caseStore.duplicateCase(id)
    ElMessage.success(`用例复制成功 【${newCase?.name}】`)
    refreshWithDefaults()
  } catch (err) {
    ElMessage.error('用例复制失败')
    console.error('duplicateCase error:', err)
  } finally {
    duplicatingCaseId.value = null
  }
}

async function handleDelete(id) {
  deletingCaseId.value = id
  try {
    await caseStore.deleteCase(id)
    ElMessage.success('删除成功')
    nextTick(() => { delete cyberConfirmRefs[id] })
    refreshWithDefaults()
  } catch (err) {
    ElMessage.error('删除失败')
    console.error('handleDelete error:', err)
    nextTick(() => {
      if (cyberConfirmRefs[id]) {
        cyberConfirmRefs[id].close()
        delete cyberConfirmRefs[id]
      }
    })
  } finally {
    deletingCaseId.value = null
  }
}

onMounted(() => {
  caseStore.fetchCases()
  caseStore.fetchFolders()
})

onActivated(() => {
  caseStore.fetchCases()
})
</script>

<style scoped>
.case-management {
  height: calc(100vh - var(--header-height) - 28px - 32px);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.toolbar-left, .toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
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

.search-input {
  padding: 8px 16px;
  width: 250px;
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 1px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-default);
  color: var(--neon-cyan);
  outline: none;
}

.search-input:focus {
  border-color: var(--neon-cyan);
  box-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
}

.content {
  flex: 1;
  display: flex;
  gap: 16px;
  overflow: hidden;
}

.content-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.content-tabs .el-tabs__content {
  flex: 1;
  overflow: hidden;
}

.content-tabs .el-tab-pane {
  height: 100%;
}

.folder-tree {
  width: 240px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
}

.panel-header {
  padding: 10px 16px;
  border-bottom: 1px solid var(--border-default);
  background: rgba(0, 255, 255, 0.02);
}

.panel-title {
  font-family: var(--font-title);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 2px;
  color: var(--text-secondary);
}

.tree-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  cursor: pointer;
  font-family: var(--font-title);
  font-size: 11px;
  letter-spacing: 1px;
  color: var(--text-secondary);
  border-left: 2px solid transparent;
  transition: all var(--transition-fast);
}

.tree-item:hover, .tree-item.active {
  background: rgba(0, 255, 255, 0.05);
  border-left-color: var(--neon-cyan);
  color: var(--neon-cyan);
}

.tree-item.active {
  background: rgba(0, 255, 255, 0.1);
}

.folder-icon {
  font-size: 12px;
}

.case-list {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.case-list .panel-header {
  flex-shrink: 0;
}

.case-table {
  flex: 1;
  overflow-y: auto;
}

.loading, .empty {
  padding: 40px;
  text-align: center;
  color: var(--text-secondary);
  font-family: var(--font-mono);
}

.loading-spinner {
  display: inline-block;
  animation: spin 1s linear infinite;
  margin-right: 10px;
  color: var(--neon-cyan);
}

.glitch {
  animation: glitch 0.5s infinite;
}

.table-header, .table-row {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  border-bottom: 1px solid var(--border-default);
}

.table-header {
  font-family: var(--font-title);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 2px;
  color: var(--neon-cyan);
  background: rgba(0, 255, 255, 0.02);
  position: sticky;
  top: 0;
}

.table-row {
  cursor: pointer;
  font-size: 12px;
  transition: all var(--transition-fast);
}

.table-row:hover {
  background: rgba(0, 255, 255, 0.05);
}

.col-method { width: 90px; }
.col-name { flex: 1; }
.col-path { width: 160px; color: var(--text-secondary); font-size: 11px; }
.col-time { width: 160px; color: var(--text-secondary); font-size: 11px; }
.col-actions { width: 120px; display: flex; gap: 4px; }

.icon-btn {
  background: transparent;
  border: 1px solid var(--border-default);
  cursor: pointer;
  padding: 4px 8px;
  font-size: 12px;
  color: var(--text-secondary);
  transition: all var(--transition-fast);
}

.icon-btn:hover {
  border-color: var(--neon-cyan);
  color: var(--neon-cyan);
}

.icon-btn.danger:hover {
  border-color: var(--neon-pink);
  color: var(--neon-pink);
}

.icon-btn.loading {
  cursor: not-allowed;
  opacity: 0.6;
}

.icon-btn.loading .loading-spinner {
  animation: spin 1s linear infinite;
  color: var(--neon-cyan);
}

/* Form Styles for CyberModal */
.form-row {
  display: flex;
  gap: 12px;
  margin-bottom: 18px;
}

.form-row:last-child {
  margin-bottom: 0;
}

.form-group {
  margin-bottom: 18px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group--shrink {
  flex-shrink: 0;
}

.flex-1 {
  flex: 1;
  min-width: 0;
}

.form-label {
  display: block;
  font-family: var(--font-title, 'Orbitron', sans-serif);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: var(--modal-text-secondary, #888);
  margin-bottom: 8px;
}

.form-input,
.form-select,
.form-textarea {
  width: 100%;
  padding: 10px 14px;
  background: var(--bg-secondary, #0a0a0f);
  border: 1px solid var(--modal-border, rgba(0, 255, 255, 0.22));
  border-radius: 4px;
  color: var(--modal-text-primary, #e0e0e0);
  font-family: var(--font-mono, 'Fira Code', monospace);
  font-size: 13px;
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
  box-sizing: border-box;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  border-color: var(--modal-ai-accent, #00f0ff);
  box-shadow: 0 0 0 2px rgba(0, 240, 255, 0.15);
}

.form-input::placeholder,
.form-textarea::placeholder {
  color: var(--modal-text-muted, #666);
}

.form-input.has-error,
.form-select.has-error {
  border-color: var(--modal-danger-accent, #ff4d7d);
}

.form-select {
  cursor: pointer;
  min-width: 100px;
}

.form-textarea {
  resize: vertical;
  min-height: 60px;
}

.form-textarea--mono {
  font-family: var(--font-mono, monospace);
}

@keyframes glitch {
  0% { transform: translate(0); opacity: 0.7; }
  20% { transform: translate(-2px, 2px); opacity: 0.8; }
  40% { transform: translate(-2px, -2px); opacity: 0.7; }
  60% { transform: translate(2px, 2px); opacity: 0.8; }
  80% { transform: translate(2px, -2px); opacity: 0.7; }
  100% { transform: translate(0); opacity: 0.7; }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Element Plus overrides */
:deep(.el-select) {
  --el-fill-color-blank: var(--bg-secondary, #1a1a2e);
  --el-text-color-regular: var(--neon-cyan, #00ffd5);
  --el-border-color: var(--border-default, #2a2a4a);
}

:deep(.el-select .el-input__wrapper) {
  background-color: var(--bg-secondary, #1a1a2e) !important;
  box-shadow: 0 0 0 1px var(--border-default, #2a2a4a) !important;
}

:deep(.el-select .el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--neon-cyan, #00ffd5) !important;
}

:deep(.el-select .el-input__inner) {
  color: var(--neon-cyan, #00ffd5) !important;
}

:deep(.el-select-dropdown) {
  background-color: var(--bg-panel, #16162a) !important;
  border-color: var(--neon-cyan, #00ffd5) !important;
}

:deep(.el-select-dropdown__item) {
  color: var(--text-primary, #e0e0e0) !important;
}

:deep(.el-select-dropdown__item.hover),
:deep(.el-select-dropdown__item:hover) {
  background-color: rgba(0, 255, 255, 0.1) !important;
}

:deep(.el-select-dropdown__item.selected) {
  color: var(--neon-cyan, #00ffd5) !important;
  font-weight: 600;
}

:deep(.el-tabs) {
  --el-tabs-header-height: 40px;
}

:deep(.el-tabs__header) {
  background-color: transparent !important;
  border-bottom: 1px solid var(--border-default, #2a2a4a) !important;
  margin-bottom: 0;
}

:deep(.el-tabs__nav-wrap::after) {
  display: none !important;
}

:deep(.el-tabs__item) {
  color: var(--text-secondary, #8a8a9a) !important;
  font-family: var(--font-title, 'Orbitron', sans-serif);
  font-size: 12px;
  letter-spacing: 1px;
  padding: 0 20px;
  height: 40px;
  line-height: 40px;
}

:deep(.el-tabs__item:hover) {
  color: var(--neon-cyan, #00ffd5) !important;
}

:deep(.el-tabs__item.is-active) {
  color: var(--neon-cyan, #00ffd5) !important;
}

:deep(.el-tabs__active-bar) {
  background-color: var(--neon-cyan, #00ffd5) !important;
  height: 2px;
}

:deep(.el-tabs__content) {
  padding: 0;
  overflow: hidden;
}

/* 排序下拉框深色主题适配 */
:deep(.el-select) {
  --el-select-border-color-hover: var(--neon-cyan, #0ff);
  --el-select-input-focus-border-color: var(--neon-cyan, #0ff);
}

:deep(.el-select .el-select__wrapper) {
  background-color: var(--bg-secondary, #0a0a0f) !important;
  box-shadow: 0 0 0 1px var(--border-default, rgba(0, 255, 255, 0.2)) !important;
  min-height: 32px !important;
  padding: 0 8px !important;
}

:deep(.el-select .el-select__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--neon-cyan, #0ff) !important;
}

:deep(.el-select .el-select__wrapper.is-focused) {
  box-shadow: 0 0 0 1px var(--neon-cyan, #0ff) !important;
}

:deep(.el-select .el-select__input) {
  color: var(--neon-cyan, #0ff) !important;
}

:deep(.el-select-dropdown) {
  background-color: var(--bg-panel, #0d0d14) !important;
  border: 1px solid var(--border-default, rgba(0, 255, 255, 0.2)) !important;
}

:deep(.el-select-dropdown__item) {
  color: var(--text-primary, #e0e0e0) !important;
  background-color: transparent !important;
}

:deep(.el-select-dropdown__item:hover) {
  background-color: rgba(0, 255, 255, 0.1) !important;
}

:deep(.el-select-dropdown__item.is-selected) {
  color: var(--neon-cyan, #0ff) !important;
  background-color: rgba(0, 255, 255, 0.15) !important;
  font-weight: 600 !important;
}

:deep(.el-popper.is-light) {
  background: var(--bg-panel, #0d0d14) !important;
  border-color: var(--border-default, rgba(0, 255, 255, 0.2)) !important;
}

:deep(.el-popper.is-light .el-popper__arrow::before) {
  background: var(--bg-panel, #0d0d14) !important;
  border-color: var(--border-default, rgba(0, 255, 255, 0.2)) !important;
}

/* 全局下拉弹窗深色主题适配 */
:deep(.el-select-dropdown) {
  background: var(--bg-panel, #0d0d14) !important;
  border: 1px solid var(--border-default, rgba(0, 255, 255, 0.2)) !important;
}

:deep(.el-select-dropdown .el-select-dropdown__item) {
  background: transparent !important;
  color: var(--text-primary, #e0e0e0) !important;
}

:deep(.el-select-dropdown .el-select-dropdown__item:hover) {
  background: rgba(0, 255, 255, 0.1) !important;
}

:deep(.el-select-dropdown .el-select-dropdown__item.is-selected) {
  color: var(--neon-cyan, #0ff) !important;
  background: rgba(0, 255, 255, 0.15) !important;
}

/* popper 深色适配 */
:deep(.el-popper) {
  background: var(--bg-panel, #0d0d14) !important;
  border-color: var(--border-default, rgba(0, 255, 255, 0.2)) !important;
}

:deep(.el-popper .el-popper__arrow::before) {
  background: var(--bg-panel, #0d0d14) !important;
  border-color: var(--border-default, rgba(0, 255, 255, 0.2)) !important;
}

/* 覆盖 Element Plus 默认的 popper 样式 */
:deep(.el-select-dropdown__popper) {
  --el-bg-color-overlay: var(--bg-panel, #0d0d14) !important;
  --el-text-color-regular: var(--text-primary, #e0e0e0) !important;
}

:deep(.el-select-dropdown__popper .el-scrollbar) {
  background: var(--bg-panel, #0d0d14) !important;
}

:deep(.el-select-dropdown__popper .el-select-dropdown__item) {
  background: transparent !important;
  color: var(--text-primary, #e0e0e0) !important;
}

:deep(.el-select-dropdown__popper .el-select-dropdown__item:hover) {
  background: rgba(0, 255, 255, 0.1) !important;
}

:deep(.el-select-dropdown__popper .el-select-dropdown__item.is-hovering) {
  background: rgba(0, 255, 255, 0.08) !important;
}
</style>
