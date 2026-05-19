<template>
  <div class="body-editor">
    <div class="body-type-tabs">
      <button
        v-for="t in bodyTypes"
        :key="t.value"
        :class="{ active: activeType === t.value }"
        @click="activeType = t.value"
      >
        {{ t.label }}
      </button>
    </div>
    <div v-if="activeType !== 'none'" class="body-content">
      <div v-if="activeType === 'json'" class="json-editor">
        <div class="editor-toolbar">
          <button @click="formatJson" title="格式化">📐 格式化</button>
          <button @click="compressJson" title="压缩">🗜 压缩</button>
          <button @click="copyJson" title="复制">📋 复制</button>
        </div>
        <textarea
          v-model="content"
          class="json-textarea"
          placeholder='{"key": "value"}'
          @input="emitUpdate"
        ></textarea>
      </div>
      <KeyValueTable
        v-else
        :modelValue="formData"
        @update:modelValue="handleFormUpdate"
      />
    </div>
    <div v-else class="body-empty">
      此请求没有 Body（GET/HEAD/OPTIONS 等方法通常不需要）
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import KeyValueTable from './KeyValueTable.vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue', 'update:type'])

const bodyTypes = [
  { label: 'none', value: 'none' },
  { label: 'JSON', value: 'json' },
  { label: 'Form Data', value: 'form-data' },
  { label: 'x-www-form', value: 'x-www-form-urlencoded' },
  { label: 'Raw', value: 'raw' },
]

const activeType = ref('none')
const content = ref(props.modelValue || '')
const formData = ref([{ key: '', value: '', enabled: true }])

watch(
  () => props.modelValue,
  (val) => {
    content.value = val || ''
  }
)

watch(activeType, (val) => {
  emit('update:type', val)
  if (val === 'json' && content.value && !content.value.startsWith('{')) {
    // 尝试解析现有 body 为 JSON
    try {
      content.value = JSON.stringify(JSON.parse(content.value), null, 2)
    } catch (e) {
      // ignore
    }
  }
})

function emitUpdate() {
  emit('update:modelValue', content.value)
}

function handleFormUpdate(val) {
  formData.value = val
  // 转换为 URLSearchParams 格式
  const params = new URLSearchParams()
  val.forEach(item => {
    if (item.key.trim()) {
      params.append(item.key, item.value)
    }
  })
  emit('update:modelValue', params.toString())
}

function formatJson() {
  try {
    content.value = JSON.stringify(JSON.parse(content.value), null, 2)
    emitUpdate()
  } catch (e) {
    alert('JSON 格式错误')
  }
}

function compressJson() {
  try {
    content.value = JSON.stringify(JSON.parse(content.value))
    emitUpdate()
  } catch (e) {
    alert('JSON 格式错误')
  }
}

function copyJson() {
  navigator.clipboard.writeText(content.value)
}
</script>

<style scoped>
.body-editor {
  min-height: 200px;
}
.body-type-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 12px;
  border-bottom: 1px solid var(--border);
  padding-bottom: 8px;
}
.body-type-tabs button {
  padding: 4px 12px;
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text);
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}
.body-type-tabs button.active {
  background: var(--bg-secondary);
  border-color: var(--primary);
  color: var(--primary);
}
.editor-toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}
.editor-toolbar button {
  padding: 4px 10px;
  background: var(--social-bg);
  border: 1px solid var(--border);
  color: var(--text);
  border-radius: 4px;
  font-size: 11px;
  cursor: pointer;
}
.editor-toolbar button:hover {
  border-color: var(--primary);
  color: var(--primary);
}
.json-textarea {
  width: 100%;
  height: 180px;
  resize: vertical;
  font-family: var(--mono);
  font-size: 12px;
  line-height: 1.5;
  padding: 10px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 4px;
  color: var(--text-h);
}
.body-empty {
  color: var(--text);
  font-size: 12px;
  padding: 20px;
  text-align: center;
}
</style>
