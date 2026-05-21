<template>
  <CaseModulePage case-type="functional" @stats-change="$emit('stats-change', $event)" />
</template>

<script setup>
import CaseModulePage from './CaseModulePage.vue'

defineEmits(['stats-change'])
</script>
