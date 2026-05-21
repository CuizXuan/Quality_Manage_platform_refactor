<template>
  <CaseModulePage case-type="api" @stats-change="$emit('stats-change', $event)" />
</template>

<script setup>
import CaseModulePage from './CaseModulePage.vue'

defineEmits(['stats-change'])
</script>
