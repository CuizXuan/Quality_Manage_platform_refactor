<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div
        v-if="modelValue"
        class="cyber-modal-overlay"
        :class="{ 'is-closing': isClosing }"
        @mousedown.self="handleOverlayClick"
      >
        <div
          ref="modalRef"
          class="cyber-modal"
          :class="[
            `cyber-modal--${size}`,
            `cyber-modal--${intent}`,
            { 'is-loading': loading }
          ]"
          role="dialog"
          :aria-labelledby="titleId"
          aria-modal="true"
          @keydown.esc="handleEsc"
          @keydown.tab="handleTab"
        >
          <!-- Header -->
          <div class="cyber-modal__header">
            <div class="cyber-modal__header-left">
              <h2 :id="titleId" class="cyber-modal__title">
                <span v-if="intent === 'ai'" class="cyber-modal__ai-tag">AI</span>
                {{ title }}
              </h2>
              <p v-if="subtitle" class="cyber-modal__subtitle">{{ subtitle }}</p>
            </div>
            <div class="cyber-modal__header-right">
              <slot name="header-extra" />
              <button
                class="cyber-modal__close"
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
          <div class="cyber-modal__body">
            <slot />
          </div>

          <!-- Footer -->
          <div v-if="showFooter" class="cyber-modal__footer">
            <slot name="footer">
              <div class="cyber-modal__footer-left">
                <slot name="footer-left" />
              </div>
              <div class="cyber-modal__footer-right">
                <button
                  class="cyber-modal__btn cyber-modal__btn--secondary"
                  type="button"
                  :disabled="loading"
                  @click="handleCancel"
                >
                  取消
                </button>
                <button
                  class="cyber-modal__btn cyber-modal__btn--primary"
                  :class="`cyber-modal__btn--${intent}`"
                  type="button"
                  :disabled="loading"
                  @click="handleConfirm"
                >
                  <span v-if="loading" class="cyber-modal__spinner"></span>
                  {{ confirmText }}
                </button>
              </div>
            </slot>
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
  subtitle?: string
  size?: 'small' | 'medium' | 'large' | 'xl'
  intent?: 'default' | 'ai' | 'danger' | 'success'
  loading?: boolean
  confirmText?: string
  showFooter?: boolean
  closeOnEsc?: boolean
  closeOnOverlay?: boolean
  destroyOnClose?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  subtitle: '',
  size: 'medium',
  intent: 'default',
  loading: false,
  confirmText: '确定',
  showFooter: true,
  closeOnEsc: true,
  closeOnOverlay: false,
  destroyOnClose: true,
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'confirm'): void
  (e: 'cancel'): void
  (e: 'after-close'): void
}>()

const modalRef = ref<HTMLElement | null>(null)
const isClosing = ref(false)
const titleId = computed(() => `modal-title-${Math.random().toString(36).slice(2, 9)}`)

let previousActiveElement: HTMLElement | null = null

const handleOverlayClick = () => {
  if (props.closeOnOverlay) {
    handleClose()
  }
}

const handleEsc = () => {
  if (props.closeOnEsc) {
    handleClose()
  }
}

const handleTab = (e: KeyboardEvent) => {
  if (!modalRef.value) return
  const focusable = modalRef.value.querySelectorAll<HTMLElement>(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  )
  const first = focusable[0]
  const last = focusable[focusable.length - 1]

  if (e.shiftKey && document.activeElement === first) {
    e.preventDefault()
    last?.focus()
  } else if (!e.shiftKey && document.activeElement === last) {
    e.preventDefault()
    first?.focus()
  }
}

const handleClose = () => {
  if (props.loading) return
  isClosing.value = true
  setTimeout(() => {
    isClosing.value = false
    emit('update:modelValue', false)
    emit('after-close')
    previousActiveElement?.focus()
  }, 200)
}

const handleCancel = () => {
  emit('cancel')
  handleClose()
}

const handleConfirm = () => {
  emit('confirm')
}

const focusFirst = () => {
  nextTick(() => {
    const focusable = modalRef.value?.querySelector<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    )
    focusable?.focus()
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
.cyber-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.72);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 99999;
  padding: 16px;
}

/* Modal Base */
.cyber-modal {
  position: relative;
  background: var(--modal-bg);
  border: 1px solid var(--modal-border);
  border-radius: var(--modal-radius);
  box-shadow: var(--modal-shadow);
  display: flex;
  flex-direction: column;
  max-height: var(--modal-max-height);
  width: var(--modal-size-medium);
  transition: opacity var(--modal-transition-normal), transform var(--modal-transition-normal);
}

