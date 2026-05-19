<template>
  <div class="model-config-page">
    <div class="page-header">
      <h1 class="page-title">AI 模型配置</h1>
      <div class="header-actions">
        <button class="btn-secondary" @click="refreshProviders">🔄 刷新</button>
        <button class="btn-primary" @click="openAddDialog">+ 添加模型</button>
      </div>
    </div>

    <!-- 提示横幅 -->
    <div class="info-banner">
      <span class="info-icon">💡</span>
      <span>配置 AI 模型供应商信息，接入后所有 AI 功能（生成用例、自愈分析、变更预测等）将使用配置的模型进行推理。</span>
    </div>

    <!-- 已有配置列表 -->
    <div class="config-list">
      <h3 class="section-title">已配置模型</h3>
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="!configs.length" class="empty-state">
        <p>暂无配置，点击上方按钮添加第一个模型</p>
      </div>
      <div v-else class="config-cards">
        <div
          v-for="cfg in configs"
          :key="cfg.id"
          class="config-card"
          :class="{ 'is-default': cfg.is_default, 'is-disabled': !cfg.enabled }"
        >
          <div class="card-header">
            <div class="card-title">
              <span class="provider-badge" :class="'provider-' + cfg.provider">
                {{ getProviderName(cfg.provider) }}
              </span>
              <strong>{{ cfg.name }}</strong>
              <span v-if="cfg.is_default" class="default-tag">默认</span>
              <span v-if="!cfg.enabled" class="disabled-tag">已禁用</span>
            </div>
            <div class="card-actions">
              <button
                class="btn-icon"
                :class="cfg.enabled ? 'warning' : 'success'"
                @click="toggleEnabled(cfg)"
                :title="cfg.enabled ? '禁用' : '启用'"
              >{{ cfg.enabled ? '⏸' : '▶' }}</button>
              <button class="btn-icon" @click="testConnection(cfg)" title="测试连接">🧪</button>
              <button class="btn-icon" @click="editConfig(cfg)" title="编辑">✏️</button>
              <button v-if="!cfg.is_default" class="btn-icon" @click="setDefault(cfg.id)" title="设为默认">⭐</button>
              <CyberConfirm
                title="确认删除该配置？"
                danger
                @confirm="deleteConfig(cfg.id)"
              >
                <template #trigger>
                  <button class="btn-icon danger" title="删除">🗑</button>
                </template>
              </CyberConfirm>
            </div>
          </div>
          <div class="card-body">
            <div class="info-grid">
              <div class="info-item">
                <span class="label">模型</span>
                <span class="value">{{ cfg.model }}</span>
              </div>
              <div class="info-item">
                <span class="label">API Key</span>
                <span class="value masked">{{ cfg.api_key_masked || '未设置' }}</span>
              </div>
              <div v-if="cfg.base_url" class="info-item">
                <span class="label">Base URL</span>
                <span class="value">{{ cfg.base_url }}</span>
              </div>
              <div v-if="cfg.group_id" class="info-item">
                <span class="label">Group ID</span>
                <span class="value masked">{{ maskGroupId(cfg.group_id) }}</span>
              </div>
              <div class="info-item">
                <span class="label">Temperature</span>
                <span class="value">{{ cfg.temperature }}</span>
              </div>
              <div class="info-item">
                <span class="label">Max Tokens</span>
                <span class="value">{{ cfg.max_tokens }}</span>
              </div>
            </div>
          </div>
          <!-- 测试结果 -->
          <div v-if="testResults[cfg.id]" class="test-result" :class="testResults[cfg.id].success ? 'success' : 'error'">
            <span>{{ testResults[cfg.id].success ? '✅ ' + testResults[cfg.id].response : '❌ ' + testResults[cfg.id].error }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 支持的供应商参考 -->
    <div class="providers-ref">
      <h3 class="section-title">支持的供应商</h3>
      <div class="provider-grid">
        <div v-for="(info, key) in providerInfo" :key="key" class="provider-card">
          <div class="provider-card-header">
            <strong>{{ info.name }}</strong>
            <span class="provider-key">{{ key }}</span>
          </div>
          <div class="provider-models">
            <code v-for="m in info.models.slice(0, 3)" :key="m">{{ m }}</code>
            <span v-if="info.models.length > 3">+{{ info.models.length - 3 }} more</span>
          </div>
          <div class="provider-hint">
            <span v-if="info.requires_group_id">需要 Group ID</span>
            <span v-else>标准 API 格式</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加/编辑弹窗 -->
    <CyberModal
      v-model="showAddDialog"
      :title="editingId ? '编辑模型配置' : '添加模型配置'"
      :subtitle="editingId ? '修改模型配置信息' : '配置新的 AI 模型供应商'"
      size="large"
      intent="ai"
      :confirm-text="editingId ? '保存' : '添加'"
      :loading="saving"
      @confirm="saveConfig"
    >
      <div class="form-group">
        <label class="form-label">配置名称 *</label>
        <input v-model="form.name" type="text" class="form-input" placeholder="例如: MiniMax M2.7" />
      </div>

      <div class="form-row">
        <div class="form-group">
          <label class="form-label">供应商 *</label>
          <select v-model="form.provider" class="form-select" @change="onProviderChange">
            <option value="">请选择</option>
            <option v-for="(info, key) in providerInfo" :key="key" :value="key">
              {{ info.name }}
            </option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">模型名称 *</label>
          <select v-model="form.model" class="form-select" v-if="selectedProviderInfo?.models?.length">
            <option value="">请选择</option>
            <option v-for="m in selectedProviderInfo.models" :key="m" :value="m">{{ m }}</option>
          </select>
          <input v-else v-model="form.model" type="text" class="form-input" placeholder="请输入模型名称" />
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">API Key *</label>
        <input v-model="form.api_key" type="password" class="form-input" placeholder="请输入 API Key" />
      </div>

      <div class="form-group" v-if="form.provider === 'minimax'">
        <label class="form-label">Group ID (MiniMax 专用) *</label>
        <input v-model="form.group_id" type="text" class="form-input" placeholder="请输入 Group ID" />
        <small class="form-hint">
          Group ID 不是 API Key。<a href="https://www.minimaxi.com/user-space/basic-setting/interface-key" target="_blank" class="form-link">点击获取 Group ID →</a>
        </small>
      </div>

      <div class="form-group">
        <label class="form-label">Base URL（可选）</label>
        <input v-model="form.base_url" type="text" class="form-input" :placeholder="selectedProviderInfo?.default_base_url || '留空使用默认地址'" />
        <small class="form-hint">留空则使用供应商默认地址，自建代理时可填写</small>
      </div>

      <div class="form-row">
        <div class="form-group">
          <label class="form-label">Temperature</label>
          <input v-model.number="form.temperature" type="number" class="form-input" min="0" max="10" />
        </div>
        <div class="form-group">
          <label class="form-label">Max Tokens</label>
          <input v-model.number="form.max_tokens" type="number" class="form-input" min="256" max="128000" />
        </div>
      </div>

      <div class="form-group form-group--checkbox">
        <label class="form-checkbox">
          <input type="checkbox" v-model="form.is_default" />
          <span class="checkbox-label">设为默认模型</span>
        </label>
      </div>
    </CyberModal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import CyberModal from '@/components/common/modal/CyberModal.vue'
import CyberConfirm from '@/components/common/CyberConfirm.vue'

const API_BASE = '/api'

function authHeaders() {
  return { Authorization: `Bearer ${localStorage.getItem('access_token') || ''}` }
}

const loading = ref(false)
const configs = ref([])
const showAddDialog = ref(false)
const editingId = ref(null)
const saving = ref(false)
const testResults = ref({})
const providerInfo = ref({})

const form = reactive({
  name: '',
  provider: '',
  api_key: '',
  model: '',
  base_url: '',
  group_id: '',
  temperature: 7,
  max_tokens: 4096,
  is_default: false,
})

const selectedProviderInfo = computed(() => providerInfo.value[form.provider])

onMounted(() => {
  loadConfigs()
  loadProviders()
})

async function loadConfigs() {
  loading.value = true
  try {
    const token = localStorage.getItem('access_token')
    const headers = token ? { Authorization: 'Bearer ' + token } : {}
    const res = await fetch(API_BASE + '/ai/models/configs?include_disabled=true', { headers })
    if (res.status === 401) { configs.value = []; loading.value = false; return }
    const data = await res.json()
    configs.value = Array.isArray(data) ? data : (data.items || [])
  } catch (e) {
    console.error('Load configs failed:', e)
  } finally {
    loading.value = false
  }
}

async function loadProviders() {
  try {
    const token = localStorage.getItem('access_token')
    const headers = token ? { Authorization: 'Bearer ' + token } : {}
    const res = await fetch(API_BASE + '/ai/models/providers', { headers })
    if (res.status === 401) return
    providerInfo.value = await res.json()
  } catch (e) {
    console.error('Load providers failed:', e)
  }
}

async function refreshProviders() {
  await loadProviders()
  await loadConfigs()
}

function onProviderChange() {
  form.model = ''
  form.base_url = selectedProviderInfo.value?.default_base_url || ''
}

function openAddDialog() {
  editingId.value = null
  Object.assign(form, {
    name: '', provider: '', api_key: '', model: '',
    base_url: '', group_id: '', temperature: 7, max_tokens: 4096, is_default: false,
  })
  showAddDialog.value = true
}

function editConfig(cfg) {
  editingId.value = cfg.id
  Object.assign(form, {
    name: cfg.name,
    provider: cfg.provider,
    api_key: '',
    model: cfg.model,
    base_url: cfg.base_url || '',
    group_id: cfg.group_id || '',
    temperature: cfg.temperature,
    max_tokens: cfg.max_tokens,
    is_default: cfg.is_default,
  })
  showAddDialog.value = true
}

async function saveConfig() {
  saving.value = true
  try {
    const token = localStorage.getItem('access_token')
    const authH = token ? { Authorization: 'Bearer ' + token } : {}
    let res
    if (editingId.value) {
      const payload = { ...form }
      if (!payload.api_key) delete payload.api_key
      res = await fetch(API_BASE + '/ai/models/configs/' + editingId.value, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', ...authH },
        body: JSON.stringify(payload),
      })
    } else {
      res = await fetch(API_BASE + '/ai/models/configs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authH },
        body: JSON.stringify({ ...form }),
      })
    }
    const result = await res.json()
    if (!res.ok) {
      alert('保存失败: ' + (result.detail || result.error))
      return
    }
    showAddDialog.value = false
    editingId.value = null
    loadConfigs()
  } catch (e) {
    alert('保存失败: ' + e.message)
  } finally {
    saving.value = false
  }
}

