<template>
  <div class="chaos-studio">
    <div class="page-header">
      <h1 class="page-title">混沌工程</h1>
      <div class="header-actions">
        <button class="btn-primary" @click="showExperimentDialog = true">
          + 新建实验
        </button>
        <button class="btn-secondary" @click="showEvaluateDialog = true">
          🔍 韧性评估
        </button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">🧪</div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.totalExperiments }}</span>
          <span class="stat-label">实验总数</span>
        </div>
      </div>
      <div class="stat-card running">
        <div class="stat-icon">⚡</div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.runningExperiments }}</span>
          <span class="stat-label">运行中</span>
        </div>
      </div>
      <div class="stat-card success">
        <div class="stat-icon">✓</div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.completedExperiments }}</span>
          <span class="stat-label">已完成</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📊</div>
        <div class="stat-info">
          <span class="stat-value">{{ latestScore || '--' }}</span>
          <span class="stat-label">韧性评分</span>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="tabs">
      <button :class="{ active: currentTab === 'experiments' }" @click="currentTab = 'experiments'">
        🧪 混沌实验
      </button>
      <button :class="{ active: currentTab === 'faults' }" @click="currentTab = 'faults'">
        ⚡ 故障注入
      </button>
      <button :class="{ active: currentTab === 'resilience' }" @click="currentTab = 'resilience'">
        📊 韧性评分
      </button>
    </div>

    <!-- 混沌实验 -->
    <div v-if="currentTab === 'experiments'" class="tab-content">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="!experiments.length" class="empty-state">
        暂无混沌实验，<button @click="showExperimentDialog = true" class="link-btn">创建第一个实验</button>
      </div>
      <div v-else class="experiment-list">
        <div v-for="exp in experiments" :key="exp.id" class="experiment-card">
          <div class="exp-header">
            <span class="exp-name">{{ exp.name }}</span>
            <span class="exp-status" :class="'status-' + exp.status">
              {{ exp.status_text }}
            </span>
          </div>
          <div v-if="exp.description" class="exp-desc">{{ exp.description }}</div>
          <div class="exp-meta">
            <span class="target-tag">{{ exp.target_type }}: {{ exp.target_id || '未指定' }}</span>
            <span v-if="exp.blast_radius">爆炸半径: {{ exp.blast_radius }}</span>
          </div>
          <div v-if="exp.hypothesis" class="exp-hypothesis">
            <span class="label">假设:</span> {{ exp.hypothesis }}
          </div>
          <div class="exp-faults" v-if="exp.faults?.length">
            <span class="label">故障:</span>
            <span v-for="fault in exp.faults" :key="fault.id" class="fault-tag" :class="'fault-' + fault.status">
              {{ fault.fault_type }} ({{ fault.status }})
            </span>
          </div>
          <div class="exp-actions">
            <button
              v-if="exp.status === 'draft'"
              class="btn-sm primary"
              @click="startExperiment(exp.id)"
            >启动</button>
            <button
              v-if="exp.status === 'running'"
              class="btn-sm danger"
              @click="stopExperiment(exp.id)"
            >停止</button>
            <button
              v-if="exp.status === 'running'"
              class="btn-sm"
              @click="openFaultDialog(exp.id)"
            >注入故障</button>
            <button class="btn-sm" @click="viewExperiment(exp.id)">详情</button>
            <button
              v-if="exp.status === 'draft'"
              class="btn-sm danger"
              @click="deleteExperiment(exp.id)"
            >删除</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 故障注入 -->
    <div v-if="currentTab === 'faults'" class="tab-content">
      <div class="fault-types-grid">
        <div
          v-for="ft in faultTypes"
          :key="ft.type"
          class="fault-type-card"
          :class="'risk-' + ft.risk_level"
          @click="selectFaultType(ft)"
        >
          <div class="fault-icon">{{ getFaultIcon(ft.type) }}</div>
          <div class="fault-name">{{ ft.name }}</div>
          <div class="fault-risk" :class="'risk-' + ft.risk_level">{{ ft.risk_level }}</div>
          <div class="fault-category">{{ ft.category }}</div>
        </div>
      </div>
      <div v-if="!faultTypes.length" class="empty-state">
        暂无可用的故障类型
      </div>
    </div>

    <!-- 韧性评分 -->
    <div v-if="currentTab === 'resilience'" class="tab-content">
      <div v-if="!resilienceScore" class="empty-state">
        暂无韧性评分数据，<button @click="showEvaluateDialog = true" class="link-btn">发起评估</button>
      </div>
      <div v-else class="resilience-container">
        <div class="score-overview">
          <div class="score-circle">
            <svg viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="45" fill="none" stroke="var(--bg-tertiary)" stroke-width="8"/>
              <circle
                cx="50" cy="50" r="45" fill="none"
                :stroke="getScoreColor(resilienceScore.score)"
                stroke-width="8"
                stroke-linecap="round"
                :stroke-dasharray="`${resilienceScore.score * 2.83} 283`"
                transform="rotate(-90 50 50)"
              />
            </svg>
            <div class="score-value">{{ resilienceScore.score }}</div>
          </div>
          <div class="score-label">韧性评分</div>
        </div>

        <div class="metrics-radar">
          <h3>各项指标</h3>
          <div class="metrics-grid">
            <div v-for="(value, key) in resilienceScore.metrics" :key="key" class="metric-item">
              <div class="metric-header">
                <span class="metric-name">{{ getMetricName(key) }}</span>
                <span class="metric-value">{{ value }}</span>
              </div>
              <div class="metric-bar">
                <div class="metric-fill" :style="{ width: value + '%' }"></div>
              </div>
            </div>
          </div>
        </div>

        <div class="weaknesses-section" v-if="resilienceScore.weaknesses?.length">
          <h3>⚠️ 发现的弱点</h3>
          <ul class="weaknesses-list">
            <li v-for="(w, idx) in resilienceScore.weaknesses" :key="idx">{{ w }}</li>
          </ul>
        </div>

        <div class="recommendations-section" v-if="resilienceScore.recommendations?.length">
          <h3>💡 改进建议</h3>
          <ul class="recommendations-list">
            <li v-for="(r, idx) in resilienceScore.recommendations" :key="idx">{{ r }}</li>
          </ul>
        </div>
      </div>
    </div>

    <!-- 创建实验弹窗 -->
    <div v-if="showExperimentDialog" class="dialog-overlay" @click.self="showExperimentDialog = false">
      <div class="dialog experiment-dialog">
        <div class="dialog-header">
          <h2>创建混沌实验</h2>
          <button class="btn-close" @click="showExperimentDialog = false">×</button>
        </div>
        <div class="dialog-body">
          <div class="form-group">
            <label>实验名称 *</label>
            <input v-model="experimentForm.name" type="text" placeholder="如: 订单服务故障演练" />
          </div>
          <div class="form-group">
            <label>实验描述</label>
            <textarea v-model="experimentForm.description" rows="2" placeholder="描述实验目的"></textarea>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>目标类型 *</label>
              <select v-model="experimentForm.targetType">
                <option value="service">服务</option>
                <option value="pod">Pod</option>
                <option value="node">节点</option>
                <option value="network">网络</option>
              </select>
            </div>
            <div class="form-group">
              <label>目标 ID</label>
              <input v-model="experimentForm.targetId" type="text" placeholder="如: order-service" />
            </div>
          </div>
          <div class="form-group">
            <label>实验假设</label>
            <textarea v-model="experimentForm.hypothesis" rows="2" placeholder="如: 即使支付服务延迟增加 2s，订单服务仍能正常响应"></textarea>
          </div>
          <div class="form-group">
            <label>爆炸半径 (影响 Pod 数)</label>
            <input v-model.number="experimentForm.blastRadius" type="number" min="0" />
          </div>
          <div class="form-group checkbox">
            <label>
              <input type="checkbox" v-model="experimentForm.autoRollback" />
              启用自动回滚
            </label>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="btn-secondary" @click="showExperimentDialog = false">取消</button>
          <button class="btn-primary" @click="createExperiment">创建</button>
        </div>
      </div>
    </div>

    <!-- 注入故障弹窗 -->
    <div v-if="showFaultDialog" class="dialog-overlay" @click.self="showFaultDialog = false">
      <div class="dialog">
        <div class="dialog-header">
          <h2>注入故障</h2>
          <button class="btn-close" @click="showFaultDialog = false">×</button>
        </div>
        <div class="dialog-body">
          <div class="form-group">
            <label>故障类型</label>
            <select v-model="faultForm.faultType">
              <option v-for="ft in faultTypes" :key="ft.type" :value="ft.type">
                {{ ft.name }} ({{ ft.risk_level }})
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>目标服务</label>
            <input v-model="faultForm.targetService" type="text" placeholder="如: payment-service" />
          </div>
          <div class="form-group">
            <label>故障配置 (JSON)</label>
            <textarea v-model="faultForm.configJson" rows="4" placeholder='{"delay_ms": 2000, "duration": 60}'></textarea>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="btn-secondary" @click="showFaultDialog = false">取消</button>
          <button class="btn-danger" @click="injectFault">注入</button>
        </div>
      </div>
    </div>

    <!-- 韧性评估弹窗 -->
    <div v-if="showEvaluateDialog" class="dialog-overlay" @click.self="showEvaluateDialog = false">
      <div class="dialog">
        <div class="dialog-header">
          <h2>韧性评估</h2>
          <button class="btn-close" @click="showEvaluateDialog = false">×</button>
        </div>
        <div class="dialog-body">
          <div class="form-row">
            <div class="form-group">
              <label>目标类型</label>
              <select v-model="evaluateForm.targetType">
                <option value="service">服务</option>
                <option value="pod">Pod</option>
                <option value="node">节点</option>
              </select>
            </div>
            <div class="form-group">
              <label>目标 ID</label>
              <input v-model="evaluateForm.targetId" type="text" placeholder="如: order-service" />
            </div>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="btn-secondary" @click="showEvaluateDialog = false">取消</button>
          <button class="btn-primary" @click="runEvaluation">开始评估</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const API_BASE = '/api'

