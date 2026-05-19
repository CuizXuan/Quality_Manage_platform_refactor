<template>
  <div class="dataset-list">
    <div class="toolbar">
      <h2 class="page-title">
        <span class="prompt">&gt;</span> 数据集管理
      </h2>
      <button class="btn primary" @click="openCreateModal">
        <span>+</span> 新建数据集
      </button>
    </div>

    <div class="split-view">
      <!-- 左侧：数据集列表 -->
      <div class="dataset-sidebar panel">
        <div v-if="dsStore.loading" class="loading">
          <span class="loading-spinner">⟳</span> 加载中...
        </div>
        <div v-else-if="dsStore.datasets.length === 0" class="empty">
          <span class="glitch">// 暂无数据集</span>
        </div>
        <div
          v-for="ds in dsStore.datasets"
          :key="ds.id"
          class="dataset-item"
          :class="{ active: dsStore.currentDataset?.id === ds.id }"
          @click="selectDataset(ds)"
        >
          <div class="ds-header">
            <span class="ds-icon">◈</span>
            <span class="ds-name">{{ ds.name }}</span>
            <span class="method-badge" style="font-size:9px">{{ ds.type || 'csv' }}</span>
          </div>
          <div class="ds-meta">
            <span>行数: {{ ds.row_count ?? '--' }}</span>
            <div class="ds-actions">
              <button class="icon-btn" @click.stop="openEditModal(ds)">✏️</button>
              <button class="icon-btn danger" @click.stop="removeDataset(ds.id)">🗑</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：数据预览 -->
      <div class="dataset-preview panel">
        <div v-if="!dsStore.currentDataset" class="empty-preview">
          <span class="glitch">// 请选择一个数据集</span>
        </div>
        <template v-else>
          <div class="preview-header">
            <h3>// {{ dsStore.currentDataset.name }}</h3>
            <span class="ds-info">行数: {{ dsStore.currentDataset.row_count ?? '--' }}</span>
          </div>
          <div class="preview-table-wrap">
            <table class="preview-table">
              <thead>
                <tr>
                  <th v-for="col in dsStore.previewData.headers" :key="col">{{ col }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in dsStore.previewData.rows" :key="i">
                  <td v-for="(cell, j) in row" :key="j">{{ cell }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>
      </div>
    </div>

    <!-- 新建/编辑弹窗 -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ editing ? '// 编辑数据集' : '// 新建数据集' }}</h3>
          <button class="btn-close" @click="showModal = false">×</button>
        </div>
        <div class="form-body">
          <div class="form-group">
            <label>名称</label>
            <input v-model="form.name" placeholder="数据集名称" />
          </div>
          <div class="form-group">
            <label>类型</label>
            <select v-model="form.type">
              <option value="csv">CSV</option>
              <option value="json">JSON</option>
            </select>
          </div>
          <div class="form-group">
            <label>数据来源</label>
            <div class="source-tabs">
              <button class="tab-btn" :class="{ active: form.source === 'upload' }" @click="form.source = 'upload'">上传文件</button>
              <button class="tab-btn" :class="{ active: form.source === 'paste' }" @click="form.source = 'paste'">粘贴数据</button>
            </div>
          </div>
          <div v-if="form.source === 'upload'" class="form-group">
            <label>CSV 文件</label>
            <input type="file" accept=".csv" @change="onFileChange" />
            <div v-if="fileName" class="file-name">{{ fileName }}</div>
          </div>
          <div v-if="form.source === 'paste'" class="form-group">
            <label>数据内容 (CSV 或 JSON)</label>
            <textarea v-model="form.data" rows="8" placeholder="在此粘贴 CSV 或 JSON 数据..."></textarea>
          </div>
        </div>
        <div class="form-actions">
          <button class="btn" @click="showModal = false">取消</button>
          <button class="btn primary" @click="saveDataset" :disabled="saving">
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useDatasetStore } from '../../stores/datasetStore'

const dsStore = useDatasetStore()

const showModal = ref(false)
const editing = ref(null)
const form = ref(defaultForm())
const saving = ref(false)
const fileName = ref('')

function defaultForm() {
  return { name: '', type: 'csv', source: 'upload', data: '' }
}

async function selectDataset(ds) {
  dsStore.setCurrentDataset(ds)
  await dsStore.fetchPreview(ds.id)
}

function openCreateModal() {
  editing.value = null
  form.value = defaultForm()
  fileName.value = ''
  showModal.value = true
}

function openEditModal(ds) {
  editing.value = ds
  form.value = { name: ds.name, type: ds.type || 'csv', source: 'paste', data: '' }
  showModal.value = true
}

function onFileChange(e) {
  const file = e.target.files[0]
  if (!file) return
  fileName.value = file.name
  const reader = new FileReader()
  reader.onload = (ev) => {
    form.value.data = ev.target.result
  }
  reader.readAsText(file)
}

async function saveDataset() {
  if (!form.value.name) return
  saving.value = true
  try {
    const data = {
      name: form.value.name,
      type: form.value.type,
      data: form.value.data,
    }
    if (editing.value) {
      await dsStore.updateDataset(editing.value.id, data)
    } else {
      await dsStore.createDataset(data)
    }
    showModal.value = false
  } finally {
    saving.value = false
  }
}

