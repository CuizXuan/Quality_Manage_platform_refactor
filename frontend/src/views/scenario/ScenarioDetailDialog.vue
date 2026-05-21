<template>
  <el-dialog
    v-model="visible"
    :title="scenario ? scenario.name : '场景详情'"
    top="4vh"
    width="min(1100px, 92vw)"
    destroy-on-close
    class="scenario-detail-dialog"
    @close="handleClose"
  >
    <template #title>
      <span class="dialog-title">
        {{ scenario?.name || '场景详情' }}
        <el-tag
          v-if="scenario"
          :type="scenario.status === 'active' ? 'success' : 'info'"
          size="small"
          style="margin-left: 8px"
        >
          {{ scenario.status === 'active' ? '启用' : '草稿' }}
        </el-tag>
      </span>
    </template>

    <!-- 顶部操作栏 -->
    <div class="detail-toolbar">
      <div class="toolbar-left">
        <el-button :icon="Clock" @click="handleExecutionHistory">执行历史</el-button>
        <el-button type="primary" :icon="VideoPlay" :loading="running" @click="handleRun">执行场景</el-button>
        <el-button type="primary" :icon="EditPen" @click="openEditDialog">编辑场景</el-button>
        <el-button type="primary" :icon="Plus" @click="handleAddStep">添加步骤</el-button>
      </div>
    </div>

    <!-- 场景基本信息卡片 -->
    <section class="detail-info">
      <div class="info-row">
        <div class="info-item">
          <span class="info-label">场景类型</span>
          <el-tag :type="getScenarioTypeTag(scenario?.scenario_type)" size="small">
            {{ formatScenarioType(scenario?.scenario_type) }}
          </el-tag>
        </div>
        <div class="info-item">
          <span class="info-label">版本</span>
          <span class="info-value">{{ scenario?.version ?? 1 }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">优先级</span>
          <span class="info-value priority-cell" :class="`priority-${scenario?.priority}`">
            {{ scenario?.priority || 'P2' }}
          </span>
        </div>
      </div>
      <div class="info-row" v-if="scenario?.description">
        <div class="info-item info-item--full">
          <span class="info-label">描述</span>
          <span class="info-value">{{ scenario.description }}</span>
        </div>
      </div>
    </section>

    <!-- 步骤编排区 -->
    <section class="detail-steps">
      <div class="steps-header">
        <span class="section-title">步骤编排</span>
        <span class="step-count">共 {{ steps.length }} 个步骤</span>
      </div>

      <el-empty v-if="steps.length === 0" description="暂无步骤，请点击「添加步骤」">
        <el-button type="primary" @click="handleAddStep">添加步骤</el-button>
      </el-empty>

      <el-table
        v-else
        :data="steps"
        row-key="id"
        class="steps-table"
        highlight-current-row
      >
        <el-table-column type="index" label="#" width="60" align="center" />
        <el-table-column prop="name" label="步骤名称" min-width="160">
          <template #default="{ row }">
            <span class="text-ellipsis" :title="row.name">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="step_type" label="类型" width="120" align="center">
          <template #default="{ row }">
            <el-tag size="small">{{ formatStepType(row.step_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="case_id" label="用例ID" width="80" align="center">
          <template #default="{ row }">
            <span class="text-muted">{{ row.case_id || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="顺序" width="70" align="center" />
        <el-table-column label="操作" width="150" fixed="right" align="center">
          <template #default="{ row }">
            <div class="actions-cell">
              <el-button type="primary" text size="small" @click.stop="handleEditStep(row)">编辑</el-button>
              <el-button type="danger" text size="small" @click.stop="handleDeleteStep(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
        <template #empty>
          <span class="empty-text">暂无步骤</span>
        </template>
      </el-table>
    </section>

    <!-- 步骤编辑弹窗 -->
    <ScenarioStepDialog
      v-model="stepDialogVisible"
      :step="currentStep"
      :scenario-id="scenarioId"
      @saved="handleStepSaved"
    />

    <!-- 场景基本信息编辑弹窗 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑场景"
      top="4vh"
      width="min(720px, 92vw)"
      destroy-on-close
      class="scenario-edit-dialog"
      append-to-body
    >
      <el-form :model="scenarioForm" label-width="90px" class="scenario-form">
        <el-form-item label="场景名称" required>
          <el-input v-model="scenarioForm.name" placeholder="请输入场景名称" />
        </el-form-item>
        <el-form-item label="场景类型">
          <el-select v-model="scenarioForm.scenario_type" placeholder="请选择类型" style="width: 100%">
            <el-option label="功能测试" value="functional" />
            <el-option label="接口测试" value="api" />
            <el-option label="端到端" value="e2e" />
          </el-select>
        </el-form-item>
        <el-form-item label="版本号">
          <el-input-number v-model="scenarioForm.version" :min="1" :max="999" controls-position="right" style="width: 100%" />
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="scenarioForm.priority" placeholder="请选择优先级" style="width: 100%">
            <el-option label="P0 - 最高" value="P0" />
            <el-option label="P1 - 高" value="P1" />
            <el-option label="P2 - 中" value="P2" />
            <el-option label="P3 - 低" value="P3" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="scenarioForm.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="scenarioForm.status">
            <el-radio value="active">启用</el-radio>
            <el-radio value="draft">草稿</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, VideoPlay, EditPen, Clock } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useScenarioStore } from '@/stores/scenarioStore'
import ScenarioStepDialog from './ScenarioStepDialog.vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  scenarioId: { type: Number, required: true },
})

const emit = defineEmits(['update:modelValue', 'closed'])

const router = useRouter()
const scenarioStore = useScenarioStore()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const scenario = computed(() => scenarioStore.currentScenario)
const steps = computed(() => scenarioStore.currentSteps)

const running = ref(false)
const saving = ref(false)
const stepDialogVisible = ref(false)
const editDialogVisible = ref(false)
const currentStep = ref(null)

const scenarioForm = ref({
  name: '',
  scenario_type: 'functional',
  version: 1,
  priority: 'P2',
  description: '',
  status: 'draft',
})

watch(
  () => props.modelValue,
  async (val) => {
    if (val) {
      await scenarioStore.fetchScenario(props.scenarioId)
      syncFormFromStore()
    }
  }
)

function syncFormFromStore() {
  const s = scenario.value
  if (!s) return
  scenarioForm.value = {
    name: s.name || '',
    scenario_type: s.scenario_type || 'functional',
    version: s.version ?? 1,
    priority: s.priority || 'P2',
    description: s.description || '',
    status: s.status || 'draft',
  }
}

function handleClose() {
  emit('closed')
}

function openEditDialog() {
  syncFormFromStore()
  editDialogVisible.value = true
}

function formatStepType(type) {
  const map = {
    api: '接口调用',
    case: '用例执行',
    condition: '条件判断',
    delay: '等待',
    script: '脚本',
  }
  return map[type] || type || '—'
}

function getScenarioTypeTag(type) {
  const map = { functional: 'success', api: 'warning', e2e: 'primary' }
  return map[type] || 'info'
}

function formatScenarioType(type) {
  const map = { functional: '功能', api: '接口', e2e: '端到端' }
  return map[type] || type || '—'
}

function handleAddStep() {
  currentStep.value = null
  stepDialogVisible.value = true
}

function handleEditStep(step) {
  currentStep.value = { ...step }
  stepDialogVisible.value = true
}

async function handleDeleteStep(step) {
  try {
    await ElMessageBox.confirm(`确定要删除步骤「${step.name}」吗？`, '删除确认', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await scenarioStore.deleteStep(step.id)
    ElMessage.success('删除成功')
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('删除失败')
  }
}

function handleStepSaved() {
  stepDialogVisible.value = false
  currentStep.value = null
}

async function handleSave() {
  if (!scenarioForm.value.name.trim()) {
    ElMessage.warning('请输入场景名称')
    return
  }
  saving.value = true
  try {
    await scenarioStore.updateScenario(props.scenarioId, scenarioForm.value)
    editDialogVisible.value = false
    ElMessage.success('保存成功')
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function handleRun() {
  try {
    await ElMessageBox.confirm('确定要执行此场景吗？', '执行确认', {
      confirmButtonText: '执行',
      cancelButtonText: '取消',
      type: 'info',
    })
    running.value = true
    const result = await scenarioStore.startExecution(props.scenarioId)
    running.value = false
    ElMessage.success(`执行已启动 (run_id: ${result.run_id})`)
    visible.value = false
    router.push({ name: 'ExecutionDetail', params: { id: result.run_id } })
  } catch (err) {
    running.value = false
    if (err !== 'cancel') ElMessage.error('执行启动失败')
  }
}

function handleExecutionHistory() {
  visible.value = false
  router.push({ name: 'ExecutionHistory', query: { scenario_id: props.scenarioId } })
}
</script>

<style scoped>
.dialog-title {
  display: flex;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
}

/* ── 顶部操作栏 ── */
.detail-toolbar {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  margin-bottom: 14px;
  gap: 8px;
}

.toolbar-left {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

/* ── 场景基本信息卡片 ── */
.detail-info {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px 16px;
  margin-bottom: 10px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: rgba(20, 22, 27, 0.4);
}

html:not(.dark) .detail-info {
  background: rgba(255, 255, 255, 0.6);
}

.info-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 24px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 120px;
}

.info-item--full {
  flex: 1 1 100%;
  min-width: 0;
}

.info-label {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-secondary);
  white-space: nowrap;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-value {
  font-size: 13px;
  color: var(--text-primary);
  font-weight: 500;
}

.priority-cell {
  font-weight: 700;
  font-size: 12px;
}

.priority-P0 { color: var(--color-danger); }
.priority-P1 { color: var(--color-warning); }
.priority-P2 { color: var(--color-primary); }
.priority-P3 { color: var(--text-secondary); }

/* ── 步骤编排区 ── */
.detail-steps {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px 16px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: rgba(20, 22, 27, 0.4);
}

html:not(.dark) .detail-steps {
  background: rgba(255, 255, 255, 0.6);
}

.steps-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.step-count {
  font-size: 12px;
  color: var(--text-secondary);
}

.steps-table {
  width: 100%;
}

.steps-table :deep(.el-table__header th) {
  background: var(--bg-container-soft) !important;
  color: var(--text-secondary);
  font-weight: 700;
  font-size: 12px;
}

.text-muted {
  color: var(--text-secondary);
  font-size: 13px;
}
</style>
