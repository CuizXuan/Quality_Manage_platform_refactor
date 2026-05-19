<template>
  <CyberModal
    v-model="visible"
    :title="isEdit ? '编辑分类' : '新增分类'"
    size="small"
    :confirm-text="isEdit ? '保存' : '创建'"
    :loading="loading"
    @confirm="submit"
    @cancel="handleCancel"
    @after-close="handleAfterClose"
  >
    <div class="form-group">
      <label class="form-label">分类名称</label>
      <input
        v-model="form.name"
        class="form-input"
        type="text"
        placeholder="请输入分类名称"
        maxlength="200"
        @keydown.enter="submit"
      />
    </div>
    <div class="form-group">
      <label class="form-label">排序</label>
      <input
        v-model.number="form.sort_order"
        class="form-input form-input--number"
        type="number"
        min="0"
        max="9999"
      />
    </div>
  </CyberModal>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { createCaseFolder, updateCaseFolder } from '@/api/caseFolders'
import { ElMessage } from 'element-plus'
import CyberModal from '@/components/common/modal/CyberModal.vue'

const visible = ref(false)
const isEdit = ref(false)
const editingId = ref<number | null>(null)
const loading = ref(false)
const form = ref({ name: '', sort_order: 0 })

watch(visible, (val) => {
  if (!val) {
    resetForm()
  }
})

function resetForm() {
  form.value = { name: '', sort_order: 0 }
  isEdit.value = false
  editingId.value = null
  loading.value = false
}

function open(row?: { id: number; name: string; sort_order?: number }) {
  if (row) {
    isEdit.value = true
    editingId.value = row.id
    form.value = { name: row.name, sort_order: row.sort_order ?? 0 }
  } else {
    isEdit.value = false
    editingId.value = null
    form.value = { name: '', sort_order: 0 }
  }
  visible.value = true
}

async function submit() {
  if (!form.value.name.trim()) {
    ElMessage.warning('请输入分类名称')
    return
  }
  loading.value = true
  try {
    if (isEdit.value && editingId.value) {
      await updateCaseFolder(editingId.value, form.value)
      ElMessage.success('编辑成功')
    } else {
      await createCaseFolder(form.value)
      ElMessage.success('创建成功')
    }
    visible.value = false
    emit('refresh')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '操作失败')
  } finally {
    loading.value = false
  }
}

function handleCancel() {
  visible.value = false
}

function handleAfterClose() {
  resetForm()
}

const emit = defineEmits<{
  (e: 'refresh'): void
}>()

defineExpose({ open })
</script>

<style scoped>
.form-group {
  margin-bottom: 18px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-label {
  display: block;
  font-family: var(--font-title, 'Orbitron', sans-serif);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: var(--modal-text-secondary, #888);
  margin-bottom: 8px;
}

.form-input {
  width: 100%;
  padding: 10px 14px;
  background: var(--bg-secondary, #0a0a0f);
  border: 1px solid var(--modal-border, rgba(0, 255, 255, 0.22));
  border-radius: 4px;
  color: var(--modal-text-primary, #e0e0e0);
  font-family: var(--font-mono, 'Fira Code', monospace);
  font-size: 13px;
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
  box-sizing: border-box;
}

.form-input:focus {
  border-color: var(--modal-ai-accent, #00f0ff);
  box-shadow: 0 0 0 2px rgba(0, 240, 255, 0.15);
}

.form-input::placeholder {
  color: var(--modal-text-muted, #666);
}

.form-input--number {
  width: 120px;
}
</style>