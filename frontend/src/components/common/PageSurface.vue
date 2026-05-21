<template>
  <component :is="as" class="page-surface" :class="surfaceClasses">
    <slot />
  </component>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  as: {
    type: String,
    default: 'section',
  },
  variant: {
    type: String,
    default: 'glass',
  },
  padding: {
    type: String,
    default: 'md',
  },
  scrollable: {
    type: Boolean,
    default: false,
  },
})

const surfaceClasses = computed(() => ({
  [`page-surface--${props.variant}`]: true,
  [`page-surface--padding-${props.padding}`]: props.padding !== 'none',
  'page-surface--scrollable': props.scrollable,
}))
</script>
