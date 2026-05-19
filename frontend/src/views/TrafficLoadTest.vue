<template>
  <div class="load-test-page">
    <div class="page-header">
      <h1 class="page-title">全链路压测</h1>
      <div class="header-actions">
        <button class="btn-primary" @click="showRecordDialog = true">
          + 新建录制
        </button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">📹</div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.totalRecords }}</span>
          <span class="stat-label">录制任务</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">▶</div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.totalReplays }}</span>
          <span class="stat-label">回放任务</span>
        </div>
      </div>
      <div class="stat-card success">
        <div class="stat-icon">✓</div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.matchRate }}%</span>
          <span class="stat-label">匹配率</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">⚡</div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.totalRequests }}</span>
          <span class="stat-label">总请求数</span>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="tabs">
      <button :class="{ active: currentTab === 'records' }" @click="currentTab = 'records'">
        📹 流量录制
      </button>
      <button :class="{ active: currentTab === 'replays' }" @click="currentTab = 'replays'">
        ▶ 流量回放
      </button>
      <button :class="{ active: currentTab === 'diff' }" @click="currentTab = 'diff'">
        📊 Diff 对比
      </button>
      <button :class="{ active: currentTab === 'tags' }" @click="currentTab = 'tags'">
        🏷 流量标签
      </button>
    </div>

    <!-- 流量录制 -->
    <div v-if="currentTab === 'records'" class="tab-content">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="!records.length" class="empty-state">
        暂无录制任务，<button @click="showRecordDialog = true" class="link-btn">创建第一个录制</button>
      </div>
      <div v-else class="record-list">
        <div v-for="record in records" :key="record.id" class="record-card">
          <div class="record-header">
            <span class="record-name">{{ record.name }}</span>
            <span class="record-status" :class="'status-' + record.status">
              {{ getStatusText(record.status) }}
            </span>
          </div>
          <div class="record-meta">
            <span class="source-tag">{{ record.source }}</span>
            <span v-if="record.request_count">请求: {{ record.request_count }}</span>
            <span v-if="record.unique_apis">API: {{ record.unique_apis }}</span>
          </div>
          <div class="record-time" v-if="record.time_range_start">
            {{ formatTime(record.time_range_start) }}
            <span v-if="record.time_range_end"> ~ {{ formatTime(record.time_range_end) }}</span>
          </div>
          <div class="record-actions">
            <button
              v-if="record.status === 'pending' || record.status === 'stopped'"
              class="btn-sm primary"
              @click="startRecord(record.id)"
            >开始录制</button>
            <button
              v-if="record.status === 'recording'"
              class="btn-sm danger"
              @click="stopRecord(record.id)"
            >停止录制</button>
            <button
              v-if="record.status === 'completed'"
              class="btn-sm"
              @click="createReplayFromRecord(record)"
            >创建回放</button>
            <button class="btn-sm" @click="deleteRecord(record.id)">删除</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 流量回放 -->
    <div v-if="currentTab === 'replays'" class="tab-content">
      <div v-if="!replays.length" class="empty-state">
        暂无回放任务，先创建录制再进行回放
      </div>
      <div v-else class="replay-list">
        <div v-for="replay in replays" :key="replay.id" class="replay-card">
          <div class="replay-header">
            <span class="replay-name">回放 #{{ replay.id }}</span>
            <span class="replay-status" :class="'status-' + replay.status">
              {{ getStatusText(replay.status) }}
            </span>
          </div>
          <div class="replay-stats">
            <div class="stat-item">
              <span class="label">总请求</span>
              <span class="value">{{ replay.total_requests || 0 }}</span>
            </div>
            <div class="stat-item success">
              <span class="label">成功</span>
              <span class="value">{{ replay.success_count || 0 }}</span>
            </div>
            <div class="stat-item warning">
              <span class="label">差异</span>
              <span class="value">{{ replay.diff_count || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="label">成功率</span>
              <span class="value">{{ ((replay.success_rate || 0) * 100).toFixed(1) }}%</span>
            </div>
          </div>
          <div class="replay-actions">
            <button
              v-if="replay.status === 'pending'"
              class="btn-sm primary"
              @click="startReplay(replay.id)"
            >开始回放</button>
            <button
              v-if="replay.status === 'running'"
              class="btn-sm danger"
              @click="stopReplay(replay.id)"
            >停止回放</button>
            <button
              v-if="replay.status === 'completed'"
              class="btn-sm"
              @click="viewDiff(replay.id)"
            >查看 Diff</button>
            <button class="btn-sm" @click="deleteReplay(replay.id)">删除</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Diff 对比 -->
    <div v-if="currentTab === 'diff'" class="tab-content">
      <div v-if="!selectedReplayId" class="empty-state">
        选择一个回放任务查看 Diff 报告
      </div>
      <div v-else class="diff-container">
        <div class="diff-summary">
          <div class="summary-item">
            <span class="label">总请求</span>
            <span class="value">{{ diffReport.summary?.total || 0 }}</span>
          </div>
          <div class="summary-item success">
            <span class="label">匹配</span>
            <span class="value">{{ diffReport.summary?.matched || 0 }}</span>
          </div>
          <div class="summary-item warning">
            <span class="label">差异</span>
            <span class="value">{{ diffReport.summary?.diff_count || 0 }}</span>
          </div>
          <div class="summary-item">
            <span class="label">匹配率</span>
            <span class="value">{{ ((diffReport.summary?.match_rate || 0) * 100).toFixed(1) }}%</span>
          </div>
        </div>

        <div class="diff-list">
          <div v-for="(diff, idx) in diffReport.diffs" :key="idx" class="diff-item">
            <div class="diff-request">{{ diff.request }}</div>
            <div class="diff-details">
              <span>原始: {{ diff.original_status }}</span>
              <span>回放: {{ diff.replay_status }}</span>
              <span v-if="diff.diff_fields">差异字段: {{ diff.diff_fields.join(', ') }}</span>
            </div>
          </div>
          <div v-if="!diffReport.diffs?.length" class="empty-diff">
            没有发现差异，所有请求完全匹配！
          </div>
        </div>
      </div>
    </div>

    <!-- 流量标签 -->
    <div v-if="currentTab === 'tags'" class="tab-content">
      <div class="tags-header">
        <button class="btn-secondary" @click="showTagDialog = true">+ 创建标签</button>
      </div>
      <div v-if="!tags.length" class="empty-state">暂无流量标签</div>
      <div v-else class="tag-list">
        <div v-for="tag in tags" :key="tag.id" class="tag-item">
          <span class="tag-name">{{ tag.tag_name }}</span>
          <span class="tag-value">{{ tag.tag_value }}</span>
          <span v-if="tag.description" class="tag-desc">{{ tag.description }}</span>
          <button class="btn-sm danger" @click="deleteTag(tag.id)">删除</button>
        </div>
      </div>
    </div>

    <!-- 创建录制弹窗 -->
    <div v-if="showRecordDialog" class="dialog-overlay" @click.self="showRecordDialog = false">
      <div class="dialog">
        <div class="dialog-header">
          <h2>新建录制任务</h2>
          <button class="btn-close" @click="showRecordDialog = false">×</button>
        </div>
        <div class="dialog-body">
          <div class="form-group">
            <label>录制名称</label>
            <input v-model="recordForm.name" type="text" placeholder="输入录制名称" />
          </div>
          <div class="form-group">
            <label>流量来源</label>
            <select v-model="recordForm.source">
              <option value="nginx">Nginx</option>
              <option value="envoy">Envoy</option>
              <option value="kubernetes">Kubernetes</option>
              <option value="custom">自定义</option>
            </select>
          </div>
          <div class="form-group">
            <label>过滤规则 (可选)</label>
            <textarea v-model="recordForm.filterRules" placeholder="JSON 格式，如: {&quot;exclude_paths&quot;: [&quot;/health&quot;]}" rows="3"></textarea>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="btn-secondary" @click="showRecordDialog = false">取消</button>
          <button class="btn-primary" @click="createRecord">创建</button>
        </div>
      </div>
    </div>

    <!-- 创建回放弹窗 -->
    <div v-if="showReplayDialog" class="dialog-overlay" @click.self="showReplayDialog = false">
      <div class="dialog">
        <div class="dialog-header">
          <h2>创建回放任务</h2>
          <button class="btn-close" @click="showReplayDialog = false">×</button>
        </div>
        <div class="dialog-body">
          <div class="form-group">
            <label>录制任务</label>
            <select v-model="replayForm.record_id">
              <option v-for="r in completedRecords" :key="r.id" :value="r.id">
                {{ r.name }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>并发数</label>
            <input v-model.number="replayForm.concurrency" type="number" min="1" max="100" />
          </div>
          <div class="form-group">
            <label>持续时间 (秒)</label>
            <input v-model.number="replayForm.duration" type="number" min="10" />
          </div>
          <div class="form-group checkbox">
            <label>
              <input type="checkbox" v-model="replayForm.enableShadow" />
              启用影子模式
            </label>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="btn-secondary" @click="showReplayDialog = false">取消</button>
          <button class="btn-primary" @click="createReplay">创建</button>
        </div>
      </div>
    </div>

    <!-- 创建标签弹窗 -->
    <div v-if="showTagDialog" class="dialog-overlay" @click.self="showTagDialog = false">
      <div class="dialog">
        <div class="dialog-header">
          <h2>创建流量标签</h2>
          <button class="btn-close" @click="showTagDialog = false">×</button>
        </div>
        <div class="dialog-body">
          <div class="form-group">
            <label>标签名称</label>
            <input v-model="tagForm.tagName" type="text" placeholder="如: x-load-test" />
          </div>
          <div class="form-group">
            <label>标签值</label>
            <input v-model="tagForm.tagValue" type="text" placeholder="如: stress-test" />
          </div>
          <div class="form-group">
            <label>描述 (可选)</label>
            <input v-model="tagForm.description" type="text" />
          </div>
        </div>
        <div class="dialog-footer">
          <button class="btn-secondary" @click="showTagDialog = false">取消</button>
          <button class="btn-primary" @click="createTag">创建</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const API_BASE = '/api'

const currentTab = ref('records')
const loading = ref(false)
const showRecordDialog = ref(false)
const showReplayDialog = ref(false)
const showTagDialog = ref(false)
const selectedReplayId = ref(null)

const records = ref([])
const replays = ref([])
const tags = ref([])
const diffReport = ref({ summary: {}, diffs: [] })

const stats = reactive({
  totalRecords: 0,
  totalReplays: 0,
  matchRate: 0,
  totalRequests: 0,
})

const recordForm = reactive({
  name: '',
  source: 'nginx',
  filterRules: '',
})

const replayForm = reactive({
  record_id: null,
  concurrency: 10,
  duration: 300,
  enableShadow: false,
})

const tagForm = reactive({
  tagName: '',
  tagValue: '',
  description: '',
})

const completedRecords = computed(() => records.value.filter(r => r.status === 'completed'))

async function loadRecords() {
  loading.value = true
  try {
    const resp = await fetch(`${API_BASE}/traffic/records/1`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    if (resp.ok) {
      const data = await resp.json()
      records.value = data.items || []
      stats.totalRecords = data.total
    }
  } catch (err) {
    console.error('加载录制失败:', err)
  } finally {
    loading.value = false
  }
}

async function loadReplays() {
  try {
    const resp = await fetch(`${API_BASE}/traffic/replays/1`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    if (resp.ok) {
      const data = await resp.json()
      replays.value = data.items || []
      stats.totalReplays = data.total
    }
  } catch (err) {
    console.error('加载回放失败:', err)
  }
}

async function loadTags() {
  try {
    const resp = await fetch(`${API_BASE}/traffic/tags`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    if (resp.ok) {
      tags.value = await resp.json()
    }
  } catch (err) {
    console.error('加载标签失败:', err)
  }
}

async function createRecord() {
  if (!recordForm.name) {
    alert('请输入录制名称')
    return
  }

  let filterRules = null
  if (recordForm.filterRules) {
    try {
      filterRules = JSON.parse(recordForm.filterRules)
    } catch (e) {
      alert('过滤规则 JSON 格式错误')
      return
    }
  }

  try {
    const resp = await fetch(`${API_BASE}/traffic/record`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authStore.accessToken}`
      },
      body: JSON.stringify({
        name: recordForm.name,
        source: recordForm.source,
        project_id: 1,
        filter_rules: filterRules,
      })
    })
    if (resp.ok) {
      showRecordDialog.value = false
      recordForm.name = ''
      recordForm.filterRules = ''
      loadRecords()
    }
  } catch (err) {
    console.error('创建录制失败:', err)
  }
}

async function startRecord(recordId) {
  try {
    const resp = await fetch(`${API_BASE}/traffic/record/${recordId}/start`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    if (resp.ok) {
      loadRecords()
    }
  } catch (err) {
    console.error('开始录制失败:', err)
  }
}

async function stopRecord(recordId) {
  try {
    const resp = await fetch(`${API_BASE}/traffic/record/${recordId}/stop`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    if (resp.ok) {
      loadRecords()
    }
  } catch (err) {
    console.error('停止录制失败:', err)
  }
}

async function deleteRecord(recordId) {
  if (!confirm('确定删除此录制?')) return
  try {
    const resp = await fetch(`${API_BASE}/traffic/record/${recordId}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    if (resp.ok) {
      loadRecords()
    }
  } catch (err) {
    console.error('删除录制失败:', err)
  }
}

function createReplayFromRecord(record) {
  replayForm.record_id = record.id
  showReplayDialog.value = true
}

async function createReplay() {
  if (!replayForm.record_id) {
    alert('请选择录制任务')
    return
  }

  try {
    const resp = await fetch(`${API_BASE}/traffic/replay`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authStore.accessToken}`
      },
      body: JSON.stringify({
        record_id: replayForm.record_id,
        project_id: 1,
        config: {
          concurrency: replayForm.concurrency,
          duration_seconds: replayForm.duration,
        },
        enable_shadow: replayForm.enableShadow,
      })
    })
    if (resp.ok) {
      showReplayDialog.value = false
      loadReplays()
    }
  } catch (err) {
    console.error('创建回放失败:', err)
  }
}

async function startReplay(replayId) {
  try {
    const resp = await fetch(`${API_BASE}/traffic/replay/${replayId}/start`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    if (resp.ok) {
      loadReplays()
    }
  } catch (err) {
    console.error('开始回放失败:', err)
  }
}

async function stopReplay(replayId) {
  try {
    const resp = await fetch(`${API_BASE}/traffic/replay/${replayId}/stop`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    if (resp.ok) {
      loadReplays()
    }
  } catch (err) {
    console.error('停止回放失败:', err)
  }
}

async function deleteReplay(replayId) {
  if (!confirm('确定删除此回放?')) return
  try {
    const resp = await fetch(`${API_BASE}/traffic/replay/${replayId}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    if (resp.ok) {
      loadReplays()
    }
  } catch (err) {
    console.error('删除回放失败:', err)
  }
}

async function viewDiff(replayId) {
  selectedReplayId.value = replayId
  currentTab.value = 'diff'
  try {
    const resp = await fetch(`${API_BASE}/traffic/replay/${replayId}/diff`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    if (resp.ok) {
      diffReport.value = await resp.json()
      stats.matchRate = ((diffReport.value.summary?.match_rate || 0) * 100).toFixed(1)
    }
  } catch (err) {
    console.error('加载 Diff 报告失败:', err)
  }
}

async function createTag() {
  if (!tagForm.tagName || !tagForm.tagValue) {
    alert('请填写标签名称和值')
    return
  }

  try {
    const resp = await fetch(`${API_BASE}/traffic/tag`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authStore.accessToken}`
      },
      body: JSON.stringify(tagForm)
    })
    if (resp.ok) {
      showTagDialog.value = false
      tagForm.tagName = ''
      tagForm.tagValue = ''
      tagForm.description = ''
      loadTags()
    }
  } catch (err) {
    console.error('创建标签失败:', err)
  }
}

async function deleteTag(tagId) {
  if (!confirm('确定删除此标签?')) return
  try {
    const resp = await fetch(`${API_BASE}/traffic/tag/${tagId}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    if (resp.ok) {
      loadTags()
    }
  } catch (err) {
    console.error('删除标签失败:', err)
  }
}

function getStatusText(status) {
  const map = {
    pending: '待开始',
    recording: '录制中',
    completed: '已完成',
    stopped: '已停止',
    running: '运行中',
    failed: '失败',
  }
  return map[status] || status
}

function formatTime(timeStr) {
  if (!timeStr) return ''
  return new Date(timeStr).toLocaleString('zh-CN')
}

onMounted(() => {
  loadRecords()
  loadReplays()
  loadTags()
})
</script>

<style scoped>
.load-test-page {
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
  color: var(--text-primary);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: var(--bg-panel);
  border: 1px solid var(--border-default);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  font-size: 32px;
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-tertiary);
  border-radius: 12px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  display: block;
}

.stat-label {
  font-size: 14px;
  color: var(--text-tertiary);
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  border-bottom: 1px solid var(--border-default);
  padding-bottom: 12px;
}

.tabs button {
  padding: 8px 20px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  cursor: pointer;
  border-radius: 6px;
}

.tabs button:hover {
  background: var(--bg-tertiary);
}

.tabs button.active {
  background: linear-gradient(135deg, var(--neon-cyan), var(--neon-magenta));
  color: #000;
  font-weight: 600;
}

.tab-content {
  min-height: 400px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-tertiary);
}

.link-btn {
  background: none;
  border: none;
  color: var(--neon-cyan);
  cursor: pointer;
  text-decoration: underline;
}

.record-list,
.replay-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.record-card,
.replay-card {
  background: var(--bg-panel);
  border: 1px solid var(--border-default);
  border-radius: 10px;
  padding: 16px;
}

.record-header,
.replay-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.record-name,
.replay-name {
  font-weight: 600;
  color: var(--text-primary);
}

.record-status,
.replay-status {
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 12px;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.status-recording {
  background: rgba(255, 166, 0, 0.1);
  color: #fa8c16;
}

.status-completed,
.status-running {
  background: rgba(82, 196, 26, 0.1);
  color: var(--success-color);
}

.record-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.source-tag {
  padding: 2px 8px;
  background: var(--neon-cyan);
  color: #000;
  border-radius: 4px;
  font-size: 12px;
}

.record-time,
.replay-time {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-bottom: 12px;
}

.record-actions,
.replay-actions {
  display: flex;
  gap: 8px;
}

.replay-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin: 12px 0;
}

.stat-item {
  text-align: center;
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: 8px;
}

.stat-item .label {
  display: block;
  font-size: 12px;
  color: var(--text-tertiary);
  margin-bottom: 4px;
}

.stat-item .value {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}

.stat-item.success .value {
  color: var(--success-color);
}

.stat-item.warning .value {
  color: #fa8c16;
}

.diff-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.summary-item {
  background: var(--bg-panel);
  border: 1px solid var(--border-default);
  border-radius: 10px;
  padding: 16px;
  text-align: center;
}

.summary-item .label {
  display: block;
  font-size: 12px;
  color: var(--text-tertiary);
  margin-bottom: 8px;
}

.summary-item .value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
}

.summary-item.success .value {
  color: var(--success-color);
}

.summary-item.warning .value {
  color: #fa8c16;
}

.diff-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.diff-item {
  background: var(--bg-panel);
  border: 1px solid var(--border-default);
  border-radius: 8px;
  padding: 12px;
}

.diff-request {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.diff-details {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--text-secondary);
}

.empty-diff {
  text-align: center;
  padding: 40px;
  color: var(--success-color);
  background: rgba(82, 196, 26, 0.05);
  border-radius: 8px;
}

.tags-header {
  margin-bottom: 16px;
}

.tag-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tag-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--bg-panel);
  border: 1px solid var(--border-default);
  border-radius: 8px;
}

.tag-name {
  padding: 4px 12px;
  background: var(--neon-cyan);
  color: #000;
  border-radius: 4px;
  font-weight: 600;
}

.tag-value {
  font-family: monospace;
  color: var(--neon-cyan);
}

.tag-desc {
  flex: 1;
  font-size: 13px;
  color: var(--text-tertiary);
}

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background: var(--bg-panel);
  border: 1px solid var(--neon-cyan);
  border-radius: 12px;
  width: 500px;
  max-width: 90%;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid var(--border-default);
}

.dialog-header h2 {
  margin: 0;
  color: var(--neon-cyan);
}

.btn-close {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  font-size: 24px;
  cursor: pointer;
}

.dialog-body {
  padding: 20px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--border-default);
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.form-group.checkbox label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-default);
  border-radius: 6px;
  font-size: 14px;
  background: var(--bg-secondary);
  color: var(--text-primary);
  box-sizing: border-box;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--neon-cyan);
}

.btn-sm {
  padding: 6px 12px;
  border: 1px solid var(--border-default);
  background: transparent;
  color: var(--text-secondary);
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}

.btn-sm:hover {
  border-color: var(--neon-cyan);
  color: var(--neon-cyan);
}

.btn-sm.primary {
  background: var(--neon-cyan);
  color: #000;
  border-color: var(--neon-cyan);
}

.btn-sm.danger {
  border-color: var(--error-color);
  color: var(--error-color);
}

.btn-secondary,
.btn-primary {
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
}

.btn-secondary {
  background: transparent;
  border: 1px solid var(--border-default);
  color: var(--text-secondary);
}

.btn-primary {
  background: linear-gradient(135deg, var(--neon-cyan), var(--neon-magenta));
  border: none;
  color: #000;
  font-weight: 600;
}

.loading {
  text-align: center;
  padding: 60px;
  color: var(--text-tertiary);
}
</style>
