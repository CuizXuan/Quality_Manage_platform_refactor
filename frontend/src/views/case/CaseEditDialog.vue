<template>
  <el-dialog
    ref="dialogRef"
    :model-value="modelValue"
    :title="dialogTitle"
    width="min(1280px, 95vw)"
    top="3vh"
    destroy-on-close
    @update:model-value="emit('update:modelValue', $event)"
    @closed="emit('closed')"
  >
    <el-scrollbar class="case-edit-dialog__body">
      <el-form :model="form" label-position="top">
        <section class="case-edit-dialog__quick">
          <div class="quick-head">
            <span>{{ caseData?.id ? '编辑用例' : '快速创建' }}</span>
            <small>聚焦名称、说明和前置条件，编号保存后在列表展示</small>
          </div>
          <el-row :gutter="12" align="middle">
            <el-col :span="18">
              <el-form-item label="用例名称" required>
                <el-input v-model="form.name" :placeholder="namePlaceholder" @blur="fillNameFromConfig" />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="优先级">
                <el-select v-model="form.priority">
                  <el-option v-for="item in priorityOptions" :key="item" :label="item" :value="item" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item :label="caseType === 'api' ? '说明' : '业务描述'" class="wide-text-item">
            <el-input
              v-model="form.description"
              type="textarea"
              :rows="3"
              placeholder="可选：补充业务背景、覆盖范围或风险点"
            />
          </el-form-item>
          <el-form-item label="前置条件" class="precondition-item">
            <RichTextEditor v-model="form.pre_condition" />
          </el-form-item>
        </section>

        <el-card shadow="never" class="case-edit-dialog__section">
          <template #header>
            <div class="section-title">
              <span>{{ caseType === 'api' ? '接口识别与请求配置' : '步骤识别与用例配置' }}</span>
              <small>{{ caseType === 'api' ? '粘贴 curl / fetch / URL 后自动填充' : '粘贴自然语言步骤后自动拆分' }}</small>
            </div>
          </template>
          <ApiCaseForm v-if="caseType === 'api'" v-model="form.api_case" />
          <FunctionalCaseForm v-else v-model="form.functional_case" />
        </el-card>

        <el-collapse class="case-edit-dialog__advanced">
          <el-collapse-item title="高级信息（自动化、脚本、标签）" name="advanced">
            <div class="script-panel">
              <el-row :gutter="12">
                <el-col :span="6">
                  <el-form-item label="自动化">
                    <el-radio-group v-model="automationValue" class="automation-choice">
                      <el-radio-button label="manual">否</el-radio-button>
                      <el-radio-button label="automated">是</el-radio-button>
                    </el-radio-group>
                  </el-form-item>
                </el-col>
                <el-col :span="10">
                  <el-form-item label="脚本路径">
                    <el-input
                      v-model="form.auto_script_path"
                      :disabled="!form.is_automated"
                      placeholder="/scripts/login_test.py"
                      clearable
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="执行器">
                    <el-select v-model="form.auto_script_config.runner" :disabled="!form.is_automated">
                      <el-option v-for="item in scriptRunnerOptions" :key="item.value" :label="item.label" :value="item.value" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row v-if="form.is_automated" :gutter="12">
                <el-col :span="8">
                  <el-form-item label="入口函数/用例标识">
                    <el-input v-model="form.auto_script_config.entrypoint" placeholder="test_login_success" clearable />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="失败策略">
                    <el-select v-model="form.auto_script_config.failure_policy">
                      <el-option label="失败即停止" value="stop" />
                      <el-option label="继续执行" value="continue" />
                      <el-option label="仅记录" value="record" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="超时时间（秒）">
                    <el-input-number v-model="form.auto_script_config.timeout_seconds" :min="10" :max="7200" controls-position="right" />
                  </el-form-item>
                </el-col>
                <el-col :span="24">
                  <el-form-item label="脚本参数（JSON）">
                    <el-input
                      v-model="form.auto_script_config.params"
                      type="textarea"
                      :rows="3"
                      placeholder='例如 {"env":"test","account":"admin"}'
                    />
                  </el-form-item>
                </el-col>
              </el-row>
              <p class="script-panel__hint">{{ scriptConfigHint }}</p>
            </div>

            <div class="foundation-panel">
              <el-row :gutter="12">
                <el-col :span="8">
                  <el-form-item label="项目">
                    <el-select
                      v-model="form.project_id"
                      placeholder="请选择项目"
                      clearable
                      filterable
                      @change="onProjectChange"
                    >
                      <el-option v-for="p in foundationProjects" :key="p.id" :label="p.name" :value="p.id" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="版本">
                    <el-select
                      v-model="form.version_id"
                      placeholder="请选择版本"
                      clearable
                      filterable
                      :disabled="!form.project_id"
                      @change="onVersionChange"
                    >
                      <el-option v-for="v in foundationVersions" :key="v.id" :label="v.name" :value="v.id" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="迭代">
                    <el-select
                      v-model="form.iteration_id"
                      placeholder="请选择迭代"
                      clearable
                      filterable
                      :disabled="!form.version_id"
                      @change="onIterationChange"
                    >
                      <el-option v-for="i in foundationIterations" :key="i.id" :label="i.name" :value="i.id" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row>
                <el-col :span="12">
                  <el-form-item label="需求">
                    <el-select
                      v-model="form.requirement_id"
                      placeholder="请选择需求"
                      clearable
                      filterable
                      :disabled="!form.project_id"
                    >
                      <el-option v-for="r in foundationRequirements" :key="r.id" :label="r.title" :value="r.id" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>
            </div>

            <el-row :gutter="12" class="advanced-meta">
              <el-col :span="15">
                <el-form-item label="标签">
                  <el-select
                    v-model="form.tags"
                    multiple
                    filterable
                    allow-create
                    default-first-option
                    placeholder="输入后回车创建，如 smoke / regression / login"
                  >
                    <el-option v-for="tag in commonTags" :key="tag" :label="tag" :value="tag" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="9">
                <div class="advanced-hint">
                  <span>建议</span>
                  <p>{{ advancedHint }}</p>
                </div>
              </el-col>
            </el-row>
          </el-collapse-item>
        </el-collapse>
      </el-form>
    </el-scrollbar>

    <template #footer>
      <div class="case-edit-dialog__footer">
        <el-button @click="emit('update:modelValue', false)">取消</el-button>
        <el-button type="primary" @click="saveCase">保存</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { caseApi } from '@/api/case'
