<template>
  <div class="coverage-dashboard">
    <div class="toolbar">
      <h2 class="page-title">
        <span class="prompt">&gt;</span> 覆盖率仪表盘
      </h2>
      <div class="toolbar-actions">
        <select v-model="selectedRepo" class="cyber-select" @change="fetchSummary">
          <option value="">全部仓库</option>
          <option v-for="r in repos" :key="r.id" :value="r.id">{{ r.name }}</option>
        </select>
        <button class="btn primary" @click="triggerUpload">
          <span>↑</span> 上传覆盖率报告
        </button>
        <input ref="fileInput" type="file" accept=".lcov,.info,.xml,cobertura" style="display:none" @change="onFileChange" />
      </div>
    </div>

    <!-- Summary Cards -->
    <div v-if="!loading && summary" class="summary-cards">
      <div class="summary-card panel">
        <div class="card-label">行覆盖率</div>
        <div class="card-value" :style="{ color: coverageColor(summary.line_rate) }">
          {{ summary.line_coverage }}%
        </div>
        <div class="card-bar">
          <div class="card-bar-fill" :style="{ width: summary.line_coverage + '%', background: coverageColor(summary.line_coverage / 100) }"></div>
        </div>
      </div>
      <div class="summary-card panel">
        <div class="card-label">分支覆盖率</div>
        <div class="card-value" :style="{ color: coverageColor((summary.branch_coverage || 0) / 100) }">
          {{ summary.branch_coverage || 0 }}%
        </div>
        <div class="card-bar">
          <div class="card-bar-fill" :style="{ width: (summary.branch_coverage || 0) + '%', background: coverageColor((summary.branch_coverage || 0) / 100) }"></div>
        </div>
      </div>
      <div class="summary-card panel">
        <div class="card-label">总文件数</div>
        <div class="card-value text-cyan">{{ summary.total_files || 0 }}</div>
      </div>
      <div class="summary-card panel">
        <div class="card-label">覆盖文件数</div>
        <div class="card-value text-green">{{ summary.files_fully_covered || 0 }}</div>
      </div>
    </div>

    <div v-if="loading" class="loading">
      <span class="loading-spinner">⟳</span> 加载中...
    </div>
    <div v-else-if="!summary" class="empty">
      <span class="glitch">// 暂无覆盖率数据</span>
    </div>

    <!-- File Coverage Table -->
    <div v-if="summary && files.length > 0" class="file-table-wrap panel">
      <table class="file-table">
        <thead>
          <tr>
            <th>文件路径</th>
            <th>行覆盖率</th>
            <th>分支覆盖率</th>
            <th>总行数</th>
            <th>覆盖行数</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="f in files" :key="f.id" class="file-row">
            <td class="file-path mono">{{ f.file_path }}</td>
            <td>
              <div class="mini-bar-wrap">
                <div class="mini-bar">
                  <div class="mini-bar-fill" :style="{ width: f.line_coverage + '%', background: coverageColor(f.line_coverage / 100) }"></div>
                </div>
                <span class="mini-val" :style="{ color: coverageColor(f.line_coverage / 100) }">{{ f.line_coverage }}%</span>
              </div>
            </td>
            <td>
              <div class="mini-bar-wrap">
                <div class="mini-bar">
                  <div class="mini-bar-fill" :style="{ width: (f.branch_coverage || 0) + '%', background: coverageColor((f.branch_coverage || 0) / 100) }"></div>
                </div>
                <span class="mini-val" :style="{ color: coverageColor((f.branch_coverage || 0) / 100) }">{{ f.branch_coverage || 0 }}%</span>
              </div>
            </td>
            <td class="mono">{{ f.total_lines || 0 }}</td>
            <td class="mono">{{ f.covered_lines || 0 }}</td>
            <td>
              <span class="status-dot" :class="coverageClass(f.line_coverage / 100)"></span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Upload Progress -->
    <div v-if="uploading" class="upload-progress">
      <span class="loading-spinner">⟳</span> 上传中...
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { coverageApi } from '../../api/coverage'
import { repositoryApi } from '../../api/repository'

const repos = ref([])
const selectedRepo = ref('')
const summary = ref(null)
const files = ref([])
const loading = ref(false)
const uploading = ref(false)
const fileInput = ref(null)

async function fetchRepos() {
  try {
    const res = await repositoryApi.list()
    repos.value = res.data.data || []
  } catch {}
}

async function fetchSummary() {
  loading.value = true
  try {
    const params = selectedRepo.value ? { repository_id: selectedRepo.value } : {}
    const res = await coverageApi.summary(params)
    summary.value = res.data.data
    await fetchFiles()
  } catch {
    summary.value = null
    files.value = []
  } finally {
    loading.value = false
  }
}

