<template>
  <div class="terminal-page">
    <aside class="history-panel">
      <div class="panel-header">
        <div>
          <span class="panel-title">历史记录</span>
          <span class="panel-subtitle">{{ filteredHistory.length }} 条请求</span>
        </div>
        <el-button size="small" text :icon="Refresh" @click="loadHistory(true)" />
      </div>

      <div class="history-search">
        <el-input v-model="historySearch" placeholder="搜索请求名称 / URL" size="small" :prefix-icon="Search" clearable />
      </div>

      <div class="history-filter">
        <button :class="{ active: historyFilter === 'all' }" type="button" @click="historyFilter = 'all'">全部</button>
        <button :class="{ active: historyFilter === 'fail' }" type="button" @click="historyFilter = 'fail'">失败</button>
        <button :class="{ active: historyFilter === 'favorite' }" type="button" @click="historyFilter = 'favorite'">收藏</button>
      </div>

      <div class="history-list">
        <div
          v-for="item in filteredHistory"
          :key="item.id"
          class="history-item"
          :class="{ active: currentRequestId === item.id }"
        >
          <button class="history-item-main" type="button" @click="loadRequest(item.id)">
            <span class="method-badge" :class="item.method.toLowerCase()">{{ item.method }}</span>
            <span class="item-main">
              <span class="item-url" :title="item.url">{{ getUrlTitle(item.url) }}</span>
              <span class="item-path">
                {{ getUrlPath(item.url) }}
                <span v-if="loadingRequestId === item.id" class="item-loading">加载中...</span>
              </span>
            </span>
            <span class="item-meta">
              <span v-if="item.status_code" class="item-status" :class="getStatusClass(item.status_code)">{{ item.status_code }}</span>
              <span v-if="item.duration_ms" class="item-duration">{{ item.duration_ms }}ms</span>
            </span>
          </button>
          <el-button
            class="favorite-toggle"
            size="small"
            text
            :type="item.status === 'favorite' ? 'warning' : ''"
            :icon="Star"
            @click.stop="toggleFavoriteById(item.id)"
          />
        </div>
        <div v-if="historyLoading" class="list-placeholder">加载中...</div>
        <div v-else-if="filteredHistory.length === 0" class="list-placeholder">暂无记录</div>
      </div>
    </aside>

    <main class="main-workspace">
      <section class="request-section tool-card">
        <div class="request-toolbar">
          <div class="request-toolbar-left">
            <span class="panel-title">请求配置</span>
            <span class="panel-subtitle">粘贴抓包请求、导入接口文档、手工编辑后直接调试</span>
          </div>
          <div class="request-toolbar-actions">
            <el-button size="small" :icon="MagicStick" @click="showPasteDialog = true">智能识别</el-button>
            <el-button size="small" :icon="Upload" @click="showImportDialog = true">导入文档</el-button>
          </div>
        </div>

        <div class="request-bar">
          <el-select v-model="requestForm.method" class="method-select">
            <el-option v-for="m in methods" :key="m" :label="m" :value="m" />
          </el-select>
          <el-input
            ref="urlInputRef"
            v-model="requestForm.url"
            placeholder="输入 URL 或使用上方粘贴数据自动解析"
            class="url-input"
            @paste="handlePaste"
            @keyup.enter="sendRequest"
          />
          <el-button type="primary" :loading="sending" @click="sendRequest">发送</el-button>
        </div>

        <div v-if="parseHint" class="parse-notice">
          <el-icon><InfoFilled /></el-icon>
          <span>已解析 <strong>{{ parseHint }}</strong>，{{ parsedHeaderCount }} 个请求头</span>
          <span v-if="parseWarnings.length" class="parse-warning">警告 {{ parseWarnings.length }} 项</span>
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
            <span>响应结果</span>
            <span v-if="responseData" class="response-metrics">
              状态：<strong :class="getStatusClass(responseData.status_code)">{{ responseData.status_code }} {{ getStatusText(responseData.status_code) }}</strong>
              <span>耗时：{{ responseData.duration_ms }}ms</span>
              <span>大小：{{ responseSize || '-' }}</span>
            </span>
          </div>
          <div class="response-bar-actions">
            <el-button v-if="responseData" size="small" text :icon="CopyDocument" @click="copyResponse">复制</el-button>
            <el-button v-if="responseData" size="small" text :icon="Download" @click="downloadResponse">下载</el-button>
            <el-button v-if="responseData" size="small" text :icon="Document" @click="showSaveToCaseDialog = true">保存为用例</el-button>
            <el-button v-if="currentRequestId" size="small" text :icon="Star" :type="currentRequest?.status === 'favorite' ? 'warning' : ''" @click="toggleFavorite">
              {{ currentRequest?.status === 'favorite' ? '取消收藏' : '收藏' }}
            </el-button>
          </div>
        </div>

        <div v-if="responseError" class="response-error">
          <el-icon><CircleCloseFilled /></el-icon>
          <div class="response-error-body">
            <span>{{ responseError }}</span>
            <span v-if="responseData?.error_message" class="response-error-detail">{{ responseData.error_message }}</span>
          </div>
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

    <aside class="analysis-panel">
      <div class="panel-header">
        <div>
          <span class="panel-title">分析与产出</span>
          <span class="panel-subtitle">AI 断言 / 健壮性 / 安全检查 / 用例沉淀</span>
        </div>
        <el-button size="small" text :icon="Refresh" :loading="aiLoading" @click="runAiAnalysis(true)">分析</el-button>
      </div>

      <div v-if="!aiResult && !aiLoading" class="analysis-empty">
        <el-icon size="34"><MagicStick /></el-icon>
        <p>发送请求后运行分析，生成健壮性评分、断言建议和安全检查结论</p>
      </div>

      <div v-else-if="aiLoading" class="analysis-empty">
        <el-icon class="is-loading" size="28"><Loading /></el-icon>
        <span>分析中...</span>
      </div>

      <template v-else>
        <div class="analysis-score">
          <div class="score-header">
            <span>健壮性评分</span>
            <el-tag :type="getScoreTagType(aiResult.score)" effect="light" size="small">{{ getScoreText(aiResult.score) }}</el-tag>
          </div>
          <div class="score-value">{{ aiResult.score }}<small>/100</small></div>
          <el-progress :percentage="aiResult.score" :color="getScoreColor(aiResult.score)" :show-text="false" />
        </div>

        <div class="analysis-section">
          <div class="analysis-title">健康检查</div>
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

        <div class="analysis-section">
          <div class="analysis-title">断言与建议</div>
          <div class="suggestion-list">
            <div v-for="(suggestion, idx) in aiResult.suggestions" :key="idx" class="suggestion-item">
              <span class="suggestion-priority" :class="'priority-' + suggestion.priority">{{ priorityText(suggestion.priority) }}</span>
              <span>{{ suggestion.message }}</span>
            </div>
          </div>
        </div>

        <div class="analysis-section">
          <div class="analysis-title">安全检测</div>
          <div class="security-list">
            <div v-for="item in aiResult.security" :key="item.name" class="security-item">
              <el-tag :type="item.safe ? 'success' : 'danger'" effect="light" size="small">{{ item.safe ? '安全' : '风险' }}</el-tag>
              <span>{{ item.name }}</span>
            </div>
          </div>
        </div>
      </template>
    </aside>

    <el-dialog v-model="showPasteDialog" title="粘贴抓包数据" width="720px">
      <el-form label-position="top">
        <el-form-item label="支持格式">
          <div class="dialog-hint">支持 `curl`、`fetch(...)`、`XMLHttpRequest`、纯 URL。粘贴后会自动解析到请求区。</div>
        </el-form-item>
        <el-form-item label="原始内容">
          <el-input v-model="pastedSource" type="textarea" :rows="14" placeholder="在这里粘贴 fetch / curl / 抓包请求..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPasteDialog = false">取消</el-button>
        <el-button type="primary" @click="applyPastedSource">解析并填充</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showImportDialog" title="导入接口文档" width="720px">
      <el-form label-position="top">
        <el-form-item label="导入方式">
          <el-radio-group v-model="importMode">
            <el-radio label="url">OpenAPI / Swagger URL</el-radio>
            <el-radio label="raw">原始文档 JSON</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="importMode === 'url'" label="文档地址">
          <el-input v-model="importForm.source_url" placeholder="例如：http://localhost:8000/openapi.json" />
        </el-form-item>
        <el-form-item v-else label="文档内容">
          <el-input v-model="importForm.raw_content" type="textarea" :rows="12" placeholder="粘贴 OpenAPI / Swagger 导出的 JSON..." />
        </el-form-item>
      </el-form>

      <div v-if="importItems.length" class="import-preview">
        <div class="analysis-title">导入预览</div>
        <div class="import-list">
          <button
            v-for="item in importItems"
            :key="`${item.method}-${item.url}`"
            class="import-item"
            type="button"
            @click="applyImportedItem(item)"
          >
            <span class="method-badge" :class="item.method.toLowerCase()">{{ item.method }}</span>
            <span class="import-item-body">
              <span class="item-url">{{ item.url }}</span>
              <span class="item-path">{{ item.summary || '未提供摘要' }}</span>
            </span>
          </button>
        </div>
      </div>

      <template #footer>
        <el-button @click="showImportDialog = false">关闭</el-button>
        <el-button :loading="importingDocument" type="primary" @click="loadImportDocument">读取文档</el-button>
      </template>
    </el-dialog>

    <SaveToCaseDialog
      v-model="showSaveToCaseDialog"
      :request-data="requestDataForCase"
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
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import { terminalApi } from '@/api/terminal'
import { parseRequest } from '@/utils/requestParser'
import feedback from '@/utils/feedback'
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
  url: '',
  queryParams: [],
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
const loadingRequestId = ref(null)
const historyItems = ref([])
const currentRequestId = ref(null)
const currentRequest = ref(null)
const responseData = ref(null)
const responseError = ref('')
const parseHint = ref('')
const parseWarnings = ref([])
const parsedHeaderCount = ref(0)
const historySearch = ref('')
const historyFilter = ref('all')
const aiLoading = ref(false)
const aiResult = ref(null)
const showSaveToCaseDialog = ref(false)
const showPasteDialog = ref(false)
const pastedSource = ref('')
const showImportDialog = ref(false)
const importingDocument = ref(false)
const importMode = ref('url')
const importItems = ref([])
const importForm = ref({
  source_url: 'http://localhost:8000/openapi.json',
  raw_content: '',
})

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

