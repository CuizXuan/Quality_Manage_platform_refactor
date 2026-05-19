<template>
  <div class="ai-insight-card" :class="[type, { loading: isLoading }]">
    <div class="card-header">
      <span class="card-icon">{{ icon }}</span>
      <span class="card-title">{{ title }}</span>
      <span v-if="badge" class="card-badge" :class="badgeClass">{{ badge }}</span>
    </div>
    <div class="card-body">
      <div v-if="isLoading" class="card-loading">
        <div class="loading-dots">
          <span></span><span></span><span></span>
        </div>
        <span class="loading-text">{{ loadingText }}</span>
      </div>
      <slot v-else />
    </div>
  </div>
</template>

<script setup>
defineProps({
  type: {
    type: String,
    default: 'default'
  },
  icon: {
    type: String,
    default: '🤖'
  },
  title: {
    type: String,
    default: ''
  },
  badge: {
    type: String,
    default: ''
  },
  badgeClass: {
    type: String,
    default: ''
  },
  isLoading: {
    type: Boolean,
    default: false
  },
  loadingText: {
    type: String,
    default: '分析中...'
  }
})
</script>

<style scoped>
.ai-insight-card {
  padding: 16px 20px;
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  transition: all var(--transition-normal);
}

.ai-insight-card:hover {
  background: var(--bg-card-hover);
  transform: translateY(-2px);
  box-shadow: var(--shadow-card-hover);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.card-icon {
  font-size: 16px;
  line-height: 1;
}

.card-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  flex: 1;
}

.card-badge {
  font-size: 11px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 10px;
  background: var(--bg-card-hover);
  color: var(--text-secondary);
}

.card-badge.success {
  background: var(--success-muted);
  color: var(--success);
}

.card-badge.warning {
  background: var(--warning-muted);
  color: var(--warning);
}

.card-badge.error {
  background: var(--error-muted);
  color: var(--error);
}

.card-body {
  min-height: 40px;
}

/* Loading state */
.card-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 0;
}

.loading-dots {
  display: flex;
  gap: 4px;
}

.loading-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--primary);
  animation: ai-thinking 1.2s ease-in-out infinite;
}

.loading-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.loading-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

.loading-text {
  font-size: 12px;
  color: var(--text-tertiary);
}

@keyframes ai-thinking {
  0%, 100% {
    opacity: 0.3;
    transform: scale(0.8);
  }
  50% {
    opacity: 1;
    transform: scale(1);
  }
}

/* Type variants */
.ai-insight-card.risk .card-icon { color: var(--warning); }
.ai-insight-card.quality .card-icon { color: var(--primary); }
.ai-insight-card.health .card-icon { color: var(--success); }
.ai-insight-card.suggestion .card-icon { color: var(--secondary); }
</style>
