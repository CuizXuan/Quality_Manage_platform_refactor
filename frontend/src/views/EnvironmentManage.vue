<template>
  <div class="env-manage">
    <div class="toolbar">
      <h2 class="page-title">
        <span class="prompt">&gt;</span> 环境管理
      </h2>
      <button class="btn primary" @click="openCreateModal">
        <span>+</span> 新建环境
      </button>
    </div>

    <div v-if="envStore.loading" class="loading">
      <span class="loading-spinner">⟳</span>
      加载中...
    </div>

    <div v-else class="env-list">
      <div v-for="env in envStore.environments" :key="env.id" class="env-card panel" :class="{ default: env.is_default }">
        <div class="env-header">
          <div class="env-name">
            <span class="env-icon">◈</span>
            {{ env.name }}
            <span v-if="env.is_default" class="badge">默认</span>
          </div>
          <div class="env-actions">
            <button class="icon-btn" @click="openEditModal(env)">✏️</button>
            <button v-if="!env.is_default" class="icon-btn" @click="envStore.setDefault(env.id)">⭐</button>
            <CyberConfirm title="确认删除该环境？" danger @confirm="removeEnv(env.id)">
              <template #trigger>
                <button class="icon-btn danger">🗑</button>
              </template>
            </CyberConfirm>
          </div>
        </div>

        <div v-if="env.description" class="env-desc">{{ env.description }}</div>

        <div class="env-vars">
          <div class="var-header">
            <span>变量</span>
          </div>
          <div v-for="(value, key) in env.variables" :key="key" class="var-row">
            <span class="var-key">{{ key }}</span>
            <span class="var-equals">=</span>
            <span class="var-val">{{ value }}</span>
          </div>
          <div v-if="!env.variables || Object.keys(env.variables).length === 0" class="empty-vars">
            -- 暂无变量 --
          </div>
        </div>
      </div>
    </div>

    <!-- 环境弹窗 -->
    <CyberModal
      v-model="showModal"
      :title="editing ? '编辑环境' : '新建环境'"
      :subtitle="editing ? `正在编辑: ${editing.name}` : '创建新的测试环境'"
      size="medium"
      :confirm-text="editing ? '保存' : '创建'"
      :loading="saving"
      @confirm="saveEnv"
    >
      <div class="form-group">
        <label class="form-label">名称</label>
        <input v-model="form.name" class="form-input" placeholder="测试环境" />
      </div>

      <div class="form-group">
        <label class="form-label">描述</label>
        <input v-model="form.description" class="form-input" placeholder="环境描述" />
      </div>

      <div class="form-group form-group--checkbox">
        <label class="form-checkbox">
          <input type="checkbox" v-model="form.is_default" />
          <span class="checkbox-label">设为默认环境</span>
        </label>
      </div>

      <div class="form-group">
        <label class="form-label">变量</label>
        <div v-for="(v, i) in form.variables" :key="i" class="var-input-row">
          <input v-model="form.variables[i].key" class="form-input form-input--inline" placeholder="键" />
          <span class="equals">=</span>
          <input v-model="form.variables[i].value" class="form-input form-input--inline" placeholder="值" />
          <button class="icon-btn danger" @click="form.variables.splice(i, 1)">×</button>
        </div>
        <button class="btn btn--add" @click="form.variables.push({ key: '', value: '' })">+ 添加变量</button>
      </div>
    </CyberModal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useEnvironmentStore } from '@/stores/environmentStore'
import CyberModal from '@/components/common/modal/CyberModal.vue'
import CyberConfirm from '@/components/common/CyberConfirm.vue'

const envStore = useEnvironmentStore()

const showModal = ref(false)
const editing = ref(null)
const saving = ref(false)
const form = ref(defaultForm())

function defaultForm() {
  return { name: '', description: '', is_default: false, variables: [] }
}

function openCreateModal() {
  editing.value = null
  form.value = defaultForm()
  showModal.value = true
}