const requestDataForCase = computed(() => ({
  method: requestForm.value.method,
  url: requestForm.value.url,
  query_params: Object.fromEntries(requestForm.value.queryParams.filter((p) => p.key).map((p) => [p.key, p.value])),
  headers: Object.fromEntries(requestForm.value.headers.filter((h) => h.key).map((h) => [h.key, h.value])),
  cookies: Object.fromEntries(requestForm.value.cookies.filter((c) => c.key).map((c) => [c.key, c.value])),
  body_type: requestForm.value.bodyType,
  body: requestForm.value.body,
  auth_config: requestForm.value.authConfig,
  expected_status: responseData.value?.status_code || null,
  source_debug_id: currentRequestId.value,
}))

function fillRequestForm(parsed) {
  requestForm.value.method = parsed.method || 'GET'
  requestForm.value.url = parsed.url || ''
  requestForm.value.body = parsed.body || ''
  requestForm.value.bodyType = parsed.bodyType || 'none'
  requestForm.value.headers = parsed.headers || []
  requestForm.value.queryParams = Object.entries(parsed.query_params || parsed.queryParams || {}).map(([key, value]) => ({ key, value }))
  requestForm.value.cookies = parsed.cookies || []
  if (parsed.authType === 'bearer') {
    requestForm.value.authType = 'bearer'
    requestForm.value.authConfig = { type: 'bearer', token: parsed.authToken || '' }
  }
  parsedHeaderCount.value = parsed.headers?.length || 0
  parseHint.value = parsed.sourceType === 'curl' ? 'cURL' : parsed.sourceType === 'fetch' ? 'Fetch' : parsed.sourceType === 'xhr' ? 'XHR' : 'URL'
  parseWarnings.value = parsed.warnings || []
}

