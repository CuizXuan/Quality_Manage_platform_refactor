<template>
  <div class="ai-activity-stream floating-card">
    <div class="stream-header">
      <span class="stream-icon">⚡</span>
      <span class="stream-title">AI Activity</span>
      <button class="clear-btn" @click="clearActivities" title="清空">×</button>
    </div>

    <div class="stream-content">
      <!-- Empty State -->
      <div v-if="activities.length === 0" class="stream-empty">
        <div class="empty-icon">🤖</div>
        <div class="empty-text">AI 活动流将显示在这里</div>
      </div>

      <!-- Activity List -->
      <div v-else class="activity-list">
        <div
          v-for="(activity, idx) in activities"
          :key="idx"
          class="activity-item"
          :class="activity.type"
        >
          <span class="activity-time">{{ activity.time }}</span>
          <span class="activity-icon">{{ activity.icon }}</span>
          <span class="activity-message">{{ activity.message }}</span>
        </div>
      </div>
    </div>

    <!-- Live Indicator -->
    <div class="stream-footer">
      <span class="live-indicator" :class="{ active: isLive }">
        <span class="live-dot"></span>
        {{ isLive ? '实时监控中' : '空闲' }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRequestStore } from '@/stores/request'

const requestStore = useRequestStore()

const activities = ref([])
const isLive = ref(false)

// 添加活动
function addActivity(message, type = 'info', icon = '→') {
  const now = new Date()
  const time = now.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })

  activities.value.unshift({
    time,
    message,
    type,
    icon
  })

  // 最多保留 20 条
  if (activities.value.length > 20) {
    activities.value.pop()
  }

  isLive.value = true

  // 3秒无活动变为空闲
  setTimeout(() => {
    const hasRecentActivity = activities.value.some(a => {
      const activityTime = new Date()
      activityTime.setHours(...a.time.split(':').map(Number))
      return (now - activityTime) < 3000
    })
    if (!hasRecentActivity) {
      isLive.value = false
    }
  }, 3000)
}

// 清空活动
function clearActivities() {
  activities.value = []
  isLive.value = false
}

// 监听请求发送
watch(() => requestStore.loading, (loading) => {
  if (loading) {
    addActivity('开始发送请求...', 'loading', '⟳')
  }
})

// 监听响应
watch(() => requestStore.response, (response) => {
  if (response) {
    const statusCode = response.status_code
    const duration = response.duration_ms

    if (statusCode >= 200 && statusCode < 300) {
      addActivity(`请求成功 [${statusCode}] - ${duration}ms`, 'success', '✓')
    } else if (statusCode >= 400 && statusCode < 500) {
      addActivity(`客户端错误 [${statusCode}]`, 'warning', '⚠')
    } else if (statusCode >= 500) {
      addActivity(`服务器错误 [${statusCode}]`, 'error', '✗')
    } else {
      addActivity(`响应 [${statusCode}] - ${duration}ms`, 'info', '→')
    }

    // 分析响应
    if (response.headers) {
      const contentType = response.headers['content-type'] || ''
      if (contentType.includes('json')) {
        addActivity('检测到 JSON 响应', 'info', '{ }')
      }
    }

    isLive.value = false
  }
})

// 监听错误
watch(() => requestStore.error, (error) => {
  if (error) {
    addActivity(`请求失败: ${error}`, 'error', '✗')
    isLive.value = false
  }
})
</script>

<style scoped>
.ai-activity-stream {
  padding: 14px 18px;
}

.stream-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.stream-icon {
  font-size: 14px;
  color: var(--warning);
}

.stream-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  flex: 1;
}

.clear-btn {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: var(--text-tertiary);
  font-size: 14px;
  cursor: pointer;
  border-radius: 4px;
  transition: all var(--transition-fast);
}

.clear-btn:hover {
  background: var(--bg-card-hover);
  color: var(--text-secondary);
}

.stream-content {
  min-height: 60px;
  max-height: 120px;
  overflow-y: auto;
}

/* Empty State */
.stream-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 16px;
  gap: 8px;
}

.empty-icon {
  font-size: 24px;
  opacity: 0.5;
}

.empty-text {
  font-size: 12px;
  color: var(--text-tertiary);
}

/* Activity List */
.activity-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  background: var(--bg-card);
  animation: slide-in 0.2s ease;
}

@keyframes slide-in {
  from {
    opacity: 0;
    transform: translateX(-8px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.activity-time {
  color: var(--text-tertiary);
  font-family: var(--font-mono);
  font-size: 10px;
  flex-shrink: 0;
}

.activity-icon {
  font-size: 12px;
  flex-shrink: 0;
}

.activity-message {
  color: var(--text-secondary);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.activity-item.success {
  border-left: 2px solid var(--success);
}

.activity-item.success .activity-icon {
  color: var(--success);
}

.activity-item.warning {
  border-left: 2px solid var(--warning);
}

.activity-item.warning .activity-icon {
  color: var(--warning);
}

.activity-item.error {
  border-left: 2px solid var(--error);
}

.activity-item.error .activity-icon {
  color: var(--error);
}

.activity-item.loading {
  border-left: 2px solid var(--primary);
}

.activity-item.loading .activity-icon {
  color: var(--primary);
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Footer */
.stream-footer {
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px solid var(--border-default);
}

.live-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--text-tertiary);
}

.live-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-tertiary);
  transition: all 0.3s ease;
}

.live-indicator.active .live-dot {
  background: var(--success);
  box-shadow: 0 0 6px var(--success);
  animation: pulse 1.5s ease-in-out infinite;
}

.live-indicator.active {
  color: var(--success);
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(1.2); }
}
</style>