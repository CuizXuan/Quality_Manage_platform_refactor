<template>
  <aside class="sidebar">
    <div class="sidebar-tabs">
      <button
        :class="{ active: activeTab === 'collections' }"
        @click="activeTab = 'collections'"
      >
        <span class="tab-icon">☰</span>
        <span>集合</span>
      </button>
      <button
        :class="{ active: activeTab === 'history' }"
        @click="activeTab = 'history'"
      >
        <span class="tab-icon">◷</span>
        <span>历史</span>
      </button>
    </div>

    <!-- 集合视图 -->
    <div v-show="activeTab === 'collections'" class="sidebar-content">
      <div class="sidebar-toolbar">
        <input
          v-model="searchKeyword"
          placeholder="搜索..."
          class="sidebar-input"
        />
        <button class="sidebar-btn-small" @click="showAddCollection = true" title="新建集合">+</button>
      </div>

      <!-- 添加集合弹窗 -->
      <div v-if="showAddCollection" class="inline-input">
        <input
          v-model="newCollectionName"
          placeholder="集合名称"
          class="sidebar-input"
          @keyup.enter="createCollection"
          ref="newColInput"
        />
        <button class="sidebar-btn-small success" @click="createCollection">✓</button>
        <button class="sidebar-btn-small danger" @click="showAddCollection = false">✕</button>
      </div>

      <!-- 集合树 -->
      <div class="collection-tree">
        <div
          v-for="col in filteredCollections"
          :key="col.id"
          class="collection-item"
        >
          <div class="collection-header" @click="toggleCollection(col.id)">
            <span class="expand-icon">{{ isExpanded(col.id) ? '📂' : '📁' }}</span>
            <span class="col-name">{{ col.name }}</span>
            <span class="col-count">[{{ col.requests.length }}]</span>
            <button
              class="col-delete-btn"
              @click.stop="deleteCollection(col.id)"
              title="删除集合"
            >✕</button>
          </div>
          <div v-show="isExpanded(col.id)" class="request-list">
            <div
              v-for="req in col.requests"
              :key="req.id"
              class="request-item"
              @click="loadRequest(req)"
            >
              <span class="method-badge" :class="'method-' + req.method.toLowerCase()">
                {{ req.method }}
              </span>
              <span class="request-name">{{ req.name || req.url }}</span>
              <button
                class="req-delete-btn"
                @click.stop="removeRequest(col.id, req.id)"
                title="删除请求"
              >✕</button>
            </div>
            <div v-if="col.requests.length === 0" class="empty-tip">
              -- EMPTY --
            </div>
          </div>
        </div>
        <div v-if="filteredCollections.length === 0" class="empty-tip">
          <span>// 暂无数据</span>
        </div>
      </div>
    </div>

    <!-- 历史视图 -->
    <div v-show="activeTab === 'history'" class="sidebar-content">
      <div class="sidebar-toolbar">
        <input
          v-model="historyKeyword"
          placeholder="搜索..."
          class="sidebar-input"
        />
        <button class="sidebar-btn-small danger" @click="clearHistory" title="清空历史">🗑</button>
      </div>
      <div class="history-list">
        <div
          v-for="item in filteredHistory"
          :key="item.id"
          class="history-item"
          @click="loadHistoryItem(item)"
        >
          <div class="history-meta">
            <span class="method-badge" :class="'method-' + item.method.toLowerCase()">
              {{ item.method }}
            </span>
            <span class="history-time">{{ formatTime(item.createdAt) }}</span>
          </div>
          <div class="history-url">{{ item.url }}</div>
          <div class="history-status" :class="getStatusClass(item.statusCode)">
            {{ item.statusCode || 'ERR' }}
          </div>
        </div>
        <div v-if="filteredHistory.length === 0" class="empty-tip">
          <span>// 暂无历史</span>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { useCollectionStore } from '../../stores/collection'
import { useHistoryStore } from '../../stores/history'
import { useRequestStore } from '../../stores/request'

const emit = defineEmits(['load-request'])

const collectionStore = useCollectionStore()
const historyStore = useHistoryStore()
const requestStore = useRequestStore()

const activeTab = ref('collections')
const searchKeyword = ref('')
const historyKeyword = ref('')
const showAddCollection = ref(false)
const newCollectionName = ref('')
const newColInput = ref(null)
const expandedCollections = ref([])

const filteredCollections = computed(() => {
  if (!searchKeyword.value) return collectionStore.collections
  const kw = searchKeyword.value.toLowerCase()
  return collectionStore.collections.filter(col =>
    col.name.toLowerCase().includes(kw) ||
    col.requests.some(r => r.name?.toLowerCase().includes(kw) || r.url?.toLowerCase().includes(kw))
  )
})

const filteredHistory = computed(() => {
  return historyStore.getFiltered({ keyword: historyKeyword.value })
})

function isExpanded(id) {
  return expandedCollections.value.includes(id)
}

function toggleCollection(id) {
  const idx = expandedCollections.value.indexOf(id)
  if (idx >= 0) {
    expandedCollections.value.splice(idx, 1)
  } else {
    expandedCollections.value.push(id)
  }
}

function deleteCollection(id) {
  if (confirm('确定删除该集合？')) {
    collectionStore.deleteCollection(id)
    // 从展开列表中移除
    const idx = expandedCollections.value.indexOf(id)
    if (idx >= 0) expandedCollections.value.splice(idx, 1)
  }
}

