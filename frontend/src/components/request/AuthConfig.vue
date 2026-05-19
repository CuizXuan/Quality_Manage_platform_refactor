<template>
  <div class="auth-config">
    <!-- Auth Type Selector -->
    <div class="auth-type-selector">
      <label>认证类型</label>
      <div class="type-buttons">
        <button
          v-for="t in authTypes"
          :key="t.value"
          :class="{ active: authType === t.value }"
          @click="authType = t.value"
        >
          {{ t.label }}
        </button>
      </div>
    </div>

    <!-- None -->
    <div v-if="authType === 'none'" class="auth-none">
      <span class="hint">此请求不需要认证</span>
    </div>

    <!-- Basic Auth -->
    <div v-else-if="authType === 'basic'" class="auth-basic">
      <div class="form-group">
        <label>用户名</label>
        <input v-model="authConfig.username" placeholder="Username" />
      </div>
      <div class="form-group">
        <label>密码</label>
        <input v-model="authConfig.password" type="password" placeholder="Password" />
      </div>
    </div>

    <!-- Bearer Token -->
    <div v-else-if="authType === 'bearer'" class="auth-bearer">
      <div class="form-group">
        <label>Token</label>
        <input v-model="authConfig.token" placeholder="Bearer Token" class="token-input" />
      </div>
      <div class="form-group">
        <label>前缀 (可选)</label>
        <input v-model="authConfig.prefix" placeholder="Bearer (默认)" />
      </div>
    </div>

    <!-- API Key -->
    <div v-else-if="authType === 'api_key'" class="auth-api-key">
      <div class="form-group">
        <label>Key 名称</label>
        <input v-model="authConfig.key_name" placeholder="如: X-API-Key" />
      </div>
      <div class="form-group">
        <label>Key 值</label>
        <input v-model="authConfig.key_value" placeholder="API Key 值" />
      </div>
      <div class="form-group">
        <label>添加位置</label>
        <div class="type-buttons">
          <button :class="{ active: authConfig.add_to === 'header' }" @click="authConfig.add_to = 'header'">Header</button>
          <button :class="{ active: authConfig.add_to === 'query' }" @click="authConfig.add_to = 'query'">Query Params</button>
        </div>
      </div>
    </div>

    <!-- Custom Header -->
    <div v-else-if="authType === 'custom'" class="auth-custom">
      <div class="form-group">
        <label>Header 名称</label>
        <input v-model="authConfig.header_name" placeholder="如: Authorization" />
      </div>
      <div class="form-group">
        <label>Header 值</label>
        <input v-model="authConfig.header_value" placeholder="值，支持 {{variable}} 语法" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({ type: 'none', config: {} })
  }
})

const emit = defineEmits(['update:modelValue'])

const authTypes = [
  { value: 'none', label: '无' },
  { value: 'basic', label: 'Basic' },
  { value: 'bearer', label: 'Bearer' },
  { value: 'api_key', label: 'API Key' },
  { value: 'custom', label: '自定义' },
]

const authType = ref(props.modelValue.type || 'none')
const authConfig = ref(props.modelValue.config || {})

// 监听变化，同步到父组件
watch([authType, authConfig], () => {
  emit('update:modelValue', {
    type: authType.value,
    config: { ...authConfig.value }
  })
}, { deep: true })

// 初始化
if (props.modelValue.type && props.modelValue.type !== 'none') {
  authConfig.value = { ...props.modelValue.config }
}
</script>

<style scoped>
.auth-config {
  padding: 8px 0;
}

.auth-type-selector {
  margin-bottom: 16px;
}

.auth-type-selector label {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.type-buttons {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.type-buttons button {
  padding: 6px 12px;
  border: 1px solid var(--border);
  background: var(--bg-secondary);
  color: var(--text);
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.type-buttons button:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.type-buttons button.active {
  background: var(--primary);
  border-color: var(--primary);
  color: #fff;
}

.auth-none {
  padding: 20px;
  text-align: center;
}

.hint {
  color: var(--text-secondary);
  font-size: 13px;
}

.auth-basic,
.auth-bearer,
.auth-api-key,
.auth-custom {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-group label {
  font-size: 12px;
  color: var(--text-secondary);
}

.form-group input {
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--bg-secondary);
  color: var(--text);
  font-size: 13px;
}

.form-group input:focus {
  outline: none;
  border-color: var(--primary);
}

.token-input {
  font-family: var(--mono);
}
</style>
