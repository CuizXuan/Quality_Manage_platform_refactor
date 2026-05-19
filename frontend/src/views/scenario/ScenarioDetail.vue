<template>
  <div class="scenario-detail">
    <!-- 顶部操作栏 -->
    <div class="detail-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" text @click="router.push('/scenario')">返回列表</el-button>
        <el-divider direction="vertical" />
        <span class="detail-title">{{ scenarioStore.currentScenario?.name || '加载中…' }}</span>
        <el-tag :type="scenarioStore.currentScenario?.status === 'active' ? 'success' : 'info'" size="small" style="margin-left: 8px">
          {{ scenarioStore.currentScenario?.status === 'active' ? '启用' : '禁用' }}
        </el-tag>
      </div>
      <div class="header-right">
        <el-button @click="handleExecutionHistory">执行历史</el-button>
        <el-button type="primary" :icon="VideoPlay" :loading="running" @click="handleRun">执行场景</el-button>
        <el-button type="primary" :icon="Plus" @click="handleAddStep">添加步骤</el-button>
        <el-button @click="handleSave">保存</el-button>
      </div>
    </div>

    <!-- 场景基本信息 -->
    <el-card class="info-card" shadow="never">
      <el-form :model="scenarioForm" label-width="90px" inline>
        <el-form-item label="场景名称">
          <el-input v-model="scenarioForm.name" placeholder="请输入场景名称" style="width: 240px" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="scenarioForm.status">
            <el-radio value="active">启用</el-radio>
            <el-radio value="inactive">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="scenarioForm.description" placeholder="请输入描述" style="width: 300px" />
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 步骤编排区 -->
    <div class="steps-section">
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
        draggable
        @row-drop="handleStepDrop"
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
        <el-table-column prop="case_name" label="关联用例" min-width="140">
          <template #default="{ row }">
            <span v-if="row.case_name" class="text-ellipsis" :title="row.case_name">{{ row.case_name }}</span>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="160">
          <template #default="{ row }">
            <span v-if="row.description" class="text-ellipsis" :title="row.description">{{ row.description }}</span>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" size="small" text @click="handleEditStep(row)">编辑</el-button>
            <el-button type="danger" size="small" text @click="handleDeleteStep(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 步骤编辑抽屉 -->
    <ScenarioStepForm
      v-model="stepDrawerVisible"
      :step="currentStep"
      :scenario-id="scenarioId"
      @saved="handleStepSaved"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Plus, VideoPlay } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useScenarioStore } from '@/stores/scenarioStore'
import ScenarioStepForm from './ScenarioStepForm.vue'

const route = useRoute()
const router = useRouter()
const scenarioStore = useScenarioStore()

const scenarioId = computed(() => Number(route.params.id))
const running = ref(false)
const stepDrawerVisible = ref(false)
const currentStep = ref(null)

const scenarioForm = ref({
  name: '',
  description: '',
  status: 'active',
})

onMounted(async () => {
  try {
    await scenarioStore.fetchScenario(scenarioId.value)
    scenarioForm.value = {
      name: scenarioStore.currentScenario.name,
      description: scenarioStore.currentScenario.description,
      status: scenarioStore.currentScenario.status,
    }
  } catch {
    ElMessage.error('加载场景详情失败')
  }
})

function formatStepType(type) {
  const map = {
    api: '接口调用',
    case: '用例执行',
    condition: '条件判断',
    delay: '等待',
    script: '脚本',
  }
  return map[type] || type
}

function handleAddStep() {
  currentStep.value = null
  stepDrawerVisible.value = true
}

function handleEditStep(step) {
  currentStep.value = { ...step }
  stepDrawerVisible.value = true
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
  stepDrawerVisible.value = false
  currentStep.value = null
}

async function handleStepDrop(newList) {
  const stepIds = newList.map(s => s.id)
  await scenarioStore.reorderSteps(scenarioId.value, stepIds)
}

async function handleSave() {
  try {
    await scenarioStore.updateScenario(scenarioId.value, scenarioForm.value)
    ElMessage.success('保存成功')
  } catch {
    // error handled in store
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
</script>

<style scoped>
.scenario-detail {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  overflow-y: auto;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--bg-container);
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--border-radius-base);
  border: 1px solid var(--border-color);
}

.header-left {
  display: flex;
  align-items: center;
}

.header-right {
  display: flex;
  gap: var(--spacing-sm);
}

.detail-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.info-card {
  border-radius: var(--border-radius-base);
}

.steps-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg-container);
  border-radius: var(--border-radius-base);
  border: 1px solid var(--border-color);
  padding: var(--spacing-md);
}

.steps-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
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
}

.text-muted {
  color: var(--text-disabled);
  font-size: 13px;
}
</style>
