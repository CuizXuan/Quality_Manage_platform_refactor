<template>
  <CaseEditDialog
    :model-value="modelValue"
    case-type="functional"
    :case-data="caseData"
    :folder-id="folderId"
    @update:model-value="$emit('update:modelValue', $event)"
    @saved="$emit('saved')"
    @closed="$emit('closed')"
  />
</template>

<script setup>
import CaseEditDialog from './CaseEditDialog.vue'

defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  caseData: {
    type: Object,
    default: null,
  },
  folderId: {
    type: Number,
    default: null,
  },
})

defineEmits(['update:modelValue', 'saved', 'closed'])
</script>
