<template>
  <div class="api-case-form">
    <el-form :model="modelValue" label-width="96px">
      <section class="api-case-form__paste">
        <el-input
          v-model="requestText"
          type="textarea"
          :rows="3"
          placeholder="粘贴 curl / fetch / URL，例如：curl -X POST https://api.example.com/login -H 'Content-Type: application/json' -d '{...}'"
        />
        <div class="api-case-form__paste-actions">
          <span>{{ parseHint }}</span>
          <el-button :icon="MagicStick" type="primary" plain @click="applyRequestText">识别并填充</el-button>
          <el-button text @click="requestText = ''">清空</el-button>
        </div>
      </section>

      <el-row :gutter="16">
        <el-col :span="8">
          <el-form-item label="请求方法">
            <el-select v-model="modelValue.method">
              <el-option v-for="method in methodOptions" :key="method" :label="method" :value="method" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="16">
          <el-form-item label="请求 URL" required>
            <el-input v-model="modelValue.url" placeholder="请输入接口请求地址" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-tabs v-model="activeTab" class="api-case-form__tabs">
        <el-tab-pane label="Params" name="params">
          <KeyValueEditor v-model="modelValue.params" />
        </el-tab-pane>
        <el-tab-pane label="Headers" name="headers">
          <KeyValueEditor v-model="modelValue.headers" />
        </el-tab-pane>
        <el-tab-pane label="Body" name="body">
          <BodyEditor
            v-model="modelValue.body"
            v-model:body-type="modelValue.body_type"
          />
        </el-tab-pane>
        <el-tab-pane label="Assert" name="assert">
          <div class="api-case-form__asserts">
            <el-row
              v-for="(assertion, index) in modelValue.assertions"
              :key="index"
              :gutter="8"
              class="api-case-form__assert-row"
            >
              <el-col :span="5">
                <el-select v-model="assertion.field" placeholder="字段">
                  <el-option label="status" value="status" />
                  <el-option label="body" value="body" />
                  <el-option label="header" value="header" />
                </el-select>
              </el-col>
              <el-col :span="5">
                <el-select v-model="assertion.operator" placeholder="操作符">
                  <el-option label="equals" value="equals" />
                  <el-option label="contains" value="contains" />
                  <el-option label="matches" value="matches" />
                </el-select>
              </el-col>
              <el-col :span="12">
                <el-input v-model="assertion.expected" placeholder="期望值" />
              </el-col>
              <el-col :span="2">
                <el-button :icon="Delete" circle type="danger" @click="removeAssert(index)" />
              </el-col>
            </el-row>
            <el-button :icon="Plus" @click="addAssert">添加断言</el-button>
          </div>
        </el-tab-pane>
      </el-tabs>

      <el-divider content-position="left">执行配置</el-divider>
      <el-form-item label="认证配置">
        <AuthEditor
          v-model="authType"
          v-model:auth-config="modelValue.auth_config"
        />
      </el-form-item>
      <el-form-item label="期望状态码">
        <el-input-number v-model="modelValue.expected_status" :min="100" :max="599" />
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Delete, MagicStick, Plus } from '@element-plus/icons-vue'
import AuthEditor from '@/components/terminal/AuthEditor.vue'
import BodyEditor from '@/components/terminal/BodyEditor.vue'
import KeyValueEditor from '@/components/terminal/KeyValueEditor.vue'
import { parseRequest } from '@/utils/requestParser'
import feedback from '@/utils/feedback'
import { methodOptions } from './caseUtils'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true,
  },
})

const activeTab = ref('params')
const requestText = ref('')
const parseHint = computed(() => {
  const text = requestText.value.trim()
  if (!text) return '支持自动识别请求方法、URL、查询参数、Header、Body 和 Bearer Token'
  if (text.startsWith('curl')) return '检测到 cURL'
  if (text.includes('fetch(')) return '检测到 fetch'
  if (text.startsWith('http')) return '检测到 URL'
  return '可粘贴常见请求文本'
})

const authType = computed({
  get: () => props.modelValue.auth_config?.type || 'none',
  set: (value) => {
    props.modelValue.auth_config = {
      ...(props.modelValue.auth_config || {}),
      type: value,
    }
  },
})

function addAssert() {
  props.modelValue.assertions.push({
    field: 'status',
    operator: 'equals',
    expected: '',
  })
}

function removeAssert(index) {
  props.modelValue.assertions.splice(index, 1)
}

function applyRequestText() {
  if (!requestText.value.trim()) {
    feedback.warning('请先粘贴请求文本')
    return
  }

  const parsed = parseRequest(requestText.value)
  if (!parsed.url) {
    feedback.warning('未识别到请求 URL')
    return
  }

  props.modelValue.method = parsed.method || 'GET'
  props.modelValue.url = parsed.url
  props.modelValue.params = toRows(parsed.query_params)
  props.modelValue.headers = parsed.headers || []
  props.modelValue.body = parsed.body || ''
  props.modelValue.body_type = parsed.bodyType || 'none'
  props.modelValue.auth_config = createAuthConfig(parsed)
  activeTab.value = props.modelValue.body ? 'body' : props.modelValue.headers.length ? 'headers' : 'params'
  feedback.success('请求配置已自动填充')
}

function toRows(value) {
  if (Array.isArray(value)) return value
  return Object.entries(value || {}).map(([key, rowValue]) => ({
    key,
    value: String(rowValue ?? ''),
  }))
}

function createAuthConfig(parsed) {
  if (parsed.authType === 'bearer') {
    return { type: 'bearer', token: parsed.authToken || '' }
  }
  return props.modelValue.auth_config || {}
}
</script>

<style scoped>
.api-case-form {
  display: grid;
  gap: var(--spacing-md);
}

.api-case-form__paste {
  display: grid;
  gap: 8px;
  padding: 12px;
  border: 1px solid var(--border-color-lighter);
  border-radius: var(--border-radius-base);
  background: var(--bg-container-soft);
}

.api-case-form__paste :deep(textarea) {
  font-family: var(--font-mono);
  font-size: var(--font-size-sm);
  line-height: 1.5;
}

.api-case-form__paste-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  align-items: center;
}

.api-case-form__paste-actions span {
  margin-right: auto;
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
}

.api-case-form__tabs {
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: var(--bg-container);
  overflow: hidden;
}

.api-case-form__tabs :deep(.el-tabs__header) {
  margin: 0;
  padding: 0 14px;
  background: var(--bg-container-soft);
}

.api-case-form__tabs :deep(.el-tabs__item) {
  height: 42px;
  font-weight: 700;
}

.api-case-form__tabs :deep(.el-tabs__content) {
  min-height: 220px;
}

.api-case-form__asserts {
  display: grid;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
}

.api-case-form__assert-row {
  align-items: center;
}
</style>
