<template>
  <div class="functional-case-form">
    <el-form :model="formData" label-width="100px">
      <el-form-item label="执行步骤">
        <div class="steps-list">
          <div v-for="(step, index) in formData.steps" :key="index" class="step-item">
            <el-input-number v-model="step.order" :min="1" size="small" style="width: 80px" />
            <el-input v-model="step.description" placeholder="步骤描述" size="small" style="flex: 1" />
            <el-input v-model="step.expected_result" placeholder="预期结果" size="small" style="flex: 1" />
            <el-button type="danger" :icon="Delete" size="small" @click="removeStep(index)" />
          </div>
          <el-button :icon="Plus" @click="addStep">添加步骤</el-button>
        </div>
      </el-form-item>

      <el-form-item label="测试数据">
        <el-input
          v-model="testDataJson"
          type="textarea"
          :rows="4"
          placeholder="JSON 格式测试数据"
          @blur="handleTestDataBlur"
        />
      </el-form-item>

      <el-form-item label="后置动作">
        <el-input
          v-model="formData.post_action"
          type="textarea"
          :rows="2"
          placeholder="清理数据、重置状态等"
        />
      </el-form-item>

      <el-form-item label="预期结果">
        <el-input
          v-model="formData.expected_result"
          type="textarea"
          :rows="2"
          placeholder="请输入预期结果"
        />
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { Plus, Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

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
}

.step-item {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  align-items: center;
}
</style>