<template>
  <div class="kv-table">
    <div class="kv-header">
      <span class="col-key">Key</span>
      <span class="col-value">Value</span>
      <span class="col-actions">操作</span>
    </div>
    <div class="kv-body">
      <div v-for="(row, index) in rows" :key="index" class="kv-row">
        <input
          v-model="row.key"
          class="col-key"
          placeholder="Key"
          @input="emitUpdate"
        />
        <input
          v-model="row.value"
          class="col-value"
          placeholder="Value"
          @input="emitUpdate"
        />
        <button class="col-actions btn-del" @click="removeRow(index)">✕</button>
      </div>
      <button class="btn-add-row" @click="addRow">
        + 添加
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => [{ key: '', value: '', enabled: true }],
  },
})
const emit = defineEmits(['update:modelValue'])

const rows = ref([...props.modelValue])

watch(
  () => props.modelValue,
  (val) => {
    rows.value = [...val]
  },
  { deep: true }
)

function emitUpdate() {
  emit('update:modelValue', [...rows.value])
}

function addRow() {
  rows.value.push({ key: '', value: '', enabled: true })
  emitUpdate()
}

function removeRow(index) {
  rows.value.splice(index, 1)
  emitUpdate()
}
</script>

<style scoped>
.kv-table {
  width: 100%;
}
.kv-header {
  display: flex;
  gap: 8px;
  padding: 0 0 6px 0;
  font-size: 11px;
  color: var(--text);
  text-transform: uppercase;
}
.col-key { flex: 1; }
.col-value { flex: 2; }
.col-actions { width: 32px; flex-shrink: 0; }
.kv-row {
  display: flex;
  gap: 8px;
  margin-bottom: 6px;
  align-items: center;
}
.kv-row input {
  padding: 6px 8px;
  font-size: 12px;
  width: 100%;
}
.btn-del {
  width: 28px;
  height: 28px;
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text);
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}
.btn-del:hover {
  background: var(--danger);
  border-color: var(--danger);
  color: white;
}
.btn-add-row {
  background: transparent;
  border: 1px dashed var(--border);
  color: var(--text);
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  width: 100%;
  margin-top: 4px;
}
.btn-add-row:hover {
  border-color: var(--primary);
  color: var(--primary);
}
</style>
