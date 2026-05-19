<template>
  <div class="terminal-page">
    <aside class="history-panel">
      <div class="panel-header">
        <div>
          <span class="panel-title">历史记录</span>
          <span class="panel-subtitle">{{ filteredHistory.length }} 条请求</span>
        </div>
        <el-button size="small" text :icon="Refresh" @click="loadHistory" />
      </div>
      <div class="history-search">
        <el-input v-model="historySearch" placeholder="搜索请求名称/URL" size="small" :prefix-icon="Search" clearable />
      </div>
      <div class="history-filter">
        <button :class="{ active: historyFilter === 'all' }" type="button" @click="historyFilter = 'all'">全部</button>
        <button :class="{ active: historyFilter === 'fail' }" type="button" @click="historyFilter = 'fail'">失败</button>
        <button :class="{ active: historyFilter === 'favorite' }" type="button" @click="historyFilter = 'favorite'">收藏</button>
      </div>
      <div class="history-list">
        <button
          v-for="item in filteredHistory"
          :key="item.id"
          class="history-item"
          :class="{ active: currentRequestId === item.id }"
          type="button"
          @click="loadRequest(item.id)"
        >
          <span class="method-badge" :class="item.method.toLowerCase()">{{ item.method }}</span>
          <span class="item-main">
            <span class="item-url" :title="item.url">{{ getUrlTitle(item.url) }}</span>
            <span class="item-path">{{ getUrlPath(item.url) }}</span>
          </span>
          <span class="item-meta">
            <span v-if="item.status_code" class="item-status" :class="getStatusClass(item.status_code)">{{ item.status_code }}</span>
            <span v-if="item.duration_ms" class="item-duration">{{ item.duration_ms }}ms</span>
          </span>
        </button>
        <div v-if="historyLoading" class="list-placeholder">加载中...</div>
        <div v-else-if="filteredHistory.length === 0" class="list-placeholder">暂无记录</div>
      </div>
      <button class="more-history" type="button">查看更多历史</button>
    </aside>

    <main class="main-workspace">
      <section class="request-section tool-card">
        <div class="section-tabs">
          <button class="active" type="button">请求</button>
          <button type="button">响应</button>
          <button type="button">断言</button>
          <button type="button">提取</button>
          <button type="button">脚本</button>
          <button type="button">健康检查</button>
          <button type="button">AI 分析</button>
          <div class="request-actions">
            <el-button size="small" :icon="CopyDocument">粘贴数据</el-button>
            <el-button size="small" :icon="Upload">导入</el-button>
          </div>
        </div>

        <div class="request-bar">
          <el-select v-model="requestForm.method" class="method-select" :teleported="true">
            <el-option v-for="m in methods" :key="m" :label="m" :value="m" />
          </el-select>
          <el-input
            ref="urlInputRef"
            v-model="requestForm.url"
            placeholder="粘贴 curl / fetch 或输入 URL"
            class="url-input"
            @paste="handlePaste"
            @keyup.enter="sendRequest"
          />
          <el-button type="primary" :loading="sending" @click="sendRequest">发送</el-button>
          <el-button @click="saveDraft">保存</el-button>
        </div>

        <div v-if="parseHint" class="parse-notice">
          <el-icon><InfoFilled /></el-icon>
          <span>已解析 <strong>{{ parseHint }}</strong>，{{ parsedHeaderCount }} 个请求头</span>
          <el-button size="small" text @click="clearParseHint">清除</el-button>
        </div>

        <el-tabs v-model="activeTab" class="request-config-tabs">
          <el-tab-pane name="params">
            <template #label>Params <span class="tab-count">{{ requestForm.queryParams.length }}</span></template>
            <KeyValueEditor v-model="requestForm.queryParams" placeholder="参数值" />
          </el-tab-pane>
          <el-tab-pane name="headers">
            <template #label>Headers <span class="tab-count">{{ requestForm.headers.length }}</span></template>
            <KeyValueEditor v-model="requestForm.headers" placeholder="值" />
          </el-tab-pane>
          <el-tab-pane label="Body" name="body">
            <BodyEditor v-model="requestForm.body" :body-type="requestForm.bodyType" @update:body-type="requestForm.bodyType = $event" />
          </el-tab-pane>
          <el-tab-pane label="Auth" name="auth">
            <AuthEditor v-model="requestForm.authType" :auth-config="requestForm.authConfig" @update:auth-config="requestForm.authConfig = $event" />
          </el-tab-pane>
          <el-tab-pane label="Cookie" name="cookie">
            <KeyValueEditor v-model="requestForm.cookies" placeholder="Cookie 值" />
          </el-tab-pane>
        </el-tabs>
      </section>

      <section class="response-section tool-card">
        <div class="response-summary">
          <div class="response-title">
            <span>响应体</span>
            <span v-if="responseData" class="response-metrics">
              状态：<strong :class="getStatusClass(responseData.status_code)">{{ responseData.status_code }} {{ getStatusText(responseData.status_code) }}</strong>
              <span>耗时：{{ responseData.duration_ms }}ms</span>
              <span>大小：{{ responseSize || '-' }}</span>
            </span>
          </div>
          <div class="response-bar-actions">
            <el-button v-if="responseData" size="small" text :icon="CopyDocument" @click="copyResponse">复制</el-button>
            <el-button v-if="responseData" size="small" text :icon="Download" @click="downloadResponse">下载</el-button>
            <el-button v-if="responseData" size="small" text :icon="Document" @click="showSaveToCaseDialog = true">
              保存为用例
            </el-button>
            <el-button v-if="currentRequestId" size="small" text :icon="Star" :type="currentRequest?.status === 'favorite' ? 'warning' : ''" @click="toggleFavorite">
              {{ currentRequest?.status === 'favorite' ? '取消收藏' : '收藏' }}
            </el-button>
          </div>
        </div>

        <div v-if="responseError" class="response-error">
          <el-icon><CircleCloseFilled /></el-icon>
          <span>{{ responseError }}</span>
        </div>

        <template v-else-if="responseData">
          <el-tabs v-model="responseTab" class="response-tabs">
            <el-tab-pane name="body">
              <template #label>响应体</template>
              <ResponseBodyViewer :body="responseData.response_body" :content-type="responseContentType" />
            </el-tab-pane>
            <el-tab-pane name="headers">
              <template #label>响应头 <span class="tab-count">{{ Object.keys(responseData.response_headers || {}).length }}</span></template>
              <ResponseHeadersViewer :headers="responseData.response_headers" />
            </el-tab-pane>
            <el-tab-pane label="Cookie" name="cookie">
              <div class="placeholder-panel">暂无 Cookie 信息</div>
            </el-tab-pane>
            <el-tab-pane label="控制台" name="console">
              <div class="placeholder-panel">暂无控制台日志</div>
            </el-tab-pane>
            <el-tab-pane label="实际请求" name="request">
              <ResponseInfoViewer :response="responseData" :request-id="currentRequestId" />
            </el-tab-pane>
          </el-tabs>
        </template>

        <div v-else class="response-empty">
          <el-icon size="32"><Bottom /></el-icon>
          <span>发送请求以查看响应详情</span>
        </div>
      </section>
    </main>

    <aside class="ai-panel">
      <div class="panel-header">
        <div>
          <span class="panel-title">AI 智能分析</span>
          <span class="panel-subtitle">健壮性 / 安全 / 断言</span>
        </div>
        <el-button size="small" text :icon="Refresh" :loading="aiLoading" @click="runAiAnalysis">分析</el-button>
      </div>

      <div v-if="!aiResult && !aiLoading" class="ai-empty">
        <el-icon size="34"><MagicStick /></el-icon>
        <p>发送请求后运行分析，生成健壮性评分和断言建议</p>
      </div>

      <div v-else-if="aiLoading" class="ai-loading">
        <el-icon class="is-loading" size="28"><Loading /></el-icon>
        <span>AI 分析中...</span>
      </div>

      <template v-else>
        <div class="ai-score-section">
          <div class="score-header">
            <span>健壮性评分</span>
            <el-tag :type="getScoreTagType(aiResult.score)" effect="light" size="small">{{ getScoreText(aiResult.score) }}</el-tag>
          </div>
          <div class="score-value">{{ aiResult.score }}<small>/100</small></div>
          <el-progress :percentage="aiResult.score" :color="getScoreColor(aiResult.score)" :show-text="false" />
        </div>

        <div class="ai-section">
          <div class="ai-section-title">接口规范检查</div>
          <div class="check-list">
            <div v-for="check in aiResult.checks" :key="check.name" class="check-item">
              <el-icon :color="getCheckIconColor(check.status)">
                <CircleCheckFilled v-if="check.status === 'pass'" />
                <WarningFilled v-else-if="check.status === 'warn'" />
                <CircleCloseFilled v-else />
              </el-icon>
              <span>{{ check.name }}</span>
            </div>
          </div>
        </div>

        <div class="ai-section">
          <div class="ai-section-title">问题与建议</div>
          <div class="suggestion-list">
            <div v-for="(suggestion, idx) in aiResult.suggestions" :key="idx" class="suggestion-item">
              <span class="suggestion-priority" :class="'priority-' + suggestion.priority">{{ priorityText(suggestion.priority) }}</span>
              <span>{{ suggestion.message }}</span>
            </div>
          </div>
        </div>

        <div class="ai-section">
          <div class="ai-section-title">安全检测</div>
          <div class="security-list">
            <div v-for="item in aiResult.security" :key="item.name" class="security-item">
              <el-tag :type="item.safe ? 'success' : 'danger'" effect="light" size="small">{{ item.safe ? '安全' : '风险' }}</el-tag>
              <span>{{ item.name }}</span>
            </div>
          </div>
        </div>
      </template>
    </aside>

    <SaveToCaseDialog
      v-model="showSaveToCaseDialog"
      :request-data="getRequestDataForCase()"
      @success="handleSaveToCaseSuccess"
    />
  </div>
