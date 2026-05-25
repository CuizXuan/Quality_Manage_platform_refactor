<template>
  <div class="ai-model-config">
    <!-- 页面标题区 -->
    <header class="ai-model-config__header">
      <div>
        <h1>AI 模型配置</h1>
        <p>配置 AI 模型连接参数，支持多模型切换。</p>
      </div>
    </header>

    <!-- 配置表单 -->
    <section class="ai-model-config__form">
      <el-form
        ref="formRef"
        :model="configForm"
        :rules="formRules"
        label-width="130px"
        class="config-form"
      >
        <el-form-item label="配置名称" prop="name">
          <el-input v-model="configForm.name" placeholder="如：MiniMax API" class="form-control" />
        </el-form-item>
        <el-form-item label="API Base URL" prop="base_url">
          <el-input v-model="configForm.base_url" placeholder="https://api.minimaxi.com" class="form-control-wide" />
        </el-form-item>
        <el-form-item label="API Key" prop="api_key">
          <el-input
            v-model="configForm.api_key"
            type="password"
            show-password
            placeholder="请输入 API Key"
            class="form-control-xwide"
          />
        </el-form-item>
        <el-form-item label="模型名称" prop="model">
          <el-input v-model="configForm.model" placeholder="MiniMax-M2.7" class="form-control" />
        </el-form-item>
        <el-form-item label="启用配置">
          <el-switch v-model="configForm.enabled" />
        </el-form-item>
        <el-form-item>
          <div class="btn-row">
            <el-button type="primary" :loading="saving" @click="handleSave">保存配置</el-button>
            <el-button :loading="testing" @click="handleTest">测试连接</el-button>
          </div>
        </el-form-item>
      </el-form>
    </section>

    <!-- 连接测试结果 -->
    <section v-if="testResult" class="ai-model-config__test-result">
      <el-alert
        :type="testResult.ok ? 'success' : 'error'"
        :title="testResult.ok ? '连接成功' : '连接失败'"
        :description="testResult.message"
        show-icon
      />
    </section>

    <!-- 当前配置状态 -->
    <section v-if="aiStore.aiConfig" class="ai-model-config__status">
      <div class="result-header">
        <span class="card-title">当前配置状态</span>
      </div>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="配置名称">{{ aiStore.aiConfig.name }}</el-descriptions-item>
        <el-descriptions-item label="模型">{{ aiStore.aiConfig.model }}</el-descriptions-item>
        <el-descriptions-item label="Base URL">{{ aiStore.aiConfig.base_url }}</el-descriptions-item>
        <el-descriptions-item label="API Key">{{ maskKey(aiStore.aiConfig.api_key) }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="aiStore.aiConfig.enabled ? 'success' : 'info'" size="small">
            {{ aiStore.aiConfig.enabled ? '已启用' : '已禁用' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ aiStore.aiConfig.updated_at || '—' }}</el-descriptions-item>
      </el-descriptions>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import feedback from '@/utils/feedback'
import { useAiStore } from '@/stores/aiStore'

const aiStore = useAiStore()

const formRef = ref(null)
const saving = ref(false)
const testing = ref(false)
const testResult = ref(null)

const configForm = ref({
  name: 'MiniMax',
  api_key: '',
  base_url: 'https://api.minimaxi.com',
  model: 'MiniMax-M2.7',
  enabled: false,
})

const formRules = {
  api_key: [{ required: true, message: '请输入 API Key', trigger: 'blur' }],
  base_url: [{ required: true, message: '请输入 Base URL', trigger: 'blur' }],
  model: [{ required: true, message: '请输入模型名称', trigger: 'blur' }],
}

onMounted(async () => {
  try {
    await aiStore.fetchConfig()
    if (aiStore.aiConfig) {
      configForm.value = {
        name: aiStore.aiConfig.name || 'MiniMax',
        api_key: aiStore.aiConfig.api_key || '',
        base_url: aiStore.aiConfig.base_url || 'https://api.minimaxi.com',
        model: aiStore.aiConfig.model || 'MiniMax-M2.7',
        enabled: aiStore.aiConfig.enabled || false,
      }
    }
  } catch {
    // no config yet, use defaults
  }
})

async function handleSave() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  saving.value = true
  try {
    await aiStore.saveConfig(configForm.value)
    feedback.success('配置保存成功')
  } catch {
    // error handled in store
  } finally {
    saving.value = false
  }
}

async function handleTest() {
  testing.value = true
  testResult.value = null
  try {
    const result = await aiStore.testConnection(configForm.value)
    testResult.value = result
    if (result.ok) feedback.success('连接测试成功')
    else feedback.error('连接测试失败：' + (result.message || ''))
  } catch {
    testResult.value = { ok: false, message: '连接超时或服务不可用' }
  } finally {
    testing.value = false
  }
}

function maskKey(key) {
  if (!key || key.length < 8) return '****'
  return key.slice(0, 4) + '****' + key.slice(-4)
}
</script>

