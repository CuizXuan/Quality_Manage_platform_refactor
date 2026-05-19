<template>
  <div class="functional-case-form">
    <el-form :model="formData" label-width="100px">
      <el-form-item label="执行步骤">
        <div class="steps-list">
          <div v-for="(step, index) in formData.steps" :key="index" class="step-item">
            <div class="step-item__header">
              <span class="step-item__title">步骤 {{ index + 1 }}</span>
              <div class="step-item__actions">
                <el-input-number v-model="step.order" :min="1" size="small" class="step-order" />
                <el-button type="danger" :icon="Delete" size="small" @click="removeStep(index)" />
              </div>
            </div>
            <el-input v-model="step.description" placeholder="步骤描述" />
            <RichTextEditor v-model="step.expected_result" />
          </div>
          <el-button :icon="Plus" @click="addStep">添加步骤</el-button>
        </div>
      </el-form-item>

      <el-form-item label="测试数据">
        <RichTextEditor v-model="testDataHtml" />
      </el-form-item>

      <el-form-item label="后置动作">
        <RichTextEditor v-model="formData.post_action" />
      </el-form-item>

      <el-form-item label="预期结果">
        <RichTextEditor v-model="formData.expected_result" />
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { Plus, Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import RichTextEditor from '@/components/common/RichTextEditor.vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue'])

const formData = ref({
  steps: [],
  test_data: {},
  post_action: '',
  expected_result: '',
})

const testDataJson = computed({
  get: () => JSON.stringify(formData.value.test_data, null, 2),
  set: (val) => {
    try {
      formData.value.test_data = JSON.parse(val)
    } catch {}
  }
})

const testDataHtml = computed({
  get: () => {
    const pretty = JSON.stringify(formData.value.test_data || {}, null, 2)
    return pretty ? `<pre>${pretty}</pre>` : ''
  },
  set: (val) => {
    const text = (val || '').replace(/<[^>]+>/g, '').trim()
    if (!text) {
      formData.value.test_data = {}
      return
    }
    try {
      formData.value.test_data = JSON.parse(text)
    } catch {}
  },
})

function addStep() {
  formData.value.steps.push({
    order: formData.value.steps.length + 1,
    description: '',
    expected_result: '',
    test_data: {},
  })
}

function removeStep(index) {
  formData.value.steps.splice(index, 1)
}

function handleTestDataBlur() {
  try {
    formData.value.test_data = JSON.parse(testDataJson.value)
  } catch {
    ElMessage.error('JSON 格式错误')
  }
}

watch(() => props.modelValue, (val) => {
  if (val) {
    formData.value = { ...formData.value, ...val }
  }
}, { immediate: true })

watch(formData, (val) => {
  emit('update:modelValue', val)
}, { deep: true })
</script>

<style scoped>
.functional-case-form {
  padding: 16px;
}

.steps-list {
  width: 100%;
  display: grid;
  gap: 12px;
}

.step-item {
  display: grid;
  gap: 10px;
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: var(--bg-container-soft);
}

.step-item__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.step-item__title {
  font-weight: 600;
  color: var(--text-primary);
}

.step-item__actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.step-order {
  width: 100px;
}
</style>
