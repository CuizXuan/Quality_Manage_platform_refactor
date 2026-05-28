<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑缺陷' : '新建缺陷'"
    top="4vh"
    width="min(600px, 92vw)"
    destroy-on-close
    append-to-body
  >
    <el-form :model="defectForm" label-width="100px" class="defect-form">
      <el-form-item label="缺陷标题" required>
        <el-input v-model="defectForm.title" placeholder="请输入缺陷标题" />
        <el-button type="primary" plain size="small" :icon="MagicStick" :loading="aiGeneratingTitle" @click="handleAiGenerateTitle" style="margin-top: 4px">AI 生成标题</el-button>
      </el-form-item>

      <el-form-item label="描述">
        <el-input v-model="defectForm.description" type="textarea" :rows="3" placeholder="请输入描述" />
        <el-button type="primary" plain size="small" :icon="MagicStick" :loading="aiGeneratingDesc" @click="handleAiGenerateDesc" style="margin-top: 4px">AI 生成描述</el-button>
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
        <el-button type="primary" plain size="small" :icon="MagicStick" :loading="aiRecommendingPriority" @click="handleAiRecommendPriority" style="margin-top: 4px">AI 推荐严重程度/优先级</el-button>
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

      <el-divider content-position="left">归属信息</el-divider>

      <el-row :gutter="12">
        <el-col :span="8">
          <el-form-item label="项目">
            <el-select v-model="defectForm.project_id" placeholder="请选择项目" clearable filterable @change="onProjectChange">
              <el-option v-for="p in foundationProjects" :key="p.id" :label="p.name" :value="p.id" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="版本">
            <el-select v-model="defectForm.version_id" placeholder="请选择版本" clearable filterable :disabled="!defectForm.project_id" @change="onVersionChange">
              <el-option v-for="v in foundationVersions" :key="v.id" :label="v.name" :value="v.id" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="迭代">
            <el-select v-model="defectForm.iteration_id" placeholder="请选择迭代" clearable filterable :disabled="!defectForm.version_id" @change="onIterationChange">
              <el-option v-for="i in foundationIterations" :key="i.id" :label="i.name" :value="i.id" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
      <el-row>
        <el-col :span="12">
          <el-form-item label="需求">
            <el-select v-model="defectForm.requirement_id" placeholder="请选择需求" clearable filterable :disabled="!defectForm.project_id">
              <el-option v-for="r in foundationRequirements" :key="r.id" :label="r.title" :value="r.id" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="saving" @click="handleSubmit">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { MagicStick } from '@element-plus/icons-vue'