import RichTextEditor from '@/components/common/RichTextEditor.vue'
import feedback from '@/utils/feedback'
import ApiCaseForm from './ApiCaseForm.vue'
import FunctionalCaseForm from './FunctionalCaseForm.vue'
import { normalizeCaseForEdit, priorityOptions } from './caseUtils'
import { useQualityFoundationStore } from '@/stores/qualityFoundationStore'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  caseType: {
    type: String,
    required: true,
  },
  caseData: {
    type: Object,
    default: null,
  },
  folderId: {
    type: Number,
    default: null,
  },
  suggestedCaseId: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['update:modelValue', 'saved', 'closed'])
const dialogRef = ref(null)

const foundationStore = useQualityFoundationStore()
const foundationProjects = computed(() => foundationStore.projects)
const foundationVersions = computed(() => foundationStore.versions)
const foundationIterations = computed(() => foundationStore.iterations)
const foundationRequirements = computed(() => foundationStore.requirements)

function onProjectChange(projectId) {
  form.value.version_id = null
  form.value.iteration_id = null
  form.value.requirement_id = null
  if (projectId) {
    foundationStore.fetchVersions(projectId)
    foundationStore.fetchRequirements({ project_id: projectId })
  } else {
    foundationStore.clearVersions()
    foundationStore.clearIterations()
    foundationStore.clearRequirements()
  }
}

function onVersionChange(versionId) {
  form.value.iteration_id = null
  if (versionId) {
    foundationStore.fetchIterations({ version_id: versionId })
  } else {
    foundationStore.clearIterations()
  }
}

function onIterationChange(iterationId) {
  form.value.requirement_id = null
  if (iterationId && form.value.project_id) {
    foundationStore.fetchRequirements({
      project_id: form.value.project_id,
      version_id: form.value.version_id,
      iteration_id: iterationId,
    })
  }
}

