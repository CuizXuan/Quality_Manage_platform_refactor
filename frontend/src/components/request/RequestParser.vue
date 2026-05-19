<template>
  <div class="request-parser panel">
    <div class="parser-header" @click="expanded = !expanded">
      <span class="parser-title">📋 请求解析器</span>
      <span class="parser-toggle">{{ expanded ? '收起 ▲' : '展开 ▼' }}</span>
    </div>
    <div v-show="expanded" class="parser-body">
      <div class="parser-tabs">
        <button
          v-for="fmt in formats"
          :key="fmt.value"
          :class="{ active: selectedFormat === fmt.value }"
          @click="selectedFormat = fmt.value"
        >
          {{ fmt.label }}
        </button>
      </div>
      <div class="parser-input-area">
        <textarea
          v-model="rawInput"
          :placeholder="placeholderText"
          class="parser-textarea"
          ref="textareaRef"
          @keydown.meta.enter="parse"
          @keydown.ctrl.enter="parse"
        ></textarea>
      </div>
      <div v-if="errorMsg" class="parser-error">❌ {{ errorMsg }}</div>
      <div class="parser-actions">
        <button class="btn-secondary" @click="clear">清空</button>
        <button class="btn-secondary" @click="runDemo">✨ 示例演示</button>
        <button class="btn-primary" @click="parse" :disabled="!rawInput.trim()">
          ✨ 智能解析
        </button>
      </div>
      <div class="parser-hint">
        支持粘贴 cURL 或 Fetch 格式，自动识别并解析
      </div>
      <div v-if="demoToast" class="demo-toast">
        <pre>{{ demoToast }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { parseRequest, detectFormat } from '../../utils/parser'
import { useRequestStore } from '../../stores/request'

const emit = defineEmits(['parsed'])
const requestStore = useRequestStore()

const expanded = ref(true)
const selectedFormat = ref('auto')
const rawInput = ref('')
const errorMsg = ref('')
const textareaRef = ref(null)
const demoToast = ref('')

const formats = [
  { label: '自动', value: 'auto' },
  { label: 'cURL', value: 'curl' },
  { label: 'Fetch', value: 'fetch' },
]

const placeholders = {
  curl: `curl -X POST https://api.example.com/users \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer xxx" \\
  -d '{"name":"test","email":"test@example.com"}'`,
  fetch: `fetch('https://api.example.com/users', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer xxx'
  },
  body: JSON.stringify({ name: 'test' })
})`,
  auto: `粘贴 cURL 或 Fetch 命令...\n\n示例 cURL:\ncurl -X POST https://api.example.com/login \\\n  -H "Content-Type: application/json" \\\n  -d '{"username":"admin","password":"123456"}'`,
}

const placeholderText = '粘贴 cURL 或 Fetch 命令，例如：curl -X POST https://api.example.com/login -H "Content-Type: application/json" -d "{\"username\":\"admin\",\"password\":\"123456\"}"'


function parse() {
  errorMsg.value = ''
  const input = rawInput.value.trim()
  if (!input) {
    errorMsg.value = '请先输入 cURL 或 Fetch 命令'
    return
  }

  console.log('[Parser] 开始解析, input:', input.substring(0, 100))
  try {
    const result = parseRequest(input)
    console.log('[Parser] 解析结果:', result)
    requestStore.setRequest(result)
    emit('parsed', result)
  } catch (e) {
    console.error('[Parser] 解析失败:', e)
    errorMsg.value = e.message
  }
}

// 示例演示：解析示例命令，只展示结果，不覆盖用户输入
function runDemo() {
  const sample = 'curl -X POST https://httpbin.org/post -H "Content-Type: application/json" -d "name=test"'
  try {
    const result = parseRequest(sample)
    const lines = [
      `✅ 解析成功`,
      `Method: ${result.method}`,
      `URL: ${result.url}`,
      result.headers && Object.keys(result.headers).length
        ? `Headers: ${JSON.stringify(result.headers)}`
        : null,
      result.body ? `Body: ${result.body}` : null,
    ].filter(Boolean)
    demoToast.value = lines.join('\n')
    setTimeout(() => { demoToast.value = '' }, 4000)
  } catch (e) {
    demoToast.value = `❌ 解析失败: ${e.message}`
    setTimeout(() => { demoToast.value = '' }, 4000)
  }
}

function clear() {
  rawInput.value = ''
  errorMsg.value = ''
  requestStore.resetRequest()
}
</script>

<style scoped>
.request-parser {
  margin-bottom: 12px;
  overflow: hidden;
}

/* 禁用 panel 角落装饰 */
.request-parser::before,
.request-parser::after {
  display: none;
}
.parser-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  cursor: pointer;
  user-select: none;
}
.parser-title {
  font-size: 13px;
  font-weight: 500;
}
.parser-toggle {
  font-size: 11px;
  color: var(--text);
}
.parser-body {
  padding: 0 16px 16px;
}
.parser-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 8px;
}
.parser-tabs button {
  padding: 4px 12px;
  background: var(--social-bg);
  border: 1px solid var(--border);
  color: var(--text);
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}
.parser-tabs button.active {
  background: var(--bg-secondary);
  border-color: var(--primary);
  color: var(--primary);
}
.parser-input-area {
  margin-bottom: 8px;
}
.parser-textarea {
  width: 100%;
  height: 120px;
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
.parser-error {
  color: var(--danger);
  font-size: 12px;
  margin-bottom: 8px;
  padding: 6px 10px;
  background: rgba(239, 68, 68, 0.1);
  border-radius: 4px;
}
.parser-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-bottom: 8px;
}
.parser-hint {
  font-size: 11px;
  color: var(--text);
}
.demo-toast {
  position: fixed;
  bottom: 80px;
  right: 24px;
  z-index: 9999;
  background: var(--bg-secondary);
  border: 1px solid var(--primary);
  border-radius: 8px;
  padding: 12px 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  max-width: 360px;
  animation: toastIn 0.2s ease;
}
.demo-toast pre {
  margin: 0;
  font-family: var(--mono);
  font-size: 12px;
  color: var(--text-h);
  white-space: pre-wrap;
  line-height: 1.6;
}
@keyframes toastIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
