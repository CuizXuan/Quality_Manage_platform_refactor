<template>
  <div class="rich-text-editor">
    <QuillEditor
      :content="normalizedContent"
      content-type="html"
      theme="snow"
      :toolbar="toolbarOptions"
      @update:content="handleUpdate"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { QuillEditor } from '@vueup/vue-quill'
import '@vueup/vue-quill/dist/vue-quill.snow.css'

const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['update:modelValue'])

const toolbarOptions = [
  ['bold', 'italic', 'underline', 'strike'],
  [{ list: 'ordered' }, { list: 'bullet' }],
  [{ color: [] }, { background: [] }],
  ['blockquote', 'code-block'],
  ['link'],
  ['clean'],
]

const normalizedContent = computed(() => {
  const value = props.modelValue || ''
  if (value === '<p><br></p>' || value === '<pre>{}</pre>') return ''
  return value
})

function handleUpdate(value) {
  emit('update:modelValue', value || '')
}
</script>

<style scoped>
.rich-text-editor {
  width: 100%;
}

.rich-text-editor :deep(.ql-toolbar.ql-snow) {
  border-color: var(--border-color);
  border-top-left-radius: var(--border-radius-base);
  border-top-right-radius: var(--border-radius-base);
  background: var(--bg-container-soft);
}

.rich-text-editor :deep(.ql-container.ql-snow) {
  min-height: 140px;
  border-color: var(--border-color);
  border-bottom-left-radius: var(--border-radius-base);
  border-bottom-right-radius: var(--border-radius-base);
  background: var(--bg-container);
  color: var(--text-primary);
}

.rich-text-editor :deep(.ql-editor) {
  min-height: 140px;
  color: var(--text-primary);
  font-family: var(--font-sans);
}

.rich-text-editor :deep(.ql-snow .ql-stroke) {
  stroke: var(--text-secondary);
}

.rich-text-editor :deep(.ql-snow .ql-fill) {
  fill: var(--text-secondary);
}

.rich-text-editor :deep(.ql-snow .ql-picker-label),
.rich-text-editor :deep(.ql-snow .ql-picker-item) {
  color: var(--text-primary);
}
</style>
