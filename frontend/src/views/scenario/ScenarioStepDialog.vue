<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑步骤' : '添加步骤'"
    top="4vh"
    width="min(640px, 92vw)"
    destroy-on-close
    :close-on-click-modal="false"
    append-to-body
  >
    <el-form :model="stepForm" label-width="100px" class="step-form">
      <el-form-item label="步骤名称" required>
        <el-input v-model="stepForm.name" placeholder="请输入步骤名称" />
      </el-form-item>

      <el-form-item label="步骤类型" required>
        <el-select v-model="stepForm.step_type" style="width: 100%" @change="handleTypeChange">
          <el-option label="接口调用" value="api" />
          <el-option label="用例执行" value="case" />
          <el-option label="条件判断" value="condition" />
          <el-option label="等待" value="delay" />
          <el-option label="脚本" value="script" />
        </el-select>
      </el-form-item>

      <!-- API 类型配置 -->
      <template v-if="stepForm.step_type === 'api'">
        <el-form-item label="请求方法">
          <el-select v-model="stepForm.config.method" style="width: 120px">
            <el-option v-for="m in ['GET','POST','PUT','DELETE','PATCH']" :key="m" :label="m" :value="m" />
          </el-select>
        </el-form-item>
        <el-form-item label="API 路径" required>
          <el-input v-model="stepForm.config.path" placeholder="/api/endpoint" />
        </el-form-item>
        <el-form-item label="请求体">
          <el-input v-model="stepForm.config.body" type="textarea" :rows="3" placeholder="JSON 请求体" />
        </el-form-item>
        <el-form-item label="预期状态码">
          <el-input-number v-model="stepForm.config.expected_status" :min="100" :max="599" />
        </el-form-item>
      </template>

      <!-- 用例类型配置 -->
      <el-form-item v-if="stepForm.step_type === 'case'" label="关联用例" required>
        <el-select
          v-model="stepForm.config.case_id"
          placeholder="请选择用例"
          filterable
          style="width: 100%"
        >
          <el-option v-for="c in availableCases" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
      </el-form-item>

      <!-- 等待类型配置 -->
      <el-form-item v-if="stepForm.step_type === 'delay'" label="等待时长(秒)">
        <el-input-number v-model="stepForm.config.duration" :min="0" :max="3600" />
      </el-form-item>

      <!-- 条件判断配置 -->
      <template v-if="stepForm.step_type === 'condition'">
        <el-form-item label="条件表达式">
          <el-input v-model="stepForm.config.expression" type="textarea" :rows="2" placeholder="例如: variables.status == 'success'" />
        </el-form-item>
        <el-form-item label="预期结果">
          <el-radio-group v-model="stepForm.config.expected_result">
            <el-radio value="pass">通过</el-radio>
            <el-radio value="fail">失败</el-radio>
          </el-radio-group>
        </el-form-item>
      </template>

      <!-- 脚本类型配置 -->
      <el-form-item v-if="stepForm.step_type === 'script'" label="脚本内容">
        <el-input v-model="stepForm.config.script" type="textarea" :rows="4" placeholder="Python 脚本" />
      </el-form-item>

      <!-- 通用配置 -->
      <el-form-item label="失败策略">
        <el-radio-group v-model="stepForm.on_error">
          <el-radio value="stop">停止执行</el-radio>
          <el-radio value="continue">继续执行</el-radio>
          <el-radio value="retry">重试</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="描述">
        <el-input v-model="stepForm.description" type="textarea" :rows="2" placeholder="请输入描述" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="saving" @click="handleSubmit">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useScenarioStore } from '@/stores/scenarioStore'
import { caseApi } from '@/api/case'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  step: { type: Object, default: null },
  scenarioId: { type: Number, required: true },
})

const emit = defineEmits(['update:modelValue', 'saved'])
const scenarioStore = useScenarioStore()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const isEdit = computed(() => !!props.step?.id)
const saving = ref(false)
const availableCases = ref([])

const defaultForm = () => ({
  name: '',
  step_type: 'api',
  description: '',
  on_error: 'stop',
  config: {
    method: 'GET',
    path: '',
    body: '',
    expected_status: 200,
    case_id: null,
    duration: 3,
    expression: '',
    expected_result: 'pass',
    script: '',
  },
})

const stepForm = ref(defaultForm())

watch(
  () => props.modelValue,
  async (val) => {
    if (val) {
      if (props.step) {
        stepForm.value = {
          ...defaultForm(),
          ...props.step,
          config: { ...defaultForm().config, ...(props.step.config || {}) },
        }
      } else {
        stepForm.value = defaultForm()
      }
      try {
        const res = await caseApi.list({ page: 1, page_size: 1000 })
        availableCases.value = res.data?.items || []
      } catch {
        availableCases.value = []
      }
    }
  },
)

function handleTypeChange() {
  stepForm.value.config = { ...defaultForm().config }
}

async function handleSubmit() {
  if (!stepForm.value.name.trim()) {
    ElMessage.warning('请输入步骤名称')
    return
  }
  if (stepForm.value.step_type === 'api' && !stepForm.value.config.path.trim()) {
    ElMessage.warning('请输入 API 路径')
    return
  }
  if (stepForm.value.step_type === 'case' && !stepForm.value.config.case_id) {
    ElMessage.warning('请选择关联用例')
    return
  }

  saving.value = true
  try {
    const data = {
      name: stepForm.value.name,
      step_type: stepForm.value.step_type,
      description: stepForm.value.description,
      on_error: stepForm.value.on_error,
      config: stepForm.value.config,
    }
    if (isEdit.value) {
      await scenarioStore.updateStep(props.step.id, data)
    } else {
      await scenarioStore.addStep(props.scenarioId, data)
    }
    visible.value = false
    emit('saved')
    ElMessage.success(isEdit.value ? '更新成功' : '添加成功')
  } catch {
    ElMessage.error(isEdit.value ? '更新失败' : '添加失败')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.step-form {
  padding-right: var(--spacing-xs);
}
</style>