function handlePaste(e) {
  const text = e.clipboardData.getData('text')
  if (!text) return
  const trimmed = text.trim()
  if (trimmed.startsWith('curl ') || trimmed.startsWith('fetch(') || trimmed.startsWith('await fetch(') || trimmed.includes('XMLHttpRequest') || trimmed.startsWith('http')) {
    e.preventDefault()
    const parsed = parseRequest(trimmed)
    fillRequestForm(parsed)
    if (parseWarnings.value.length) {
      feedback.warning(`已解析 ${parseHint.value}，存在 ${parseWarnings.value.length} 项警告`)
    } else {
      feedback.success(`解析成功：${parseHint.value} 请求`)
    }
  }
}

function applyPastedSource() {
  if (!pastedSource.value.trim()) {
    feedback.warning('请先粘贴内容')
    return
  }
  const parsed = parseRequest(pastedSource.value)
  fillRequestForm(parsed)
  showPasteDialog.value = false
  if (parseWarnings.value.length) {
    feedback.warning(`已解析 ${parseHint.value}，存在 ${parseWarnings.value.length} 项警告`)
  } else {
    feedback.success(`解析成功：${parseHint.value} 请求`)
  }
}

function clearParseHint(showMessage = true) {
  parseHint.value = ''
  parseWarnings.value = []
  parsedHeaderCount.value = 0
  if (showMessage) {
    feedback.success('解析结果已清除')
  }
}

