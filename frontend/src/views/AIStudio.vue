<template>
  <div class="ai-studio">
    <!-- 头部 -->
    <div class="page-header">
      <h1 class="page-title">AI 实验室</h1>
      <div class="header-actions">
        <button class="btn-secondary" @click="showHistory = true">
          📋 生成历史
        </button>
      </div>
    </div>

    <!-- 标签页 -->
    <div class="tabs">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        :class="{ active: currentTab === tab.key }"
        @click="currentTab = tab.key"
      >
        {{ tab.icon }} {{ tab.label }}
      </button>
    </div>

    <!-- 自愈配置 Tab -->
    <SelfHealConfig v-if="currentTab === 'self-heal'" />

    <!-- 主内容区 -->
    <div class="studio-content">
      <!-- 左侧: 输入源 -->
      <div class="input-panel">
        <!-- 输入源选择 -->
        <div class="source-selector">
          <label>输入源类型</label>
          <div class="source-buttons">
            <button
              v-for="source in sourceTypes"
              :key="source.value"
              :class="{ active: sourceType === source.value }"
              @click="sourceType = source.value"
            >
              {{ source.icon }} {{ source.label }}
            </button>
          </div>
        </div>

        <!-- 代码编辑器 -->
        <div class="editor-container">
          <label>
            {{ sourceType === 'code' ? '代码片段' :
               sourceType === 'doc' ? 'OpenAPI 规范 (JSON)' :
               sourceType === 'curl' ? 'cURL 命令' : '自然语言描述' }}
          </label>
          <textarea
            v-model="sourceContent"
            class="code-editor"
            :placeholder="getPlaceholder()"
            rows="15"
          ></textarea>
        </div>

        <!-- 生成选项 -->
        <div class="options-section">
          <label>生成选项</label>
          <div class="options-grid">
            <label class="checkbox-item">
              <input type="checkbox" v-model="options.include_success" />
              <span>成功场景</span>
            </label>
            <label class="checkbox-item">
              <input type="checkbox" v-model="options.include_error" />
              <span>错误场景</span>
            </label>
            <label class="checkbox-item">
              <input type="checkbox" v-model="options.include_boundary" />
              <span>边界测试</span>
            </label>
            <label class="checkbox-item">
              <input type="checkbox" v-model="options.include_performance" />
              <span>性能断言</span>
            </label>
          </div>
        </div>

        <!-- 生成按钮 -->
        <button
          class="btn-generate"
          @click="generateCases"
          :disabled="loading || !sourceContent.trim()"
        >
          {{ loading ? '🤖 AI 生成中...' : '✨ AI 生成测试用例' }}
        </button>
      </div>

      <!-- 右侧: 生成结果 -->
      <div class="result-panel">
        <div v-if="loading" class="loading-state">
          <div class="loading-spinner"></div>
          <p>AI 正在分析并生成测试用例...</p>
        </div>

        <div v-else-if="!generatedCases.length" class="empty-state">
          <div class="empty-icon">🤖</div>
          <p>在左侧输入代码/OpenAPI/cURL/描述</p>
          <p>点击生成按钮获取 AI 测试用例</p>
        </div>

        <div v-else class="results-container">
          <div class="results-header">
            <span class="results-count">生成 {{ generatedCases.length }} 个用例</span>
            <button class="btn-primary" @click="acceptAllCases">
              ✓ 全部采纳
            </button>
          </div>

          <div class="cases-list">
            <div
              v-for="(caseItem, index) in generatedCases"
              :key="index"
              class="case-card"
              :class="{ accepted: caseItem.accepted, ignored: caseItem.ignored }"
            >
              <div class="case-header">
                <span class="case-name">{{ caseItem.name }}</span>
                <span class="case-method" :class="'method-' + caseItem.method.toLowerCase()">
                  {{ caseItem.method }}
                </span>
              </div>

              <div class="case-url">{{ caseItem.url }}</div>

              <div class="case-assertions">
                <span
                  v-for="(assertion, idx) in caseItem.assertions"
                  :key="idx"
                  class="assertion-tag"
                >
                  {{ assertion.type }}: {{ assertion.expected }}
                </span>
              </div>

              <div class="case-actions">
                <button
                  v-if="!caseItem.accepted && !caseItem.ignored"
                  class="btn-accept"
                  @click="acceptCase(index)"
                >
                  ✓ 采纳
                </button>
                <button
                  v-if="!caseItem.ignored"
                  class="btn-ignore"
                  @click="ignoreCase(index)"
                >
                  ✕ 忽略
                </button>
                <span v-if="caseItem.accepted" class="accepted-badge">✓ 已采纳</span>
                <span v-if="caseItem.ignored" class="ignored-badge">已忽略</span>
              </div>
            </div>
          </div>

          <!-- AI 建议 -->
          <div v-if="aiSuggestion" class="ai-suggestion">
            <div class="suggestion-header">🤖 AI 建议</div>
            <div class="suggestion-content">{{ aiSuggestion }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 历史记录弹窗 -->
    <div v-if="showHistory" class="dialog-overlay" @click.self="showHistory = false">
      <div class="dialog history-dialog">
        <div class="dialog-header">
          <h2>生成历史</h2>
          <button class="btn-close" @click="showHistory = false">×</button>
        </div>

        <div class="history-list">
          <div
            v-for="item in historyItems"
            :key="item.id"
            class="history-item"
          >
            <div class="history-info">
              <span class="history-type">{{ item.source_type }}</span>
              <span class="history-time">{{ formatTime(item.created_at) }}</span>
            </div>
            <div class="history-preview">{{ item.source_content }}</div>
            <div class="history-meta">
              <span>{{ item.case_count }} 个用例</span>
              <span v-if="item.accepted">✓ 已采纳</span>
              <span v-if="item.feedback_score">评分: {{ item.feedback_score }}/5</span>
            </div>
          </div>
          <div v-if="!historyItems.length" class="empty-history">
            暂无生成历史
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import SelfHealConfig from './SelfHealConfig.vue'

const API_BASE = '/api'

// 状态
const currentTab = ref('generate')
const tabs = [
  { key: 'generate', label: '用例生成', icon: '✨' },
  { key: 'self-heal', label: '自愈配置', icon: '🔧' },
  { key: 'advisor', label: 'AI 顾问', icon: '💬' },
]

const sourceTypes = [
  { value: 'code', label: '代码', icon: '📝' },
  { value: 'doc', label: 'OpenAPI', icon: '📄' },
  { value: 'curl', label: 'cURL', icon: '🔗' },
  { value: 'description', label: '描述', icon: '💭' },
]

const sourceType = ref('code')
const sourceContent = ref('')
const loading = ref(false)
const generatedCases = ref([])
const aiSuggestion = ref('')
const showHistory = ref(false)
const historyItems = ref([])

const options = reactive({
  include_success: true,
  include_error: true,
  include_boundary: false,
  include_performance: false,
})

function getPlaceholder() {
  switch (sourceType.value) {
    case 'code':
      return `// 输入代码片段，例如：
@RestController
@RequestMapping("/api/users")
public class UserController {
    @PostMapping("/login")
    public Result login(@RequestBody LoginRequest request) {
        // ...
    }
}`
    case 'doc':
      return `// 输入 OpenAPI 规范 JSON，例如：
{
  "openapi": "3.0.0",
  "paths": {
    "/api/users/login": {
      "post": {
        "summary": "用户登录",
        "requestBody": {...},
        "responses": {...}
      }
    }
  }
}`
    case 'curl':
      return `// 输入 cURL 命令，例如：
curl -X POST https://api.example.com/api/users/login \\
  -H "Content-Type: application/json" \\
  -d '{"username": "test", "password": "123456"}'`
    default:
      return `// 输入自然语言描述，例如：
生成用户登录接口的测试用例，包括：
1. 正常登录成功
2. 密码错误
3. 用户名为空`
  }
}

async function generateCases() {
  if (!sourceContent.value.trim()) return

  loading.value = true
  generatedCases.value = []
  aiSuggestion.value = ''

  try {
    const response = await fetch(`${API_BASE}/ai-gen/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + (localStorage.getItem('access_token') || '')
      },
      body: JSON.stringify({
        source_type: sourceType.value,
        source_content: sourceContent.value,
        project_id: 1, // TODO: 从当前项目获取
        options: {
          include_success: options.include_success,
          include_error: options.include_error,
          include_boundary: options.include_boundary,
          include_performance: options.include_performance,
        }
      })
    })

    if (response.ok) {
      const data = await response.json()
      generatedCases.value = data.cases.map(c => ({ ...c, accepted: false, ignored: false }))
      
      // 模拟 AI 建议
      aiSuggestion.value = '检测到该接口需要参数校验，建议添加 @Valid 注解以增强接口健壮性。'
    } else {
      alert('生成失败，请重试')
    }
  } catch (err) {
    console.error('生成失败:', err)
    alert('网络错误，请重试')
  } finally {
    loading.value = false
  }
}

function acceptCase(index) {
  generatedCases.value[index].accepted = true
}

function ignoreCase(index) {
  generatedCases.value[index].ignored = true
}

function acceptAllCases() {
  generatedCases.value.forEach(c => {
    c.accepted = true
    c.ignored = false
  })
}

async function loadHistory() {
  try {
    const response = await fetch(`${API_BASE}/ai-gen/history/1`, {
      headers: {
        'Authorization': 'Bearer ' + (localStorage.getItem('access_token') || '')
      }
    })
    if (response.ok) {
      const data = await response.json()
      historyItems.value = data.items
    }
  } catch (err) {
    console.error('加载历史失败:', err)
  }
}

function formatTime(timeStr) {
  if (!timeStr) return ''
  return new Date(timeStr).toLocaleString('zh-CN')
}

// 监听 showHistory 变化
import { watch } from 'vue'
watch(showHistory, (newVal) => {
  if (newVal) {
    loadHistory()
  }
})
</script>

<style scoped>
.ai-studio {
  padding: 24px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
  color: var(--text-primary);
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  border-bottom: 1px solid var(--border-default);
  padding-bottom: 12px;
}

.tabs button {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
}

.tabs button:hover {
  background: var(--bg-tertiary);
}

.tabs button.active {
  background: linear-gradient(135deg, var(--neon-cyan), var(--neon-magenta));
  color: #000;
  font-weight: 600;
}

.studio-content {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  min-height: 0;
}

.input-panel,
.result-panel {
  background: var(--bg-panel);
  border: 1px solid var(--border-default);
  border-radius: 12px;
  padding: 20px;
  overflow-y: auto;
}

.source-selector label,
.editor-container label,
.options-section label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.source-buttons {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-bottom: 16px;
}

.source-buttons button {
  padding: 10px;
  border: 1px solid var(--border-default);
  background: var(--bg-secondary);
  color: var(--text-secondary);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 13px;
}

.source-buttons button:hover {
  border-color: var(--neon-cyan);
}

.source-buttons button.active {
  border-color: var(--neon-cyan);
  background: rgba(0, 255, 255, 0.1);
  color: var(--neon-cyan);
}

.code-editor {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--border-default);
  border-radius: 8px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
  background: var(--bg-secondary);
  color: var(--text-primary);
  resize: vertical;
  box-sizing: border-box;
}

.code-editor:focus {
  outline: none;
  border-color: var(--neon-cyan);
}

.options-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  margin-bottom: 16px;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bg-secondary);
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-secondary);
}

.checkbox-item input {
  accent-color: var(--neon-cyan);
}

.btn-generate {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, var(--neon-cyan), var(--neon-magenta));
  color: #000;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-generate:hover:not(:disabled) {
  box-shadow: 0 0 20px rgba(0, 255, 255, 0.4);
  transform: translateY(-2px);
}

.btn-generate:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 300px;
  color: var(--text-tertiary);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border-default);
  border-top-color: var(--neon-cyan);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.results-count {
  font-size: 14px;
  color: var(--text-secondary);
}

.cases-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.case-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-default);
  border-radius: 10px;
  padding: 16px;
  transition: all 0.2s;
}

.case-card:hover {
  border-color: var(--border-active);
}

.case-card.accepted {
  border-color: var(--success-color);
  background: rgba(82, 196, 26, 0.05);
}

.case-card.ignored {
  opacity: 0.5;
}

.case-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.case-name {
  font-weight: 600;
  color: var(--text-primary);
}

.case-method {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.method-get { background: #e6f7e6; color: #52c41a; }
.method-post { background: #e6f7ff; color: #1890ff; }
.method-put { background: #fff7e6; color: #fa8c16; }
.method-delete { background: #fff1f0; color: #ff4d4f; }

.case-url {
  font-family: monospace;
  font-size: 13px;
  color: var(--neon-cyan);
  margin-bottom: 12px;
  padding: 8px;
  background: var(--bg-tertiary);
  border-radius: 4px;
}

.case-assertions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.assertion-tag {
  padding: 2px 8px;
  background: var(--bg-tertiary);
  border-radius: 10px;
  font-size: 12px;
  color: var(--text-secondary);
}

.case-actions {
  display: flex;
  gap: 8px;
}

.btn-accept,
.btn-ignore {
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-accept {
  background: var(--success-bg);
  color: var(--success-color);
  border: 1px solid var(--success-color);
}

.btn-accept:hover {
  background: var(--success-color);
  color: #fff;
}

.btn-ignore {
  background: transparent;
  color: var(--text-tertiary);
  border: 1px solid var(--border-default);
}

.btn-ignore:hover {
  border-color: var(--error-color);
  color: var(--error-color);
}

.accepted-badge,
.ignored-badge {
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 13px;
}

.accepted-badge {
  background: var(--success-bg);
  color: var(--success-color);
}

.ignored-badge {
  background: var(--bg-tertiary);
  color: var(--text-tertiary);
}

.ai-suggestion {
  margin-top: 20px;
  padding: 16px;
  background: rgba(0, 255, 255, 0.05);
  border: 1px solid var(--neon-cyan);
  border-radius: 10px;
}

.suggestion-header {
  font-weight: 600;
  color: var(--neon-cyan);
  margin-bottom: 8px;
}

.suggestion-content {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background: var(--bg-panel);
  border: 1px solid var(--neon-cyan);
  border-radius: 12px;
  padding: 24px;
  width: 600px;
  max-width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.history-dialog {
  width: 700px;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.dialog-header h2 {
  margin: 0;
  color: var(--neon-cyan);
}

.btn-close {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  font-size: 24px;
  cursor: pointer;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-item {
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: 8px;
  border: 1px solid var(--border-default);
}

.history-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.history-type {
  padding: 2px 8px;
  background: var(--neon-cyan);
  color: #000;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
}

.history-time {
  font-size: 12px;
  color: var(--text-tertiary);
}

.history-preview {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--text-tertiary);
}

.empty-history {
  text-align: center;
  padding: 40px;
  color: var(--text-tertiary);
}

.btn-secondary {
  padding: 8px 16px;
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-default);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary:hover {
  border-color: var(--neon-cyan);
  color: var(--neon-cyan);
}

.btn-primary {
  padding: 8px 16px;
  background: linear-gradient(135deg, var(--neon-cyan), var(--neon-magenta));
  color: #000;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}
</style>
