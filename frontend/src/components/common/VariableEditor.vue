<template>
  <div class="variable-editor">
    <div class="editor-header">
      <span class="title">{{ title }}</span>
      <button class="btn-add" @click="addVariable" title="添加变量">+ 添加</button>
    </div>

    <!-- 变量列表 -->
    <div class="var-table">
      <div class="var-header">
        <span class="col-enable">启用</span>
        <span class="col-key">变量名</span>
        <span class="col-value">值</span>
        <span class="col-actions">操作</span>
      </div>

      <div v-if="variables.length === 0" class="var-empty">
        暂无变量，点击"添加"开始
      </div>

      <div
        v-for="(variable, index) in variables"
        :key="index"
        class="var-row"
        :class="{ disabled: !variable.enabled }"
      >
        <div class="col-enable">
          <input
            type="checkbox"
            :checked="variable.enabled"
            @change="toggleVariable(index)"
          />
        </div>
        <div class="col-key">
          <input
            v-model="variable.key"
            placeholder="variable_name"
            class="key-input"
            @input="onKeyChange(variable)"
          />
          <span v-if="variable.key" class="var-preview">/{{ variable.key }}/</span>
        </div>
        <div class="col-value">
          <input
            v-model="variable.value"
            placeholder="值"
            class="value-input"
          />
        </div>
        <div class="col-actions">
          <button class="icon-btn danger" @click="removeVariable(index)" title="删除">×</button>
        </div>
      </div>
    </div>

    <!-- 预览区域 -->
    <div v-if="showPreview && variables.length > 0" class="preview-section">
      <div class="preview-header">
        <span class="title">替换预览</span>
        <button class="btn-toggle" @click="showRawPreview = !showRawPreview">
          {{ showRawPreview ? '预览模式' : '原始模式' }}
        </button>
      </div>
      <div class="preview-content">
        <textarea
          v-if="showRawPreview"
          v-model="previewText"
          class="preview-textarea"
          placeholder="输入包含 {{variable}} 的文本..."
          @input="updatePreview"
        ></textarea>
        <div v-else class="preview-result">
          <pre class="preview-output">{{ previewResult || '在左侧输入包含变量的文本...' }}</pre>
        </div>
      </div>
    </div>

    <!-- 导入/导出 -->
    <div class="editor-footer">
      <button class="btn" @click="importVariables">📥 导入</button>
      <button class="btn" @click="exportVariables">📤 导出</button>
    </div>

    <!-- 导入弹窗 -->
    <div v-if="showImportModal" class="modal-overlay" @click.self="showImportModal = false">
      <div class="modal">
        <h3>导入变量</h3>
        <div class="form-group">
          <label>粘贴 JSON 格式变量</label>
          <textarea
            v-model="importText"
            class="import-textarea"
            placeholder='{"base_url": "http://localhost:8080", "api_key": "xxx"}'
          ></textarea>
        </div>
        <div class="form-actions">
          <button class="btn" @click="showImportModal = false">取消</button>
          <button class="btn primary" @click="confirmImport">导入</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  },
  title: {
    type: String,
    default: '环境变量'
  },
  showPreview: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

// 变量列表
const variables = ref([])

// 预览相关
const previewText = ref('')
const previewResult = ref('')
const showRawPreview = ref(false)

// 导入弹窗
const showImportModal = ref(false)
const importText = ref('')

// 初始化变量
function initVariables() {
  const vars = []
  for (const [key, value] of Object.entries(props.modelValue)) {
    vars.push({ key, value, enabled: true })
  }
  variables.value = vars
  updateModelValue()
}

// 添加变量
function addVariable() {
  variables.value.push({ key: '', value: '', enabled: true })
}

// 删除变量
function removeVariable(index) {
  variables.value.splice(index, 1)
  updateModelValue()
}

// 切换启用状态
function toggleVariable(index) {
  variables.value[index].enabled = !variables.value[index].enabled
  updateModelValue()
}

// Key 变化时
function onKeyChange(variable) {
  // 自动清理 key 中的非法字符
  variable.key = variable.key.replace(/[^a-zA-Z0-9_]/g, '_')
  updateModelValue()
}

// 更新父组件
function updateModelValue() {
  const obj = {}
  variables.value.forEach(v => {
    if (v.key.trim() && v.enabled) {
      obj[v.key] = v.value
    }
  })
  emit('update:modelValue', obj)
}

// 变量替换逻辑
function replaceVariables(text) {
  if (!text) return ''

  // 构建启用变量的 map
  const varMap = {}
  variables.value.forEach(v => {
    if (v.enabled && v.key) {
      varMap[v.key] = v.value
    }
  })

  // 替换 {{variable}} 格式
  return text.replace(/\{\{(\w+)\}\}/g, (match, varName) => {
    if (varMap.hasOwnProperty(varName)) {
      return varMap[varName]
    }
    return match // 未找到保持原样
  })
}