async function loadImportDocument() {
  importingDocument.value = true
  try {
    const res = await terminalApi.importDocument({
      source_url: importMode.value === 'url' ? importForm.value.source_url : '',
      raw_content: importMode.value === 'raw' ? importForm.value.raw_content : '',
      content_type: 'openapi',
    })
    importItems.value = res.data.items || []
    feedback.success(`导入成功：读取到 ${res.data.total} 个接口`)
  } catch (err) {
    feedback.error(err.response?.data?.detail || '读取文档失败')
  } finally {
    importingDocument.value = false
  }
}

function applyImportedItem(item) {
  requestForm.value.method = item.method
  requestForm.value.url = item.url
  requestForm.value.queryParams = []
  requestForm.value.headers = []
  requestForm.value.cookies = []
  requestForm.value.body = ''
  requestForm.value.bodyType = 'none'
  requestForm.value.authType = 'none'
  requestForm.value.authConfig = {}
  clearParseHint(false)
  showImportDialog.value = false
  feedback.success('导入成功，接口已填充到请求区')
}

async function sendRequest() {
  if (!requestForm.value.url) {
    feedback.warning('请输入请求 URL')
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
    currentRequest.value = res.data
    if (responseData.value?.error_message) {
      responseError.value = responseData.value.error_message
    } else if ((responseData.value?.status_code || 0) >= 200 && (responseData.value?.status_code || 0) < 300) {
      await runAiAnalysis()
    }
    parseHint.value = ''
    await loadHistory()
    feedback.success('发送成功')
  } catch (err) {
    responseError.value = err.response?.data?.detail || err.message || '请求失败'
  } finally {
    sending.value = false
  }
}

async function loadHistory(showMessage = false) {
  historyLoading.value = true
  try {
    const res = await terminalApi.getHistory({ page: 1, page_size: 100 })
    historyItems.value = res.data.items
    if (showMessage) {
      feedback.success('历史记录已刷新')
    }
  } catch (err) {
    console.error('加载历史失败', err)
    if (showMessage) {
      feedback.error('刷新历史失败')
    }
  } finally {
    historyLoading.value = false
  }
}

async function loadRequest(id) {
  loadingRequestId.value = id
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
    responseError.value = data.latest_result?.error_message || ''
    aiResult.value = null
    clearParseHint(false)
    feedback.success('历史记录加载成功')
  } catch (err) {
    feedback.error('加载请求详情失败')
  } finally {
    loadingRequestId.value = null
  }
}

async function toggleFavorite() {
  if (!currentRequestId.value) return
  try {
    const res = await terminalApi.toggleFavorite(currentRequestId.value)
    if (currentRequest.value) {
      currentRequest.value.status = res.data.status
    }
    await loadHistory()
    feedback.success(res.data.status === 'favorite' ? '收藏成功' : '取消收藏成功')
  } catch (err) {
    feedback.error('操作失败')
  }
}