.cyber-modal--small { width: var(--modal-size-small); }
.cyber-modal--medium { width: var(--modal-size-medium); }
.cyber-modal--large { width: var(--modal-size-large); max-height: var(--modal-max-height-large); }
.cyber-modal--xl { width: var(--modal-size-xl); max-height: var(--modal-max-height-large); }

/* Intent Variants */
.cyber-modal--ai {
  border-color: var(--modal-ai-accent);
  box-shadow: var(--modal-shadow), 0 0 40px rgba(0, 240, 255, 0.15);
}

.cyber-modal--danger {
  border-color: var(--modal-danger-accent);
}

.cyber-modal--success {
  border-color: var(--modal-success-accent);
}

/* Header */
.cyber-modal__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: var(--modal-padding-header);
  background: var(--modal-header-bg);
  border-bottom: 1px solid var(--modal-border);
  border-radius: var(--modal-radius) var(--modal-radius) 0 0;
  flex-shrink: 0;
}

.cyber-modal__header-left {
  flex: 1;
  min-width: 0;
}

.cyber-modal__title {
  margin: 0;
  font-family: var(--font-title, 'Orbitron', sans-serif);
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 1.5px;
  color: var(--modal-ai-accent);
  display: flex;
  align-items: center;
  gap: 10px;
}

.cyber-modal__ai-tag {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 1px;
  padding: 2px 6px;
  background: var(--modal-ai-accent);
  color: #000;
  border-radius: 3px;
}

.cyber-modal__subtitle {
  margin: 6px 0 0;
  font-size: 12px;
  color: var(--modal-text-secondary);
  line-height: 1.4;
}

.cyber-modal__header-right {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: 16px;
}

.cyber-modal__close {
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

.cyber-modal__close:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: var(--modal-border);
  color: var(--modal-ai-accent);
}

/* Body */
.cyber-modal__body {
  flex: 1;
  overflow-y: auto;
  padding: var(--modal-padding-body);
  scrollbar-width: thin;
  scrollbar-color: var(--modal-border) transparent;
}

.cyber-modal__body::-webkit-scrollbar {
  width: 6px;
}

.cyber-modal__body::-webkit-scrollbar-track {
  background: transparent;
}

.cyber-modal__body::-webkit-scrollbar-thumb {
  background: var(--modal-border);
  border-radius: 3px;
}

/* Footer */
.cyber-modal__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--modal-padding-footer);
  background: var(--modal-footer-bg);
  border-top: 1px solid var(--modal-border);
  border-radius: 0 0 var(--modal-radius) var(--modal-radius);
  flex-shrink: 0;
}

.cyber-modal__footer-left,
.cyber-modal__footer-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* Buttons */
.cyber-modal__btn {
  font-family: var(--font-title, 'Orbitron', sans-serif);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 1px;
  text-transform: uppercase;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  transition: all var(--modal-transition-fast);
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.cyber-modal__btn--secondary {
  background: transparent;
  border: 1px solid var(--modal-border);
  color: var(--modal-text-secondary);
}

.cyber-modal__btn--secondary:hover {
  border-color: var(--modal-ai-accent);
  color: var(--modal-ai-accent);
}

.cyber-modal__btn--primary {
  background: var(--modal-ai-accent);
  border: 1px solid var(--modal-ai-accent);
  color: #000;
}

.cyber-modal__btn--primary:hover {
  filter: brightness(1.1);
  box-shadow: 0 0 16px rgba(0, 240, 255, 0.4);
}

.cyber-modal__btn--danger {
  background: var(--modal-danger-accent);
  border-color: var(--modal-danger-accent);
  color: #fff;
}

.cyber-modal__btn--danger:hover {
  filter: brightness(1.1);
  box-shadow: 0 0 16px rgba(255, 77, 125, 0.4);
}

.cyber-modal__btn--success {
  background: var(--modal-success-accent);
  border-color: var(--modal-success-accent);
  color: #000;
}

.cyber-modal__btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Loading Spinner */
.cyber-modal__spinner {
  width: 14px;
  height: 14px;
  border: 2px solid transparent;
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Transitions */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity var(--modal-transition-normal);
}

.modal-fade-enter-active .cyber-modal,
.modal-fade-leave-active .cyber-modal {
  transition: opacity var(--modal-transition-normal), transform var(--modal-transition-normal);
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.modal-fade-enter-from .cyber-modal,
.modal-fade-leave-to .cyber-modal {
  opacity: 0;
  transform: scale(0.95) translateY(-10px);
}

/* Loading State */
.cyber-modal.is-loading {
  pointer-events: none;
}

/* Light Theme Adjustments */
.theme-light .cyber-modal__title {
  color: var(--modal-ai-accent);
}

.theme-light .cyber-modal__btn--primary {
  color: #fff;
}
</style>