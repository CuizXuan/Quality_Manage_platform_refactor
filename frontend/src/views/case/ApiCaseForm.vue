<template>
  <div class="api-case-form">
    <el-form :model="formData" label-width="100px">
      <el-form-item label="请求方法">
        <el-select v-model="formData.method" style="width: 150px">
          <el-option v-for="m in methods" :key="m" :label="m" :value="m" />
        </el-select>
      </el-form-item>

      <el-form-item label="URL" required>
        <el-input v-model="formData.url" placeholder="请输入请求 URL" />
      </el-form-item>

      <el-form-item label="请求头">
        <div class="input-mode-toggle">
          <el-radio-group v-model="headersInputMode" size="small">
            <el-radio-button label="row">行输入</el-radio-button>
            <el-radio-button label="json">JSON</el-radio-button>
          </el-radio-group>
        </div>
        <div v-if="headersInputMode === 'row'" class="kv-editor">
          <div v-for="(item, index) in formData.headers" :key="index" class="kv-row">
            <el-input v-model="item.key" placeholder="参数名" size="small" />
            <el-input v-model="item.value" placeholder="参数值" size="small" />
            <el-button type="danger" :icon="Delete" size="small" @click="removeHeader(index)" />
          </div>
          <el-button :icon="Plus" size="small" @click="addHeader">添加请求头</el-button>
        </div>
        <div v-else class="json-editor">
          <el-input
            v-model="headersJson"
            type="textarea"
            :rows="4"
            placeholder='{"Content-Type": "application/json"}'
            @blur="parseHeadersJson"
          />
          <div v-if="headersJsonError" class="json-error">{{ headersJsonError }}</div>
        </div>
      </el-form-item>

      <el-form-item label="Query 参数">
        <div class="input-mode-toggle">
          <el-radio-group v-model="paramsInputMode" size="small">
            <el-radio-button label="row">行输入</el-radio-button>
            <el-radio-button label="json">JSON</el-radio-button>
          </el-radio-group>
        </div>
        <div v-if="paramsInputMode === 'row'" class="kv-editor">
          <div v-for="(item, index) in formData.params" :key="index" class="kv-row">
            <el-input v-model="item.key" placeholder="参数名" size="small" />
            <el-input v-model="item.value" placeholder="参数值" size="small" />
            <el-button type="danger" :icon="Delete" size="small" @click="removeParam(index)" />
          </div>
          <el-button :icon="Plus" size="small" @click="addParam">添加参数</el-button>
        </div>
        <div v-else class="json-editor">
          <el-input
            v-model="paramsJson"
            type="textarea"
            :rows="4"
            placeholder='{"page": 1, "size": 20}'
            @blur="parseParamsJson"
          />
          <div v-if="paramsJsonError" class="json-error">{{ paramsJsonError }}</div>
        </div>
      </el-form-item>

      <el-form-item label="Body 类型">
        <el-radio-group v-model="formData.body_type">
          <el-radio label="none">无</el-radio>
          <el-radio label="form">form</el-radio>
          <el-radio label="json">JSON</el-radio>
          <el-radio label="raw">Raw</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="Body 内容" v-if="formData.body_type !== 'none'">
        <el-input
          v-model="formData.body"
          type="textarea"
          :rows="4"
          placeholder="请输入请求体"
        />
      </el-form-item>

      <el-form-item label="认证配置">
        <el-select v-model="authType" placeholder="选择认证方式" style="width: 150px" @change="handleAuthTypeChange">
          <el-option label="无" value="none" />
          <el-option label="Basic" value="basic" />
          <el-option label="Bearer" value="bearer" />
          <el-option label="API Key" value="apikey" />
        </el-select>
        <div v-if="authType === 'basic'" class="auth-fields">
          <el-input v-model="formData.auth_config.username" placeholder="用户名" size="small" />
          <el-input v-model="formData.auth_config.password" placeholder="密码" size="small" type="password" />
        </div>
        <div v-if="authType === 'bearer'" class="auth-fields">
          <el-input v-model="formData.auth_config.token" placeholder="Token" size="small" />
        </div>
        <div v-if="authType === 'apikey'" class="auth-fields">
          <el-input v-model="formData.auth_config.key" placeholder="Key" size="small" />
          <el-input v-model="formData.auth_config.value" placeholder="Value" size="small" />
          <el-select v-model="formData.auth_config.add_to" placeholder="添加位置" size="small">
            <el-option label="Header" value="header" />
            <el-option label="Query" value="query" />
          </el-select>
        </div>
      </el-form-item>

      <el-form-item label="期望状态码">
        <el-input-number v-model="formData.expected_status" :min="100" :max="599" />
      </el-form-item>

      <el-form-item label="断言规则">
        <div class="assertions-list">
          <div v-for="(assert, index) in formData.assertions" :key="index" class="assert-row">
            <el-select v-model="assert.field" placeholder="字段" size="small" style="width: 120px">
              <el-option label="status" value="status" />
              <el-option label="body" value="body" />
              <el-option label="header" value="header" />
            </el-select>
            <el-select v-model="assert.operator" placeholder="操作符" size="small" style="width: 100px">
              <el-option label="equals" value="equals" />
              <el-option label="contains" value="contains" />
              <el-option label="startsWith" value="startsWith" />
              <el-option label="endsWith" value="endsWith" />
              <el-option label="matches" value="matches" />
            </el-select>
            <el-input v-model="assert.expected" placeholder="期望值" size="small" style="flex: 1" />
            <el-button type="danger" :icon="Delete" size="small" @click="removeAssert(index)" />
          </div>
          <el-button :icon="Plus" size="small" @click="addAssert">添加断言</el-button>
        </div>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Plus, Delete } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue'])

const methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
const authType = ref('none')

// 双输入模式控制
const headersInputMode = ref('row')
const paramsInputMode = ref('row')
const headersJson = ref('')
const paramsJson = ref('')
const headersJsonError = ref('')
const paramsJsonError = ref('')

const formData = ref({
  method: 'GET',
  url: '',
  headers: [],
  params: [],
  body_type: 'none',
  body: '',
  auth_config: {},
  expected_status: 200,
  assertions: [],
})

function addHeader() {
  formData.value.headers.push({ key: '', value: '' })
}

function removeHeader(index) {
  formData.value.headers.splice(index, 1)
}

function addParam() {
  formData.value.params.push({ key: '', value: '' })
}

function removeParam(index) {
  formData.value.params.splice(index, 1)
}

function addAssert() {
  formData.value.assertions.push({ field: 'status', operator: 'equals', expected: '' })
}

function removeAssert(index) {
  formData.value.assertions.splice(index, 1)
}

function handleAuthTypeChange(type) {
  if (type === 'none') {
    formData.value.auth_config = {}
  }
}

function parseHeadersJson() {
  if (!headersJson.value.trim()) {
    formData.value.headers = []
    headersJsonError.value = ''
    return
  }
  try {
    const parsed = JSON.parse(headersJson.value)
    if (typeof parsed === 'object' && parsed !== null) {
      formData.value.headers = Object.entries(parsed).map(([key, value]) => ({ key, value: String(value) }))
      headersJsonError.value = ''
    } else {
      headersJsonError.value = 'JSON 必须是对象格式'
    }
  } catch {
    headersJsonError.value = 'JSON 格式错误'
  }
}

function parseParamsJson() {
  if (!paramsJson.value.trim()) {
    formData.value.params = []
    paramsJsonError.value = ''
    return
  }
  try {
    const parsed = JSON.parse(paramsJson.value)
    if (typeof parsed === 'object' && parsed !== null) {
      formData.value.params = Object.entries(parsed).map(([key, value]) => ({ key, value: String(value) }))
      paramsJsonError.value = ''
    } else {
      paramsJsonError.value = 'JSON 必须是对象格式'
    }
  } catch {
    paramsJsonError.value = 'JSON 格式错误'
  }
}

function updateHeadersJson() {
  if (headersInputMode.value === 'json') {
    const obj = {}
    formData.value.headers.forEach(item => {
      if (item.key) obj[item.key] = item.value
    })
    headersJson.value = JSON.stringify(obj, null, 2)
  }
}

function updateParamsJson() {
  if (paramsInputMode.value === 'json') {
    const obj = {}
    formData.value.params.forEach(item => {
      if (item.key) obj[item.key] = item.value
    })
    paramsJson.value = JSON.stringify(obj, null, 2)
  }
}

watch(() => props.modelValue, (val) => {
  if (val) {
    formData.value = { ...formData.value, ...val }
    // Parse auth type from auth_config
    if (val.auth_config) {
      if (val.auth_config.type) {
        authType.value = val.auth_config.type
      } else if (val.auth_config.username !== undefined) {
        authType.value = 'basic'
      } else if (val.auth_config.token !== undefined) {
        authType.value = 'bearer'
      } else if (val.auth_config.key !== undefined) {
        authType.value = 'apikey'
      } else {
        authType.value = 'none'
      }
    }
    // Initialize JSON from headers/params
    if (val.headers && Array.isArray(val.headers)) {
      const obj = {}
      val.headers.forEach(item => { if (item.key) obj[item.key] = item.value })
      headersJson.value = JSON.stringify(obj, null, 2)
    }
    if (val.params && Array.isArray(val.params)) {
      const obj = {}
      val.params.forEach(item => { if (item.key) obj[item.key] = item.value })
      paramsJson.value = JSON.stringify(obj, null, 2)
    }
  }
}, { immediate: true })

// Watch row data changes to update JSON when in JSON mode
watch(() => formData.value.headers, () => {
  updateHeadersJson()
}, { deep: true })

watch(() => formData.value.params, () => {
  updateParamsJson()
}, { deep: true })

watch(formData, (val) => {
  emit('update:modelValue', val)
}, { deep: true })
</script>

<style scoped>
.api-case-form {
  padding: 16px;
}

.kv-editor {
  width: 100%;
}

.input-mode-toggle {
  margin-bottom: 8px;
}

.json-editor {
  width: 100%;
}

.json-error {
  color: var(--el-color-danger);
  font-size: 12px;
  margin-top: 4px;
}

.kv-row {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  align-items: center;
}

.kv-row .el-input {
  flex: 1;
}

.auth-fields {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.assertions-list {
  width: 100%;
}

.assert-row {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  align-items: center;
}

.assert-row .el-input {
  flex: 1;
}
</style>