async function fetchFiles() {
  if (!selectedRepo.value) {
    files.value = []
    return
  }
  try {
    const res = await coverageApi.fileList(selectedRepo.value)
    files.value = res.data.data || []
  } catch {
    files.value = []
  }
}

function triggerUpload() {
  fileInput.value?.click()
}

async function onFileChange(e) {
  const file = e.target.files[0]
  if (!file) return
  uploading.value = true
  const fd = new FormData()
  fd.append('file', file)
  try {
    await coverageApi.upload(fd, { repository_id: selectedRepo.value || undefined, commit_hash: 'HEAD', report_format: 'lcov' })
    await fetchSummary()
  } finally {
    uploading.value = false
    e.target.value = ''
  }
}

function coverageColor(rate) {
  if (rate >= 0.8) return 'var(--neon-green)'
  if (rate >= 0.5) return 'var(--neon-yellow)'
  return 'var(--neon-red)'
}

function coverageClass(rate) {
  if (rate >= 0.8) return 'good'
  if (rate >= 0.5) return 'medium'
  return 'poor'
}

onMounted(() => {
  fetchRepos()
  fetchSummary()
})
</script>

<style scoped>
.coverage-dashboard { padding: 16px; }

.toolbar {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; flex-wrap: wrap; gap: 12px;
}
.page-title {
  font-family: var(--font-title); font-size: 16px; font-weight: 700;
  letter-spacing: 3px; color: var(--neon-cyan); margin: 0; text-shadow: 0 0 10px var(--neon-cyan);
}
.prompt { color: var(--neon-magenta); }
.toolbar-actions { display: flex; gap: 12px; align-items: center; }

.cyber-select {
  font-family: var(--font-title); font-size: 11px; font-weight: 600;
  letter-spacing: 1px; padding: 8px 12px; background: var(--bg-secondary);
  border: 1px solid var(--neon-cyan); color: var(--neon-cyan); cursor: pointer; outline: none;
}

.loading { padding: 40px; text-align: center; color: var(--neon-cyan); }
.loading-spinner { display: inline-block; animation: spin 1s linear infinite; margin-right: 10px; }
.empty { padding: 40px; text-align: center; color: var(--text-secondary); }
.glitch { font-family: var(--font-mono); animation: glitch 0.5s infinite; }

.summary-cards {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px;
}
.summary-card {
  padding: 20px; text-align: center;
}
.card-label {
  font-family: var(--font-title); font-size: 10px; letter-spacing: 2px;
  color: var(--text-secondary); margin-bottom: 12px; text-transform: uppercase;
}
.card-value {
  font-family: var(--font-title); font-size: 32px; font-weight: 800;
  letter-spacing: 2px; margin-bottom: 12px;
}
.card-bar {
  height: 4px; background: var(--bg-secondary); border-radius: 2px; overflow: hidden;
}
.card-bar-fill {
  height: 100%; transition: width 0.5s ease; border-radius: 2px;
}
.text-cyan { color: var(--neon-cyan); }
.text-green { color: var(--neon-green); }

.file-table-wrap { padding: 0; overflow: auto; max-height: calc(100vh - 340px); }
.file-table {
  width: 100%; border-collapse: collapse;
}
.file-table th {
  background: rgba(0,255,255,0.05); color: var(--neon-cyan);
  padding: 10px 16px; text-align: left;
  font-family: var(--font-title); font-size: 10px; letter-spacing: 1px;
  border-bottom: 1px solid var(--border-default); white-space: nowrap; position: sticky; top: 0;
}
.file-table td {
  padding: 8px 16px; border-bottom: 1px solid var(--border-default);
  font-family: var(--font-mono); font-size: 12px; color: var(--text-primary);
}
.file-row:hover td { background: rgba(0,255,255,0.03); }
.file-path { max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.mono { font-family: var(--font-mono); font-size: 11px; }

.mini-bar-wrap { display: flex; align-items: center; gap: 8px; }
.mini-bar { width: 80px; height: 4px; background: var(--bg-secondary); border-radius: 2px; overflow: hidden; }
.mini-bar-fill { height: 100%; border-radius: 2px; }
.mini-val { font-family: var(--font-mono); font-size: 11px; min-width: 40px; }

.status-dot {
  display: inline-block; width: 10px; height: 10px; border-radius: 50%;
}
.status-dot.good { background: var(--neon-green); box-shadow: 0 0 8px var(--neon-green); }
.status-dot.medium { background: var(--neon-yellow); box-shadow: 0 0 8px var(--neon-yellow); }
.status-dot.poor { background: var(--neon-red); box-shadow: 0 0 8px var(--neon-red); animation: alert-flash 0.5s infinite; }

.upload-progress {
  margin-top: 16px; text-align: center; color: var(--neon-cyan); font-family: var(--font-mono);
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
@keyframes alert-flash {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