const currentTab = ref('experiments')
const loading = ref(false)
const showExperimentDialog = ref(false)
const showFaultDialog = ref(false)
const showEvaluateDialog = ref(false)

const experiments = ref([])
const faultTypes = ref([])
const resilienceScore = ref(null)
const latestScore = ref(null)

const stats = reactive({
  totalExperiments: 0,
  runningExperiments: 0,
  completedExperiments: 0,
})

const experimentForm = reactive({
  name: '',
  description: '',
  targetType: 'service',
  targetId: '',
  hypothesis: '',
  blastRadius: 0,
  autoRollback: true,
})

const faultForm = reactive({
  experimentId: null,
  faultType: '',
  targetService: '',
  configJson: '{"duration": 60}',
})

const evaluateForm = reactive({
  targetType: 'service',
  targetId: '',
})

async function loadExperiments() {
  loading.value = true
  try {
    const resp = await fetch(`${API_BASE}/chaos/experiments/list/1`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    if (resp.ok) {
      const data = await resp.json()
      experiments.value = data.items || []
      stats.totalExperiments = data.total
      stats.runningExperiments = experiments.value.filter(e => e.status === 'running').length
      stats.completedExperiments = experiments.value.filter(e => e.status === 'completed').length
    }
  } catch (err) {
    console.error('加载实验失败:', err)
  } finally {
    loading.value = false
  }
}

async function loadFaultTypes() {
  try {
    const resp = await fetch(`${API_BASE}/chaos/fault-types`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    if (resp.ok) {
      faultTypes.value = await resp.json()
    }
  } catch (err) {
    console.error('加载故障类型失败:', err)
  }
}

async function loadLatestScore() {
  try {
    const resp = await fetch(`${API_BASE}/chaos/score/service/order-service`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    if (resp.ok) {
      resilienceScore.value = await resp.json()
      latestScore.value = resilienceScore.value.score
    }
  } catch (err) {
    // No score yet
  }
}

async function createExperiment() {
  if (!experimentForm.name) {
    alert('请输入实验名称')
    return
  }

  try {
    const resp = await fetch(`${API_BASE}/chaos/experiments`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authStore.accessToken}`
      },
      body: JSON.stringify({
        name: experimentForm.name,
        description: experimentForm.description,
        target_type: experimentForm.targetType,
        target_id: experimentForm.targetId || null,
        hypothesis: experimentForm.hypothesis || null,
        blast_radius: experimentForm.blastRadius,
        auto_rollback: experimentForm.autoRollback,
        project_id: 1,
      })
    })
    if (resp.ok) {
      showExperimentDialog.value = false
      Object.assign(experimentForm, {
        name: '', description: '', targetType: 'service',
        targetId: '', hypothesis: '', blastRadius: 0, autoRollback: true,
      })
      loadExperiments()
    }
  } catch (err) {
    console.error('创建实验失败:', err)
  }
}

async function startExperiment(expId) {
  try {
    const resp = await fetch(`${API_BASE}/chaos/experiments/${expId}/start`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    if (resp.ok) {
      loadExperiments()
    }
  } catch (err) {
    console.error('启动实验失败:', err)
  }
}

async function stopExperiment(expId) {
  try {
    const resp = await fetch(`${API_BASE}/chaos/experiments/${expId}/stop`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    if (resp.ok) {
      loadExperiments()
    }
  } catch (err) {
    console.error('停止实验失败:', err)
  }
}

async function deleteExperiment(expId) {
  if (!confirm('确定删除此实验?')) return
  try {
    const resp = await fetch(`${API_BASE}/chaos/experiments/${expId}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    if (resp.ok) {
      loadExperiments()
    }
  } catch (err) {
    console.error('删除实验失败:', err)
  }
}

function openFaultDialog(expId) {
  faultForm.experimentId = expId
  faultForm.faultType = faultTypes.value[0]?.type || ''
  faultForm.targetService = ''
  faultForm.configJson = '{"duration": 60}'
  showFaultDialog.value = true
}

async function injectFault() {
  if (!faultForm.faultType || !faultForm.targetService) {
    alert('请填写故障类型和目标服务')
    return
  }

  let config = {}
  try {
    if (faultForm.configJson) {
      config = JSON.parse(faultForm.configJson)
    }
  } catch (e) {
    alert('故障配置 JSON 格式错误')
    return
  }

  try {
    const resp = await fetch(`${API_BASE}/chaos/faults`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authStore.accessToken}`
      },
      body: JSON.stringify({
        experiment_id: faultForm.experimentId,
        fault_type: faultForm.faultType,
        target_service: faultForm.targetService,
        fault_config: config,
      })
    })
    if (resp.ok) {
      showFaultDialog.value = false
      loadExperiments()
    }
  } catch (err) {
    console.error('注入故障失败:', err)
  }
}

async function runEvaluation() {
  if (!evaluateForm.targetId) {
    alert('请输入目标 ID')
    return
  }

  try {
    const resp = await fetch(`${API_BASE}/chaos/evaluate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authStore.accessToken}`
      },
      body: JSON.stringify({
        target_type: evaluateForm.targetType,
        target_id: evaluateForm.targetId,
        project_id: 1,
      })
    })
    if (resp.ok) {
      resilienceScore.value = await resp.json()
      latestScore.value = resilienceScore.value.score
      showEvaluateDialog.value = false
      currentTab.value = 'resilience'
    }
  } catch (err) {
    console.error('评估失败:', err)
  }
}

function viewExperiment(expId) {
  // TODO: Navigate to experiment detail
}

function selectFaultType(ft) {
  faultForm.faultType = ft.type
  showFaultDialog.value = true
}

function getFaultIcon(type) {
  const icons = {
    'cpu-stress': '🔥',
    'memory-stress': '💾',
    'network-delay': '⏳',
    'network-loss': '📦',
    'pod-kill': '💀',
    'service-down': '⬇️',
    'disk-fill': '💽',
    'dns-failure': '🌐',
  }
  return icons[type] || '⚡'
}

function getMetricName(key) {
  const names = {
    redundancy: '冗余能力',
    isolation: '故障隔离',
    observability: '可观测性',
    recovery: '恢复能力',
    fault_tolerance: '容错能力',
  }
  return names[key] || key
}

function getScoreColor(score) {
  if (score >= 80) return 'var(--success-color)'
  if (score >= 60) return '#fa8c16'
  return 'var(--error-color)'
}

onMounted(() => {
  loadExperiments()
  loadFaultTypes()
  loadLatestScore()
})
</script>

<style scoped>
.chaos-studio {
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

.stat-card.running .stat-icon {
  background: rgba(255, 166, 0, 0.1);
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

.experiment-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.experiment-card {
  background: var(--bg-panel);
  border: 1px solid var(--border-default);
  border-radius: 10px;
  padding: 16px;
}

.exp-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.exp-name {
  font-weight: 600;
  color: var(--text-primary);
}

.exp-status {
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 12px;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.status-running {
  background: rgba(255, 166, 0, 0.1);
  color: #fa8c16;
}

.status-completed {
  background: rgba(82, 196, 26, 0.1);
  color: var(--success-color);
}

.exp-desc {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.exp-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.target-tag {
  padding: 2px 8px;
  background: var(--neon-cyan);
  color: #000;
  border-radius: 4px;
  font-size: 12px;
}

.exp-hypothesis,
.exp-faults {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.exp-hypothesis .label,
.exp-faults .label {
  color: var(--text-tertiary);
}

.fault-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  margin-left: 8px;
  background: var(--bg-tertiary);
}

.fault-tag.fault-success {
  background: rgba(82, 196, 26, 0.1);
  color: var(--success-color);
}

.fault-tag.fault-running {
  background: rgba(255, 166, 0, 0.1);
  color: #fa8c16;
}

.exp-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.fault-types-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.fault-type-card {
  background: var(--bg-panel);
  border: 1px solid var(--border-default);
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.fault-type-card:hover {
  border-color: var(--neon-cyan);
  transform: translateY(-2px);
}

.fault-type-card.risk-critical {
  border-color: var(--error-color);
}

.fault-type-card.risk-high {
  border-color: #fa8c16;
}

.fault-icon {
  font-size: 36px;
  margin-bottom: 8px;
}

.fault-name {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.fault-risk {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  margin-bottom: 4px;
}

.fault-risk.risk-low {
  background: rgba(82, 196, 26, 0.1);
  color: var(--success-color);
}

.fault-risk.risk-medium {
  background: rgba(255, 166, 0, 0.1);
  color: #fa8c16;
}

.fault-risk.risk-high,
.fault-risk.risk-critical {
  background: rgba(255, 77, 79, 0.1);
  color: var(--error-color);
}

.fault-category {
  font-size: 12px;
  color: var(--text-tertiary);
}

.resilience-container {
  max-width: 800px;
}

.score-overview {
  text-align: center;
  margin-bottom: 32px;
}

.score-circle {
  position: relative;
  width: 160px;
  height: 160px;
  margin: 0 auto 16px;
}

.score-circle svg {
  width: 100%;
  height: 100%;
}

.score-circle circle {
  transition: stroke-dasharray 0.5s ease;
}

.score-value {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 48px;
  font-weight: 700;
  color: var(--text-primary);
}

.score-label {
  font-size: 18px;
  color: var(--text-secondary);
}

.metrics-radar {
  background: var(--bg-panel);
  border: 1px solid var(--border-default);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
}

.metrics-radar h3 {
  margin: 0 0 16px;
  color: var(--text-primary);
}

.metrics-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.metric-item {
  display: block;
}

.metric-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.metric-name {
  font-size: 14px;
  color: var(--text-secondary);
}

.metric-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.metric-bar {
  height: 8px;
  background: var(--bg-tertiary);
  border-radius: 4px;
  overflow: hidden;
}

.metric-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--neon-cyan), var(--neon-magenta));
  border-radius: 4px;
  transition: width 0.3s ease;
}

.weaknesses-section,
.recommendations-section {
  background: var(--bg-panel);
  border: 1px solid var(--border-default);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
}

.weaknesses-section h3 {
  margin: 0 0 12px;
  color: #fa8c16;
}

.recommendations-section h3 {
  margin: 0 0 12px;
  color: var(--neon-cyan);
}

.weaknesses-list,
.recommendations-list {
  margin: 0;
  padding-left: 20px;
  color: var(--text-secondary);
}

.weaknesses-list li,
.recommendations-list li {
  margin-bottom: 8px;
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

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
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
.btn-primary,
.btn-danger {
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

.btn-danger {
  background: var(--error-color);
  border: none;
  color: #fff;
}

.loading {
  text-align: center;
  padding: 60px;
  color: var(--text-tertiary);
}
</style>