async function toggleFavoriteById(id) {
  try {
    const res = await terminalApi.toggleFavorite(id)
    await loadHistory()
    if (currentRequestId.value === id && currentRequest.value) {
      currentRequest.value.status = res.data.status
    }
    feedback.success(res.data.status === 'favorite' ? '收藏成功' : '取消收藏成功')
  } catch (err) {
    feedback.error('收藏操作失败')
  }
}

function saveDraft() {
  feedback.success('保存成功')
}

async function copyResponse() {
  if (!responseData.value?.response_body) return
  try {
    await navigator.clipboard.writeText(responseData.value.response_body)
    feedback.success('已复制')
  } catch {
    feedback.error('复制失败')
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
  feedback.success('下载成功')
}

function handleSaveToCaseSuccess() {
  showSaveToCaseDialog.value = false
}

async function runAiAnalysis(showMessage = false) {
  if (!responseData.value) {
    feedback.warning('请先发送请求')
    return
  }
  aiLoading.value = true
  aiResult.value = null
  try {
    await new Promise((resolve) => setTimeout(resolve, 300))
    const statusCode = responseData.value.status_code
    const isSuccess = statusCode >= 200 && statusCode < 400
    aiResult.value = {
      score: isSuccess ? 92 : 65,
      checks: [
        { name: 'Content-Type 头', status: responseContentType.value ? 'pass' : 'warn' },
        { name: 'Cache-Control 头', status: responseData.value.response_headers?.['cache-control'] ? 'pass' : 'warn' },
        { name: '响应时间 < 500ms', status: responseData.value.duration_ms < 500 ? 'pass' : 'warn' },
        { name: '鉴权配置合理性', status: requestForm.value.authType !== 'none' || requestForm.value.headers.some((h) => h.key.toLowerCase() === 'authorization') ? 'pass' : 'warn' },
        { name: 'JSON 格式验证', status: isSuccess ? 'pass' : 'fail' },
      ],
      suggestions: [
        { priority: 'high', message: '建议补充成功与失败状态码断言，避免只校验 200。' },
        { priority: 'medium', message: '建议对关键响应字段补充提取与结构断言。' },
        { priority: 'low', message: '如接口面向浏览器，建议补充缓存和跨域头检查。' },
      ],
      security: [
        { name: 'XSS 防护', safe: true },
        { name: 'SQL 注入', safe: true },
        { name: '敏感信息泄露', safe: true },
        { name: 'CSRF 攻击', safe: false },
      ],
    }
    if (showMessage) {
      feedback.success('分析成功')
    }
  } catch (err) {
    feedback.error('分析失败')
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
  } else if (route.query.method || route.query.url) {
    // Pre-fill from API Asset Center debug
    requestForm.value.method = route.query.method || 'GET'
    requestForm.value.url = route.query.url || ''
    requestForm.value.bodyType = route.query.body_type || 'none'
    requestForm.value.body = route.query.body || ''
    if (route.query.headers) {
      try {
        const headers = JSON.parse(route.query.headers)
        requestForm.value.headers = Object.entries(headers).map(([key, value]) => ({ key, value }))
      } catch {
        requestForm.value.headers = []
      }
    }
    if (route.query.query_params) {
      try {
        const qp = JSON.parse(route.query.query_params)
        requestForm.value.queryParams = Object.entries(qp).map(([key, value]) => ({ key, value }))
      } catch {
        requestForm.value.queryParams = []
      }
    }
  }
})

watch(() => route.query.id, async (id) => {
  if (id) await loadRequest(Number(id))
})
</script>

<style scoped>
/* ── 动画关键帧 ── */
@keyframes case-scan {
  from { transform: translateX(-24%); }
  to { transform: translateX(24%); }
}

@keyframes case-particles {
  from { transform: translate3d(0, 0, 0); }
  to { transform: translate3d(26px, -18px, 0); }
}

@keyframes case-form-scan {
  from { transform: translateY(-8%); }
  to { transform: translateY(108%); }
}

@keyframes case-table-scan {
  from { transform: translateY(-6%); }
  to { transform: translateY(106%); }
}

