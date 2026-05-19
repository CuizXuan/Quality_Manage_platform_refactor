<template>
  <div class="settings-page">
    <div class="page-nav">
      <router-link to="/" class="back-btn">← 返回调试</router-link>
    </div>
    <h2 class="page-title">⚙ 设置</h2>
    <div class="settings-list panel">
      <div class="setting-item">
        <div class="setting-info">
          <div class="setting-label">默认超时时间</div>
          <div class="setting-desc">单次请求的最大等待时间</div>
        </div>
        <select v-model="settings.defaultTimeout">
          <option value="10">10 秒</option>
          <option value="30">30 秒</option>
          <option value="60">60 秒</option>
          <option value="120">120 秒</option>
        </select>
      </div>
      <div class="setting-item">
        <div class="setting-info">
          <div class="setting-label">历史记录保留</div>
          <div class="setting-desc">自动清理超出时间范围的记录</div>
        </div>
        <select v-model="settings.historyDays">
          <option value="7">7 天</option>
          <option value="30">30 天</option>
          <option value="90">90 天</option>
          <option value="0">永不清理</option>
        </select>
      </div>
      <div class="setting-item">
        <div class="setting-info">
          <div class="setting-label">最大历史数量</div>
          <div class="setting-desc">超出数量后自动清理最旧记录</div>
        </div>
        <select v-model="settings.maxHistoryItems">
          <option value="100">100 条</option>
          <option value="500">500 条</option>
          <option value="1000">1000 条</option>
        </select>
      </div>
    </div>

    <h2 class="page-title" style="margin-top: 24px;">🗄 数据管理</h2>
    <div class="settings-list panel">
      <div class="setting-item">
        <div class="setting-info">
          <div class="setting-label">导出全部数据</div>
          <div class="setting-desc">导出集合、历史记录到 JSON 文件</div>
        </div>
        <button class="btn-secondary" @click="exportData">导出</button>
      </div>
      <div class="setting-item">
        <div class="setting-info">
          <div class="setting-label">清空所有数据</div>
          <div class="setting-desc">清除所有集合、历史记录（不可恢复）</div>
        </div>
        <button class="btn-danger" @click="clearAllData">清空</button>
      </div>
    </div>

    <h2 class="page-title" style="margin-top: 24px;">ℹ 关于</h2>
    <div class="settings-list panel">
      <div class="setting-item">
        <div class="setting-info">
          <div class="setting-label">APIDebug</div>
          <div class="setting-desc">版本 1.0.0 - API 调试工具</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useHistoryStore } from '../stores/history'
import { useCollectionStore } from '../stores/collection'

const historyStore = useHistoryStore()
const collectionStore = useCollectionStore()

const settings = ref({
  defaultTimeout: '30',
  historyDays: '30',
  maxHistoryItems: '500',
})

function exportData() {
  const data = {
    collections: collectionStore.collections,
    history: historyStore.items,
    settings: settings.value,
    exportedAt: new Date().toISOString(),
  }
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `apidebug-backup-${Date.now()}.json`
  a.click()
  URL.revokeObjectURL(url)
}

function clearAllData() {
  if (confirm('确定清空所有数据？此操作不可恢复！')) {
    historyStore.clearAll()
    alert('已清空')
  }
}
</script>

<style scoped>
.settings-page {
  padding: 24px;
  max-width: 700px;
}
.page-nav {
  margin-bottom: 16px;
}
.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--text);
  text-decoration: none;
  font-size: 13px;
  padding: 6px 12px;
  border-radius: 4px;
  transition: all var(--transition-fast);
}
.back-btn:hover {
  color: var(--primary);
  background: var(--bg-secondary);
}
.page-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
}
.settings-list {
  overflow: hidden;
}
.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border);
}
.setting-item:last-child {
  border-bottom: none;
}
.setting-label {
  font-size: 13px;
  color: var(--text-h);
  margin-bottom: 2px;
}
.setting-desc {
  font-size: 11px;
  color: var(--text);
}
.setting-item select {
  padding: 6px 10px;
  background: var(--bg);
  border: 1px solid var(--border);
  color: var(--text-h);
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}
</style>