async function testConnection(cfg) {
  testResults.value[cfg.id] = null
  try {
    const res = await fetch(API_BASE + '/ai/models/configs/' + cfg.id + '/test', { method: 'POST', headers: { Authorization: 'Bearer ' + (localStorage.getItem('access_token') || '') } })
    const result = await res.json()
    if (!res.ok) {
      testResults.value[cfg.id] = { success: false, error: result.detail || result.error }
    } else {
      testResults.value[cfg.id] = { success: true, response: result.response || 'OK' }
    }
  } catch (e) {
    testResults.value[cfg.id] = { success: false, error: e.message }
  }
}

async function toggleEnabled(cfg) {
  try {
    const newEnabled = !cfg.enabled
    const res = await fetch(API_BASE + '/ai/models/configs/' + cfg.id, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + (localStorage.getItem('access_token') || '') },
      body: JSON.stringify({ enabled: newEnabled }),
    })
    const r = await res.json()
    if (!res.ok) {
      alert((newEnabled ? '启用' : '禁用') + '失败: ' + (r.detail || r.error))
      return
    }
    loadConfigs()
  } catch (e) {
    alert('操作失败')
  }
}

async function setDefault(id) {
  try {
    const res = await fetch(API_BASE + '/ai/models/configs/' + id + '/set-default', { method: 'POST', headers: { Authorization: 'Bearer ' + (localStorage.getItem('access_token') || '') } })
    if (res.ok) loadConfigs()
    else {
      const r = await res.json()
      alert('设置失败: ' + (r.detail || r.error))
    }
  } catch (e) {
    alert('设置失败')
  }
}