<style scoped>
/* ── 页面容器 ── */
.ai-model-config {
  position: relative;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-height: 0;
  min-width: 0;
  gap: 10px;
  padding: 12px;
  background:
    linear-gradient(rgba(56, 189, 248, 0.095) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.085) 1px, transparent 1px),
    linear-gradient(145deg, rgba(34, 211, 166, 0.18), transparent 30%),
    linear-gradient(225deg, rgba(56, 189, 248, 0.22), transparent 36%),
    linear-gradient(0deg, rgba(22, 119, 255, 0.12), transparent 50%),
    var(--bg-page);
  background-size: 28px 28px, 28px 28px, auto, auto, auto, auto;
  overflow: hidden;
}

.ai-model-config::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 24%, rgba(56, 189, 248, 0.16) 44%, transparent 62%),
    repeating-linear-gradient(90deg, transparent 0 92px, rgba(56, 189, 248, 0.075) 92px 93px);
  content: "";
  animation: case-scan 14s linear infinite;
}

.ai-model-config::after {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background-image:
    radial-gradient(circle, rgba(125, 211, 252, 0.72) 0 1.2px, transparent 1.8px),
    radial-gradient(circle, rgba(45, 212, 191, 0.52) 0 1.1px, transparent 1.7px);
  background-position: 8% 16%, 80% 42%;
  background-size: 180px 160px, 240px 220px;
  opacity: 0.48;
  content: "";
  animation: case-particles 18s ease-in-out infinite alternate;
}

@keyframes case-scan {
  from { transform: translateX(-24%); }
  to { transform: translateX(24%); }
}

@keyframes case-particles {
  from { transform: translate3d(0, 0, 0); }
  to { transform: translate3d(26px, -18px, 0); }
}

@media (prefers-reduced-motion: reduce) {
  .ai-model-config::before,
  .ai-model-config::after {
    animation: none;
  }
}

/* ── 标题区 ── */
.ai-model-config__header {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-height: 56px;
  padding: 12px 16px;
  border: 1px solid rgba(56, 189, 248, 0.22);
  border-radius: var(--border-radius-base);
  background:
    linear-gradient(135deg, rgba(15, 23, 42, 0.68), rgba(15, 23, 42, 0.42)),
    rgba(20, 22, 27, 0.48);
  box-shadow: 0 18px 48px rgba(2, 8, 23, 0.24), inset 0 1px 0 rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(18px) saturate(1.25);
  overflow: hidden;
}

.ai-model-config__header::after {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(90deg, rgba(56, 189, 248, 0.22), transparent 18% 82%, rgba(34, 211, 166, 0.18)),
    repeating-linear-gradient(90deg, transparent 0 42px, rgba(56, 189, 248, 0.06) 42px 43px);
  opacity: 0.65;
  content: "";
}

html:not(.dark) .ai-model-config__header {
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.86), rgba(245, 250, 255, 0.68)),
    rgba(255, 255, 255, 0.72);
  box-shadow: 0 18px 46px rgba(20, 42, 76, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.82);
}

.ai-model-config__header h1,
.ai-model-config__header p {
  margin: 0;
  position: relative;
  z-index: 1;
}

.ai-model-config__header h1 {
  color: var(--text-strong);
  font-size: 24px;
  line-height: 1.25;
}

.ai-model-config__header p {
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 13px;
}

/* ── 表单区 ── */
.ai-model-config__form {
  position: relative;
  padding: 14px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background:
    linear-gradient(rgba(56, 189, 248, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.045) 1px, transparent 1px);
  background-size: 32px 32px;
  backdrop-filter: blur(10px);
}

.ai-model-config__form::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(56, 189, 248, 0.12) 50%, transparent 66%);
  opacity: 0.6;
  content: "";
  animation: case-form-scan 10s linear infinite;
}

html:not(.dark) .ai-model-config__form {
  background:
    linear-gradient(rgba(22, 119, 255, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.03) 1px, transparent 1px),
    rgba(255, 255, 255, 0.44);
  background-size: 32px 32px, 32px 32px, auto;
}

@keyframes case-form-scan {
  from { transform: translateX(-22%); }
  to { transform: translateX(22%); }
}

/* ── 测试结果 ── */
.ai-model-config__test-result {
  position: relative;
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background:
    linear-gradient(rgba(56, 189, 248, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.045) 1px, transparent 1px);
  background-size: 32px 32px;
  backdrop-filter: blur(10px);
}

html:not(.dark) .ai-model-config__test-result {
  background:
    linear-gradient(rgba(22, 119, 255, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.03) 1px, transparent 1px),
    rgba(255, 255, 255, 0.44);
  background-size: 32px 32px, 32px 32px, auto;
}

/* ── 配置状态 ── */
.ai-model-config__status {
  position: relative;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background:
    linear-gradient(rgba(56, 189, 248, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.045) 1px, transparent 1px);
  background-size: 32px 32px;
  backdrop-filter: blur(10px);
  overflow: hidden;
}

.ai-model-config__status::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(56, 189, 248, 0.12) 50%, transparent 66%);
  opacity: 0.6;
  content: "";
  animation: case-form-scan 10s linear infinite;
}

html:not(.dark) .ai-model-config__status {
  background:
    linear-gradient(rgba(22, 119, 255, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.03) 1px, transparent 1px),
    rgba(255, 255, 255, 0.44);
  background-size: 32px 32px, 32px 32px, auto;
}

.result-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-strong);
}
</style>