// 更新预览
function updatePreview() {
  previewResult.value = replaceVariables(previewText.value)
}

// 导入
function importVariables() {
  importText.value = ''
  showImportModal.value = true
}

function confirmImport() {
  try {
    const imported = JSON.parse(importText.value)
    for (const [key, value] of Object.entries(imported)) {
      const existing = variables.value.find(v => v.key === key)
      if (existing) {
        existing.value = value
      } else {
        variables.value.push({ key, value, enabled: true })
      }
    }
    updateModelValue()
    showImportModal.value = false
  } catch (e) {
    alert('JSON 格式错误: ' + e.message)
  }
}

// 导出
function exportVariables() {
  const obj = {}
  variables.value.forEach(v => {
    if (v.key.trim()) {
      obj[v.key] = v.value
    }
  })
  const json = JSON.stringify(obj, null, 2)
  navigator.clipboard.writeText(json).then(() => {
    alert('已复制到剪贴板')
  })
}

// 暴露方法给父组件
function setVariables(obj) {
  variables.value = []
  for (const [key, value] of Object.entries(obj || {})) {
    variables.value.push({ key, value, enabled: true })
  }
  updateModelValue()
}

function getVariables() {
  const obj = {}
  variables.value.forEach(v => {
    if (v.key.trim() && v.enabled) {
      obj[v.key] = v.value
    }
  })
  return obj
}

defineExpose({
  setVariables,
  getVariables,
})

// 监听外部值变化
watch(() => props.modelValue, () => {
  initVariables()
}, { immediate: true })
</script>

<style scoped>
.variable-editor {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
}

.btn-add {
  padding: 4px 10px;
  background: var(--primary);
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}

.var-table {
  border: 1px solid var(--border);
  border-radius: 6px;
  overflow: hidden;
}

.var-header {
  display: flex;
  padding: 8px 12px;
  background: var(--bg-secondary);
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
}

.var-empty {
  padding: 20px;
  text-align: center;
  color: var(--text-secondary);
  font-size: 12px;
}

.var-row {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border-top: 1px solid var(--border);
  gap: 8px;
}

.var-row.disabled {
  opacity: 0.5;
}

.col-enable {
  width: 40px;
  flex-shrink: 0;
}

.col-enable input {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.col-key {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  position: relative;
}

.col-value {
  flex: 2;
}

.col-actions {
  width: 40px;
  flex-shrink: 0;
}

.key-input,
.value-input {
  width: 100%;
  padding: 6px 8px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--bg-secondary);
  color: var(--text);
  font-size: 12px;
  box-sizing: border-box;
}

.key-input:focus,
.value-input:focus {
  outline: none;
  border-color: var(--primary);
}

.var-preview {
  font-size: 10px;
  color: var(--primary);
  font-family: var(--mono);
}

.icon-btn {
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 16px;
  cursor: pointer;
  border-radius: 4px;
}

.icon-btn.danger:hover {
  background: var(--bg-secondary);
  color: var(--danger);
}

.preview-section {
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 12px;
  background: var(--bg-secondary);
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.btn-toggle {
  padding: 4px 8px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--bg);
  color: var(--text);
  font-size: 11px;
  cursor: pointer;
}

.preview-textarea {
  width: 100%;
  min-height: 80px;
  padding: 8px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--bg);
  color: var(--text);
  font-family: var(--mono);
  font-size: 12px;
  resize: vertical;
  box-sizing: border-box;
}

.preview-result {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 8px;
  max-height: 120px;
  overflow: auto;
}

.preview-output {
  margin: 0;
  font-family: var(--mono);
  font-size: 12px;
  color: var(--text);
  white-space: pre-wrap;
  word-break: break-all;
}

.editor-footer {
  display: flex;
  gap: 8px;
}

.btn {
  padding: 6px 12px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--bg-secondary);
  color: var(--text);
  font-size: 12px;
  cursor: pointer;
}

.btn:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal {
  background: var(--bg);
  border-radius: 12px;
  padding: 20px;
  width: 480px;
  max-height: 80vh;
  overflow-y: auto;
}

.modal h3 {
  margin: 0 0 16px;
  font-size: 15px;
}

.form-group {
  margin-bottom: 12px;
}

.form-group label {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.import-textarea {
  width: 100%;
  min-height: 150px;
  padding: 8px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg-secondary);
  color: var(--text);
  font-family: var(--mono);
  font-size: 12px;
  resize: vertical;
  box-sizing: border-box;
}

.form-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-top: 16px;
}

.btn.primary {
  background: var(--primary);
  color: #fff;
  border-color: var(--primary);
}
</style>
