<template>
  <div class="response-headers-viewer">
    <div class="viewer-toolbar">
      <el-input v-model="searchKeyword" size="small" placeholder="搜索" clearable style="width: 160px;" />
      <el-button size="small" text @click="copyHeaders">复制</el-button>
    </div>
    <div class="headers-list">
      <table class="headers-table">
        <tbody>
          <tr v-for="(value, key) in filteredHeaders" :key="key" class="header-row">
            <td class="header-key-cell">{{ key }}</td>
            <td class="header-value-cell">{{ value }}</td>
          </tr>
        </tbody>
      </table>
      <div v-if="Object.keys(filteredHeaders).length === 0" class="list-empty">
        {{ searchKeyword ? '无匹配' : '暂无响应头' }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { computed, ref } from 'vue'

const props = defineProps({
  headers: { type: Object, default: () => ({}) },
})

const searchKeyword = ref('')

const filteredHeaders = computed(() => {
  if (!searchKeyword.value) return props.headers
  const q = searchKeyword.value.toLowerCase()
  const result = {}
  Object.entries(props.headers).forEach(([key, value]) => {
    if (key.toLowerCase().includes(q) || value.toLowerCase().includes(q)) {
      result[key] = value
    }
  })
  return result
})

async function copyHeaders() {
  const text = Object.entries(props.headers).map(([k, v]) => `${k}: ${v}`).join('\n')
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制')
  } catch {
    ElMessage.error('复制失败')
  }
}
</script>

<style scoped>
.response-headers-viewer {
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

.headers-list {
  flex: 1;
  overflow: auto;
}

.headers-table {
  width: 100%;
  border-collapse: collapse;
}

.header-row {
  border-bottom: 1px solid var(--border-color-lighter);
}

.header-row:last-child {
  border-bottom: none;
}

.header-key-cell {
  padding: 10px 12px;
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--color-primary);
  font-weight: 750;
  width: 35%;
  vertical-align: top;
}

.header-value-cell {
  padding: 10px 12px;
  font-family: var(--font-mono);
  font-size: 12px;
  word-break: break-all;
  color: var(--text-strong);
}

.list-empty {
  padding: 24px;
  text-align: center;
  color: var(--text-secondary);
  font-size: 12px;
}
</style>

