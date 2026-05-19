<template>
  <div class="recent-debug">
    <div class="widget-header">
      <span class="widget-title">最近调试</span>
      <el-button size="small" text @click="$emit('refresh')">刷新</el-button>
    </div>
    <div class="debug-list">
      <div
        v-for="item in items"
        :key="item.id"
        class="debug-item"
        :class="{ active: item.id === activeId }"
        @click="$emit('select', item)"
      >
        <span class="method-badge" :class="item.method.toLowerCase()">{{ item.method }}</span>
        <span class="item-url truncate-cell" :title="item.url">{{ item.url }}</span>
        <span v-if="item.status_code" class="item-status" :class="getStatusClass(item.status_code)">
          {{ item.status_code }}
        </span>
        <span class="item-duration">{{ item.duration_ms ? `${item.duration_ms}ms` : '' }}</span>
        <el-button
          v-if="item.status === 'favorite'"
          class="star-btn"
          size="small"
          text
          @click.stop="$emit('unfavorite', item.id)"
        >
          <StarFilled style="color: var(--el-color-warning);" />
        </el-button>
        <el-button v-else size="small" text @click.stop="$emit('favorite', item.id)">
          <Star />
        </el-button>
      </div>
      <div v-if="loading" class="list-empty">加载中...</div>
      <div v-else-if="items.length === 0" class="list-empty">暂无调试记录</div>
    </div>
  </div>
</template>

<script setup>
import { Star, StarFilled } from '@element-plus/icons-vue'

defineProps({
  items: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  activeId: { type: [Number, String], default: null },
})

defineEmits(['select', 'refresh', 'favorite', 'unfavorite'])

function getStatusClass(code) {
  if (!code) return ''
  if (code >= 200 && code < 300) return 'status-success'
  if (code >= 400 && code < 500) return 'status-warning'
  if (code >= 500) return 'status-danger'
  return ''
}
</script>

<style scoped>
.recent-debug {
  display: flex;
  flex-direction: column;
}

.widget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  margin-bottom: 8px;
}

.widget-title {
  font-weight: 600;
  font-size: 13px;
}

.debug-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  max-height: 220px;
  overflow-y: auto;
}

.debug-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 4px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.15s;
}

.debug-item:hover {
  background: var(--el-fill-color-light);
}

.debug-item.active {
  background: var(--el-color-primary-light-9);
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
.status-warning { color: var(--el-color-warning); }
.status-danger { color: var(--el-color-danger); }

.item-duration {
  font-size: 10px;
  color: var(--el-text-color-secondary);
  font-family: 'JetBrains Mono', monospace;
  flex-shrink: 0;
}

.star-btn {
  padding: 0;
}

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
