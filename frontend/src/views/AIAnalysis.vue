<template>
  <div class="ai-analysis">
    <!-- 标签页 -->
    <div class="tabs">
      <button 
        v-for="tab in tabs" 
        :key="tab.key"
        :class="{ active: currentTab === tab.key }"
        @click="currentTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- 失败聚类 -->
    <div v-if="currentTab === 'clusters'" class="tab-content">
      <div class="section-header">
        <h2>失败聚类分析</h2>
        <button class="btn-primary" @click="analyzeFailures">触发分析</button>
      </div>
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="clusters.length === 0" class="empty-state">
        <p>暂无失败聚类数据</p>
      </div>
      <div v-else class="cluster-list">
        <div v-for="cluster in clusters" :key="cluster.id" class="cluster-card">
          <div class="cluster-header">
            <span class="cluster-type" :class="getTypeClass(cluster.error_type)">
              {{ cluster.error_type }}
            </span>
            <span class="cluster-count">{{ cluster.occurrence_count }} 次</span>
            <span v-if="cluster.resolved" class="resolved-badge">已解决</span>
          </div>
          <div class="cluster-body">
            <p class="error-pattern">{{ cluster.error_pattern }}</p>
            <div v-if="cluster.root_cause" class="root-cause">
              <strong>根因:</strong> {{ cluster.root_cause }}
            </div>
            <div v-if="cluster.suggested_fix" class="suggested-fix">
              <strong>建议:</strong> {{ cluster.suggested_fix }}
            </div>
          </div>
          <div class="cluster-actions">
            <button class="btn-secondary btn-sm" @click="analyzeRootCause(cluster)">
              AI分析
            </button>
            <button v-if="!cluster.resolved" class="btn-secondary btn-sm" @click="resolveCluster(cluster)">
              标记解决
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 变更影响 -->
    <div v-if="currentTab === 'impact'" class="tab-content">
      <div class="section-header">
        <h2>变更影响预测</h2>
        <button class="btn-primary" @click="showPredictDialog = true">预测影响</button>
      </div>
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="impacts.length === 0" class="empty-state">
        <p>暂无预测历史</p>
      </div>
      <div v-else class="impact-list">
        <div v-for="impact in impacts" :key="impact.id" class="impact-card">
          <div class="impact-header">
            <span class="commit-hash">{{ impact.commit_hash }}</span>
            <span class="risk-badge" :class="getRiskClass(impact.risk_level)">
              {{ impact.risk_level }}
            </span>
          </div>
          <div class="impact-body">
            <p><strong>变更文件:</strong> {{ impact.changed_files?.length || 0 }} 个</p>
            <p><strong>建议:</strong> {{ impact.recommendation }}</p>
            <p><strong>预测准确率:</strong> {{ (impact.prediction_accuracy * 100).toFixed(0) }}%</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 告警配置 -->
    <div v-if="currentTab === 'alerts'" class="tab-content">
      <div class="section-header">
        <h2>智能告警规则</h2>
        <button class="btn-primary" @click="showAlertDialog = true">创建规则</button>
      </div>
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="alertRules.length === 0" class="empty-state">
        <p>暂无告警规则</p>
      </div>
      <div v-else class="rule-list">
        <div v-for="rule in alertRules" :key="rule.id" class="rule-card">
          <div class="rule-header">
            <span class="rule-name">{{ rule.name }}</span>
            <span class="rule-type">{{ rule.type }}</span>
            <span class="severity-badge" :class="rule.severity">{{ rule.severity }}</span>
            <label class="toggle">
              <input type="checkbox" :checked="rule.enabled" @change="toggleRule(rule)">
              <span>启用</span>
            </label>
          </div>
          <div class="rule-body">
            <p>阈值: {{ rule.threshold }}</p>
            <p>通知: {{ (rule.notify_channels || []).join(', ') }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 性能基线 -->
    <div v-if="currentTab === 'baselines'" class="tab-content">
      <div class="section-header">
        <h2>性能基线</h2>
        <button class="btn-primary" @click="showBaselineDialog = true">创建基线</button>
      </div>
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="baselines.length === 0" class="empty-state">
        <p>暂无性能基线</p>
      </div>
      <div v-else class="baseline-list">
        <div v-for="baseline in baselines" :key="baseline.id" class="baseline-card">
          <div class="baseline-header">
            <span class="metric-name">{{ baseline.metric_name }}</span>
            <span class="baseline-value">{{ baseline.baseline_value }} ms</span>
          </div>
          <div class="baseline-body">
            <p>上界: {{ baseline.upper_bound || '-' }} ms</p>
            <p>下界: {{ baseline.lower_bound || '-' }} ms</p>
            <p>样本数: {{ baseline.sample_count }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建基线弹窗 -->
    <div v-if="showBaselineDialog" class="dialog-overlay" @click.self="showBaselineDialog = false">
      <div class="dialog">
        <h2>创建性能基线</h2>
        <form @submit.prevent="createBaseline">
          <div class="form-group">
            <label>指标名称</label>
            <select v-model="baselineForm.metric_name" required>
              <option value="avg_rt">平均响应时间</option>
              <option value="p95_rt">P95响应时间</option>
              <option value="tps">每秒事务数</option>
              <option value="error_rate">错误率</option>
            </select>
          </div>
          <div class="form-group">
            <label>基准值 (ms)</label>
            <input v-model.number="baselineForm.baseline_value" type="number" required>
          </div>
          <div class="form-group">
            <label>上限 (ms)</label>
            <input v-model.number="baselineForm.upper_bound" type="number">
          </div>
          <div class="form-group">
            <label>下限 (ms)</label>
            <input v-model.number="baselineForm.lower_bound" type="number">
          </div>
          <div class="dialog-actions">
            <button type="button" class="btn-secondary" @click="showBaselineDialog = false">取消</button>
            <button type="submit" class="btn-primary">创建</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const API_BASE = '/api'

const currentTab = ref('clusters')
const tabs = [
  { key: 'clusters', label: '失败聚类' },
  { key: 'impact', label: '变更影响' },
  { key: 'alerts', label: '告警配置' },
  { key: 'baselines', label: '性能基线' }
]

const loading = ref(false)
const clusters = ref([])
const impacts = ref([])
const alertRules = ref([])
const baselines = ref([])

const showPredictDialog = ref(false)
const showAlertDialog = ref(false)
const showBaselineDialog = ref(false)

const baselineForm = ref({
  metric_name: 'avg_rt',
  baseline_value: 100,
  upper_bound: null,
  lower_bound: null
})

async function loadClusters() {
  loading.value = true
  try {
    const response = await fetch(`${API_BASE}/ai/clusters?project_id=1`, {
      headers: { 'Authorization': `Bearer ${authStore.accessToken}` }
    })
    if (response.ok) {
      const data = await response.json()
      clusters.value = data.items
    }
  } catch (err) {
    console.error('加载失败:', err)
  } finally {
    loading.value = false
  }
}

async function loadImpacts() {
  loading.value = true
  try {
    const response = await fetch(`${API_BASE}/ai/impact/history?project_id=1`, {
      headers: { 'Authorization': `Bearer ${authStore.accessToken}` }
    })
    if (response.ok) {
      const data = await response.json()
      impacts.value = data.items
    }
  } catch (err) {
    console.error('加载失败:', err)
  } finally {
    loading.value = false
  }
}

async function loadAlertRules() {
  loading.value = true
  try {
    const response = await fetch(`${API_BASE}/ai/alerts/rules?project_id=1`, {
      headers: { 'Authorization': `Bearer ${authStore.accessToken}` }
    })
    if (response.ok) {
      const data = await response.json()
      alertRules.value = data.items
    }
  } catch (err) {
    console.error('加载失败:', err)
  } finally {
    loading.value = false
  }
}

async function loadBaselines() {
  loading.value = true
  try {
    const response = await fetch(`${API_BASE}/ai/baselines?project_id=1`, {
      headers: { 'Authorization': `Bearer ${authStore.accessToken}` }
    })
    if (response.ok) {
      const data = await response.json()
      baselines.value = data.items
    }
  } catch (err) {
    console.error('加载失败:', err)
  } finally {
    loading.value = false
  }
}

async function analyzeRootCause(cluster) {
  try {
    const response = await fetch(`${API_BASE}/ai/clusters/${cluster.id}/analyze`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${authStore.accessToken}` }
    })
    if (response.ok) {
      const result = await response.json()
      alert(`根因分析结果:\n\n${result.root_cause}\n\n建议: ${result.suggested_fix}`)
      loadClusters()
    }
  } catch (err) {
    alert('分析失败')
  }
}

async function resolveCluster(cluster) {
  try {
    const response = await fetch(`${API_BASE}/ai/clusters/${cluster.id}/resolve`, {
      method: 'PUT',
      headers: { 'Authorization': `Bearer ${authStore.accessToken}` }
    })
    if (response.ok) {
      loadClusters()
    }
  } catch (err) {
    alert('操作失败')
  }
}

async function toggleRule(rule) {
  try {
    await fetch(`${API_BASE}/ai/alerts/rules/${rule.id}/toggle`, {
      method: 'PUT',
      headers: { 'Authorization': `Bearer ${authStore.accessToken}` }
    })
    loadAlertRules()
  } catch (err) {
    alert('操作失败')
  }
}

async function createBaseline() {
  try {
    const response = await fetch(`${API_BASE}/ai/baselines?project_id=1`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authStore.accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(baselineForm.value)
    })
    if (response.ok) {
      showBaselineDialog.value = false
      loadBaselines()
    }
  } catch (err) {
    alert('创建失败')
  }
}

function getTypeClass(type) {
  const map = {
    timeout: 'type-timeout',
    assertion: 'type-assertion',
    connection: 'type-connection',
    parse: 'type-parse',
    auth: 'type-auth'
  }
  return map[type] || 'type-default'
}

function getRiskClass(level) {
  const map = {
    low: 'risk-low',
    medium: 'risk-medium',
    high: 'risk-high',
    critical: 'risk-critical'
  }
  return map[level] || ''
}

async function analyzeFailures() {
  alert('请在执行历史中触发失败分析')
}

onMounted(() => {
  loadClusters()
})
</script>

<style scoped>
.ai-analysis {
  padding: 24px;
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  border-bottom: 1px solid var(--border-default);
  padding-bottom: 12px;
}

.tabs button {
  padding: 8px 16px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
}

.tabs button:hover {
  background: var(--bg-tertiary);
}

.tabs button.active {
  background: linear-gradient(135deg, var(--neon-cyan), var(--neon-magenta));
  color: #000;
  font-weight: 600;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h2 {
  margin: 0;
  font-size: 18px;
  color: var(--text-primary);
}

.loading, .empty-state {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
}

.cluster-list, .impact-list, .rule-list, .baseline-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.cluster-card, .impact-card, .rule-card, .baseline-card {
  background: var(--bg-panel);
  border: 1px solid var(--border-default);
  border-radius: 10px;
  padding: 16px;
  transition: all 0.2s;
}

.cluster-card:hover, .impact-card:hover, .rule-card:hover, .baseline-card:hover {
  border-color: var(--border-active);
}

.cluster-header, .impact-header, .rule-header, .baseline-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.cluster-type {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.type-timeout { background: var(--warning-bg, #fff7e6); color: var(--warning-color, #fa8c16); }
.type-assertion { background: var(--error-bg, #fff1f0); color: var(--error-color, #ff4d4f); }
.type-connection { background: var(--purple-bg, #f9f0ff); color: var(--purple-color, #722ed1); }
.type-parse { background: var(--info-bg, #e6f7ff); color: var(--info-color, #1890ff); }
.type-auth { background: var(--warning-bg, #fff7e6); color: var(--warning-color, #faad14); }
.type-default { background: var(--bg-tertiary, #f5f5f5); color: var(--text-secondary, #666); }

.cluster-count, .commit-hash {
  font-size: 14px;
  color: var(--text-secondary);
}

.resolved-badge {
  padding: 2px 8px;
  background: var(--success-bg, #e6f7e6);
  color: var(--success-color, #52c41a);
  border-radius: 10px;
  font-size: 12px;
}

.risk-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.risk-low { background: #e6f7e6; color: #52c41a; }
.risk-medium { background: #fff7e6; color: #fa8c16; }
.risk-high { background: #fff1f0; color: #ff4d4f; }
.risk-critical { background: #f9f0ff; color: #722ed1; }

.severity-badge {
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
}

.severity-badge.critical { background: #fff1f0; color: #ff4d4f; }
.severity-badge.high { background: #fff7e6; color: #fa8c16; }
.severity-badge.medium { background: #e6f7ff; color: #1890ff; }
.severity-badge.low { background: #e6f7e6; color: #52c41a; }

.rule-name, .metric-name {
  font-weight: 600;
  font-size: 14px;
}

.rule-type {
  font-size: 12px;
  color: #888;
}

.toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
  cursor: pointer;
}

.toggle input {
  width: 16px;
  height: 16px;
}

.cluster-body p, .impact-body p, .rule-body p, .baseline-body p {
  margin: 4px 0;
  font-size: 14px;
  color: #666;
}

.root-cause, .suggested-fix {
  margin-top: 8px;
  padding: 8px;
  background: #f5f5f5;
  border-radius: 6px;
  font-size: 13px;
}

.cluster-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.btn-primary {
  padding: 8px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
}

.btn-secondary {
  padding: 8px 16px;
  background: white;
  color: #666;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 13px;
}

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background: white;
  border-radius: 12px;
  padding: 24px;
  width: 480px;
}

.dialog h2 {
  margin: 0 0 16px 0;
}

.form-group {
  margin-bottom: 12px;
}

.form-group label {
  display: block;
  margin-bottom: 4px;
  font-size: 14px;
  font-weight: 500;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
}
</style>
