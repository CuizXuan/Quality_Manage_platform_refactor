<template>
  <footer class="status-bar">
    <div class="status-left">
      <span class="status-item">
        <span class="status-dot online"></span>
        <span>系统在线</span>
      </span>
      <span class="status-item">
        <span class="separator">|</span>
        <span>v1.0.0</span>
      </span>
    </div>
    <div class="status-right">
      <span class="status-item">
        <span class="label">环境:</span>
        <span class="value">{{ envName }}</span>
      </span>
      <span class="status-item">
        <span class="separator">|</span>
        <span>{{ currentTime }}</span>
      </span>
    </div>
  </footer>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const envName = ref('DEV')
const currentTime = ref('')
let timeInterval = null

function updateTime() {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('en-US', { hour12: false }) + ' UTC'
}

onMounted(() => {
  updateTime()
  timeInterval = setInterval(updateTime, 1000)
})

onUnmounted(() => {
  if (timeInterval) clearInterval(timeInterval)
})
</script>

<style scoped>
.status-bar {
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  background: var(--bg-secondary);
  border-top: 1px solid var(--border-default);
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 100;
  font-family: var(--font-body);
  font-size: 11px;
  color: var(--text-secondary);
}

.status-left, .status-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.status-dot.online {
  background: var(--success);
}

.status-dot.offline {
  background: var(--error);
}

.separator {
  color: var(--text-tertiary);
}

.label {
  color: var(--text-tertiary);
}

.value {
  color: var(--primary);
  font-weight: 500;
}
</style>