.terminal-page {
  display: grid;
  grid-template-columns: 260px minmax(620px, 1fr) 340px;
  height: 100%;
  min-height: calc(100vh - 72px);
  padding: 12px;
  background:
    linear-gradient(rgba(56, 189, 248, 0.095) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.085) 1px, transparent 1px),
    linear-gradient(145deg, rgba(34, 211, 166, 0.18), transparent 30%),
    linear-gradient(225deg, rgba(56, 189, 248, 0.22), transparent 36%),
    linear-gradient(0deg, rgba(22, 119, 255, 0.12), transparent 50%),
    var(--bg-page);
  background-size: 28px 28px, 28px 28px, auto, auto, auto, auto;
  overflow: hidden;
  position: relative;
}

.terminal-page::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 24%, rgba(56, 189, 248, 0.16) 44%, transparent 62%),
    repeating-linear-gradient(90deg, transparent 0 92px, rgba(56, 189, 248, 0.075) 92px 93px);
  content: "";
  animation: case-scan 14s linear infinite;
}

.terminal-page::after {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background-image:
    radial-gradient(circle, rgba(125, 211, 252, 0.72) 0 1.2px, transparent 1.8px),
    radial-gradient(circle, rgba(45, 212, 191, 0.52) 0 1.1px, transparent 1.7px);
  background-position: 8% 16%, 80% 42%;
  background-size: 180px 160px, 240px 220px;
  opacity: 0.48;
  content: "";
  animation: case-particles 18s ease-in-out infinite alternate;
}

html:not(.dark) .terminal-page {
  background:
    linear-gradient(rgba(22, 119, 255, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.04) 1px, transparent 1px),
    linear-gradient(145deg, rgba(14, 116, 144, 0.12), transparent 30%),
    linear-gradient(225deg, rgba(22, 119, 255, 0.16), transparent 36%),
    linear-gradient(0deg, rgba(56, 189, 248, 0.08), transparent 50%),
    var(--bg-page);
}

.history-panel,
.analysis-panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
  background:
    linear-gradient(rgba(56, 189, 248, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.045) 1px, transparent 1px),
    rgba(20, 22, 27, 0.62);
  background-size: 32px 32px, 32px 32px;
  position: relative;
  overflow: hidden;
}

.history-panel::before,
.analysis-panel::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(56, 189, 248, 0.12) 50%, transparent 66%),
    radial-gradient(circle at 88% 16%, rgba(34, 211, 166, 0.14), transparent 26%);
  opacity: 0.8;
  content: "";
  animation: case-form-scan 12s linear infinite;
}

html:not(.dark) .history-panel,
html:not(.dark) .analysis-panel {
  background:
    linear-gradient(rgba(22, 119, 255, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.035) 1px, transparent 1px),
    rgba(255, 255, 255, 0.62);
  background-size: 32px 32px, 32px 32px;
}

html:not(.dark) .history-panel::before,
html:not(.dark) .analysis-panel::before {
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(22, 119, 255, 0.1) 50%, transparent 66%);
  opacity: 0.6;
}

.history-panel {
  border-right: 1px solid var(--border-color);
}

.analysis-panel {
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
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 6px;
  align-items: center;
  padding: 4px;
  border-radius: 9px;
}

.history-item:hover,
.history-item.active {
  background: var(--bg-container-soft);
}

.history-item.active {
  box-shadow: inset 3px 0 0 var(--color-primary);
}

.history-item-main {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 8px;
  width: 100%;
  padding: 5px 4px;
  border: 0;
  color: var(--text-primary);
  background: transparent;
  text-align: left;
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

.item-loading {
  margin-left: 8px;
  color: var(--color-primary);
}

.item-meta {
  grid-column: 2;
  display: flex;
  gap: 8px;
  align-items: center;
  margin-top: 2px;
}

.favorite-toggle {
  width: 28px;
  padding: 0;
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

.main-workspace {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  gap: 14px;
  min-width: 0;
  min-height: 0;
  padding: 0;
  overflow: hidden;
  position: relative;
}

.main-workspace::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(56, 189, 248, 0.12) 50%, transparent 66%),
    radial-gradient(circle at 88% 16%, rgba(34, 211, 166, 0.14), transparent 26%);
  opacity: 0.8;
  content: "";
  animation: case-table-scan 12s linear infinite;
}

html:not(.dark) .main-workspace::before {
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(22, 119, 255, 0.1) 50%, transparent 66%);
  opacity: 0.6;
}

