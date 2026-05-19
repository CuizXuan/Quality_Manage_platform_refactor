<template>
  <div class="terminal-quick-debug">
    <div class="quick-url-bar">
      <el-select v-model="method" class="method-select">
        <el-option v-for="m in methods" :key="m" :label="m" :value="m" />
      </el-select>
      <el-input
        v-model="url"
        placeholder="粘贴 curl/fetch 或输入 URL"
        @paste="handlePaste"
        @keyup.enter="handleSend"
      />
      <el-button type="primary" :loading="sending" @click="handleSend">发送</el-button>
    </div>

    <div v-if="parseInfo" class="parse-info">
      <el-icon><InfoFilled /></el-icon>
      <span>已解析 {{ parseInfo.type }}：{{ parseInfo.summary }}</span>
      <el-button size="small" text @click="clearParse">清除</el-button>
    </div>

    <div v-if="quickResult" class="quick-result">
      <el-tag :type="getStatusType(quickResult.status_code)" effect="dark" size="small">
        {{ quickResult.status_code || 'ERR' }}
      </el-tag>
      <span class="result-duration">{{ quickResult.duration_ms }}ms</span>
      <span class="result-size">{{ formatSize(quickResult.response_body) }}</span>
    </div>

    <div class="quick-actions">
      <el-button size="small" text @click="openTerminal">打开完整调试台</el-button>
    </div>
  </div>
</template>

<script setup>
import { InfoFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { terminalApi } from '@/api/terminal'
import { parseRequest } from '@/utils/requestParser'

const router = useRouter()
const methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']

const method = ref('GET')
const url = ref('')
const sending = ref(false)
const parseInfo = ref(null)
const quickResult = ref(null)

function handlePaste(e) {
  const text = e.clipboardData.getData('text')
  if (!text) return
  if (text.startsWith('curl ') || text.startsWith('fetch(') || text.includes('XMLHttpRequest') || text.startsWith('http')) {
    e.preventDefault()
    const parsed = parseRequest(text)
    if (parsed.url) {
      method.value = parsed.method
      url.value = parsed.url
      const headerCount = parsed.headers?.length || 0
      parseInfo.value = {
        type: parsed.sourceType === 'curl' ? 'cURL' : parsed.sourceType === 'fetch' ? 'Fetch' : 'URL',
        summary: `${headerCount} 个请求头${parsed.body ? `, ${parsed.bodyType} body` : ''}`,
      }
      if (parsed.warnings?.length) {
        parseInfo.value.summary += `, ${parsed.warnings.length} 个警告`
      }
      ElMessage.success(`已解析 ${parseInfo.value.type} 请求`)
    }
  }
}

function clearParse() {
  parseInfo.value = null
}

async function handleSend() {
  if (!url.value) {
    ElMessage.warning('请输入 URL')
    return
  }
  sending.value = true
  quickResult.value = null
  try {
    const res = await terminalApi.debug({ method: method.value, url: url.value, headers: {}, query_params: {} })
    quickResult.value = res.data.latest_result
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '请求失败')
  } finally {
    sending.value = false
  }
}

function openTerminal() {
  router.push('/terminal')
}

function getStatusType(code) {
  if (!code) return 'info'
  if (code >= 200 && code < 300) return 'success'
  if (code >= 400 && code < 500) return 'warning'
  if (code >= 500) return 'danger'
  return 'info'
}

function formatSize(body) {
  if (!body) return ''
  const bytes = new Blob([body]).size
  if (bytes < 1024) return `${bytes}B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`
  return `${(bytes / 1024 / 1024).toFixed(1)}MB`
}
</script>

<style scoped>
.terminal-quick-debug {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.quick-url-bar {
  display: flex;
  gap: 8px;
  align-items: center;
}

.method-select {
  width: 90px;
  flex-shrink: 0;
}

.quick-url-bar .el-input {
  flex: 1;
}

.parse-info {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: var(--el-color-primary-light-9);
  border-radius: 4px;
  font-size: 12px;
  color: var(--el-color-primary);
}

.parse-info .el-button {
  margin-left: auto;
}

.quick-result {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  font-size: 13px;
}

.result-duration,
.result-size {
  color: var(--el-text-color-secondary);
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
}

.quick-actions {
  display: flex;
  justify-content: flex-end;
}
</style>