const form = ref(normalizeCaseForEdit(null, props.caseType))
const caseTitle = computed(() => (props.caseType === 'api' ? '接口用例' : '功能用例'))
const dialogTitle = computed(() => `${props.caseData?.id ? '编辑' : '新增'}${caseTitle.value}`)
const namePlaceholder = computed(() => (props.caseType === 'api' ? '如：登录接口-成功获取 Token' : '如：登录成功后进入工作台'))
const commonTags = ['smoke', 'regression', 'login', 'query', 'create', 'p0', 'api', 'ui']
const scriptRunnerOptions = [
  { label: 'pytest', value: 'pytest' },
  { label: 'Playwright', value: 'playwright' },
  { label: 'Shell', value: 'shell' },
  { label: '自定义', value: 'custom' },
]
const advancedHint = computed(() => {
  if (props.caseType === 'api') return '接口用例可用标签标记协议、模块或冒烟等级；前置条件建议写清依赖账号、环境和数据准备。'
  return '功能用例可用标签标记业务域、端到端链路或回归范围；前置条件建议写清角色、入口和数据状态。'
})
const scriptConfigHint = computed(() => {
  if (!form.value.is_automated) return '开启自动化后，可绑定脚本路径和执行参数；当前先保存配置，后续执行器可直接消费。'
  return '脚本配置会随用例保存，后续可扩展为选择脚本仓库、变量注入、执行前后钩子和结果回写。'
})
const automationValue = computed({
  get: () => form.value.is_automated ? 'automated' : 'manual',
  set: (value) => {
    form.value.is_automated = value === 'automated'
  },
})

function resetForm() {
  form.value = normalizeCaseForEdit(props.caseData, props.caseType, props.folderId)
  if (!props.caseData?.id && !form.value.auto_case_id) {
    form.value.auto_case_id = props.suggestedCaseId
  }
  // 编辑时加载级联数据
  if (form.value.project_id) {
    foundationStore.fetchVersions(form.value.project_id)
    foundationStore.fetchRequirements({ project_id: form.value.project_id })
  }
  if (form.value.version_id) {
    foundationStore.fetchIterations({ version_id: form.value.version_id })
  }
  if (form.value.iteration_id && form.value.project_id) {
    foundationStore.fetchRequirements({
      project_id: form.value.project_id,
      version_id: form.value.version_id,
      iteration_id: form.value.iteration_id,
    })
  }
}

function regenerateCaseId() {
  form.value.auto_case_id = props.suggestedCaseId
}

watch(() => form.value.is_automated, (enabled) => {
  if (enabled) return
  form.value.auto_script_path = ''
  form.value.auto_script_config.entrypoint = ''
  form.value.auto_script_config.params = ''
})

function fillNameFromConfig() {
  if (form.value.name.trim()) return
  if (props.caseType === 'api') {
    const apiCase = form.value.api_case || {}
    if (apiCase.url) form.value.name = `${apiCase.method || 'GET'} ${apiCase.url}`
    return
  }
  const firstStep = form.value.functional_case?.steps?.[0]
  if (firstStep?.description) form.value.name = firstStep.description
}

function validateForm() {
  if (!form.value.name.trim()) {
    feedback.warning('请输入用例名称')
    return false
  }
  if (props.caseType === 'api' && !form.value.api_case.url.trim()) {
    feedback.warning('请输入请求 URL')
    return false
  }
  if (props.caseType === 'functional' && !form.value.functional_case.steps.length) {
    feedback.warning('请至少添加一个测试步骤')
    return false
  }
  if (form.value.is_automated && form.value.auto_script_config.params) {
    try {
      JSON.parse(form.value.auto_script_config.params)
    } catch {
      feedback.warning('脚本参数必须是合法 JSON')
      return false
    }
  }
  return true
}

async function saveCase() {
  fillNameFromConfig()
  if (!form.value.auto_case_id) form.value.auto_case_id = props.suggestedCaseId
  if (!validateForm()) return

  try {
    const payload = {
      ...form.value,
      auto_script_config: normalizeScriptConfig(),
      case_type: props.caseType,
      api_case: props.caseType === 'api' ? form.value.api_case : undefined,
      functional_case: props.caseType === 'functional' ? form.value.functional_case : undefined,
    }
    if (props.caseData?.id) {
      await caseApi.update(props.caseData.id, payload)
      feedback.success(`${caseTitle.value}更新成功`)
    } else {
      await caseApi.create(payload)
      feedback.success(`${caseTitle.value}创建成功`)
    }
    emit('saved')
    // 关闭弹窗 - 先通过 emit 关闭
    emit('update:modelValue', false)
    // 确保弹窗关闭
    await nextTick()
    if (dialogRef.value?.visible !== false) {
      // 如果弹窗仍未关闭，尝试直接关闭
      dialogRef.value?.handleClose?.()
    }
  } catch {
    feedback.error(`${caseTitle.value}保存失败`)
  }
}

