<template>
  <div class="cyber-confirm-wrapper" ref="wrapperRef">
    <div class="trigger-slot" @click.stop="togglePopover">
      <slot name="trigger">
        <slot></slot>
      </slot>
    </div>

    <Teleport to="body">
      <Transition name="popover">
        <div
          v-if="visible"
          ref="popoverRef"
          class="cyber-popover"
          :class="[
            { 'is-danger': danger },
            placementClass
          ]"
          :style="popoverStyle"
          @mousedown.stop
        >
          <div class="popover-content">
            <div class="popover-icon" v-if="!hideIcon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
              </svg>
            </div>
            <div class="popover-message">
              <div class="popover-title">{{ title }}</div>
            </div>
          </div>
          <div class="popover-actions">
            <button class="btn-cancel" @click="handleCancel">{{ cancelText }}</button>
            <button class="btn-confirm" :class="{ danger, loading: props.loading }" :disabled="props.loading" @click="handleConfirm">
              <span v-if="props.loading" class="loading-spinner">⟳</span>
              <span v-else>{{ okText }}</span>
            </button>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'

const props = defineProps({
  title: {
    type: String,
    default: '确认操作？',
  },
  okText: {
    type: String,
    default: '确认',
  },
  cancelText: {
    type: String,
    default: '取消',
  },
  danger: {
    type: Boolean,
    default: false,
  },
  hideIcon: {
    type: Boolean,
    default: false,
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['confirm', 'cancel'])

const wrapperRef = ref(null)
const popoverRef = ref(null)
const visible = ref(false)
const popoverStyle = ref({})
const placementClass = ref('')
let isUnmounted = false

// Ant Design Popconfirm-style positioning with viewport boundary detection
function getPopoverPosition() {
  if (!wrapperRef.value) return {}
  const rect = wrapperRef.value.getBoundingClientRect()
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight
  const popoverWidth = 260 // approximate width, will be adjusted after render
  const popoverHeight = 140 // approximate height
  const offset = 8

  let top, left
  let placement = 'bottom'

  // Calculate horizontal position
  const spaceRight = viewportWidth - rect.right
  const spaceLeft = rect.left

  if (spaceRight >= popoverWidth && rect.left + popoverWidth <= viewportWidth) {
    // Normal: position below trigger, left-aligned
    left = rect.left
  } else if (spaceRight < popoverWidth && spaceLeft >= popoverWidth) {
    // Flip to left side of trigger
    left = rect.right - popoverWidth
    placement = 'left'
  } else {
    // Edge case: center it
    left = Math.max(8, (viewportWidth - popoverWidth) / 2)
  }

  // Calculate vertical position
  const spaceBelow = viewportHeight - rect.bottom
  const spaceAbove = rect.top

  if (spaceBelow >= popoverHeight + offset) {
    top = rect.bottom + offset
  } else if (spaceAbove >= popoverHeight + offset) {
    top = rect.top - popoverHeight - offset
    placement = 'top'
  } else {
    // Fallback: position below anyway
    top = rect.bottom + offset
  }

  // Ensure within viewport horizontally
  left = Math.max(8, Math.min(left, viewportWidth - popoverWidth - 8))

  placementClass.value = `placement-${placement}`

  return {
    position: 'fixed',
    top: `${top}px`,
    left: `${left}px`,
    zIndex: 99999,
  }
}

function updatePosition() {
  if (visible.value) {
    popoverStyle.value = getPopoverPosition()
  }
}

// Re-calculate position after popover renders to get exact dimensions
watch(visible, (val) => {
  if (val) {
    nextTick(() => {
      if (isUnmounted || !popoverRef.value || !wrapperRef.value) return
      const rect = wrapperRef.value.getBoundingClientRect()
      const popRect = popoverRef.value.getBoundingClientRect()
      const viewportWidth = window.innerWidth
      const viewportHeight = window.innerHeight
      const offset = 8

      let top, left
      let placement = 'bottom'

      const spaceRight = viewportWidth - rect.right
      const spaceBelow = viewportHeight - rect.bottom
      const spaceAbove = rect.top

      const actualWidth = popRect.width || 260
      const actualHeight = popRect.height || 140

      // Horizontal
      if (rect.left + actualWidth <= viewportWidth - 8) {
        left = rect.left
      } else if (spaceRight >= actualWidth) {
        left = rect.right
      } else {
        left = Math.max(8, viewportWidth - actualWidth - 8)
      }

      // Vertical
      if (spaceBelow >= actualHeight + offset) {
        top = rect.bottom + offset
      } else if (spaceAbove >= actualHeight + offset) {
        top = rect.top - actualHeight - offset
        placement = 'top'
      } else {
        top = rect.bottom + offset
      }

      placementClass.value = `placement-${placement}`
      popoverStyle.value = {
        position: 'fixed',
        top: `${top}px`,
        left: `${left}px`,
        zIndex: 99999,
      }
    })
  }
})

function togglePopover() {
  if (visible.value) {
    close()
  } else {
    show()
  }
}

function show() {
  visible.value = true
  nextTick(() => updatePosition())
}

function close() {
  visible.value = false
  emit('cancel')
}

function handleConfirm() {
  emit('confirm')
  close()
}

function handleCancel() {
  close()
}

function onDocumentMousedown(e) {
  if (!wrapperRef.value) return close()
  if (!wrapperRef.value.contains(e.target)) {
    close()
  }
}

function onDocumentKeydown(e) {
  if (e.key === 'Escape' && visible.value) {
    close()
  }
}

// Handle scroll and resize
function onWindowScroll() {
  if (visible.value) updatePosition()
}
function onWindowResize() {
  if (visible.value) updatePosition()
}

onMounted(() => {
  document.addEventListener('mousedown', onDocumentMousedown)
  document.addEventListener('keydown', onDocumentKeydown)
  window.addEventListener('scroll', onWindowScroll, true)
  window.addEventListener('resize', onWindowResize)
})

onUnmounted(() => {
  isUnmounted = true
  // 强制立即关闭弹窗，防止 parentNode null 错误
  // 当父组件 DOM 被移除时（如删除列表项），Transition 还在执行 leave 动画
  // 此时 popover 已脱离 DOM，强行触发动画完成避免 parentNode 报错
  if (visible.value) {
    visible.value = false
  }
  document.removeEventListener('mousedown', onDocumentMousedown)
  document.removeEventListener('keydown', onDocumentKeydown)
  window.removeEventListener('scroll', onWindowScroll, true)
  window.removeEventListener('resize', onWindowResize)
})

// 暴露 close 方法供父组件手动控制关闭
defineExpose({ close })
</script>

<style scoped>
.cyber-confirm-wrapper {
  display: inline-block;
  position: relative;
}

.trigger-slot {
  cursor: pointer;
}

.cyber-popover {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: 14px 16px;
  min-width: 200px;
  max-width: 320px;
  box-shadow: var(--shadow-xl);
}

.cyber-popover.is-danger {
  border-color: var(--error-border);
}

.cyber-popover.placement-top {
  --popover-arrow-direction: downward;
}

.cyber-popover.placement-left {
  --popover-arrow-direction: rightward;
}

.popover-content {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 12px;
}

.popover-icon {
  flex-shrink: 0;
  width: 16px;
  height: 16px;
  color: var(--warning);
  margin-top: 1px;
}

.is-danger .popover-icon {
  color: var(--error);
}

.popover-icon svg {
  width: 100%;
  height: 100%;
}

.popover-message {
  flex: 1;
}

.popover-title {
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--text-primary);
  line-height: 1.5;
}

.popover-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.btn-cancel,
.btn-confirm {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 6px 14px;
  border-radius: var(--radius-sm);
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  border: 1px solid var(--border-default);
  background: var(--bg-card);
  color: var(--text-secondary);
}

.btn-cancel:hover {
  background: var(--bg-card-hover);
  color: var(--text-primary);
  border-color: var(--border-hover);
}

.btn-confirm {
  border-color: var(--primary);
  color: var(--primary);
  background: var(--primary-muted);
}

.btn-confirm:hover {
  background: var(--primary);
  color: white;
}

.btn-confirm.danger {
  border-color: var(--error);
  color: var(--error);
  background: var(--error-muted);
}

.btn-confirm.danger:hover {
  background: var(--error);
  color: white;
}

.btn-confirm.loading {
  cursor: not-allowed;
  opacity: 0.7;
}

.loading-spinner {
  display: inline-block;
  animation: spin 1s linear infinite;
  font-size: 12px;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.popover-enter-active {
  transition: opacity 0.2s ease-out, transform 0.2s ease-out;
}
.popover-leave-active {
  transition: opacity 0.15s ease-in;
}
.popover-enter-from {
  opacity: 0;
  transform: scale(0.95);
}
.popover-leave-to {
  opacity: 0;
}
.popover-enter-to,
.popover-leave-from {
  opacity: 1;
  transform: scale(1);
}
</style>