async function removeDataset(id) {
  if (!confirm('确定要删除吗？')) return
  await dsStore.deleteDataset(id)
  if (dsStore.currentDataset?.id === id) {
    dsStore.currentDataset = null
    dsStore.previewData = { headers: [], rows: [] }
  }
}

onMounted(() => dsStore.fetchDatasets())
</script>

<style scoped>
.dataset-list { padding: 16px; }

.toolbar {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;
}

.page-title {
  font-family: var(--font-title); font-size: 16px; font-weight: 700;
  letter-spacing: 3px; color: var(--neon-cyan); margin: 0; text-shadow: 0 0 10px var(--neon-cyan);
}
.prompt { color: var(--neon-magenta); }

.split-view {
  display: grid; grid-template-columns: 340px 1fr; gap: 16px; height: calc(100vh - 160px);
}

.dataset-sidebar {
  overflow-y: auto; padding: 12px;
}

.dataset-item {
  padding: 10px 12px; border: 1px solid var(--border-default); margin-bottom: 8px;
  cursor: pointer; transition: all var(--transition-fast);
}
.dataset-item:hover, .dataset-item.active {
  border-color: var(--neon-cyan); box-shadow: 0 0 10px rgba(0,255,255,0.2);
}
.dataset-item.active { background: rgba(0,255,255,0.05); }

.ds-header {
  display: flex; align-items: center; gap: 8px; margin-bottom: 4px;
  font-family: var(--font-title); font-size: 12px; font-weight: 600; letter-spacing: 1px;
}
.ds-icon { color: var(--neon-magenta); }
.ds-name { color: var(--neon-cyan); flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ds-meta {
  display: flex; justify-content: space-between; align-items: center;
  font-family: var(--font-mono); font-size: 10px; color: var(--text-secondary);
}
.ds-actions { display: flex; gap: 4px; }

.dataset-preview { padding: 16px; overflow: auto; }
.empty-preview {
  display: flex; align-items: center; justify-content: center; height: 100%;
  color: var(--text-secondary); font-family: var(--font-mono);
}
.glitch { animation: glitch 0.5s infinite; }

.preview-header {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;
}
.preview-header h3 {
  font-family: var(--font-title); font-size: 13px; letter-spacing: 2px; color: var(--neon-cyan); margin: 0;
}
.ds-info { font-family: var(--font-mono); font-size: 11px; color: var(--text-secondary); }

.preview-table-wrap { overflow: auto; max-height: calc(100% - 50px); }
.preview-table {
  width: 100%; border-collapse: collapse; font-family: var(--font-mono); font-size: 12px;
}
.preview-table th {
  background: rgba(0,255,255,0.05); color: var(--neon-cyan); padding: 8px 12px;
  text-align: left; font-family: var(--font-title); font-size: 10px; letter-spacing: 1px;
  border-bottom: 1px solid var(--border-default); white-space: nowrap;
}
.preview-table td {
  padding: 6px 12px; border-bottom: 1px solid var(--border-default); color: var(--text-primary);
  max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.preview-table tr:hover td { background: rgba(0,255,255,0.03); }

.loading { padding: 40px; text-align: center; color: var(--neon-cyan); }
.loading-spinner { display: inline-block; animation: spin 1s linear infinite; margin-right: 10px; }

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
.form-group input[type="text"], .form-group textarea, .form-group select {
  width: 100%; padding: 10px 12px; background: var(--bg-secondary);
  border: 1px solid var(--border-default); color: var(--neon-cyan);
  font-family: var(--font-mono); font-size: 12px; outline: none; box-sizing: border-box;
}
.form-group textarea { resize: vertical; }
.form-group input[type="file"] { font-family: var(--font-mono); font-size: 12px; color: var(--neon-cyan); }
.file-name { font-family: var(--font-mono); font-size: 11px; color: var(--neon-magenta); margin-top: 6px; }

.source-tabs { display: flex; gap: 8px; }
.tab-btn {
  font-family: var(--font-title); font-size: 11px; font-weight: 600; letter-spacing: 1px;
  text-transform: uppercase; padding: 8px 16px; background: transparent; border: 1px solid var(--border-default);
  color: var(--text-secondary); cursor: pointer; transition: all var(--transition-fast);
}
.tab-btn.active { border-color: var(--neon-cyan); color: var(--neon-cyan); }

.form-actions {
  display: flex; gap: 12px; justify-content: flex-end;
  padding: 16px 20px; border-top: 1px solid var(--border-default);
}

.icon-btn {
  background: transparent; border: 1px solid var(--border-default); cursor: pointer;
  padding: 4px 8px; font-size: 12px; color: var(--text-secondary); transition: all var(--transition-fast);
}
.icon-btn:hover { border-color: var(--neon-cyan); color: var(--neon-cyan); }
.icon-btn.danger:hover { border-color: var(--neon-pink); color: var(--neon-pink); }

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
