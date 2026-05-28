<template>
  <div class="scenario-detail-page">
    <!-- 顶部操作栏 -->
    <header class="scenario-detail-page__header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" text @click="router.push('/scenario')">返回列表</el-button>
        <el-divider direction="vertical" />
        <span class="detail-title">{{ scenarioStore.currentScenario?.name || '加载中…' }}</span>
        <el-tag :type="scenarioStore.currentScenario?.status === 'active' ? 'success' : 'info'" size="small" style="margin-left: 8px">
          {{ scenarioStore.currentScenario?.status === 'active' ? '启用' : '禁用' }}
        </el-tag>
      </div>
      <div class="header-right">
        <el-button :icon="History" @click="handleExecutionHistory">执行历史</el-button>
        <el-button type="primary" :icon="MagicStick" :loading="aiLoading" @click="handleAiGenerateSteps">AI 生成步骤</el-button>
        <el-button type="primary" :icon="VideoPlay" :loading="running" @click="handleRun">执行场景</el-button>
        <el-button type="primary" :icon="EditPen" @click="openEditDialog">编辑场景</el-button>
        <el-button type="primary" :icon="Plus" @click="handleAddStep">添加步骤</el-button>
      </div>
    </header>

    <!-- 场景基本信息卡片（只读展示） -->
    <section class="scenario-detail-page__info">
      <div class="info-row">
        <div class="info-item">
          <span class="info-label">场景名称</span>
          <span class="info-value">{{ scenarioStore.currentScenario?.name || '—' }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">场景类型</span>
          <el-tag :type="getScenarioTypeTag(scenarioStore.currentScenario?.scenario_type)" size="small">
            {{ formatScenarioType(scenarioStore.currentScenario?.scenario_type) }}
          </el-tag>
        </div>
        <div class="info-item">
          <span class="info-label">版本</span>
          <span class="info-value">{{ scenarioStore.currentScenario?.version ?? 1 }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">优先级</span>
          <span class="info-value priority-cell" :class="`priority-${scenarioStore.currentScenario?.priority}`">
            {{ scenarioStore.currentScenario?.priority || 'P2' }}
          </span>
        </div>
        <div class="info-item">
          <span class="info-label">状态</span>
          <el-tag :type="scenarioStore.currentScenario?.status === 'active' ? 'success' : 'info'" size="small">
            {{ scenarioStore.currentScenario?.status === 'active' ? '启用' : '草稿' }}
          </el-tag>
        </div>
      </div>
      <div class="info-row" v-if="scenarioStore.currentScenario?.description">
        <div class="info-item info-item--full">
          <span class="info-label">描述</span>
          <span class="info-value">{{ scenarioStore.currentScenario.description }}</span>
        </div>
      </div>
    </section>

    <!-- 步骤编排区 -->
    <section class="scenario-detail-page__steps">
      <div class="steps-header">
        <span class="section-title">步骤编排</span>
        <span class="step-count">共 {{ scenarioStore.currentSteps.length }} 个步骤</span>
      </div>

      <el-empty v-if="scenarioStore.currentSteps.length === 0" description="暂无步骤，请点击「添加步骤」">
        <el-button type="primary" @click="handleAddStep">添加步骤</el-button>
      </el-empty>

      <el-table
        v-else
        :data="scenarioStore.currentSteps"
        row-key="id"
        class="steps-table"
        height="100%"
        highlight-current-row
        @row-click="handleRowClick"
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

    <!-- AI 步骤建议弹窗 -->
    <el-dialog v-model="aiStepsDialogVisible" title="AI 步骤建议" width="600px" destroy-on-close>
      <div v-if="aiSuggestedSteps.length" class="ai-steps-suggestions">
        <p class="ai-steps-hint">以下是 AI 建议的步骤，采纳后将填入步骤草稿，请选择用例后保存：</p>
        <ul>
          <li v-for="(step, i) in aiSuggestedSteps" :key="i">
            <strong>{{ typeof step === 'string' ? step : (step.description || step.name || JSON.stringify(step)) }}</strong>
          </li>
        </ul>
      </div>
      <el-empty v-else description="暂无步骤建议" />
      <template #footer>
        <el-button @click="aiStepsDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleAcceptAiSteps" :disabled="!aiSuggestedSteps.length">填入草稿</el-button>
      </template>
    </el-dialog>

    <!-- 场景基本信息编辑弹窗 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑场景"
      top="4vh"
      width="min(720px, 92vw)"
      destroy-on-close
      class="scenario-edit-dialog"
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Plus, VideoPlay, EditPen, History, MagicStick } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useScenarioStore } from '@/stores/scenarioStore'
import { useAiStore } from '@/stores/aiStore'
import ScenarioStepDialog from './ScenarioStepDialog.vue'