function openEditModal(env) {
  editing.value = env
  const vars = Object.entries(env.variables || {}).map(([key, value]) => ({ key, value }))
  form.value = { name: env.name, description: env.description, is_default: env.is_default, variables: vars }
  showModal.value = true
}

async function saveEnv() {
  if (!form.value.name.trim()) {
    return
  }
  saving.value = true
  try {
    const variables = {}
    form.value.variables.forEach(v => { if (v.key) variables[v.key] = v.value })
    const data = { ...form.value, variables }
    if (editing.value) {
      await envStore.updateEnvironment(editing.value.id, data)
    } else {
      await envStore.createEnvironment(data)
    }
    showModal.value = false
  } finally {
    saving.value = false
  }
}

async function removeEnv(id) {
  await envStore.deleteEnvironment(id)
}

onMounted(() => envStore.fetchEnvironments())
</script>

<style scoped>
.env-manage {
  padding: 16px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
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

.loading {
  padding: 40px;
  text-align: center;
  color: var(--neon-cyan);
  font-family: var(--font-mono);
}

.loading-spinner {
  display: inline-block;
  animation: spin 1s linear infinite;
  margin-right: 10px;
}

.env-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 16px;
}

.env-card {
  padding: 16px;
}

.env-card.default {
  border-color: var(--neon-cyan);
  box-shadow: 0 0 20px rgba(0, 255, 255, 0.2);
}

.env-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.env-name {
  font-family: var(--font-title);
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 1px;
  color: var(--neon-cyan);
  display: flex;
  align-items: center;
  gap: 8px;
}

.env-icon {
  color: var(--neon-magenta);
}

.badge {
  font-size: 9px;
  background: var(--neon-cyan);
  color: var(--bg-primary);
  padding: 2px 6px;
  border-radius: 2px;
  letter-spacing: 1px;
}

.env-desc {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.env-vars {
  background: var(--bg-secondary);
  border-radius: 4px;
  overflow: hidden;
}

.var-header {
  padding: 8px 12px;
  font-family: var(--font-title);
  font-size: 10px;
  letter-spacing: 2px;
  color: var(--text-secondary);
  background: rgba(0, 255, 255, 0.05);
  border-bottom: 1px solid var(--border-default);
}

.var-row {
  display: flex;
  padding: 6px 12px;
  font-family: var(--font-mono);
  font-size: 12px;
  border-bottom: 1px solid var(--border-default);
}

.var-row:last-child {
  border-bottom: none;
}

.var-key {
  color: var(--neon-cyan);
}

.var-equals {
  color: var(--text-secondary);
  margin: 0 8px;
}

.var-val {
  color: var(--neon-magenta);
  word-break: break-all;
}

.empty-vars {
  padding: 12px;
  text-align: center;
  color: var(--text-secondary);
  font-family: var(--font-mono);
  font-size: 11px;
}

.env-actions {
  display: flex;
  gap: 4px;
}

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

/* Form Styles */
.form-group {
  margin-bottom: 18px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group--checkbox {
  margin-top: -6px;
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

.form-input {
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

.form-input:focus {
  border-color: var(--modal-ai-accent, #00f0ff);
  box-shadow: 0 0 0 2px rgba(0, 240, 255, 0.15);
}

.form-input::placeholder {
  color: var(--modal-text-muted, #666);
}

.form-input--inline {
  flex: 1;
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

.var-input-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.equals {
  color: var(--modal-text-secondary, #888);
  flex-shrink: 0;
}

.btn--add {
  margin-top: 8px;
  font-family: var(--font-title, 'Orbitron', sans-serif);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 1px;
  text-transform: uppercase;
  padding: 8px 16px;
  background: transparent;
  border: 1px dashed var(--modal-border, rgba(0, 255, 255, 0.22));
  border-radius: 4px;
  color: var(--modal-text-secondary, #888);
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn--add:hover {
  border-color: var(--modal-ai-accent, #00f0ff);
  color: var(--modal-ai-accent, #00f0ff);
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>