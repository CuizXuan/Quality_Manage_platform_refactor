<template>
  <Teleport to="body">
    <div class="cyber-toast-container">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="cyber-toast"
          :class="`toast-${toast.type}`"
        >
          <div class="toast-icon">
            <svg v-if="toast.type === 'success'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
            <svg v-else-if="toast.type === 'error'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
            <svg v-else-if="toast.type === 'warning'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
              <line x1="12" y1="9" x2="12" y2="13"></line>
              <line x1="12" y1="17" x2="12.01" y2="17"></line>
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="16" x2="12" y2="12"></line>
              <line x1="12" y1="8" x2="12.01" y2="8"></line>
            </svg>
          </div>
          <div class="toast-content">
            <div class="toast-title">{{ toast.title }}</div>
            <div v-if="toast.message" class="toast-message">{{ toast.message }}</div>
          </div>
          <button class="toast-close" @click="toastStore.removeToast(toast.id)">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup>
import { useToastStore } from '@/stores/toast'

const toastStore = useToastStore()
const { toasts } = toastStore
</script>

<style scoped>
.cyber-toast-container {
  position: fixed;
  top: 15%;
  left: 50%;
  transform: translateX(-50%);
  z-index: 99999;
  display: flex;
  flex-direction: column;
  gap: 8px;
  pointer-events: none;
  align-items: center;
}

.cyber-toast {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px 18px;
  background: rgba(15, 18, 28, 0.78);
  backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 18px;
  min-width: 300px;
  max-width: 360px;
  pointer-events: auto;
  box-shadow:
    0 12px 40px rgba(0, 0, 0, 0.28),
    0 0 0 1px rgba(255, 255, 255, 0.02);
  position: relative;
  overflow: hidden;
}

.cyber-toast::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: transparent;
}

.toast-success::before {
  background: linear-gradient(180deg, var(--success), rgba(34, 197, 94, 0.3));
}
.toast-success .toast-icon {
  color: var(--success);
  filter: drop-shadow(0 0 12px rgba(34, 197, 94, 0.25));
}

.toast-error::before {
  background: linear-gradient(180deg, var(--error), rgba(239, 68, 68, 0.3));
}
.toast-error .toast-icon {
  color: var(--error);
  filter: drop-shadow(0 0 12px rgba(239, 68, 68, 0.25));
}

.toast-warning::before {
  background: linear-gradient(180deg, var(--warning), rgba(245, 158, 11, 0.3));
}
.toast-warning .toast-icon {
  color: var(--warning);
  filter: drop-shadow(0 0 12px rgba(245, 158, 11, 0.25));
}

.toast-info::before {
  background: linear-gradient(180deg, var(--info), rgba(59, 130, 246, 0.3));
}
.toast-info .toast-icon {
  color: var(--info);
  filter: drop-shadow(0 0 12px rgba(59, 130, 246, 0.25));
}

.toast-icon {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  margin-top: 1px;
}

.toast-icon svg {
  width: 100%;
  height: 100%;
}

.toast-content {
  flex: 1;
  min-width: 0;
}

.toast-title {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.92);
  line-height: 1.4;
}

.toast-message {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.52);
  margin-top: 4px;
  line-height: 1.4;
}

.toast-close {
  flex-shrink: 0;
  width: 16px;
  height: 16px;
  padding: 0;
  border: none;
  background: none;
  color: rgba(255, 255, 255, 0.3);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.15s;
}

.toast-close:hover {
  color: rgba(255, 255, 255, 0.6);
}

.toast-close svg {
  width: 100%;
  height: 100%;
}

/* Transitions */
.toast-enter-active {
  transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
}

.toast-leave-active {
  transition: all 0.18s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateY(8px) scale(0.98);
}

.toast-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.toast-move {
  transition: transform 0.3s ease;
}
</style>
