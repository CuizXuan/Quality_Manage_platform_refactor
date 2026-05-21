<template>
  <el-dialog
    :model-value="modelValue"
    :title="isNew ? '新建用例' : '编辑用例'"
    width="min(1180px, 92vw)"
    top="4vh"
    destroy-on-close
    @update:model-value="emit('update:modelValue', $event)"
    @closed="emit('closed')"
  >
    <div class="editor-dialog">
      <CaseDetail
        ref="detailRef"
        :case-data="caseData"
        @saved="handleSaved"
        @deleted="handleDeleted"
      />
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleCancel">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, ref } from 'vue'
import CaseDetail from '@/views/case/CaseDetail.vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  caseData: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['update:modelValue', 'saved', 'deleted', 'closed'])
const detailRef = ref(null)

const isNew = computed(() => !props.caseData?.id)

function handleSave() {
  detailRef.value?.handleSave?.()
}

function handleCancel() {
  detailRef.value?.handleCancel?.()
}

function handleSaved() {
  emit('saved')
  emit('update:modelValue', false)
}

function handleDeleted() {
  emit('deleted')
  emit('update:modelValue', false)
}
</script>

<style scoped>
.editor-dialog {
  min-height: 72vh;
}

.editor-dialog :deep(.case-detail) {
  height: 72vh;
}

.editor-dialog :deep(.detail-form) {
  max-height: calc(72vh - 72px);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
}
</style>