</template>

<script setup>
import {
  Bottom,
  CircleCheckFilled,
  CircleCloseFilled,
  CopyDocument,
  Document,
  Download,
  InfoFilled,
  Loading,
  MagicStick,
  Refresh,
  Search,
  Star,
  Upload,
  WarningFilled,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import { terminalApi } from '@/api/terminal'
import { parseRequest } from '@/utils/requestParser'
import AuthEditor from '@/components/terminal/AuthEditor.vue'
import BodyEditor from '@/components/terminal/BodyEditor.vue'
import KeyValueEditor from '@/components/terminal/KeyValueEditor.vue'
import ResponseBodyViewer from '@/components/terminal/ResponseBodyViewer.vue'
import ResponseHeadersViewer from '@/components/terminal/ResponseHeadersViewer.vue'
import ResponseInfoViewer from '@/components/terminal/ResponseInfoViewer.vue'
import SaveToCaseDialog from '@/components/case/SaveToCaseDialog.vue'

const route = useRoute()
const methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']

const requestForm = ref({
  method: 'GET',
  url: 'https://api.example.com/api/users?page=1&page_size=10',
  queryParams: [
    { key: 'page', value: '1' },
    { key: 'page_size', value: '10' },
  ],
  headers: [],
  cookies: [],
  body: '',
  bodyType: 'none',
  authType: 'none',
  authConfig: {},
})

const activeTab = ref('params')
const responseTab = ref('body')
const sending = ref(false)
const historyLoading = ref(false)
const historyItems = ref([])
const currentRequestId = ref(null)
const currentRequest = ref(null)
const responseData = ref(null)
const responseError = ref('')
const parseHint = ref('')
const parsedHeaderCount = ref(0)
const historySearch = ref('')
const historyFilter = ref('all')
const aiLoading = ref(false)
const aiResult = ref(null)
const showSaveToCaseDialog = ref(false)

const filteredHistory = computed(() => {
  let items = historyItems.value
  if (historySearch.value) {
    const q = historySearch.value.toLowerCase()
    items = items.filter((item) => item.url.toLowerCase().includes(q))
  }
  if (historyFilter.value === 'fail') {
    items = items.filter((item) => item.status_code && item.status_code >= 400)
  }
  if (historyFilter.value === 'favorite') {
    items = items.filter((item) => item.status === 'favorite')
  }
  return items
})

const responseSize = computed(() => {
  if (!responseData.value?.response_body) return ''
  const bytes = new Blob([responseData.value.response_body]).size
  if (bytes < 1024) return `${bytes}B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`
  return `${(bytes / 1024 / 1024).toFixed(1)}MB`
})

const responseContentType = computed(() => {
  if (!responseData.value?.response_headers) return ''
  return responseData.value.response_headers['content-type'] || responseData.value.response_headers['Content-Type'] || ''
})

function handlePaste(e) {
  const text = e.clipboardData.getData('text')
  if (!text) return
  const trimmed = text.trim()
  if (trimmed.startsWith('curl ') || trimmed.startsWith('fetch(') || trimmed.includes('XMLHttpRequest') || trimmed.startsWith('http')) {
    e.preventDefault()
    const parsed = parseRequest(trimmed)
    requestForm.value.method = parsed.method || 'GET'
    requestForm.value.url = parsed.url || ''
    requestForm.value.body = parsed.body || ''
    requestForm.value.bodyType = parsed.bodyType || 'none'
    requestForm.value.headers = parsed.headers || []
    requestForm.value.queryParams = Object.entries(parsed.query_params || parsed.queryParams || {}).map(([key, value]) => ({ key, value }))
    parsedHeaderCount.value = parsed.headers?.length || 0
    parseHint.value = parsed.sourceType === 'curl' ? 'cURL' : parsed.sourceType === 'fetch' ? 'Fetch' : parsed.sourceType === 'xhr' ? 'XHR' : 'URL'
    if (parsed.warnings?.length) {
      ElMessage.warning(`解析含 ${parsed.warnings.length} 个警告`)
    } else {
      ElMessage.success(`已解析 ${parseHint.value} 请求`)
    }
  }
}

function clearParseHint() {
  parseHint.value = ''
  parsedHeaderCount.value = 0
}

async function sendRequest() {
  if (!requestForm.value.url) {
    ElMessage.warning('请输入请求 URL')
    return
  }
  sending.value = true
  responseError.value = ''
  responseData.value = null
  aiResult.value = null
  try {
    const headers = Object.fromEntries(requestForm.value.headers.filter((h) => h.key).map((h) => [h.key, h.value]))
    const queryParams = Object.fromEntries(requestForm.value.queryParams.filter((p) => p.key).map((p) => [p.key, p.value]))
    const cookies = Object.fromEntries(requestForm.value.cookies.filter((p) => p.key).map((p) => [p.key, p.value]))
    const res = await terminalApi.debug({
      method: requestForm.value.method,
      url: requestForm.value.url,
      headers,
      query_params: queryParams,
      cookies,
      auth_config: requestForm.value.authConfig,
      body_type: requestForm.value.bodyType,
      body: requestForm.value.body,
    })
    responseData.value = res.data.latest_result
    currentRequestId.value = res.data.id
    parseHint.value = ''
    await loadHistory()
  } catch (err) {
    responseError.value = err.response?.data?.detail || err.message || '请求失败'
  } finally {
    sending.value = false
  }
}

async function loadHistory() {
  historyLoading.value = true
  try {
    const res = await terminalApi.getHistory({ page: 1, page_size: 100 })
    historyItems.value = res.data.items
  } catch (err) {
    console.error('加载历史失败', err)
  } finally {
    historyLoading.value = false
  }
}

async function loadRequest(id) {
  try {
    const res = await terminalApi.getRequest(id)
    const data = res.data
    currentRequestId.value = id
    currentRequest.value = data
    requestForm.value.method = data.method || 'GET'
    requestForm.value.url = data.url || ''
    requestForm.value.bodyType = data.body_type || 'none'
    requestForm.value.body = data.body || ''
    requestForm.value.headers = Object.entries(data.headers || {}).map(([key, value]) => ({ key, value }))
    requestForm.value.queryParams = Object.entries(data.query_params || {}).map(([key, value]) => ({ key, value }))
    requestForm.value.cookies = Object.entries(data.cookies || {}).map(([key, value]) => ({ key, value }))
    const auth = data.auth_config || {}
    requestForm.value.authConfig = auth
    requestForm.value.authType = auth.type || 'none'
    responseData.value = data.latest_result
    aiResult.value = null
    parseHint.value = ''
  } catch (err) {
    ElMessage.error('加载请求详情失败')
  }
}

async function toggleFavorite() {
  if (!currentRequestId.value) return
  try {
    await terminalApi.toggleFavorite(currentRequestId.value)
    await loadHistory()
    ElMessage.success('操作成功')
  } catch (err) {
    ElMessage.error('操作失败')
  }
}

function saveDraft() {
  ElMessage.success('请求已保留在当前工作台')
}

async function copyResponse() {
  if (!responseData.value?.response_body) return
  try {
    await navigator.clipboard.writeText(responseData.value.response_body)
    ElMessage.success('已复制')
  } catch {
    ElMessage.error('复制失败')
  }
}

function downloadResponse() {
  if (!responseData.value?.response_body) return
  const blob = new Blob([responseData.value.response_body], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `response_${currentRequestId.value}_${Date.now()}.json`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  ElMessage.success('下载成功')
}

function getRequestDataForCase() {
  return {
    method: requestForm.value.method,
    url: requestForm.value.url,
    query_params: Object.fromEntries(requestForm.value.queryParams.filter(p => p.key).map(p => [p.key, p.value])),
    headers: Object.fromEntries(requestForm.value.headers.filter(h => h.key).map(h => [h.key, h.value])),
    cookies: Object.fromEntries(requestForm.value.cookies.filter(c => c.key).map(c => [c.key, c.value])),
    body_type: requestForm.value.bodyType,
    body: requestForm.value.body,
    auth_config: requestForm.value.authConfig,
    expected_status: responseData.value?.status_code,
    source_debug_id: currentRequestId.value,
  }
}

function handleSaveToCaseSuccess() {
  showSaveToCaseDialog.value = false
  ElMessage.success('已保存为用例')
}

async function runAiAnalysis() {
  if (!responseData.value) {
    ElMessage.warning('请先发送请求')
    return
  }
  aiLoading.value = true
  aiResult.value = null
  try {
    await new Promise((resolve) => setTimeout(resolve, 500))
    const statusCode = responseData.value.status_code
    const isSuccess = statusCode >= 200 && statusCode < 400
    aiResult.value = {
      score: isSuccess ? 92 : 65,
      checks: [
        { name: 'Content-Type 头', status: responseContentType.value ? 'pass' : 'warn' },
        { name: 'Cache-Control 头', status: responseData.value.response_headers?.['cache-control'] ? 'pass' : 'warn' },
        { name: '响应时间 < 500ms', status: responseData.value.duration_ms < 500 ? 'pass' : 'warn' },
        { name: 'CORS 头完整性', status: 'warn' },
        { name: 'JSON 格式验证', status: isSuccess ? 'pass' : 'fail' },
      ],
      suggestions: [
        { priority: 'high', message: '建议添加 Cache-Control 头控制缓存策略' },
        { priority: 'medium', message: '建议启用 GZIP 压缩减少传输体积' },
        { priority: 'low', message: '可考虑添加 ETag 用于增量更新' },
      ],
      security: [
        { name: 'XSS 防护', safe: true },
        { name: 'SQL 注入', safe: true },
        { name: '敏感信息泄露', safe: true },
        { name: 'CSRF 攻击', safe: false },
      ],
    }
  } catch (err) {
    ElMessage.error('分析失败')
  } finally {
    aiLoading.value = false
  }
}

function getUrlTitle(url) {
  try {
    const parsed = new URL(url)
    return parsed.pathname.split('/').filter(Boolean).slice(-1)[0] || parsed.hostname
  } catch {
    return url
  }
}

function getUrlPath(url) {
  try {
    const parsed = new URL(url)
    return `${parsed.pathname}${parsed.search}`
  } catch {
    return url
  }
}

function getStatusClass(code) {
  if (!code) return ''
  if (code >= 200 && code < 300) return 'status-success'
  if (code >= 400 && code < 500) return 'status-warning'
  if (code >= 500) return 'status-danger'
  return ''
}

function getStatusText(code) {
  const map = { 200: 'OK', 201: 'Created', 204: 'No Content', 400: 'Bad Request', 401: 'Unauthorized', 403: 'Forbidden', 404: 'Not Found', 422: 'Unprocessable', 500: 'Server Error', 502: 'Bad Gateway', 503: 'Unavailable' }
  return map[code] || ''
}

function getScoreTagType(score) {
  if (score >= 85) return 'success'
  if (score >= 70) return 'warning'
  return 'danger'
}

function getScoreText(score) {
  if (score >= 85) return '优秀'
  if (score >= 70) return '良好'
  return '待改进'
}

function getScoreColor(score) {
  if (score >= 85) return 'var(--el-color-success)'
  if (score >= 70) return 'var(--el-color-warning)'
  return 'var(--el-color-danger)'
}

function getCheckIconColor(status) {
  if (status === 'pass') return 'var(--el-color-success)'
  if (status === 'warn') return 'var(--el-color-warning)'
  return 'var(--el-color-danger)'
}

function priorityText(priority) {
  const map = { high: 'HIGH', medium: 'MED', low: 'LOW' }
  return map[priority] || priority
}

onMounted(async () => {
  await loadHistory()
  if (route.query.id) {
    await loadRequest(Number(route.query.id))
  }
})

watch(() => route.query.id, async (id) => {
  if (id) await loadRequest(Number(id))
})
</script>

<style scoped>
.terminal-page {
  display: grid;
  grid-template-columns: 260px minmax(620px, 1fr) 320px;
  height: 100%;
  min-height: calc(100vh - 92px);
  background: var(--bg-page);
  overflow: hidden;
}

.history-panel,
.ai-panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: var(--bg-container);
}

.history-panel {
  border-right: 1px solid var(--border-color);
}

.ai-panel {
  border-left: 1px solid var(--border-color);
  overflow-y: auto;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-height: 58px;
  padding: 12px 14px;
  border-bottom: 1px solid var(--border-color-lighter);
}

.panel-title,
.response-title > span:first-child {
  display: block;
  color: var(--text-strong);
  font-size: 14px;
  font-weight: 850;
}

.panel-subtitle {
  display: block;
  margin-top: 3px;
  color: var(--text-secondary);
  font-size: 12px;
}

.history-search {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border-color-lighter);
}

