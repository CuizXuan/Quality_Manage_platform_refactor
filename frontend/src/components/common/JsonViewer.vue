<template>
  <div class="json-viewer">
    <div class="viewer-toolbar">
      <div class="toolbar-left">
        <span class="viewer-title">{{ title }}</span>
        <span v-if="size" class="viewer-size">{{ size }}</span>
      </div>
      <div class="toolbar-right">
        <button @click="toggleFormat" :class="{ active: formatted }" title="格式化/原始">
          {{ formatted ? '📐 格式化' : '📄 原始' }}
        </button>
        <button @click="copyContent" title="复制">📋 复制</button>
        <button @click="downloadContent" title="下载">⬇ 下载</button>
        <button v-if="searchable" @click="toggleSearch" :class="{ active: showSearch }" title="搜索">
          🔍 搜索
        </button>
      </div>
    </div>

    <!-- 搜索框 -->
    <div v-if="showSearch" class="search-bar">
      <input
        v-model="searchKeyword"
        placeholder="搜索..."
        class="search-input"
        ref="searchInput"
        @input="handleSearch"
      />
      <span v-if="searchResult" class="search-result">{{ searchResult }}</span>
      <button class="btn-nav" @click="prevMatch" :disabled="!hasPrev">▲</button>
      <button class="btn-nav" @click="nextMatch" :disabled="!hasNext">▼</button>
    </div>

    <!-- JSON 内容 -->
    <div class="viewer-content" ref="viewerRef">
      <pre v-if="parsed" class="json-content" :class="{ 'line-numbers': showLineNumbers }"><code ref="codeRef" v-html="highlightedJson"></code></pre>
      <pre v-else class="json-content plain">{{ displayContent }}</pre>
    </div>

    <!-- 语法高亮样式 -->
    <div v-if="expandable && hasChildren" class="expand-controls">
      <button @click="expandAll" class="btn-expand">展开全部</button>
      <button @click="collapseAll" class="btn-expand">折叠全部</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'

const props = defineProps({
  data: {
    type: [String, Object, Array],
    default: null
  },
  title: {
    type: String,
    default: 'JSON'
  },
  formatted: {
    type: Boolean,
    default: true
  },
  showLineNumbers: {
    type: Boolean,
    default: true
  },
  searchable: {
    type: Boolean,
    default: true
  },
  expandable: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:formatted'])

const content = ref('')
const parsed = ref(false)
const hasChildren = ref(false)
const showSearch = ref(false)
const searchKeyword = ref('')
const searchResult = ref('')
const currentMatchIndex = ref(0)
const searchMatches = ref([])
const viewerRef = ref(null)
const codeRef = ref(null)

// 解析数据
watch(() => props.data, (val) => {
  if (typeof val === 'string') {
    content.value = val
    try {
      const parsedObj = JSON.parse(val)
      content.value = JSON.stringify(parsedObj, null, 2)
      parsed.value = true
      checkHasChildren(parsedObj)
    } catch (e) {
      parsed.value = false
      hasChildren.value = false
    }
  } else if (typeof val === 'object' && val !== null) {
    content.value = JSON.stringify(val, null, 2)
    parsed.value = true
    checkHasChildren(val)
  } else {
    content.value = String(val || '')
    parsed.value = false
    hasChildren.value = false
  }
}, { immediate: true })

function checkHasChildren(obj) {
  hasChildren.value = typeof obj === 'object' && obj !== null && Object.keys(obj).length > 0
}

// 显示内容
const displayContent = computed(() => {
  if (props.formatted && parsed.value) {
    return content.value
  }
  return content.value
})

// 格式化后的大小
const size = computed(() => {
  const str = typeof props.data === 'string' ? props.data : JSON.stringify(props.data)
  const bytes = new Blob([str]).size
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(1) + ' MB'
})

// JSON 语法高亮
const highlightedJson = computed(() => {
  if (!parsed.value) return escapeHtml(content.value)

  try {
    return syntaxHighlight(content.value)
  } catch (e) {
    return escapeHtml(content.value)
  }
})

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function syntaxHighlight(json) {
  // 先 escape HTML
  json = escapeHtml(json)

  // 高亮规则
  json = json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, (match) => {
    let cls = 'json-number'
    if (/^"/.test(match)) {
      if (/:$/.test(match)) {
        cls = 'json-key'
        match = match.slice(0, -1) // 移除冒号，稍后加回去
        return `<span class="${cls}">${match}</span>:`
      } else {
        cls = 'json-string'
      }
    } else if (/true|false/.test(match)) {
      cls = 'json-boolean'
    } else if (/null/.test(match)) {
      cls = 'json-null'
    }
    return `<span class="${cls}">${match}</span>`
  })

  // 高亮括号
  json = json
    .replace(/([{}\[\]])/g, '<span class="json-bracket">$1</span>')

  return json
}

// 格式化切换
function toggleFormat() {
  emit('update:formatted', !props.formatted)
}

// 复制
function copyContent() {
  const text = typeof props.data === 'string' ? props.data : JSON.stringify(props.data, null, 2)
  navigator.clipboard.writeText(text)
}

// 下载
function downloadContent() {
  const text = typeof props.data === 'string' ? props.data : JSON.stringify(props.data, null, 2)
  const blob = new Blob([text], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `response-${Date.now()}.json`
  a.click()
  URL.revokeObjectURL(url)
}

// 搜索
function toggleSearch() {
  showSearch.value = !showSearch.value
  if (showSearch.value) {
    nextTick(() => {
      viewerRef.value?.querySelector('.search-input')?.focus()
    })
  }
}

function handleSearch() {
  const keyword = searchKeyword.value.trim()
  if (!keyword) {
    searchMatches.value = []
    searchResult.value = ''
    return
  }

  const contentEl = viewerRef.value?.querySelector('.json-content')
  if (!contentEl) return

  // 获取纯文本进行搜索
  const text = content.value
  const regex = new RegExp(escapeRegExp(keyword), 'gi')
  const matches = []
  let match
  while ((match = regex.exec(text)) !== null) {
    matches.push(match.index)
  }

  searchMatches.value = matches
  currentMatchIndex.value = 0

  if (matches.length > 0) {
    searchResult.value = `${currentMatchIndex.value + 1} / ${matches.length}`
    scrollToMatch(matches[0], keyword.length)
  } else {
    searchResult.value = '无匹配'
  }
}

function escapeRegExp(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function scrollToMatch(index, length) {
  // 简化实现：滚动到顶部
  if (viewerRef.value) {
    viewerRef.value.scrollTop = 0
  }
}

function prevMatch() {
  if (currentMatchIndex.value > 0) {
    currentMatchIndex.value--
    searchResult.value = `${currentMatchIndex.value + 1} / ${searchMatches.value.length}`
  }
}

function nextMatch() {
  if (currentMatchIndex.value < searchMatches.value.length - 1) {
    currentMatchIndex.value++
    searchResult.value = `${currentMatchIndex.value + 1} / ${searchMatches.value.length}`
  }
}

const hasPrev = computed(() => currentMatchIndex.value > 0)
const hasNext = computed(() => currentMatchIndex.value < searchMatches.value.length - 1)

// 展开/折叠
function expandAll() {
  // TODO: 实现展开/折叠功能
}

function collapseAll() {
  // TODO: 实现展开/折叠功能
}
</script>

<style scoped>
.json-viewer {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border);
  border-radius: 6px;
  overflow: hidden;
  background: var(--bg);
}

.viewer-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.viewer-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text);
}