async function deleteConfig(id) {
  try {
    const res = await fetch(API_BASE + '/ai/models/configs/' + id, { method: 'DELETE', headers: { Authorization: 'Bearer ' + (localStorage.getItem('access_token') || '') } })
    const r = await res.json()
    if (!res.ok) {
      alert('删除失败: ' + (r.detail || r.error))
      return
    }
    loadConfigs()
  } catch (e) {
    alert('删除失败')
  }
}

function getProviderName(key) {
  return providerInfo.value[key]?.name || key
}

function maskGroupId(id) {
  if (!id || id.length < 8) return '***'
  return id.slice(0, 6) + '***'
}
</script>

<style scoped>
.model-config-page {
  padding: 24px;
  max-width: 1200px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.info-banner {
  background: rgba(0, 255, 255, 0.08);
  border: 1px solid rgba(0, 255, 255, 0.3);
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 24px;
  display: flex;
  gap: 10px;
  align-items: flex-start;
  font-size: 13px;
  color: var(--text-secondary);
}

.info-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin: 0 0 16px;
}

.config-list {
  margin-bottom: 32px;
}

.config-cards {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.config-card {
  background: var(--bg-panel);
  border: 1px solid var(--border-default);
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.2s;
}

.config-card.is-default {
  border-color: var(--neon-cyan);
  box-shadow: 0 0 10px rgba(0, 255, 255, 0.15);
}

.config-card.is-disabled {
  opacity: 0.6;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-default);
}

