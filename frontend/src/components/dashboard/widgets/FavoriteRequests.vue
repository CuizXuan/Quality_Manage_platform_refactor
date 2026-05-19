<template>
  <div class="favorite-requests">
    <div class="widget-header">
      <span class="widget-title">收藏请求</span>
    </div>
    <div class="request-list">
      <div v-for="item in items" :key="item.id" class="request-item">
        <span class="method-badge" :class="item.method.toLowerCase()">{{ item.method }}</span>
        <span class="item-url truncate-cell" :title="item.url">{{ item.url }}</span>
        <span v-if="item.status_code" class="item-status" :class="getStatusClass(item.status_code)">{{ item.status_code }}</span>
        <el-button size="small" text :loading="sendingId === item.id" @click="$emit('send', item)">发送</el-button>
        <el-button size="small" text @click="$emit('unfavorite', item.id)">取消</el-button>
      </div>
      <div v-if="loading" class="list-empty">加载中...</div>
      <div v-else-if="items.length === 0" class="list-empty">暂无收藏请求</div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  items: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})

defineEmits(['select', 'send', 'unfavorite'])

const sendingId = ref(null)

function getStatusClass(code) {
  if (!code) return ''
  if (code >= 200 && code < 300) return 'status-success'
  if (code >= 400) return 'status-danger'
  return ''
}
</script>

<style scoped>
.favorite-requests {
  display: flex;
  flex-direction: column;
}

.widget-header {
  padding-bottom: 8px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  margin-bottom: 8px;
}

.widget-title {
  font-weight: 600;
  font-size: 13px;
}

.request-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 180px;
  overflow-y: auto;
}

.request-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 4px;
  border-radius: 4px;
}

.request-item:hover {
  background: var(--el-fill-color-light);
}

.method-badge {
  flex-shrink: 0;
}

.item-url {
  flex: 1;
  font-size: 12px;
  font-family: 'JetBrains Mono', monospace;
  min-width: 0;
}

.item-status {
  font-size: 11px;
  font-weight: 600;
  font-family: 'JetBrains Mono', monospace;
}

.status-success { color: var(--el-color-success); }
.status-danger { color: var(--el-color-danger); }

.list-empty {
  padding: 16px;
  text-align: center;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.truncate-cell {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
