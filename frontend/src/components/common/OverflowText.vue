<template>
  <el-tooltip
    :content="tooltipText"
    :disabled="!tooltipEnabled"
    :hide-after="0"
    :placement="placement"
    :popper-class="tooltipClass"
    :show-after="showAfter"
    :teleported="true"
  >
    <component
      :is="as"
      v-bind="$attrs"
      class="overflow-text"
      :class="textClass"
      :style="textStyle"
      :type="buttonType"
    >
      <slot>{{ displayText }}</slot>
    </component>
  </el-tooltip>
</template>

<script setup>
import { computed } from 'vue'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  text: {
    type: [String, Number],
    default: '',
  },
  placeholder: {
    type: String,
    default: '-',
  },
  as: {
    type: String,
    default: 'span',
  },
  rows: {
    type: Number,
    default: 1,
  },
  placement: {
    type: String,
    default: 'top',
  },
  showAfter: {
    type: Number,
    default: 260,
  },
  tooltip: {
    type: Boolean,
    default: true,
  },
  muted: {
    type: Boolean,
    default: false,
  },
  primary: {
    type: Boolean,
    default: false,
  },
  strong: {
    type: Boolean,
    default: false,
  },
  mono: {
    type: Boolean,
    default: false,
  },
  popperClass: {
    type: String,
    default: '',
  },
})

const normalizedText = computed(() => String(props.text ?? '').trim())
const displayText = computed(() => normalizedText.value || props.placeholder)
const tooltipText = computed(() => normalizedText.value || props.placeholder)
const tooltipEnabled = computed(() => props.tooltip && Boolean(normalizedText.value))
const buttonType = computed(() => (props.as === 'button' ? 'button' : undefined))
const tooltipClass = computed(() => ['overflow-text-tooltip', props.popperClass].filter(Boolean).join(' '))

const textClass = computed(() => ({
  'overflow-text--single': props.rows === 1,
  'overflow-text--multi': props.rows > 1,
  'overflow-text--wrap': props.rows < 1,
  'overflow-text--muted': props.muted,
  'overflow-text--primary': props.primary,
  'overflow-text--strong': props.strong,
  'overflow-text--mono': props.mono,
  'overflow-text--empty': !normalizedText.value,
}))

const textStyle = computed(() => {
  if (props.rows > 1) return { '--overflow-text-rows': props.rows }
  return {}
})
</script>

<style scoped>
.overflow-text {
  display: inline-block;
  max-width: 100%;
  min-width: 0;
  border: 0;
  background: transparent;
  color: inherit;
  font: inherit;
  line-height: 1.45;
  overflow-wrap: anywhere;
  text-align: left;
  vertical-align: middle;
  word-break: break-word;
}

.overflow-text--single {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.overflow-text--multi {
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: var(--overflow-text-rows);
}

.overflow-text--wrap {
  display: block;
  white-space: normal;
}

.overflow-text--muted {
  color: var(--text-secondary);
}

.overflow-text--primary {
  color: var(--color-primary);
}

.overflow-text--strong {
  color: var(--text-strong);
  font-weight: 700;
}

.overflow-text--primary.overflow-text--strong {
  color: var(--color-primary);
}

.overflow-text--mono {
  font-family: var(--font-mono);
}

.overflow-text--empty {
  color: var(--text-secondary);
}

button.overflow-text {
  width: 100%;
  padding: 0;
  cursor: pointer;
}

button.overflow-text:hover {
  color: var(--color-primary-hover);
}
</style>