.card-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.default-tag {
  font-size: 11px;
  padding: 2px 8px;
  background: rgba(0, 255, 255, 0.2);
  color: var(--neon-cyan);
  border-radius: 4px;
}

.disabled-tag {
  font-size: 11px;
  padding: 2px 8px;
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-secondary);
  border-radius: 4px;
}

.provider-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 600;
}

.provider-minimax { background: #e3f2fd; color: #1565c0; }
.provider-openai { background: #e8f5e9; color: #2e7d32; }
.provider-anthropic { background: #fff3e0; color: #e65100; }
.provider-deepseek { background: #f3e5f5; color: #6a1b9a; }
.provider-custom { background: #f5f5f5; color: #616161; }

.card-actions {
  display: flex;
  gap: 4px;
}

.btn-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid var(--border-default);
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-icon:hover {
  border-color: var(--neon-cyan);
  color: var(--neon-cyan);
}

.btn-icon.danger:hover {
  border-color: var(--neon-pink);
  color: var(--neon-pink);
}

.btn-icon.success:hover {
  border-color: var(--neon-green);
  color: var(--neon-green);
}

.btn-icon.warning:hover {
  border-color: #ff9800;
  color: #ff9800;
}

.card-body {
  padding: 16px 20px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item .label {
  font-size: 11px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-item .value {
  font-size: 13px;
  color: var(--text-primary);
}

.info-item .value.masked {
  color: var(--neon-cyan);
  font-family: monospace;
}

.test-result {
  padding: 10px 20px;
  font-size: 13px;
  border-top: 1px solid var(--border-default);
}

.test-result.success {
  background: rgba(0, 255, 136, 0.05);
  color: var(--neon-green);
}

.test-result.error {
  background: rgba(255, 71, 87, 0.05);
  color: var(--neon-pink);
}

/* 供应商参考 */
.providers-ref {
  margin-top: 32px;
}

.provider-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}

.provider-card {
  background: var(--bg-panel);
  border: 1px solid var(--border-default);
  border-radius: 8px;
  padding: 14px 16px;
}

.provider-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.provider-key {
  font-size: 10px;
  padding: 2px 6px;
  background: var(--bg-secondary);
  border-radius: 3px;
  color: var(--text-secondary);
  font-family: monospace;
}

.provider-models {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 8px;
}

.provider-models code {
  font-size: 11px;
  padding: 2px 6px;
  background: var(--bg-secondary);
  border-radius: 3px;
  color: var(--neon-cyan);
}

.provider-hint {
  font-size: 11px;
  color: var(--text-secondary);
}

/* Form Styles for CyberModal */
.form-group {
  margin-bottom: 18px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group--checkbox {
  margin-top: -6px;
}

.form-row {
  display: flex;
  gap: 12px;
}

.form-row .form-group {
  flex: 1;
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
.form-select {
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
.form-select:focus {
  border-color: var(--modal-ai-accent, #00f0ff);
  box-shadow: 0 0 0 2px rgba(0, 240, 255, 0.15);
}

.form-input::placeholder {
  color: var(--modal-text-muted, #666);
}

.form-select {
  cursor: pointer;
}

.form-hint {
  display: block;
  font-size: 11px;
  color: var(--modal-text-muted, #666);
  margin-top: 6px;
}

.form-link {
  color: var(--modal-ai-accent, #00f0ff);
  text-decoration: none;
}

.form-link:hover {
  text-decoration: underline;
}

.form-checkbox {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.form-checkbox input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: var(--modal-ai-accent, #00f0ff);
}

.checkbox-label {
  font-family: var(--font-title, 'Orbitron', sans-serif);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 1px;
  color: var(--modal-text-primary, #e0e0e0);
}

/* Buttons */
.btn-primary {
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-secondary {
  padding: 10px 20px;
  background: var(--bg-secondary);
  color: var(--neon-cyan);
  border: 1px solid var(--neon-cyan);
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
  font-size: 14px;
}

.loading {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
}

/* Buttons */
.btn-primary {
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-secondary {
  padding: 10px 20px;
  background: var(--bg-secondary);
  color: var(--neon-cyan);
  border: 1px solid var(--neon-cyan);
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: rgba(0, 255, 255, 0.1);
}
</style>
