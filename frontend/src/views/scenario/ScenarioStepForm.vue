<template>
  <el-drawer
    v-model="visible"
    :title="isEdit ? '编辑步骤' : '添加步骤'"
    size="560px"
    :before-close="handleClose"
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

      <el-form-item v-if="stepForm.step_type === 'api'" label="API 路径" required>
        <el-input v-model="stepForm.config.method" placeholder="GET/POST/PUT/DELETE" style="width: 100px" />
        <el-input v-model="stepForm.config.path" placeholder="/api/endpoint" style="width: calc(100% - 110px); margin-left: 8px" />
      </el-form-item>

      <el-form-item v-if="stepForm.step_type === 'api'" label="请求体">
        <el-input v-model="stepForm.config.body" type="textarea" :rows="4" placeholder="JSON 请求体" />
      </el-form-item>

      <el-form-item v-if="stepForm.step_type === 'api'" label="预期状态码">
        <el-input-number v-model="stepForm.config.expected_status" :min="100" :max="599" placeholder="200" style="width: 120px" />
      </el-form-item>

      <el-form-item v-if="stepForm.step_type === 'case'" label="关联用例" required>
        <el-select
          v-model="stepForm.config.case_id"
          placeholder="请选择用例"
          filterable
          style="width: 100%"
        >
          <el-option
            v-for="c in availableCases"
            :key="c.id"
            :label="c.name"
            :value="c.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item v-if="stepForm.step_type === 'delay'" label="等待时长(秒)">
        <el-input-number v-model="stepForm.config.duration" :min="0" :max="3600" placeholder="3" style="width: 120px" />
      </el-form-item>

      <el-form-item v-if="stepForm.step_type === 'condition'" label="条件表达式">
        <el-input v-model="stepForm.config.expression" type="textarea" :rows="2" placeholder="例如: variables.status == 'success'" />
      </el-form-item>

      <el-form-item v-if="stepForm.step_type === 'condition'" label="预期结果">
        <el-radio-group v-model="stepForm.config.expected_result">
          <el-radio value="pass">通过</el-radio>
          <el-radio value="fail">失败</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item v-if="stepForm.step_type === 'script'" label="脚本内容">
        <el-input v-model="stepForm.config.script" type="textarea" :rows="4" placeholder="Python 脚本" />
      </el-form-item>

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
      <div style="display: flex; justify-content: flex-end; gap: 8px">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSubmit">保存</el-button>
      </div>
    </template>
  </el-drawer>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useScenarioStore } from '@/stores/scenarioStore'
import { caseApi } from '@/api/case'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  step: {
    type: Object,
    default: null,
  },
  scenarioId: {
    type: Number,
    required: true,
  },
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
      // 加载可用用例列表
      try {
        const res = await caseApi.list({ page: 1, page_size: 1000 })
        availableCases.value = res.data.items
      } catch {
        availableCases.value = []
      }
    }
  },
)

function handleTypeChange() {
  // 重置 config 当类型切换时
  stepForm.value.config = { ...defaultForm().config }
}

function handleClose() {
  visible.value = false
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
    ElMessage.success(isEdit.value ? '更新成功' : '添加成功')
    emit('saved')
  } catch {
    // error handled in store
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.step-form {
  padding-right: var(--spacing-md);
}
</style>