const route = useRoute()
const router = useRouter()
const scenarioStore = useScenarioStore()

const scenarioId = computed(() => Number(route.params.id))
const running = ref(false)
const aiLoading = ref(false)
const saving = ref(false)
const stepDialogVisible = ref(false)
const editDialogVisible = ref(false)
const currentStep = ref(null)
const aiSuggestedSteps = ref([])

const aiStepsDialogVisible = ref(false)

const scenarioForm = ref({
  name: '',
  scenario_type: 'functional',
  version: 1,
  priority: 'P2',
  description: '',
  status: 'draft',
})

onMounted(async () => {
  try {
    await scenarioStore.fetchScenario(scenarioId.value)
    syncFormFromStore()
  } catch {
    ElMessage.error('加载场景详情失败')
  }
})

function syncFormFromStore() {
  const s = scenarioStore.currentScenario
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

function handleRowClick(row) {
  // 点击行不编辑，仅高亮
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

async function handleAcceptAiSteps() {
  if (!aiSuggestedSteps.value.length) return

  // 方案 B：提示用户手动添加步骤并选择用例后保存（避免草稿弹窗 422）
  const first = aiSuggestedSteps.value[0]
  const desc = typeof first === 'string' ? first : (first.description || first.name || '')
  aiSuggestedSteps.value = []
  aiStepsDialogVisible.value = false
  ElMessage.info('AI 已生成步骤建议，请点击「添加步骤」手动录入信息并选择用例后保存')
}

async function handleSave() {
  if (!scenarioForm.value.name.trim()) {
    ElMessage.warning('请输入场景名称')
    return
  }
  saving.value = true
  try {
    await scenarioStore.updateScenario(scenarioId.value, scenarioForm.value)
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
    const result = await scenarioStore.startExecution(scenarioId.value)
    running.value = false
    ElMessage.success(`执行已启动 (run_id: ${result.run_id})`)
    router.push({ name: 'ExecutionDetail', params: { id: result.run_id } })
  } catch (err) {
    running.value = false
    if (err !== 'cancel') ElMessage.error('执行启动失败')
  }
}

function handleExecutionHistory() {
  router.push({ name: 'ExecutionHistory', query: { scenario_id: scenarioId.value } })
}

// ── AI 生成步骤 ────────────────────────────────────────────

const aiStore = useAiStore()

async function handleAiGenerateSteps() {
  aiLoading.value = true
  aiSuggestedSteps.value = []
  try {
    const scenario = scenarioStore.currentScenario
    const caseData = {
      name: scenario?.name || '',
      description: scenario?.description || '',
      scenario_id: scenarioId.value,
      steps: scenarioStore.currentSteps.map(s => ({ name: s.name, case_id: s.case_id })),
    }
    const result = await aiStore.analyzeFailure({ case_data: caseData })
    if (result?.suggestions?.length) {
      aiSuggestedSteps.value = result.suggestions
      aiStepsDialogVisible.value = true
      ElMessage.success(`生成 ${result.suggestions.length} 条步骤建议`)
    } else {
      ElMessage.warning('暂未生成步骤建议')
    }
  } catch (e) {
    ElMessage.error('AI 生成失败: ' + (e.response?.data?.detail || e.message || '请检查 AI 配置'))
  } finally {
    aiLoading.value = false
  }
}
</script>

<style scoped>
/* ── 页面容器 ── */
.scenario-detail-page {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-height: 0;
  min-width: 0;
  gap: 10px;
  padding: 12px;
  background:
    radial-gradient(circle at top right, rgba(56, 189, 248, 0.13), transparent 30%),
    var(--bg-page);
  overflow: hidden;
}

/* ── 顶部操作栏 ── */
.scenario-detail-page__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-height: 56px;
  padding: 10px 16px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: rgba(20, 22, 27, 0.7);
  box-shadow: var(--box-shadow-light);
  backdrop-filter: blur(10px);
  gap: 12px;
}

html:not(.dark) .scenario-detail-page__header {
  background: rgba(255, 255, 255, 0.86);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.detail-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-right {
  display: flex;
  flex-wrap: nowrap;
  gap: 8px;
  justify-content: flex-end;
  flex-shrink: 0;
}

/* ── 场景基本信息卡片 ── */
.scenario-detail-page__info {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px 16px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: rgba(20, 22, 27, 0.7);
  box-shadow: var(--box-shadow-light);
  backdrop-filter: blur(10px);
}

html:not(.dark) .scenario-detail-page__info {
  background: rgba(255, 255, 255, 0.86);
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
.scenario-detail-page__steps {
  display: flex;
  flex: 1;
  min-height: 0;
  flex-direction: column;
  gap: 10px;
  padding: 14px 16px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: rgba(20, 22, 27, 0.7);
  box-shadow: var(--box-shadow-light);
  backdrop-filter: blur(10px);
  overflow: hidden;
}

html:not(.dark) .scenario-detail-page__steps {
  background: rgba(255, 255, 255, 0.86);
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
  flex: 1;
  min-height: 0;
}

.steps-table :deep(.el-table__header th) {
  background: var(--bg-container-soft) !important;
  color: var(--text-secondary);
  font-weight: 700;
  font-size: 12px;
}

.steps-table :deep(.el-table__body tr) {
  cursor: default;
}

.steps-table :deep(.el-table__row:hover > td) {
  background: rgba(56, 189, 248, 0.1) !important;
}

.steps-table :deep(.el-table__cell) {
  vertical-align: middle;
}

.steps-table :deep(.el-table__body tr:nth-child(even) td.el-table__cell) {
  background: rgba(15, 31, 52, 0.28) !important;
  background-color: rgba(15, 31, 52, 0.28) !important;
}

html:not(.dark) .steps-table :deep(.el-table__body tr:nth-child(even) td.el-table__cell) {
  background: rgba(245, 250, 255, 0.5) !important;
  background-color: rgba(245, 250, 255, 0.5) !important;
}

html:not(.dark) .scenario-detail-page__info {
  background: rgba(255, 255, 255, 0.86);
  border-color: rgba(22, 119, 255, 0.14);
}

html:not(.dark) .scenario-detail-page__header {
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.86), rgba(245, 250, 255, 0.68)),
    rgba(255, 255, 255, 0.72);
  box-shadow: 0 18px 46px rgba(20, 42, 76, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.82);
  border-color: rgba(22, 119, 255, 0.18);
}

html:not(.dark) .scenario-form {
  background: rgba(255, 255, 255, 0.6);
  border-color: rgba(22, 119, 255, 0.14);
}

.text-muted {
  color: var(--text-secondary);
  font-size: 13px;
}

.empty-text {
  color: var(--text-secondary);
  font-size: 13px;
}

/* ── 弹窗表单 ── */
.scenario-form :deep(.el-form-item) {
  margin-bottom: 16px;
}

.scenario-form :deep(.el-select),
.scenario-form :deep(.el-input-number) {
  width: 100%;
}
</style>
