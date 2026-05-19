<template>
  <div class="response-info-viewer">
    <div class="info-section">
      <div class="info-row">
        <span class="info-label">请求ID</span>
        <span class="info-value">{{ requestId || '-' }}</span>
      </div>
      <div class="info-row">
        <span class="info-label">响应时间</span>
        <span class="info-value">{{ response.duration_ms }}ms</span>
      </div>
      <div class="info-row">
        <span class="info-label">响应大小</span>
        <span class="info-value">{{ formatSize(response.response_body) }}</span>
      </div>
      <div class="info-row">
        <span class="info-label">状态码</span>
        <span class="info-value" :class="getStatusClass(response.status_code)">
          {{ response.status_code }} {{ getStatusText(response.status_code) }}
        </span>
      </div>
      <div class="info-row">
        <span class="info-label">内容类型</span>
        <span class="info-value">{{ getContentType(response.response_headers) }}</span>
      </div>
      <div v-if="response.error_message" class="info-row">
        <span class="info-label">错误信息</span>
        <span class="info-value error">{{ response.error_message }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  response: { type: Object, default: () => ({}) },
  requestId: { type: [Number, String], default: null },
})

function formatSize(body) {
  if (!body) return '-'
  const bytes = new Blob([body]).size
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function getStatusClass(code) {
  if (!code) return ''
  if (code >= 200 && code < 300) return 'success'
  if (code >= 400 && code < 500) return 'warning'
  if (code >= 500) return 'danger'
  return ''
}

function getStatusText(code) {
  const map = {
    0: 'Request Error',
    200: 'OK',
    201: 'Created',
    204: 'No Content',
    400: 'Bad Request',
    401: 'Unauthorized',
    403: 'Forbidden',
    404: 'Not Found',
    422: 'Unprocessable',
    500: 'Server Error',
    502: 'Bad Gateway',
    503: 'Unavailable',
  }
  return map[code] || ''
}

function getContentType(headers) {
  if (!headers) return '-'
  return headers['content-type'] || headers['Content-Type'] || '-'
}
</script>

<style scoped>
.response-info-viewer {
  padding: 14px 16px;
}

.info-section {
  display: flex;
  flex-direction: column;
}

.info-row {
  display: flex;
  padding: 10px 0;
  border-bottom: 1px solid var(--border-color-lighter);
  font-size: 13px;
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  width: 110px;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.info-value {
  color: var(--text-strong);
  font-family: var(--font-mono);
}

.info-value.success { color: var(--el-color-success); }
.info-value.warning { color: var(--el-color-warning); }
.info-value.danger { color: var(--el-color-danger); }
.info-value.error { color: var(--el-color-danger); }
</style>

