<template>
  <div class="kv-editor">
    <div v-for="(item, idx) in modelValue" :key="idx" class="kv-row">
      <el-input v-model="item.key" placeholder="Key" @blur="emitUpdate" />
      <el-input v-model="item.value" placeholder="Value" @blur="emitUpdate" />
      <el-button type="danger" :icon="Delete" circle size="small" @click="remove(idx)" />
    </div>
    <el-button :icon="Plus" size="small" @click="add">添加</el-button>
  </div>
</template>

<script setup>
import { Delete, Plus } from '@element-plus/icons-vue'
import { watch } from 'vue'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  placeholder: { type: String, default: '值' },
})

const emit = defineEmits(['update:modelValue'])

function emitUpdate() {
  emit('update:modelValue', [...props.modelValue])
}

function add() {
  props.modelValue.push({ key: '', value: '' })
  emitUpdate()
}

function remove(idx) {
  props.modelValue.splice(idx, 1)
  emitUpdate()
}
</script>

<style scoped>
.kv-editor {
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.kv-row {
  display: grid;
  grid-template-columns: minmax(160px, 0.72fr) minmax(220px, 1fr) 32px;
  gap: 8px;
  align-items: center;
}

.kv-editor > .el-button {
  width: 100%;
  border-style: dashed;
  color: var(--color-primary);
  background: var(--bg-container-soft);
}

@media (max-width: 900px) {
  .kv-row {
    grid-template-columns: 1fr;
  }
}
</style>

