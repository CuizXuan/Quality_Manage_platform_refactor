<template>
  <div class="asset-center">
    <!-- 标签页切换 -->
    <div class="tabs">
      <button 
        v-for="tab in tabs" 
        :key="tab.key"
        :class="{ active: currentTab === tab.key }"
        @click="currentTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- 工具栏 -->
    <div class="toolbar">
      <input
        v-model="searchKeyword"
        type="text"
        placeholder="搜索模板名称..."
        class="search-input"
        @input="handleSearch"
      />
      <select v-model="typeFilter" class="type-filter" @change="loadData">
        <option value="">全部类型</option>
        <option value="case">用例</option>
        <option value="scenario">场景</option>
        <option value="environment">环境</option>
        <option value="report">报告</option>
      </select>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading">加载中...</div>

    <!-- 空状态 -->
    <div v-else-if="items.length === 0" class="empty-state">
      <p>暂无数据</p>
    </div>

    <!-- 列表视图 -->
    <div v-else class="asset-list">
      <div v-for="item in items" :key="item.id" class="asset-card">
        <div class="asset-icon" :class="getTypeClass(item.type)">
          {{ getTypeIcon(item.type) }}
        </div>
        <div class="asset-info">
          <h3 class="asset-name">{{ item.name }}</h3>
          <p class="asset-desc">{{ item.description || '暂无描述' }}</p>
          <div class="asset-tags">
            <span v-for="tag in (item.tags || [])" :key="tag" class="tag">
              {{ tag }}
            </span>
          </div>
        </div>
        <div class="asset-meta">
          <span class="usage-count">{{ item.usage_count || 0 }} 次使用</span>
          <span v-if="item.is_public" class="public-badge">公开</span>
          <span v-if="item.tenant_id" class="private-badge">私有</span>
        </div>
        <div class="asset-actions">
          <button class="btn-primary btn-sm" @click="useTemplate(item)">
            使用
          </button>
          <button v-if="currentTab === 'mine'" class="btn-secondary btn-sm" @click="editTemplate(item)">
            编辑
          </button>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="totalPages > 1" class="pagination">
      <button :disabled="page <= 1" @click="page--; loadData()">上一页</button>
      <span>第 {{ page }} / {{ totalPages }} 页</span>
      <button :disabled="page >= totalPages" @click="page++; loadData()">下一页</button>
    </div>

    <!-- 使用模板弹窗 -->
    <div v-if="showUseDialog" class="dialog-overlay" @click.self="showUseDialog = false">
      <div class="dialog">
        <h2 class="dialog-title">使用模板</h2>
        <div class="template-preview">
          <h3>{{ selectedTemplate?.name }}</h3>
          <p>{{ selectedTemplate?.description }}</p>
          <div class="template-content">
            <pre>{{ JSON.stringify(selectedTemplate?.content, null, 2) }}</pre>
          </div>
        </div>
        <div class="dialog-actions">
          <button class="btn-secondary" @click="showUseDialog = false">关闭</button>
          <button class="btn-primary" @click="copyTemplateContent">复制内容</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const API_BASE = '/api'

const currentTab = ref('market')
const tabs = [
  { key: 'market', label: '模板市场' },
  { key: 'mine', label: '我的模板' },
  { key: 'shared', label: '收到的共享' }
]

const loading = ref(false)
const items = ref([])
const searchKeyword = ref('')
const typeFilter = ref('')
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

const showUseDialog = ref(false)
const selectedTemplate = ref(null)

async function loadData() {
  loading.value = true
  try {
    let url = `${API_BASE}/templates`
    if (currentTab.value === 'mine') {
      url = `${API_BASE}/templates/mine`
    } else if (currentTab.value === 'market') {
      url = `${API_BASE}/templates/market`
    }
    
    const params = new URLSearchParams({
      page: page.value,
      page_size: pageSize.value
    })
    if (searchKeyword.value) params.append('keyword', searchKeyword.value)
    if (typeFilter.value) params.append('type', typeFilter.value)
    
    const response = await fetch(`${url}?${params}`, {
      headers: {
        'Authorization': `Bearer ${authStore.accessToken}`
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      items.value = data.items
      total.value = data.total
    }
  } catch (err) {
    console.error('加载失败:', err)
  } finally {
    loading.value = false
  }
}

let searchTimer = null
function handleSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    page.value = 1
    loadData()
  }, 300)
}