function removeRequest(colId, reqId) {
  collectionStore.removeRequest(colId, reqId)
}

function createCollection() {
  if (newCollectionName.value.trim()) {
    collectionStore.createCollection(newCollectionName.value.trim())
    newCollectionName.value = ''
    showAddCollection.value = false
  }
}

function clearHistory() {
  if (confirm('确定清空所有历史记录？')) {
    historyStore.clearAll()
  }
}

function loadRequest(req) {
  requestStore.setRequest({
    method: req.method,
    url: req.url,
    fullUrl: req.fullUrl || req.url,
    headers: req.headers || {},
    params: req.params || {},
    body: req.body || '',
  })
  emit('load-request')
}

function loadHistoryItem(item) {
  requestStore.setRequest({
    method: item.method,
    url: item.url,
    fullUrl: item.fullUrl || item.url,
    headers: item.headers || {},
    params: item.params || {},
    body: item.body || '',
  })
  emit('load-request')
}

function formatTime(isoString) {
  if (!isoString) return ''
  const date = new Date(isoString)
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return 'NOW'
  if (minutes < 60) return `${minutes}m`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h`
  return `${Math.floor(hours / 24)}d`
}

function getStatusClass(code) {
  if (!code) return 'status-error'
  if (code >= 200 && code < 300) return 'status-success'
  if (code >= 400) return 'status-error'
  return ''
}
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  height: calc(100vh - var(--header-height) - 28px);
  background: var(--bg-panel);
  border-right: 1px solid var(--border-default);
  display: flex;
  flex-direction: column;
  position: fixed;
  top: var(--header-height);
  left: 0;
  overflow: hidden;
  font-size: 13px;
  z-index: 50;
}

.sidebar-tabs {
  display: flex;
  border-bottom: 1px solid var(--border-default);
}

.sidebar-tabs button {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 12px 8px;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text-secondary);
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.sidebar-tabs button.active {
  color: var(--primary);
  background: var(--primary-muted);
  border-bottom-color: var(--primary);
}

.sidebar-tabs button:hover:not(.active) {
  color: var(--text-primary);
  background: var(--bg-card);
}

.tab-icon {
  font-size: 14px;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  position: relative;
}

.sidebar-toolbar {
  display: flex;
  gap: 6px;
  margin-bottom: 8px;
}

.sidebar-input {
  flex: 1;
  padding: 6px 10px;
  font-family: var(--font-body);
  font-size: 13px;
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  color: var(--text-primary);
  outline: none;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.sidebar-input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-muted);
}

.sidebar-input::placeholder {
  color: var(--text-tertiary);
}

.sidebar-btn-small {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  color: var(--text-secondary);
  font-size: 14px;
  cursor: pointer;
  transition: all var(--transition-fast);
  border-radius: var(--radius-sm);
}

.sidebar-btn-small:hover {
  background: var(--bg-card-hover);
  border-color: var(--border-hover);
  color: var(--text-primary);
}

.sidebar-btn-small.success {
  border-color: var(--success-border);
  color: var(--success);
}

.sidebar-btn-small.danger {
  border-color: var(--error-border);
  color: var(--error);
}

.inline-input {
  display: flex;
  gap: 4px;
  margin-bottom: 8px;
}

.inline-input .sidebar-input {
  flex: 1;
}

.collection-tree {
  overflow: hidden;
}

.collection-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  cursor: pointer;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-family: var(--font-body);
  font-size: 13px;
  transition: all var(--transition-fast);
  overflow: hidden;
  min-width: 0;
}

.collection-header:hover {
  background: var(--bg-card);
  color: var(--text-primary);
}

.col-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.col-count {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-left: auto;
  flex-shrink: 0;
}

.col-delete-btn,
.req-delete-btn {
  width: 18px;
  height: 18px;
  display: none;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-xs);
  color: var(--text-secondary);
  font-size: 10px;
  cursor: pointer;
  flex-shrink: 0;
  transition: all var(--transition-fast);
  margin-left: 4px;
}

.collection-header:hover .col-delete-btn,
.request-item:hover .req-delete-btn {
  display: flex;
}

.col-delete-btn:hover,
.req-delete-btn:hover {
  background: var(--error-muted);
  color: var(--error);
}

.request-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px 8px 24px;
  cursor: pointer;
  border-radius: var(--radius-sm);
  font-size: 13px;
  border-left: 2px solid transparent;
  transition: all var(--transition-fast);
  position: relative;
  min-width: 0;
  overflow: hidden;
}

.request-item:hover {
  background: var(--bg-card);
  border-left-color: var(--primary);
}

.request-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-primary);
  min-width: 0;
  font-size: 13px;
}

.history-item {
  padding: 10px;
  cursor: pointer;
  border-radius: var(--radius-sm);
  margin-bottom: 4px;
  position: relative;
  border: 1px solid transparent;
  transition: all var(--transition-fast);
}

.history-item:hover {
  background: var(--bg-card);
  border-color: var(--border-default);
}

.history-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.history-time {
  color: var(--text-secondary);
  font-size: 10px;
}

.history-url {
  font-size: 11px;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: var(--font-mono);
}

.history-status {
  position: absolute;
  right: 10px;
  top: 10px;
  font-family: var(--font-body);
  font-size: 10px;
  font-weight: 600;
}

.status-success { color: var(--success); }
.status-error { color: var(--error); }

.empty-tip {
  text-align: center;
  color: var(--text-secondary);
  font-size: 12px;
  padding: 20px;
}
</style>
