<template>
  <div class="test-data-page">
    <div class="page-header">
      <h1 class="page-title">测试数据工厂</h1>
      <div class="header-actions">
        <button class="btn-primary" @click="showTemplateDialog = true">
          + 新建模板
        </button>
        <button class="btn-secondary" @click="showMaskRuleDialog = true">
          + 新建脱敏规则
        </button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">📝</div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.templates }}</span>
          <span class="stat-label">数据模板</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🔒</div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.maskRules }}</span>
          <span class="stat-label">脱敏规则</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📸</div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.snapshots }}</span>
          <span class="stat-label">数据快照</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🔄</div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.cloneTasks }}</span>
          <span class="stat-label">克隆任务</span>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="tabs">
      <button :class="{ active: currentTab === 'templates' }" @click="currentTab = 'templates'">
        📝 数据模板
      </button>
      <button :class="{ active: currentTab === 'generate' }" @click="currentTab = 'generate'">
        ⚡ 数据生成
      </button>
      <button :class="{ active: currentTab === 'mask-rules' }" @click="currentTab = 'mask-rules'">
        🔒 脱敏规则
      </button>
      <button :class="{ active: currentTab === 'clone' }" @click="currentTab = 'clone'">
        🔄 数据克隆
      </button>
      <button :class="{ active: currentTab === 'snapshots' }" @click="currentTab = 'snapshots'">
        📸 数据快照
      </button>
    </div>

    <!-- 数据模板 -->
    <div v-if="currentTab === 'templates'" class="tab-content">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="!templates.length" class="empty-state">
        暂无数据模板，<button @click="showTemplateDialog = true" class="link-btn">创建第一个模板</button>
      </div>
      <div v-else class="template-list">
        <div v-for="tpl in templates" :key="tpl.id" class="template-card">
          <div class="tpl-header">
            <span class="tpl-name">{{ tpl.name }}</span>
            <span class="tpl-type">{{ tpl.template_type_name }}</span>
          </div>
          <div class="tpl-schema">
            <span class="label">字段:</span>
            <code>{{ Object.keys(tpl.schema || {}).join(', ') }}</code>
          </div>
          <div class="tpl-stats">
            <span>使用 {{ tpl.usage_count }} 次</span>
          </div>
          <div class="tpl-actions">
            <button class="btn-sm" @click="previewTemplate(tpl.id)">预览</button>
            <button class="btn-sm primary" @click="selectTemplate(tpl)">生成数据</button>
            <button class="btn-sm danger" @click="deleteTemplate(tpl.id)">删除</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 数据生成 -->
    <div v-if="currentTab === 'generate'" class="tab-content">
      <div class="generate-form">
        <div class="form-group">
          <label>选择模板</label>
          <select v-model="generateForm.templateId">
            <option value="">-- 选择模板 --</option>
            <option v-for="tpl in templates" :key="tpl.id" :value="tpl.id">
              {{ tpl.name }} ({{ tpl.template_type_name }})
            </option>
          </select>
        </div>
        <div class="form-group">
          <label>生成数量</label>
          <input v-model.number="generateForm.count" type="number" min="1" max="1000" />
        </div>
        <div class="form-group">
          <label>唯一字段 (逗号分隔)</label>
          <input v-model="generateForm.uniqueFields" type="text" placeholder="如: email, phone" />
        </div>
        <button class="btn-primary" @click="generateData" :disabled="!generateForm.templateId || generating">
          {{ generating ? '生成中...' : '生成数据' }}
        </button>
      </div>

      <div v-if="generatedData.length" class="generated-result">
        <div class="result-header">
          <span>生成 {{ generatedData.length }} 条数据</span>
          <button class="btn-sm" @click="exportData">导出 JSON</button>
        </div>
        <div class="result-preview">
          <pre>{{ JSON.stringify(generatedData.slice(0, 5), null, 2) }}</pre>
          <div v-if="generatedData.length > 5" class="more-hint">
            还有 {{ generatedData.length - 5 }} 条数据...
          </div>
        </div>
      </div>
    </div>

    <!-- 脱敏规则 -->
    <div v-if="currentTab === 'mask-rules'" class="tab-content">
      <div v-if="!maskRules.length" class="empty-state">
        暂无脱敏规则，<button @click="showMaskRuleDialog = true" class="link-btn">创建第一条规则</button>
      </div>
      <div v-else class="mask-rules-list">
        <div v-for="rule in maskRules" :key="rule.id" class="mask-rule-card">
          <div class="rule-header">
            <span class="rule-name">{{ rule.name }}</span>
            <span class="rule-type">{{ rule.mask_type_name }}</span>
            <span class="rule-status" :class="{ enabled: rule.enabled }">
              {{ rule.enabled ? '已启用' : '已禁用' }}
            </span>
          </div>
          <div class="rule-pattern">
            <span class="label">字段匹配:</span>
            <code>{{ rule.field_pattern }}</code>
          </div>
          <div class="rule-actions">
            <button class="btn-sm" @click="toggleMaskRule(rule)">
              {{ rule.enabled ? '禁用' : '启用' }}
            </button>
            <button class="btn-sm danger" @click="deleteMaskRule(rule.id)">删除</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 数据克隆 -->
    <div v-if="currentTab === 'clone'" class="tab-content">
      <div class="clone-form">
        <div class="form-group">
          <label>任务名称</label>
          <input v-model="cloneForm.name" type="text" placeholder="输入任务名称" />
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>源环境</label>
            <select v-model="cloneForm.sourceEnvId">
              <option value="">-- 选择环境 --</option>
              <option v-for="env in environments" :key="env.id" :value="env.id">
                {{ env.name }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>目标环境</label>
            <select v-model="cloneForm.targetEnvId">
              <option value="">-- 选择环境 --</option>
              <option v-for="env in environments" :key="env.id" :value="env.id">
                {{ env.name }}
              </option>
            </select>
          </div>
        </div>
        <div class="form-group">
          <label>克隆类型</label>
          <select v-model="cloneForm.cloneType">
            <option value="full">全量克隆</option>
            <option value="partial">部分克隆</option>
            <option value="mask">脱敏克隆</option>
          </select>
        </div>
        <button class="btn-primary" @click="createCloneTask">
          创建克隆任务
        </button>
      </div>

      <div v-if="cloneTasks.length" class="clone-tasks-list">
        <h3>最近任务</h3>
        <div v-for="task in cloneTasks.slice(0, 5)" :key="task.id" class="clone-task-item">
          <div class="task-info">
            <span class="task-name">{{ task.name }}</span>
            <span class="task-status" :class="'status-' + task.status">{{ task.status }}</span>
          </div>
          <div class="task-meta">
            <span>{{ task.clone_type_name }}</span>
            <span v-if="task.progress">进度: {{ task.progress }}%</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 数据快照 -->
    <div v-if="currentTab === 'snapshots'" class="tab-content">
      <div class="snapshot-actions">
        <button class="btn-secondary" @click="showSnapshotDialog = true">创建快照</button>
      </div>
      <div v-if="!snapshots.length" class="empty-state">暂无数据快照</div>
      <div v-else class="snapshot-list">
        <div v-for="snap in snapshots" :key="snap.id" class="snapshot-card">
          <div class="snap-header">
            <span class="snap-name">{{ snap.name }}</span>
            <span class="snap-source">{{ snap.source_type }}</span>
          </div>
          <div class="snap-meta">
            <span>{{ snap.record_count }} 条记录</span>
            <span>{{ formatSize(snap.size_bytes) }}</span>
            <span v-if="snap.expires_at" class="expires">过期: {{ formatTime(snap.expires_at) }}</span>
          </div>
          <div class="snap-actions">
            <button class="btn-sm" @click="restoreSnapshot(snap.id)">恢复</button>
            <button class="btn-sm danger" @click="deleteSnapshot(snap.id)">删除</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建模板弹窗 -->
    <div v-if="showTemplateDialog" class="dialog-overlay" @click.self="closeTemplateDialog">
      <div class="dialog">
        <div class="dialog-header">
          <h2>创建数据模板</h2>
          <button class="btn-close" @click="closeTemplateDialog">×</button>
        </div>
        <div class="dialog-body">
          <div class="form-group">
            <label>模板名称</label>
            <input v-model="templateForm.name" type="text" placeholder="如: 用户数据模板" />
          </div>
          <div class="form-group">
            <label>模板类型</label>
            <select v-model="templateForm.templateType">
              <option value="user">用户</option>
              <option value="order">订单</option>
              <option value="product">商品</option>
              <option value="card">卡片</option>
            </select>
          </div>
          <div class="form-group">
            <label>数据字段 (JSON)</label>
            <textarea v-model="templateForm.schemaJson" rows="6" placeholder='{"name": "name", "email": "email", "phone": "phone"}'></textarea>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="btn-secondary" @click="closeTemplateDialog">取消</button>
          <button class="btn-primary" @click="createTemplate">创建</button>
        </div>
      </div>
    </div>

    <!-- 创建脱敏规则弹窗 -->
    <div v-if="showMaskRuleDialog" class="dialog-overlay" @click.self="closeMaskRuleDialog">
      <div class="dialog">
        <div class="dialog-header">
          <h2>创建脱敏规则</h2>
          <button class="btn-close" @click="closeMaskRuleDialog">×</button>
        </div>
        <div class="dialog-body">
          <div class="form-group">
            <label>规则名称</label>
            <input v-model="maskRuleForm.name" type="text" placeholder="如: 手机号脱敏" />
          </div>
          <div class="form-group">
            <label>字段匹配模式</label>
            <input v-model="maskRuleForm.fieldPattern" type="text" placeholder="如: $.phone 或 mobile" />
          </div>
          <div class="form-group">
            <label>脱敏类型</label>
            <select v-model="maskRuleForm.maskType">
              <option value="phone">手机号</option>
              <option value="email">邮箱</option>
              <option value="id_card">身份证</option>
              <option value="bank_card">银行卡</option>
              <option value="password">密码</option>
              <option value="token">Token</option>
              <option value="custom">自定义</option>
            </select>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="btn-secondary" @click="closeMaskRuleDialog">取消</button>
          <button class="btn-primary" @click="createMaskRule">创建</button>
        </div>
      </div>
    </div>

    <!-- 创建快照弹窗 -->
    <div v-if="showSnapshotDialog" class="dialog-overlay" @click.self="closeSnapshotDialog">
      <div class="dialog">
        <div class="dialog-header">
          <h2>创建数据快照</h2>
          <button class="btn-close" @click="closeSnapshotDialog">×</button>
        </div>
        <div class="dialog-body">
          <div class="form-group">
            <label>快照名称</label>
            <input v-model="snapshotForm.name" type="text" placeholder="输入快照名称" />
          </div>
          <div class="form-group">
            <label>数据来源</label>
            <select v-model="snapshotForm.sourceType">
              <option value="database">数据库</option>
              <option value="table">数据表</option>
              <option value="api">API</option>
            </select>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="btn-secondary" @click="closeSnapshotDialog">取消</button>
          <button class="btn-primary" @click="createSnapshot">创建</button>
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

const currentTab = ref('templates')
const loading = ref(false)
const generating = ref(false)
const showTemplateDialog = ref(false)
const showMaskRuleDialog = ref(false)
const showSnapshotDialog = ref(false)

const templates = ref([])
const maskRules = ref([])
const snapshots = ref([])
const cloneTasks = ref([])
const environments = ref([])
const generatedData = ref([])

const stats = reactive({
  templates: 0,
  maskRules: 0,
  snapshots: 0,
  cloneTasks: 0,
})

const generateForm = reactive({
  templateId: '',
  count: 10,
  uniqueFields: '',
})

const templateForm = reactive({
  name: '',
  templateType: 'user',
  schemaJson: '{"name": "name", "email": "email", "phone": "phone"}',
})

const maskRuleForm = reactive({
  name: '',
  fieldPattern: '',
  maskType: 'phone',
})

const cloneForm = reactive({
  name: '',
  sourceEnvId: '',
  targetEnvId: '',
  cloneType: 'full',
})

const snapshotForm = reactive({
  name: '',
  sourceType: 'database',
})

async function loadTemplates() {
  loading.value = true
  try {
    const resp = await fetch(`${API_BASE}/test-data/templates?project_id=1`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    if (resp.ok) {
      templates.value = await resp.json()
      stats.templates = templates.value.length
    }
  } catch (err) {
    console.error('加载模板失败:', err)
  } finally {
    loading.value = false
  }
}

async function loadMaskRules() {
  try {
    const resp = await fetch(`${API_BASE}/test-data/mask-rules?project_id=1`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    if (resp.ok) {
      maskRules.value = await resp.json()
      stats.maskRules = maskRules.value.length
    }
  } catch (err) {
    console.error('加载脱敏规则失败:', err)
  }
}

async function loadSnapshots() {
  try {
    const resp = await fetch(`${API_BASE}/test-data/snapshots?project_id=1`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    if (resp.ok) {
      snapshots.value = await resp.json()
      stats.snapshots = snapshots.value.length
    }
  } catch (err) {
    console.error('加载快照失败:', err)
  }
}

async function loadCloneTasks() {
  try {
    const resp = await fetch(`${API_BASE}/test-data/clone-tasks?project_id=1`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    if (resp.ok) {
      const data = await resp.json()
      cloneTasks.value = data.items || []
      stats.cloneTasks = data.total
    }
  } catch (err) {
    console.error('加载克隆任务失败:', err)
  }
}

async function loadEnvironments() {
  try {
    const resp = await fetch(`${API_BASE}/environments`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    if (resp.ok) {
      environments.value = await resp.json()
    }
  } catch (err) {
    console.error('加载环境失败:', err)
  }
}

async function createTemplate() {
  if (!templateForm.name) {
    alert('请输入模板名称')
    return
  }

  let schema = {}
  try {
    schema = JSON.parse(templateForm.schemaJson)
  } catch (e) {
    alert('数据字段 JSON 格式错误')
    return
  }

  try {
    const resp = await fetch(`${API_BASE}/test-data/templates`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authStore.accessToken}`
      },
      body: JSON.stringify({
        name: templateForm.name,
        template_type: templateForm.templateType,
        project_id: 1,
        schema,
      })
    })
    if (resp.ok) {
      closeTemplateDialog()
      loadTemplates()
    }
  } catch (err) {
    console.error('创建模板失败:', err)
  }
}

function closeTemplateDialog() {
  showTemplateDialog.value = false
  templateForm.name = ''
  templateForm.schemaJson = '{"name": "name", "email": "email", "phone": "phone"}'
}

async function previewTemplate(templateId) {
  try {
    const resp = await fetch(`${API_BASE}/test-data/templates/${templateId}/preview`, {
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    if (resp.ok) {
      const data = await resp.json()
      alert('预览:\n' + JSON.stringify(data.preview, null, 2))
    }
  } catch (err) {
    console.error('预览失败:', err)
  }
}

function selectTemplate(tpl) {
  generateForm.templateId = tpl.id
  currentTab.value = 'generate'
}

async function generateData() {
  if (!generateForm.templateId) return

  generating.value = true
  try {
    const uniqueFields = generateForm.uniqueFields
      ? generateForm.uniqueFields.split(',').map(s => s.trim())
      : []

    const resp = await fetch(`${API_BASE}/test-data/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authStore.accessToken}`
      },
      body: JSON.stringify({
        template_id: generateForm.templateId,
        count: generateForm.count,
        unique_fields: uniqueFields,
      })
    })
    if (resp.ok) {
      const data = await resp.json()
      generatedData.value = data.data || []
    }
  } catch (err) {
    console.error('生成失败:', err)
  } finally {
    generating.value = false
  }
}

function exportData() {
  const blob = new Blob([JSON.stringify(generatedData.value, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'generated_data.json'
  a.click()
  URL.revokeObjectURL(url)
}

async function deleteTemplate(templateId) {
  if (!confirm('确定删除此模板?')) return
  try {
    const resp = await fetch(`${API_BASE}/test-data/templates/${templateId}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    if (resp.ok) {
      loadTemplates()
    }
  } catch (err) {
    console.error('删除失败:', err)
  }
}

async function createMaskRule() {
  if (!maskRuleForm.name || !maskRuleForm.fieldPattern) {
    alert('请填写完整信息')
    return
  }

  try {
    const resp = await fetch(`${API_BASE}/test-data/mask-rules`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authStore.accessToken}`
      },
      body: JSON.stringify({
        name: maskRuleForm.name,
        field_pattern: maskRuleForm.fieldPattern,
        mask_type: maskRuleForm.maskType,
        project_id: 1,
      })
    })
    if (resp.ok) {
      closeMaskRuleDialog()
      loadMaskRules()
    }
  } catch (err) {
    console.error('创建规则失败:', err)
  }
}

function closeMaskRuleDialog() {
  showMaskRuleDialog.value = false
  maskRuleForm.name = ''
  maskRuleForm.fieldPattern = ''
  maskRuleForm.maskType = 'phone'
}

async function toggleMaskRule(rule) {
  try {
    const resp = await fetch(`${API_BASE}/test-data/mask-rules/${rule.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authStore.accessToken}`
      },
      body: JSON.stringify({ enabled: !rule.enabled })
    })
    if (resp.ok) {
      loadMaskRules()
    }
  } catch (err) {
    console.error('切换规则状态失败:', err)
  }
}

async function deleteMaskRule(ruleId) {
  if (!confirm('确定删除此规则?')) return
  try {
    const resp = await fetch(`${API_BASE}/test-data/mask-rules/${ruleId}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    if (resp.ok) {
      loadMaskRules()
    }
  } catch (err) {
    console.error('删除失败:', err)
  }
}

async function createCloneTask() {
  if (!cloneForm.name) {
    alert('请输入任务名称')
    return
  }

  try {
    const resp = await fetch(`${API_BASE}/test-data/clone-tasks`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authStore.accessToken}`
      },
      body: JSON.stringify({
        name: cloneForm.name,
        source_env_id: cloneForm.sourceEnvId || 1,
        target_env_id: cloneForm.targetEnvId || 1,
        project_id: 1,
        clone_type: cloneForm.cloneType,
      })
    })
    if (resp.ok) {
      const data = await resp.json()
      // 自动启动任务
      await fetch(`${API_BASE}/test-data/clone-tasks/${data.task_id}/start`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${authStore.accessToken}` }
      })
      loadCloneTasks()
    }
  } catch (err) {
    console.error('创建任务失败:', err)
  }
}

async function createSnapshot() {
  if (!snapshotForm.name) {
    alert('请输入快照名称')
    return
  }

  try {
    const resp = await fetch(`${API_BASE}/test-data/snapshots`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authStore.accessToken}`
      },
      body: JSON.stringify({
        name: snapshotForm.name,
        source_type: snapshotForm.sourceType,
        project_id: 1,
      })
    })
    if (resp.ok) {
      closeSnapshotDialog()
      loadSnapshots()
    }
  } catch (err) {
    console.error('创建快照失败:', err)
  }
}

function closeSnapshotDialog() {
  showSnapshotDialog.value = false
  snapshotForm.name = ''
  snapshotForm.sourceType = 'database'
}

async function restoreSnapshot(snapshotId) {
  if (!confirm('确定恢复此快照?')) return
  try {
    const resp = await fetch(`${API_BASE}/test-data/snapshots/${snapshotId}/restore`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    if (resp.ok) {
      alert('快照恢复成功')
    }
  } catch (err) {
    console.error('恢复快照失败:', err)
  }
}

async function deleteSnapshot(snapshotId) {
  if (!confirm('确定删除此快照?')) return
  try {
    const resp = await fetch(`${API_BASE}/test-data/snapshots/${snapshotId}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${authStore.accessToken}` }
    })
    if (resp.ok) {
      loadSnapshots()
    }
  } catch (err) {
    console.error('删除快照失败:', err)
  }
}

function formatSize(bytes) {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function formatTime(timeStr) {
  if (!timeStr) return ''
  return new Date(timeStr).toLocaleString('zh-CN')
}

onMounted(() => {
  loadTemplates()
  loadMaskRules()
  loadSnapshots()
  loadCloneTasks()
  loadEnvironments()
})
</script>

<style scoped>
.test-data-page {
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

.template-list,
.mask-rules-list,
.clone-tasks-list,
.snapshot-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.template-card,
.mask-rule-card,
.clone-task-item,
.snapshot-card {
  background: var(--bg-panel);
  border: 1px solid var(--border-default);
  border-radius: 10px;
  padding: 16px;
}

.tpl-header,
.rule-header,
.snap-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.tpl-name,
.rule-name,
.snap-name {
  font-weight: 600;
  color: var(--text-primary);
}

.tpl-type,
.rule-type,
.snap-source {
  padding: 2px 8px;
  background: var(--neon-cyan);
  color: #000;
  border-radius: 4px;
  font-size: 12px;
}

.rule-status {
  font-size: 12px;
  color: var(--text-tertiary);
}

.rule-status.enabled {
  color: var(--success-color);
}

.tpl-schema,
.rule-pattern {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.tpl-schema .label,
.rule-pattern .label {
  color: var(--text-tertiary);
}

.tpl-schema code,
.rule-pattern code {
  background: var(--bg-secondary);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  color: var(--neon-cyan);
}

.tpl-stats,
.task-meta {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-bottom: 12px;
}

.tpl-actions,
.rule-actions,
.snap-actions {
  display: flex;
  gap: 8px;
}

.task-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.task-name {
  font-weight: 600;
  color: var(--text-primary);
}

.task-status {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  background: var(--bg-tertiary);
}

.task-status.status-completed {
  background: rgba(82, 196, 26, 0.1);
  color: var(--success-color);
}

.task-status.status-running {
  background: rgba(255, 166, 0, 0.1);
  color: #fa8c16;
}

.generate-form,
.clone-form {
  background: var(--bg-panel);
  border: 1px solid var(--border-default);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
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

.generated-result {
  background: var(--bg-panel);
  border: 1px solid var(--border-default);
  border-radius: 12px;
  padding: 20px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.result-preview pre {
  background: var(--bg-secondary);
  padding: 12px;
  border-radius: 8px;
  font-size: 12px;
  overflow-x: auto;
  max-height: 300px;
  overflow-y: auto;
}

.more-hint {
  text-align: center;
  padding: 12px;
  color: var(--text-tertiary);
  font-size: 13px;
}

.snapshot-actions {
  margin-bottom: 16px;
}

.snap-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.expires {
  color: var(--error-color);
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
