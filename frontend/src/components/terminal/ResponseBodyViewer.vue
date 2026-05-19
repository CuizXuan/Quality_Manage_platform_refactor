<template>
  <div class="response-body-viewer">
    <div class="viewer-toolbar">
      <el-input v-model="searchKeyword" size="small" placeholder="搜索响应内容" clearable style="width: 180px;" />
      <div class="toolbar-actions">
        <el-button size="small" text @click="toggleRaw">{{ showRaw ? '原始' : '格式化' }}</el-button>
        <el-button size="small" text @click="copyBody">复制</el-button>
      </div>
    </div>
    <div class="body-content">
      <pre ref="preRef">{{ showRaw ? rawBody : formattedJson }}</pre>
    </div>
    <div v-if="searchKeyword && highlightCount > 0" class="search-info">
      命中 {{ highlightCount }} 处
    </div>
  </div>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { computed, ref, watch } from 'vue'

const props = defineProps({
  body: { type: String, default: '' },
  contentType: { type: String, default: '' },
})

const searchKeyword = ref('')
const showRaw = ref(false)
const preRef = ref(null)
const highlightCount = ref(0)

const isJson = computed(() => {
  try {
    JSON.parse(props.body)
    return true
  } catch {
    return false
  }
})

const rawBody = computed(() => props.body || '')

const formattedJson = computed(() => {
  try {
    return JSON.stringify(JSON.parse(props.body), null, 2)
  } catch {
    return props.body
  }
})

watch(searchKeyword, (keyword) => {
  if (!keyword || !preRef.value) {
    highlightCount.value = 0
    return
  }
  const text = preRef.value.textContent || ''
  const regex = new RegExp(keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi')
  const matches = text.match(regex) || []
  highlightCount.value = matches.length
})

function toggleRaw() {
  showRaw.value = !showRaw.value
}

async function copyBody() {
  try {
    await navigator.clipboard.writeText(rawBody.value)
    ElMessage.success('已复制')
  } catch {
    ElMessage.error('复制失败')
  }
}
</script>

<style scoped>
.response-body-viewer {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.viewer-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 9px 12px;
  border-bottom: 1px solid var(--border-color-lighter);
  background: var(--bg-container);
}

.toolbar-actions {
  display: flex;
  gap: 4px;
}

.body-content {
  flex: 1;
  overflow: auto;
  padding: 14px 16px;
  background: var(--bg-container-soft);
  min-height: 0;
}

.body-content pre {
  font-family: var(--font-mono);
  font-size: 12px;
  line-height: 1.65;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
  color: var(--text-strong);
}

.search-info {
  padding: 6px 12px;
  font-size: 12px;
  color: var(--color-primary);
  background: var(--bg-container);
  border-top: 1px solid var(--border-color-lighter);
}
</style>