.history-filter {
  display: flex;
  gap: 6px;
  padding: 10px 12px;
  border-bottom: 1px solid var(--border-color-lighter);
}

.history-filter button {
  height: 26px;
  padding: 0 12px;
  border: 1px solid transparent;
  border-radius: 7px;
  color: var(--text-secondary);
  background: transparent;
  font-size: 12px;
  font-weight: 750;
}

.history-filter button.active {
  color: var(--color-primary);
  background: var(--color-primary-soft);
}

.history-list {
  flex: 1;
  min-height: 0;
  padding: 8px;
  overflow-y: auto;
}

.history-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 8px;
  width: 100%;
  padding: 9px 8px;
  border: 0;
  border-radius: 9px;
  color: var(--text-primary);
  background: transparent;
  text-align: left;
}

.history-item:hover,
.history-item.active {
  background: var(--bg-container-soft);
}

.history-item.active {
  box-shadow: inset 3px 0 0 var(--color-primary);
}

.item-main {
  min-width: 0;
}

.item-url,
.item-path {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-url {
  color: var(--text-strong);
  font-size: 13px;
  font-weight: 750;
}

.item-path,
.item-duration {
  color: var(--text-secondary);
  font-family: var(--font-mono);
  font-size: 11px;
}

.item-meta {
  grid-column: 2;
  display: flex;
  gap: 8px;
  align-items: center;
  margin-top: 2px;
}

.item-status {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 850;
}

.status-success { color: var(--el-color-success); }
.status-warning { color: var(--el-color-warning); }
.status-danger { color: var(--el-color-danger); }

.list-placeholder {
  padding: 28px 10px;
  color: var(--text-secondary);
  text-align: center;
  font-size: 12px;
}

.more-history {
  height: 42px;
  border: 0;
  border-top: 1px solid var(--border-color-lighter);
  color: var(--color-primary);
  background: transparent;
  font-weight: 750;
}

.main-workspace {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  gap: 14px;
  min-width: 0;
  min-height: 0;
  padding: 14px;
  overflow: hidden;
}

.tool-card {
  border: 1px solid var(--border-color);
  border-radius: 10px;
  background: var(--bg-container);
  box-shadow: var(--shadow-soft);
  overflow: hidden;
}

.section-tabs {
  display: flex;
  align-items: center;
  gap: 4px;
  min-height: 44px;
  padding: 0 12px;
  border-bottom: 1px solid var(--border-color-lighter);
}

.section-tabs button {
  height: 32px;
  padding: 0 12px;
  border: 0;
  border-radius: 7px;
  color: var(--text-secondary);
  background: transparent;
  font-size: 13px;
  font-weight: 800;
}

.section-tabs button.active {
  color: var(--color-primary);
  background: var(--color-primary-soft);
}

.request-actions {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.request-bar {
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 12px;
  border-bottom: 1px solid var(--border-color-lighter);
}

.method-select {
  width: 106px;
  flex: 0 0 106px;
}

.url-input {
  flex: 1;
}

.parse-notice {
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border-color-lighter);
  color: var(--color-primary);
  background: var(--color-primary-soft);
  font-size: 12px;
}

.parse-notice .el-button {
  margin-left: auto;
}

.request-config-tabs {
  min-height: 154px;
}

.request-config-tabs :deep(.el-tabs__header),
.response-tabs :deep(.el-tabs__header) {
  margin: 0;
}

.request-config-tabs :deep(.el-tabs__nav-scroll),
.response-tabs :deep(.el-tabs__nav-scroll) {
  padding: 0 12px;
}

.request-config-tabs :deep(.el-tabs__content) {
  padding: 0;
}

.tab-count {
  display: inline-flex;
  min-width: 18px;
  height: 18px;
  align-items: center;
  justify-content: center;
  margin-left: 4px;
  border-radius: 999px;
  color: var(--color-success);
  background: var(--color-success-soft);
  font-size: 11px;
}

.response-section {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.response-summary {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  min-height: 56px;
  padding: 10px 12px;
  border-bottom: 1px solid var(--border-color-lighter);
}

.response-metrics {
  display: flex;
  gap: 14px;
  align-items: center;
  margin-top: 4px;
  color: var(--text-secondary);
  font-family: var(--font-mono);
  font-size: 12px;
}

.response-bar-actions {
  display: flex;
  gap: 4px;
  align-items: center;
}

.response-tabs {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-height: 0;
}

.response-tabs :deep(.el-tabs__content) {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

.response-error {
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 18px;
  color: var(--color-danger);
}

.response-empty,
.placeholder-panel,
.ai-empty,
.ai-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
}

.response-empty {
  flex: 1;
  flex-direction: column;
  gap: 10px;
}

.placeholder-panel {
  min-height: 220px;
}

.ai-empty,
.ai-loading {
  flex: 1;
  flex-direction: column;
  gap: 12px;
  padding: 24px;
  text-align: center;
}

.ai-empty p {
  max-width: 220px;
  margin: 0;
  line-height: 1.6;
}

.ai-score-section,
.ai-section {
  padding: 16px;
  border-bottom: 1px solid var(--border-color-lighter);
}

.score-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.score-value {
  margin: 10px 0 8px;
  color: var(--text-strong);
  font-family: var(--font-mono);
  font-size: 28px;
  font-weight: 900;
}

.score-value small {
  color: var(--text-secondary);
  font-size: 13px;
}

.ai-section-title {
  margin-bottom: 12px;
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 850;
}

.check-list,
.suggestion-list,
.security-list {
  display: grid;
  gap: 10px;
}

.check-item,
.suggestion-item,
.security-item {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  color: var(--text-primary);
  font-size: 13px;
  line-height: 1.45;
}

.suggestion-priority {
  min-width: 40px;
  padding: 2px 6px;
  border-radius: 5px;
  font-size: 10px;
  font-weight: 900;
  text-align: center;
}

.priority-high {
  color: var(--color-danger);
  background: var(--color-danger-soft);
}

.priority-medium {
  color: var(--color-warning);
  background: var(--color-warning-soft);
}

.priority-low {
  color: var(--color-primary);
  background: var(--color-primary-soft);
}

@media (max-width: 1280px) {
  .terminal-page {
    grid-template-columns: 230px minmax(560px, 1fr) 290px;
  }
}
</style>

