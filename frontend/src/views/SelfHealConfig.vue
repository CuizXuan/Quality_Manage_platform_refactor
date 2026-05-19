<template>
  <div class="self-heal-config">
    <div class="page-header">
      <h1 class="page-title">测试自愈配置</h1>
      <div class="header-actions">
        <button class="btn-secondary" @click="showRuleDialog = true">
          + 创建规则
        </button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">🔧</div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.totalHeals }}</span>
          <span class="stat-label">自愈总数</span>
        </div>
      </div>
      <div class="stat-card success">
        <div class="stat-icon">✓</div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.successRate }}%</span>
          <span class="stat-label">自愈成功率</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">⏱</div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.pendingApprovals }}</span>
          <span class="stat-label">待审批</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📋</div>
        <div class="stat-info">
          <span class="stat-value">{{ rules.length }}</span>
          <span class="stat-label">活跃规则</span>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="tabs">
      <button :class="{ active: currentTab === 'history' }" @click="currentTab = 'history'">
        自愈历史
      </button>
      <button :class="{ active: currentTab === 'rules' }" @click="currentTab = 'rules'">
        智能规则
      </button>
      <button :class="{ active: currentTab === 'pending' }" @click="currentTab = 'pending'">
        待审批 ({{ pendingItems.length }})
      </button>
    </div>

    <!-- 自愈历史 -->
    <div v-if="currentTab === 'history'" class="tab-content">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="!healHistory.length" class="empty-state">
        暂无自愈记录
      </div>
      <div v-else class="history-list">
        <div v-for="item in healHistory" :key="item.id" class="history-item">
          <div class="history-header">
            <span class="heal-action" :class="'action-' + item.heal_action">
              {{ item.heal_action_name }}
            </span>
            <span class="confidence" :class="{ high: item.confidence >= 0.8 }">
              置信度: {{ (item.confidence * 100).toFixed(0) }}%
            </span>
          </div>
          <div class="heal-reasoning">{{ item.ai_reasoning }}</div>
          <div class="history-footer">
            <span class="heal-status" :class="{ success: item.heal_success }">
              {{ item.heal_success ? '自愈成功' : '自愈失败' }}
            </span>
            <span v-if="item.human_approved" class="approved-badge">已审批</span>
            <span class="heal-time">{{ formatTime(item.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 智能规则 -->
    <div v-if="currentTab === 'rules'" class="tab-content">
      <div v-if="!rules.length" class="empty-state">
        暂无自愈规则，<button @click="showRuleDialog = true" class="link-btn">创建第一条规则</button>
      </div>
      <div v-else class="rules-list">
        <div v-for="rule in rules" :key="rule.id" class="rule-card">
          <div class="rule-header">
            <span class="rule-name">{{ rule.name }}</span>
            <span class="rule-priority" :style="{ background: getPriorityColor(rule.priority) }">
              P{{ rule.priority }}
            </span>
          </div>
          <div v-if="rule.description" class="rule-desc">{{ rule.description }}</div>
          <div class="rule-condition">
            <span class="label">触发条件:</span>
            <code>{{ JSON.stringify(rule.condition) }}</code>
          </div>
          <div class="rule-action">
            <span class="label">执行动作:</span>
            <code>{{ JSON.stringify(rule.action) }}</code>
          </div>
          <div class="rule-stats">
            <span>使用 {{ rule.usage_count }} 次</span>
            <span v-if="rule.success_rate">成功率 {{ (rule.success_rate * 100).toFixed(0) }}%</span>
          </div>
          <div class="rule-actions">
            <button class="btn-sm" @click="toggleRule(rule)">
              {{ rule.enabled ? '禁用' : '启用' }}
            </button>
            <button class="btn-sm" @click="editRule(rule)">编辑</button>
            <button class="btn-sm danger" @click="deleteRule(rule.id)">删除</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 待审批 -->
    <div v-if="currentTab === 'pending'" class="tab-content">
      <div v-if="!pendingItems.length" class="empty-state">
        暂无待审批项
      </div>
      <div v-else class="pending-list">
        <div v-for="item in pendingItems" :key="item.id" class="pending-item">
          <div class="pending-header">
            <span class="pending-type">{{ item.heal_action_name }}</span>
            <span class="pending-time">{{ formatTime(item.created_at) }}</span>
          </div>
          <div class="pending-reasoning">{{ item.ai_reasoning }}</div>
          <div class="pending-changes" v-if="item.changes">
            <div class="change-label">变更内容:</div>
            <pre>{{ JSON.stringify(item.changes, null, 2) }}</pre>
          </div>
          <div class="pending-actions">
            <button class="btn-approve" @click="approveHeal(item.id, true)">批准</button>
            <button class="btn-reject" @click="approveHeal(item.id, false)">拒绝</button>
            <button class="btn-rollback" @click="rollbackHeal(item.id)">回滚</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建规则弹窗 -->
    <div v-if="showRuleDialog" class="dialog-overlay" @click.self="closeRuleDialog">
      <div class="dialog rule-dialog">
        <div class="dialog-header">
          <h2>{{ editingRule ? '编辑规则' : '创建自愈规则' }}</h2>
          <button class="btn-close" @click="closeRuleDialog">×</button>
        </div>

        <div class="dialog-body">
          <div class="form-group">
            <label>规则名称</label>
            <input v-model="ruleForm.name" type="text" placeholder="输入规则名称" />
          </div>

          <div class="form-group">
            <label>规则描述</label>
            <textarea v-model="ruleForm.description" placeholder="可选描述" rows="2"></textarea>
          </div>

          <div class="form-group">
            <label>优先级 (0-100)</label>
            <input v-model.number="ruleForm.priority" type="number" min="0" max="100" />
          </div>

          <div class="form-group">
            <label>触发条件</label>
            <select v-model="ruleForm.conditionType" @change="updateConditionTemplate">
              <option value="">选择模板</option>
              <option value="failure_type_is">失败类型匹配</option>
              <option value="response_status_is">响应状态码匹配</option>
              <option value="error_contains">错误关键字匹配</option>
            </select>
            <div v-if="ruleForm.conditionType === 'failure_type_is'" class="sub-field">
              <label>失败类型</label>
              <select v-model="ruleForm.failureTypes" multiple>
                <option value="locator_not_found">元素定位失败</option>
                <option value="assertion_error">断言错误</option>
                <option value="timeout">超时</option>
                <option value="network_error">网络错误</option>
                <option value="auth_expired">认证过期</option>
              </select>
            </div>
            <div v-if="ruleForm.conditionType === 'response_status_is'" class="sub-field">
              <label>状态码</label>
              <input v-model="ruleForm.statusCodes" type="text" placeholder="400,401,500" />
            </div>
          </div>

          <div class="form-group">
            <label>执行动作</label>
            <select v-model="ruleForm.actionType" @change="updateActionTemplate">
              <option value="">选择动作</option>
              <option value="update_locator">更新元素定位器</option>
              <option value="update_assertion">更新断言值</option>
              <option value="add_wait">增加等待时间</option>
              <option value="retry_with_backoff">重试并退避</option>
              <option value="skip_step">跳过失败步骤</option>
            </select>
          </div>

          <div class="form-preview">
            <label>规则预览</label>
            <pre>{{ JSON.stringify(ruleForm, null, 2) }}</pre>
          </div>
        </div>

        <div class="dialog-footer">
          <button class="btn-secondary" @click="closeRuleDialog">取消</button>
          <button class="btn-primary" @click="saveRule">{{ editingRule ? '保存' : '创建' }}</button>
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

const currentTab = ref('history')
const loading = ref(false)
const showRuleDialog = ref(false)
const editingRule = ref(null)

const healHistory = ref([])
const rules = ref([])
const pendingItems = ref([])

const stats = reactive({
  totalHeals: 0,
  successRate: 0,
  pendingApprovals: 0,
  totalRules: 0,
})

const ruleForm = reactive({
  name: '',
  description: '',
  priority: 0,
  conditionType: '',
  failureTypes: [],
  statusCodes: '',
  actionType: '',
})

function updateConditionTemplate() {
  // 根据选择的模板更新 condition
}

function updateActionTemplate() {
  // 根据选择更新 action
}

async function loadHistory() {
  loading.value = true
  try {
    const resp = await fetch(`${API_BASE}/ai-gen/self-heal/history/1`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    if (resp.ok) {
      const data = await resp.json()
      healHistory.value = data.items || []
      stats.totalHeals = data.total
      stats.successRate = (data.success_rate || 0) * 100
      pendingItems.value = healHistory.value.filter(h => !h.human_approved && h.heal_success)
      stats.pendingApprovals = pendingItems.value.length
    }
  } catch (err) {
    console.error('加载历史失败:', err)
  } finally {
    loading.value = false
  }
}

async function loadRules() {
  try {
    const resp = await fetch(`${API_BASE}/ai-gen/orch-rules/1`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    if (resp.ok) {
      const data = await resp.json()
      rules.value = data.items || []
      stats.totalRules = data.total
    }
  } catch (err) {
    console.error('加载规则失败:', err)
  }
}

async function saveRule() {
  if (!ruleForm.name || !ruleForm.actionType) {
    alert('请填写必填项')
    return
  }

  const condition = {}
  if (ruleForm.conditionType === 'failure_type_is') {
    condition.type = 'failure_types'
    condition.failure_types = ruleForm.failureTypes
  } else if (ruleForm.conditionType === 'response_status_is') {
    condition.type = 'response_status'
    condition.values = ruleForm.statusCodes.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n))
  }

  const action = { type: ruleForm.actionType }

  try {
    const resp = await fetch(`${API_BASE}/ai-gen/orch-rules`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authStore.accessToken}`
      },
      body: JSON.stringify({
        name: ruleForm.name,
        description: ruleForm.description,
        condition,
        action,
        priority: ruleForm.priority,
        project_id: 1
      })
    })
    if (resp.ok) {
      closeRuleDialog()
      loadRules()
    }
  } catch (err) {
    console.error('保存规则失败:', err)
  }
}

async function toggleRule(rule) {
  try {
    const resp = await fetch(`${API_BASE}/ai-gen/orch-rules/${rule.id}/toggle`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    if (resp.ok) {
      loadRules()
    }
  } catch (err) {
    console.error('切换规则失败:', err)
  }
}

function editRule(rule) {
  editingRule.value = rule
  ruleForm.name = rule.name
  ruleForm.description = rule.description || ''
  ruleForm.priority = rule.priority
  try {
    const cond = typeof rule.condition === 'string' ? JSON.parse(rule.condition) : rule.condition
    const act = typeof rule.action === 'string' ? JSON.parse(rule.action) : rule.action
    ruleForm.conditionType = cond.type || ''
    ruleForm.actionType = act.type || ''
  } catch (e) {}
  showRuleDialog.value = true
}

async function deleteRule(ruleId) {
  if (!confirm('确定删除此规则?')) return
  try {
    const resp = await fetch(`${API_BASE}/ai-gen/orch-rules/${ruleId}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    if (resp.ok) {
      loadRules()
    }
  } catch (err) {
    console.error('删除规则失败:', err)
  }
}

async function approveHeal(healId, approved) {
  try {
    const resp = await fetch(`${API_BASE}/ai-gen/self-heal/${healId}/approve?approved=${approved}`, {
      method: 'PUT',
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    if (resp.ok) {
      loadHistory()
    }
  } catch (err) {
    console.error('审批失败:', err)
  }
}

async function rollbackHeal(healId) {
  if (!confirm('确定回滚此自愈?')) return
  try {
    const resp = await fetch(`${API_BASE}/ai-gen/self-heal/${healId}/rollback`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    if (resp.ok) {
      loadHistory()
    }
  } catch (err) {
    console.error('回滚失败:', err)
  }
}

function closeRuleDialog() {
  showRuleDialog.value = false
  editingRule.value = null
  ruleForm.name = ''
  ruleForm.description = ''
  ruleForm.priority = 0
  ruleForm.conditionType = ''
  ruleForm.failureTypes = []
  ruleForm.statusCodes = ''
  ruleForm.actionType = ''
}

function getPriorityColor(priority) {
  if (priority >= 80) return '#f5222d'
  if (priority >= 50) return '#fa8c16'
  return '#52c41a'
}

function formatTime(timeStr) {
  if (!timeStr) return ''
  return new Date(timeStr).toLocaleString('zh-CN')
}

onMounted(() => {
  loadHistory()
  loadRules()
})
</script>

<style scoped>
.self-heal-config {
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

.stat-card.success .stat-icon {
  background: rgba(82, 196, 26, 0.1);
  color: var(--success-color);
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

.history-list,
.rules-list,
.pending-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-item,
.rule-card,
.pending-item {
  background: var(--bg-panel);
  border: 1px solid var(--border-default);
  border-radius: 10px;
  padding: 16px;
}

.history-header,
.pending-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.heal-action,
.pending-type {
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  background: var(--bg-tertiary);
  color: var(--neon-cyan);
}

.confidence {
  font-size: 13px;
  color: var(--text-tertiary);
}

.confidence.high {
  color: var(--success-color);
}

.heal-reasoning,
.pending-reasoning {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 8px 0;
  line-height: 1.5;
}

.history-footer,
.pending-footer {
  display: flex;
  gap: 12px;
  align-items: center;
  font-size: 12px;
  color: var(--text-tertiary);
}

.heal-status.success {
  color: var(--success-color);
}

.approved-badge {
  padding: 2px 8px;
  background: var(--success-bg);
  color: var(--success-color);
  border-radius: 10px;
}

.rule-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.rule-name {
  font-weight: 600;
  color: var(--text-primary);
}

.rule-priority {
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  color: #fff;
}

.rule-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.rule-condition,
.rule-action {
  margin: 8px 0;
}

.rule-condition .label,
.rule-action .label {
  font-size: 12px;
  color: var(--text-tertiary);
  display: block;
  margin-bottom: 4px;
}

.rule-condition code,
.rule-action code,
.form-preview pre {
  display: block;
  padding: 8px;
  background: var(--bg-secondary);
  border-radius: 6px;
  font-size: 12px;
  color: var(--neon-cyan);
  overflow-x: auto;
}

.rule-stats {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--text-tertiary);
  margin: 12px 0;
}

.rule-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.btn-sm {
  padding: 4px 12px;
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

.btn-sm.danger:hover {
  border-color: var(--error-color);
  color: var(--error-color);
}

.pending-changes {
  margin: 12px 0;
}

.change-label {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-bottom: 4px;
}

.pending-changes pre {
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: 6px;
  font-size: 12px;
  overflow-x: auto;
}

.pending-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.btn-approve,
.btn-reject,
.btn-rollback {
  padding: 6px 16px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
}

.btn-approve {
  background: var(--success-color);
  color: #fff;
}

.btn-reject {
  background: var(--error-color);
  color: #fff;
}

.btn-rollback {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
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
  width: 600px;
  max-width: 90%;
  max-height: 80vh;
  overflow-y: auto;
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

.sub-field {
  margin-top: 8px;
  padding-left: 12px;
  border-left: 2px solid var(--border-default);
}

.form-preview {
  margin-top: 16px;
}

.form-preview label {
  font-size: 12px;
  color: var(--text-tertiary);
  display: block;
  margin-bottom: 4px;
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
