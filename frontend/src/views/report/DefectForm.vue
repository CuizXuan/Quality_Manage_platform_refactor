<template>
  <el-drawer
    v-model="visible"
    :title="isEdit ? '编辑缺陷' : '新建缺陷'"
    size="600px"
    :before-close="handleClose"
  >
    <el-form :model="defectForm" label-width="100px" class="defect-form">
      <el-form-item label="缺陷标题" required>
        <el-input v-model="defectForm.title" placeholder="请输入缺陷标题" />
      </el-form-item>

      <el-form-item label="描述">
        <el-input v-model="defectForm.description" type="textarea" :rows="3" placeholder="请输入描述" />
      </el-form-item>

      <el-form-item label="严重程度">
        <el-select v-model="defectForm.severity" style="width: 100%">
          <el-option label="Critical" value="critical" />
          <el-option label="High" value="high" />
          <el-option label="Medium" value="medium" />
          <el-option label="Low" value="low" />
        </el-select>
      </el-form-item>

      <el-form-item label="优先级">
        <el-select v-model="defectForm.priority" style="width: 100%">
          <el-option label="P0" value="P0" />
          <el-option label="P1" value="P1" />
          <el-option label="P2" value="P2" />
          <el-option label="P3" value="P3" />
        </el-select>
      </el-form-item>

      <el-form-item label="缺陷类型">
        <el-select v-model="defectForm.defect_type" style="width: 100%">
          <el-option label="功能缺陷" value="functional" />
          <el-option label="接口缺陷" value="api" />
          <el-option label="性能缺陷" value="performance" />
          <el-option label="安全缺陷" value="security" />
        </el-select>
      </el-form-item>

      <el-form-item label="标签">
        <el-select v-model="defectForm.tags" multiple placeholder="选择或输入标签" style="width: 100%" allow-create filterable>
          <el-option v-for="tag in availableTags" :key="tag" :label="tag" :value="tag" />
        </el-select>
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
import { useReportStore } from '@/stores/reportStore'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  defect: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['update:modelValue', 'saved'])

const reportStore = useReportStore()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const isEdit = computed(() => !!props.defect?.id)
const saving = ref(false)
const availableTags = ref(['登录', '支付', '接口', 'UI', '性能', '安全'])

const defaultForm = () => ({
  title: '',
  description: '',
  severity: 'medium',
  priority: 'P2',
  defect_type: 'functional',
  tags: [],
})

const defectForm = ref(defaultForm())

watch(
  () => props.modelValue,
  (val) => {
    if (val) {
      if (props.defect) {
        defectForm.value = {
          title: props.defect.title || '',
          description: props.defect.description || '',
          severity: props.defect.severity || 'medium',
          priority: props.defect.priority || 'P2',
          defect_type: props.defect.defect_type || 'functional',
          tags: props.defect.tags || [],
        }
      } else {
        defectForm.value = defaultForm()
      }
    }
  },
)

function handleClose() {
  visible.value = false
}

async function handleSubmit() {
  if (!defectForm.value.title.trim()) {
    ElMessage.warning('请输入缺陷标题')
    return
  }

  saving.value = true
  try {
    if (isEdit.value) {
      await reportStore.updateDefect(props.defect.id, defectForm.value)
    } else {
      await reportStore.createDefect(defectForm.value)
    }
    ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
    emit('saved')
  } catch {
    // error handled in store
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.defect-form {
  padding-right: var(--spacing-md);
}
</style>