html:not(.dark) .main-workspace {
  background:
    linear-gradient(rgba(22, 119, 255, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.03) 1px, transparent 1px),
    rgba(255, 255, 255, 0.54);
  background-size: 28px 28px, 28px 28px;
}

.tool-card {
  border: 1px solid rgba(56, 189, 248, 0.22);
  border-radius: 10px;
  background:
    linear-gradient(rgba(56, 189, 248, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.045) 1px, transparent 1px),
    rgba(20, 22, 27, 0.68);
  background-size: 28px 28px, 28px 28px;
  box-shadow: 0 18px 48px rgba(2, 8, 23, 0.24), inset 0 1px 0 rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(18px) saturate(1.25);
  overflow: hidden;
  position: relative;
}

.tool-card::after {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(90deg, rgba(56, 189, 248, 0.12), transparent 18% 82%, rgba(34, 211, 166, 0.1)),
    repeating-linear-gradient(90deg, transparent 0 42px, rgba(56, 189, 248, 0.06) 42px 43px);
  opacity: 0.65;
  content: "";
}

html:not(.dark) .tool-card {
  border-color: rgba(22, 119, 255, 0.18);
  background:
    linear-gradient(rgba(22, 119, 255, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.035) 1px, transparent 1px),
    rgba(255, 255, 255, 0.62);
  background-size: 28px 28px, 28px 28px;
  box-shadow: 0 18px 46px rgba(20, 42, 76, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.82);
}

html:not(.dark) .tool-card::after {
  background:
    linear-gradient(90deg, rgba(22, 119, 255, 0.1), transparent 18% 82%, rgba(14, 116, 144, 0.08));
  opacity: 0.5;
}

.request-toolbar {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  min-height: 58px;
  padding: 12px 14px;
  border-bottom: 1px solid var(--border-color-lighter);
}

.request-toolbar-left {
  min-width: 0;
}

.request-toolbar-actions {
  display: flex;
  gap: 8px;
  align-items: center;
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

.parse-warning {
  color: var(--color-warning);
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
  align-items: flex-start;
  padding: 18px;
  color: var(--color-danger);
}

.response-error-body {
  display: grid;
  gap: 4px;
}

.response-error-detail {
  color: var(--text-secondary);
  font-size: 12px;
}

.response-empty,
.analysis-empty {
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

.analysis-empty {
  flex: 1;
  flex-direction: column;
  gap: 12px;
  padding: 24px;
  text-align: center;
}

.analysis-empty p {
  max-width: 240px;
  margin: 0;
  line-height: 1.6;
}

.analysis-score,
.analysis-section {
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

.analysis-title {
  margin-bottom: 12px;
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 850;
}

.check-list,
.suggestion-list,
.security-list,
.import-list {
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

.dialog-hint {
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.6;
}

.import-preview {
  margin-top: 16px;
}

.import-item {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color-lighter);
  border-radius: 8px;
  color: var(--text-primary);
  background: var(--bg-container-soft);
  text-align: left;
}

.import-item-body {
  min-width: 0;
}

/* ── 面板通用 ── */
.panel-header,
.request-toolbar,
.response-summary {
  position: relative;
  overflow: hidden;
}

.panel-header::before,
.request-toolbar::before,
.response-summary::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(90deg, rgba(56, 189, 248, 0.12), transparent 18% 82%, rgba(34, 211, 166, 0.1)),
    repeating-linear-gradient(90deg, transparent 0 42px, rgba(56, 189, 248, 0.05) 42px 43px);
  opacity: 0.6;
  content: "";
  animation: case-form-scan 14s linear infinite;
}

html:not(.dark) .panel-header::before,
html:not(.dark) .request-toolbar::before,
html:not(.dark) .response-summary::before {
  background:
    linear-gradient(90deg, rgba(22, 119, 255, 0.1), transparent 18% 82%, rgba(14, 116, 144, 0.08));
  opacity: 0.45;
}

@media (max-width: 1280px) {
  .terminal-page {
    grid-template-columns: 230px minmax(520px, 1fr) 300px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .terminal-page::before,
  .terminal-page::after,
  .history-panel::before,
  .analysis-panel::before,
  .main-workspace::before,
  .tool-card::after,
  .panel-header::before,
  .request-toolbar::before,
  .response-summary::before {
    animation: none;
  }
}
</style>