.viewer-size {
  font-size: 11px;
  color: var(--text-secondary);
  background: var(--bg);
  padding: 2px 6px;
  border-radius: 3px;
}

.toolbar-right {
  display: flex;
  gap: 6px;
}

.toolbar-right button {
  padding: 4px 8px;
  background: var(--bg);
  border: 1px solid var(--border);
  color: var(--text);
  border-radius: 4px;
  font-size: 11px;
  cursor: pointer;
}

.toolbar-right button:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.toolbar-right button.active {
  background: var(--primary);
  border-color: var(--primary);
  color: #fff;
}

.search-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: var(--bg);
  border-bottom: 1px solid var(--border);
}

.search-input {
  flex: 1;
  padding: 4px 8px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--bg-secondary);
  color: var(--text);
  font-size: 12px;
}

.search-result {
  font-size: 11px;
  color: var(--text-secondary);
  white-space: nowrap;
}

.btn-nav {
  padding: 2px 6px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  color: var(--text);
  border-radius: 3px;
  font-size: 10px;
  cursor: pointer;
}

.btn-nav:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.viewer-content {
  flex: 1;
  overflow: auto;
  max-height: 400px;
}

.json-content {
  margin: 0;
  padding: 12px;
  font-family: var(--mono);
  font-size: 12px;
  line-height: 1.6;
  color: var(--text-h);
  white-space: pre-wrap;
  word-break: break-all;
}

.json-content.plain {
  color: var(--text);
}

.json-content code {
  display: block;
}

/* JSON 语法高亮 */
:deep(.json-key) {
  color: #9cdcfe;
}

:deep(.json-string) {
  color: #ce9178;
}

:deep(.json-number) {
  color: #b5cea8;
}

:deep(.json-boolean) {
  color: #569cd6;
}

:deep(.json-null) {
  color: #569cd6;
}

:deep(.json-bracket) {
  color: #ffd700;
}

.expand-controls {
  display: flex;
  gap: 8px;
  padding: 8px 12px;
  border-top: 1px solid var(--border);
}

.btn-expand {
  padding: 4px 10px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  color: var(--text);
  border-radius: 4px;
  font-size: 11px;
  cursor: pointer;
}

.btn-expand:hover {
  border-color: var(--primary);
  color: var(--primary);
}
</style>