function getTypeClass(type) {
  const map = {
    case: 'type-case',
    scenario: 'type-scenario',
    environment: 'type-environment',
    report: 'type-report'
  }
  return map[type] || 'type-default'
}

function getTypeIcon(type) {
  const map = {
    case: '📋',
    scenario: '📝',
    environment: '🌐',
    report: '📊'
  }
  return map[type] || '📄'
}

function useTemplate(template) {
  selectedTemplate.value = template
  showUseDialog.value = true
}

function editTemplate(template) {
  alert(`编辑模板: ${template.name}`)
}

function copyTemplateContent() {
  if (selectedTemplate.value?.content) {
    navigator.clipboard.writeText(JSON.stringify(selectedTemplate.value.content, null, 2))
    alert('内容已复制到剪贴板')
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.asset-center {
  padding: 24px;
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  border-bottom: 1px solid #eee;
  padding-bottom: 12px;
}

.tabs button {
  padding: 8px 16px;
  border: none;
  background: transparent;
  color: #666;
  font-size: 14px;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
}

.tabs button.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.search-input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid var(--border-color, #ddd);
  border-radius: 8px;
  font-size: 14px;
  background: var(--bg-primary, white);
  color: var(--text-primary, #333);
}

.type-filter {
  padding: 10px 14px;
  border: 1px solid var(--border-color, #ddd);
  border-radius: 8px;
  background: var(--bg-primary, white);
  color: var(--text-primary, #333);
}

.loading, .empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-secondary, #666);
}

.asset-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.asset-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: var(--bg-secondary, white);
  border: 1px solid var(--border-color, #e8e8e8);
  border-radius: 10px;
  transition: box-shadow 0.2s;
}

.asset-card:hover {
  box-shadow: 0 4px 12px var(--shadow-color, rgba(0, 0, 0, 0.08));
}

.asset-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.type-case { background: var(--info-bg, #e6f7ff); }
.type-scenario { background: var(--warning-bg, #fff7e6); }
.type-environment { background: var(--success-bg, #f6ffed); }
.type-report { background: var(--purple-bg, #f9f0ff); }
.type-default { background: var(--bg-tertiary, #f5f5f5); }

.asset-info {
  flex: 1;
}

.asset-name {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary, #333);
}

.asset-desc {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: var(--text-secondary, #666);
}

.asset-tags {
  display: flex;
  gap: 6px;
}

.tag {
  padding: 2px 8px;
  background: var(--bg-tertiary, #f0f0f0);
  border-radius: 10px;
  font-size: 12px;
  color: var(--text-secondary, #666);
}

.asset-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  min-width: 80px;
}

.usage-count {
  font-size: 12px;
  color: var(--text-secondary, #888);
}

.public-badge {
  padding: 2px 8px;
  background: var(--success-bg, #e6f7e6);
  color: var(--success-color, #52c41a);
  border-radius: 10px;
  font-size: 12px;
}

.private-badge {
  padding: 2px 8px;
  background: var(--bg-tertiary, #f5f5f5);
  color: var(--text-tertiary, #999);
  border-radius: 10px;
  font-size: 12px;
}

.asset-actions {
  display: flex;
  gap: 8px;
}

.btn-primary {
  padding: 8px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
}

.btn-secondary {
  padding: 8px 16px;
  background: var(--bg-secondary, white);
  color: var(--text-secondary, #666);
  border: 1px solid var(--border-color, #ddd);
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 13px;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 24px;
}

.pagination button {
  padding: 8px 16px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 6px;
  cursor: pointer;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background: var(--bg-secondary, white);
  border-radius: 12px;
  padding: 24px;
  width: 600px;
  max-width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.dialog-title {
  margin: 0 0 16px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary, #333);
}

.template-preview {
  margin-bottom: 16px;
}

.template-preview h3 {
  margin: 0 0 8px 0;
  color: var(--text-primary, #333);
}

.template-preview p {
  margin: 0 0 12px 0;
  color: var(--text-secondary, #666);
}

.template-content {
  background: var(--bg-tertiary, #f5f5f5);
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
}

.template-content pre {
  margin: 0;
  font-size: 13px;
  white-space: pre-wrap;
  word-break: break-all;
  color: var(--text-primary, #333);
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