import { useReportStore } from '@/stores/reportStore'
import { useQualityFoundationStore } from '@/stores/qualityFoundationStore'
import { useAiStore } from '@/stores/aiStore'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  defect: {
    type: Object,
    default: null,
  },
  initialData: {
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

const foundationStore = useQualityFoundationStore()
const foundationProjects = computed(() => foundationStore.projects)
const foundationVersions = computed(() => foundationStore.versions)
const foundationIterations = computed(() => foundationStore.iterations)
const foundationRequirements = computed(() => foundationStore.requirements)

function onProjectChange(projectId) {
  defectForm.value.version_id = null
  defectForm.value.iteration_id = null
  defectForm.value.requirement_id = null
  if (projectId) {
    foundationStore.fetchVersions({ project_id: projectId })
    foundationStore.fetchRequirements({ project_id: projectId })
  } else {
    foundationStore.clearVersions()
    foundationStore.clearIterations()
    foundationStore.clearRequirements()
  }
}

function onVersionChange(versionId) {
  defectForm.value.iteration_id = null
  if (versionId) {
    foundationStore.fetchIterations({ version_id: versionId })
  } else {
    foundationStore.clearIterations()
  }
}

function onIterationChange(iterationId) {
  defectForm.value.requirement_id = null
  if (iterationId && defectForm.value.project_id) {
    foundationStore.fetchRequirements({
      project_id: defectForm.value.project_id,
      version_id: defectForm.value.version_id,
      iteration_id: iterationId,
    })
  }
}

const defaultForm = () => ({
  title: '',
  description: '',
  severity: 'medium',
  priority: 'P2',
  defect_type: 'functional',
  tags: [],
  project_id: null,
  version_id: null,
  iteration_id: null,
  requirement_id: null,
})

const defectForm = ref(defaultForm())

watch(
  () => props.modelValue,
  (val) => {
    if (val) {
      foundationStore.fetchProjects()
      if (props.defect) {
        defectForm.value = {
          title: props.defect.title || '',
          description: props.defect.description || '',
          severity: props.defect.severity || 'medium',
          priority: props.defect.priority || 'P2',
          defect_type: props.defect.defect_type || 'functional',
          tags: props.defect.tags || [],
          project_id: props.defect.project_id ?? null,
          version_id: props.defect.version_id ?? null,
          iteration_id: props.defect.iteration_id ?? null,
          requirement_id: props.defect.requirement_id ?? null,
        }
        // 加载级联数据
        if (props.defect.project_id) {
          foundationStore.fetchVersions({ project_id: props.defect.project_id })
          foundationStore.fetchRequirements({ project_id: props.defect.project_id })
        }
        if (props.defect.version_id) {
          foundationStore.fetchIterations({ version_id: props.defect.version_id })
        }
        if (props.defect.iteration_id && props.defect.project_id) {
          foundationStore.fetchRequirements({
            project_id: props.defect.project_id,
            version_id: props.defect.version_id,
            iteration_id: props.defect.iteration_id,
          })
        }
      } else if (props.initialData) {
        // 新建模式：从 query params 预填
        defectForm.value = {
          title: props.initialData.title || '',
          description: props.initialData.description || '',
          severity: props.initialData.severity || 'medium',
          priority: props.initialData.priority || 'P2',
          defect_type: props.initialData.defect_type || 'functional',
          tags: Array.isArray(props.initialData.tags) ? props.initialData.tags : [],
          project_id: props.initialData.project_id ?? null,
          version_id: props.initialData.version_id ?? null,
          iteration_id: props.initialData.iteration_id ?? null,
          requirement_id: props.initialData.requirement_id ?? null,
        }
        if (props.initialData.project_id) {
          foundationStore.fetchVersions({ project_id: props.initialData.project_id })
          foundationStore.fetchRequirements({ project_id: props.initialData.project_id })
        }
        if (props.initialData.project_id && props.initialData.version_id) {
          foundationStore.fetchIterations({
            project_id: props.initialData.project_id,
            version_id: props.initialData.version_id,
          })
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
      ElMessage.success('更新成功')
    } else {
      await reportStore.createDefect(defectForm.value)
      ElMessage.success('创建成功')
    }
    emit('saved')
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

// ── AI 辅助 ────────────────────────────────────────────

const aiStore = useAiStore()
const aiGeneratingTitle = ref(false)
const aiGeneratingDesc = ref(false)
const aiRecommendingPriority = ref(false)

async function handleAiGenerateTitle() {
  if (!defectForm.value.description && !defectForm.value.title) {
    ElMessage.warning('请先填写描述再生成标题')
    return
  }
  aiGeneratingTitle.value = true
  try {
    const result = await aiStore.analyzeFailure({
      case_data: { scenario_name: defectForm.value.title || '', step_results: [] },
    })
    if (result?.root_cause) {
      defectForm.value.title = result.root_cause
      ElMessage.success('已生成标题')
    } else {
      ElMessage.warning('未生成标题建议')
    }
  } catch (e) {
    ElMessage.error('AI 生成失败: ' + (e.response?.data?.detail || e.message || '请检查 AI 配置'))
  } finally {
    aiGeneratingTitle.value = false
  }
}

async function handleAiGenerateDesc() {
  if (!defectForm.value.title) {
    ElMessage.warning('请先填写标题再生成描述')
    return
  }
  aiGeneratingDesc.value = true
  try {
    const result = await aiStore.analyzeFailure({
      case_data: { scenario_name: defectForm.value.title, description: defectForm.value.description, step_results: [] },
    })
    if (result?.suggestions?.length) {
      const descList = result.suggestions.map(s => typeof s === 'string' ? s : (s.description || ''))
      defectForm.value.description = descList.join('\n')
      ElMessage.success('已生成描述')
    } else {
      ElMessage.warning('未生成描述建议')
    }
  } catch (e) {
    ElMessage.error('AI 生成失败: ' + (e.response?.data?.detail || e.message || '请检查 AI 配置'))
  } finally {
    aiGeneratingDesc.value = false
  }
}

async function handleAiRecommendPriority() {
  if (!defectForm.value.title && !defectForm.value.description) {
    ElMessage.warning('请先填写标题或描述')
    return
  }
  aiRecommendingPriority.value = true
  try {
    const result = await aiStore.analyzeFailure({
      case_data: { scenario_name: defectForm.value.title || '', description: defectForm.value.description, step_results: [] },
    })
    if (result?.severity) {
      const severityMap = { critical: 'critical', high: 'high', medium: 'medium', low: 'low' }
      const sev = typeof result.severity === 'string' ? result.severity.toLowerCase() : ''
      if (sev && severityMap[sev]) {
        defectForm.value.severity = severityMap[sev]
      }
    }
    if (result?.suggestions?.length) {
      const priorityMatch = result.suggestions.find(s => {
        const desc = typeof s === 'string' ? s : (s.description || '')
        return /^P[0-3]/.test(desc.trim())
      })
      if (priorityMatch) {
        const desc = typeof priorityMatch === 'string' ? priorityMatch : (priorityMatch.description || '')
        const match = desc.trim().match(/^P[0-3]/)
        if (match) {
          defectForm.value.priority = match[0]
        }
      }
    }
    ElMessage.success('已推荐严重程度/优先级')
  } catch (e) {
    ElMessage.error('AI 推荐失败: ' + (e.response?.data?.detail || e.message || '请检查 AI 配置'))
  } finally {
    aiRecommendingPriority.value = false
  }
}
</script>

<style scoped>
.defect-form :deep(.el-form-item) {
  margin-bottom: 16px;
}
</style>
