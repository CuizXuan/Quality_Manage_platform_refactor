<template>
  <Teleport to="body">
    <Transition name="drawer-slide">
      <div
        v-if="modelValue"
        class="cyber-drawer-overlay"
        @mousedown.self="handleOverlayClick"
      >
        <div
          ref="drawerRef"
          class="cyber-drawer"
          :class="[`cyber-drawer--${placement}`, { 'is-loading': loading }]"
          role="dialog"
          :aria-labelledby="titleId"
          aria-modal="true"
          tabindex="-1"
          @keydown.esc="handleEsc"
        >
          <!-- Header -->
          <div class="cyber-drawer__header">
            <div class="cyber-drawer__header-left">
              <h2 :id="titleId" class="cyber-drawer__title">{{ title }}</h2>
              <div v-if="status" class="cyber-drawer__status" :class="`cyber-drawer__status--${status}`">
                {{ statusText }}
              </div>
            </div>
            <div class="cyber-drawer__header-right">
              <slot name="header-extra" />
              <button
                class="cyber-drawer__close"
                type="button"
                aria-label="关闭"
                @click="handleClose"
              >
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                  <path d="M4.5 4.5L13.5 13.5M4.5 13.5L13.5 4.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
              </button>
            </div>
          </div>

          <!-- Body -->
          <div class="cyber-drawer__body">
            <slot />
          </div>

          <!-- Footer -->
          <div v-if="$slots.footer" class="cyber-drawer__footer">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'

interface Props {
  modelValue: boolean
  title: string
  placement?: 'left' | 'right'
  width?: string
  status?: 'pending' | 'running' | 'success' | 'error'
  statusText?: string
  loading?: boolean
  closeOnOverlay?: boolean
  destroyOnClose?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  placement: 'right',
  width: '720px',
  status: undefined,
  statusText: '',
  loading: false,
  closeOnOverlay: true,
  destroyOnClose: true,
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'close'): void
  (e: 'after-close'): void
}>()

const drawerRef = ref<HTMLElement | null>(null)
const titleId = computed(() => `drawer-title-${Math.random().toString(36).slice(2, 9)}`)

let previousActiveElement: HTMLElement | null = null

const handleOverlayClick = () => {
  if (props.closeOnOverlay) {
    handleClose()
  }
}

const handleEsc = () => {
  handleClose()
}

const handleClose = () => {
  emit('update:modelValue', false)
  emit('close')
  emit('after-close')
  previousActiveElement?.focus()
}

const focusFirst = () => {
  nextTick(() => {
    drawerRef.value?.focus()
  })
}

watch(() => props.modelValue, (val) => {
  if (val) {
    previousActiveElement = document.activeElement as HTMLElement
    focusFirst()
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }
})

onMounted(() => {
  if (props.modelValue) {
    previousActiveElement = document.activeElement as HTMLElement
    focusFirst()
    document.body.style.overflow = 'hidden'
  }
})

onBeforeUnmount(() => {
  document.body.style.overflow = ''
})
</script>

<style scoped>
/* Overlay */
.cyber-drawer-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(2px);
  z-index: 99999;
}

/* Drawer Base */
.cyber-drawer {
  position: fixed;
  top: 0;
  right: 0;
  height: 100vh;
  width: var(--drawer-width, 720px);
  max-width: calc(100vw - 48px);
  background: var(--modal-bg);
  border-left: 1px solid var(--modal-border);
  box-shadow: var(--modal-shadow);
  display: flex;
  flex-direction: column;
  transition: transform var(--modal-transition-drawer);
  outline: none;
}

.cyber-drawer--left {
  left: 0;
  right: auto;
  border-left: none;
  border-right: 1px solid var(--modal-border);
}

/* Header */
.cyber-drawer__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--modal-padding-header);
  background: var(--modal-header-bg);
  border-bottom: 1px solid var(--modal-border);
  flex-shrink: 0;
}

.cyber-drawer__header-left {
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 0;
}

.cyber-drawer__title {
  margin: 0;
  font-family: var(--font-title, 'Orbitron', sans-serif);
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 1.5px;
  color: var(--modal-ai-accent);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.cyber-drawer__status {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 1px;
  text-transform: uppercase;
  padding: 4px 10px;
  border-radius: 4px;
  flex-shrink: 0;
}

.cyber-drawer__status--pending {
  background: rgba(255, 170, 0, 0.2);
  color: var(--modal-warning-accent);
  border: 1px solid var(--modal-warning-accent);
}

.cyber-drawer__status--running {
  background: rgba(0, 240, 255, 0.2);
  color: var(--modal-ai-accent);
  border: 1px solid var(--modal-ai-accent);
  animation: pulse 1.5s infinite;
}

.cyber-drawer__status--success {
  background: rgba(0, 255, 136, 0.2);
  color: var(--modal-success-accent);
  border: 1px solid var(--modal-success-accent);
}

.cyber-drawer__status--error {
  background: rgba(255, 77, 125, 0.2);
  color: var(--modal-danger-accent);
  border: 1px solid var(--modal-danger-accent);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.cyber-drawer__header-right {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: 16px;
}

.cyber-drawer__close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 6px;
  color: var(--modal-text-secondary);
  cursor: pointer;
  transition: all var(--modal-transition-fast);
}

.cyber-drawer__close:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: var(--modal-border);
  color: var(--modal-ai-accent);
}

/* Body */
.cyber-drawer__body {
  flex: 1;
  overflow-y: auto;
  padding: var(--modal-padding-body);
  scrollbar-width: thin;
  scrollbar-color: var(--modal-border) transparent;
}

.cyber-drawer__body::-webkit-scrollbar {
  width: 6px;
}

.cyber-drawer__body::-webkit-scrollbar-track {
  background: transparent;
}

.cyber-drawer__body::-webkit-scrollbar-thumb {
  background: var(--modal-border);
  border-radius: 3px;
}

/* Footer */
.cyber-drawer__footer {
  padding: var(--modal-padding-footer);
  background: var(--modal-footer-bg);
  border-top: 1px solid var(--modal-border);
  flex-shrink: 0;
}

/* Transitions */
.drawer-slide-enter-active,
.drawer-slide-leave-active {
  transition: opacity var(--modal-transition-drawer);
}

.drawer-slide-enter-active .cyber-drawer,
.drawer-slide-leave-active .cyber-drawer {
  transition: transform var(--modal-transition-drawer);
}

.drawer-slide-enter-from,
.drawer-slide-leave-to {
  opacity: 0;
}

.drawer-slide-enter-from .cyber-drawer--right,
.drawer-slide-leave-to .cyber-drawer--right {
  transform: translateX(100%);
}

.drawer-slide-enter-from .cyber-drawer--left,
.drawer-slide-leave-to .cyber-drawer--left {
  transform: translateX(-100%);
}

/* Light Theme */
.theme-light .cyber-drawer__title {
  color: var(--modal-ai-accent);
}
</style>