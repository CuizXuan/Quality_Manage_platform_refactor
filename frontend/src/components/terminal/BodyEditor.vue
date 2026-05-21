<template>
  <div class="body-editor">
    <div class="body-type-select">
      <el-radio-group v-model="localBodyType">
        <el-radio label="none">none</el-radio>
        <el-radio label="json">JSON</el-radio>
        <el-radio label="form">form-data</el-radio>
        <el-radio label="raw">Raw</el-radio>
      </el-radio-group>
      <el-button v-if="localBodyType === 'json'" size="small" text @click="formatJson">格式化</el-button>
    </div>
    <el-input
      v-if="localBodyType !== 'none'"
      v-model="localBody"
      type="textarea"
      :rows="6"
      placeholder="请求体内容"
      class="body-textarea"
      @blur="emitUpdate"
    />
  </div>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  bodyType: { type: String, default: 'none' },
})

const emit = defineEmits(['update:modelValue', 'update:bodyType'])

const localBody = ref(props.modelValue)
const localBodyType = ref(props.bodyType)

watch(() => props.modelValue, (v) => { localBody.value = v })
watch(() => props.bodyType, (v) => { localBodyType.value = v })
watch(localBodyType, emitUpdate)

function emitUpdate() {
  emit('update:modelValue', localBody.value)
  emit('update:bodyType', localBodyType.value)
}

function formatJson() {
  try {
    const obj = JSON.parse(localBody.value)
    localBody.value = JSON.stringify(obj, null, 2)
    emitUpdate()
    ElMessage.success('已格式化')
  } catch {
    ElMessage.warning('内容不是有效 JSON')
  }
}
</script>

<style scoped>
.body-editor {
  display: flex;
  flex-direction: column;
}

.body-type-select {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 14px;
}

.body-textarea {
  margin: 0 14px 14px;
}

.body-textarea :deep(textarea) {
  min-height: 148px;
  font-family: var(--font-mono);
  font-size: 13px;
  line-height: 1.55;
}
</style>
