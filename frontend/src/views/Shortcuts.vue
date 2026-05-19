<template>
  <div class="shortcuts-page">
    <div class="page-nav">
      <router-link to="/" class="back-btn">← 返回调试</router-link>
    </div>
    <h2 class="page-title">⌨ 快捷键</h2>
    <div class="shortcuts-list panel">
      <div v-for="s in shortcuts" :key="s.keys" class="shortcut-item">
        <div class="shortcut-keys">
          <kbd v-for="k in s.keys" :key="k">{{ k }}</kbd>
        </div>
        <div class="shortcut-desc">{{ s.desc }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
const shortcuts = [
  { keys: ['Ctrl', 'Enter'], desc: '发送请求' },
  { keys: ['Ctrl', 'S'], desc: '保存到集合' },
  { keys: ['Ctrl', 'Shift', 'P'], desc: '展开请求解析器' },
  { keys: ['Ctrl', 'H'], desc: '聚焦 URL 输入框' },
  { keys: ['Esc'], desc: '取消当前请求' },
  { keys: ['Ctrl', 'L'], desc: '清空当前输入' },
]
</script>

<style scoped>
.shortcuts-page {
  padding: 24px;
  max-width: 600px;
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
  margin-bottom: 16px;
}
.shortcuts-list {
  overflow: hidden;
}
.shortcut-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
}
.shortcut-item:last-child {
  border-bottom: none;
}
.shortcut-keys {
  display: flex;
  gap: 4px;
}
kbd {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 3px 8px;
  font-size: 12px;
  font-family: var(--mono);
  color: var(--primary);
}
.shortcut-desc {
  color: var(--text);
  font-size: 13px;
}
</style>