function normalizeScriptConfig() {
  const config = form.value.auto_script_config || {}
  return {
    runner: config.runner || 'pytest',
    entrypoint: config.entrypoint || '',
    timeout_seconds: config.timeout_seconds || 300,
    failure_policy: config.failure_policy || 'stop',
    params: config.params ? JSON.parse(config.params) : {},
  }
}

watch(() => props.modelValue, (visible) => {
  if (visible) {
    foundationStore.fetchProjects()
    resetForm()
  }
})
</script>

<style scoped>
.case-edit-dialog__body {
  height: min(80vh, 820px);
  padding-right: var(--spacing-sm);
}

.case-edit-dialog__quick {
  margin-bottom: 12px;
  padding: 14px 14px 2px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: var(--bg-container);
}

.quick-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 800;
  line-height: 1.55;
}

.quick-head small {
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.automation-choice {
  display: grid;
  grid-template-columns: 1fr 1fr;
  width: 100%;
}

.automation-choice :deep(.el-radio-button__inner) {
  width: 100%;
}

.case-edit-dialog__section {
  margin-bottom: 12px;
  border-radius: var(--border-radius-base);
}

.section-title {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.section-title small {
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 500;
  line-height: 1.5;
}

.case-edit-dialog__section :deep(.el-card__header) {
  min-height: 42px;
  padding: 10px 14px;
  color: var(--text-primary);
  background: var(--bg-container-soft);
  font-size: var(--font-size-base);
  font-weight: 700;
}

.case-edit-dialog__section :deep(.el-card__body) {
  padding: 14px;
}

.case-edit-dialog__body :deep(.el-form-item) {
  margin-bottom: 14px;
}

.wide-text-item :deep(.el-textarea__inner) {
  min-height: 76px !important;
  resize: vertical;
}

.case-edit-dialog__body :deep(.ql-container.ql-snow),
.case-edit-dialog__body :deep(.ql-editor) {
  min-height: 96px;
}

.precondition-item :deep(.ql-container.ql-snow),
.precondition-item :deep(.ql-editor) {
  min-height: 82px;
}

.case-edit-dialog__advanced {
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: var(--bg-container);
}

.case-edit-dialog__advanced :deep(.el-collapse-item__header) {
  padding: 0 14px;
  border-bottom-color: var(--border-color-lighter);
  color: var(--text-secondary);
  background: var(--bg-container-soft);
  font-size: var(--font-size-base);
  font-weight: 700;
}

.case-edit-dialog__advanced :deep(.el-collapse-item__content) {
  padding: 14px;
}

.script-panel {
  margin-bottom: 12px;
  padding: 12px;
  border: 1px solid var(--border-color-lighter);
  border-radius: var(--border-radius-base);
  background: var(--bg-container-soft);
}

.script-panel__hint {
  margin: -2px 0 0;
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  line-height: 1.6;
}

.script-panel :deep(.el-input-number) {
  width: 100%;
}

.advanced-meta {
  align-items: stretch;
}

.advanced-hint {
  min-height: 82px;
  padding: 10px 12px;
  border: 1px dashed var(--border-color);
  border-radius: var(--border-radius-base);
  background: var(--bg-container-soft);
}

.advanced-hint span {
  color: var(--color-primary);
  font-size: var(--font-size-sm);
  font-weight: 800;
}

.advanced-hint p {
  margin: 6px 0 0;
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  line-height: 1.6;
}

.foundation-panel {
  margin-bottom: 12px;
  padding: 12px;
  border: 1px solid var(--border-color-lighter);
  border-radius: var(--border-radius-base);
  background: var(--bg-container-soft);
}

.case-edit-dialog__footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
}
</style>
