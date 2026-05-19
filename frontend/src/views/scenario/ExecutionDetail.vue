<template>
  <div class="execution-detail">
    <!-- 顶部 -->
    <div class="detail-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" text @click="router.push('/scenario/executions')">返回</el-button>
        <el-divider direction="vertical" />
        <span class="page-title">执行详情</span>
        <el-tag :type="getStatusType(execution?.status)" style="margin-left: 8px">
          {{ getStatusLabel(execution?.status) }}
        </el-tag>
      </div>
      <div class="header-right">
        <el-button v-if="execution?.status === 'failed'" type="warning" @click="handleRetry">重试</el-button>
        <el-button type="primary" @click="handleRerun">重新执行</el-button>
      </div>
    </div>

    <!-- 执行概览 -->
    <el-row :gutter="16" v-if="execution">
      <el-col :span="6">
        <el-card class="stat-card" shadow="never">
          <div class="stat-label">场景</div>
          <div class="stat-value text-ellipsis" :title="execution.scenario_name">{{ execution.scenario_name }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="never">
          <div class="stat-label">总步骤</div>
          <div class="stat-value">{{ execution.total_steps }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="never">
          <div class="stat-label">成功 / 失败</div>
          <div class="stat-value">
            <span style="color: var(--el-color-success)">{{ execution.passed_steps }}</span>
            /
            <span style="color: var(--el-color-danger)">{{ execution.failed_steps }}</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="never">
          <div class="stat-label">耗时</div>
          <div class="stat-value">{{ execution.duration ? `${execution.duration}s` : '—' }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 时间线 -->
    <el-card v-if="execution" class="timeline-card" shadow="never">
      <el-descriptions :column="3" border>
        <el-descriptions-item label="Run ID">{{ execution.id }}</el-descriptions-item>
        <el-descriptions-item label="触发者">{{ execution.triggered_by || '—' }}</el-descriptions-item>
        <el-descriptions-item label="开始时间">{{ execution.started_at || '—' }}</el-descriptions-item>
        <el-descriptions-item label="结束时间">{{ execution.finished_at || '—' }}</el-descriptions-item>
        <el-descriptions-item label="失败策略" :span="2">{{ execution.on_error || 'stop' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 步骤结果 -->
    <div class="steps-result">
      <div class="section-header">步骤结果</div>

      <el-empty v-if="!execution?.step_results?.length" description="暂无步骤结果" />

      <el-table
        v-else
        :data="execution.step_results"
        row-key="id"
        class="result-table"
      >
        <el-table-column type="index" label="#" width="60" align="center" />
        <el-table-column prop="step_name" label="步骤名称" min-width="160">
          <template #default="{ row }">
            <span class="text-ellipsis" :title="row.step_name">{{ row.step_name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="step_type" label="类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small">{{ row.step_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="耗时(s)" width="90" align="center">
          <template #default="{ row }">
            {{ row.duration != null ? row.duration : '—' }}
          </template>
        </el-table-column>
        <el-table-column prop="actual_result" label="实际结果" min-width="160">
          <template #default="{ row }">
            <span v-if="row.actual_result" class="text-ellipsis" :title="row.actual_result">{{ row.actual_result }}</span>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="错误信息" min-width="160">
          <template #default="{ row }">
            <span v-if="row.error_message" class="error-text">{{ row.error_message }}</span>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right" align="center">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              text
              @click="handleViewStepDetail(row)"
            >详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 步骤详情弹窗 -->
    <el-dialog v-model="stepDetailVisible" title="步骤详情" width="640px">
      <el-descriptions v-if="currentStepResult" :column="1" border>
        <el-descriptions-item label="步骤名称">{{ currentStepResult.step_name }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ currentStepResult.step_type }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentStepResult.status)" size="small">
            {{ getStatusLabel(currentStepResult.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="耗时">{{ currentStepResult.duration != null ? `${currentStepResult.duration}s` : '—' }}</el-descriptions-item>
        <el-descriptions-item label="实际结果">{{ currentStepResult.actual_result || '—' }}</el-descriptions-item>
        <el-descriptions-item label="错误信息" v-if="currentStepResult.error_message">
          <span style="color: var(--el-color-danger)">{{ currentStepResult.error_message }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="请求数据" v-if="currentStepResult.request_data">
          <pre class="code-block">{{ JSON.stringify(JSON.parse(currentStepResult.request_data), null, 2) }}</pre>
        </el-descriptions-item>
        <el-descriptions-item label="响应数据" v-if="currentStepResult.response_data">
          <pre class="code-block">{{ JSON.stringify(JSON.parse(currentStepResult.response_data), null, 2) }}</pre>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useScenarioStore } from '@/stores/scenarioStore'

const route = useRoute()
const router = useRouter()
const scenarioStore = useScenarioStore()

const runId = computed(() => Number(route.params.id))
const execution = computed(() => scenarioStore.currentExecution)
const stepDetailVisible = ref(false)
const currentStepResult = ref(null)

onMounted(async () => {
  try {
    await scenarioStore.fetchExecution(runId.value)
  } catch {
    ElMessage.error('加载执行详情失败')
  }
})

async function handleRetry() {
  if (!execution.value?.scenario_id) return
  try {
    await ElMessageBox.confirm('确定要重试此执行吗？', '重试确认', { type: 'info' })
    const result = await scenarioStore.startExecution(execution.value.scenario_id)
    ElMessage.success(`重试已启动 (run_id: ${result.run_id})`)
    router.push({ name: 'ExecutionDetail', params: { id: result.run_id } })
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('重试失败')
  }
}

async function handleRerun() {
  if (!execution.value?.scenario_id) return
  try {
    await ElMessageBox.confirm('确定要重新执行场景吗？', '重新执行', { type: 'info' })
    const result = await scenarioStore.startExecution(execution.value.scenario_id)
    ElMessage.success(`重新执行已启动 (run_id: ${result.run_id})`)
    router.push({ name: 'ExecutionDetail', params: { id: result.run_id } })
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('执行失败')
  }
}

function handleViewStepDetail(row) {
  currentStepResult.value = row
  stepDetailVisible.value = true
}

function getStatusType(status) {
  const map = {
    pending: 'info',
    running: 'primary',
    passed: 'success',
    success: 'success',
    failed: 'danger',
    error: 'danger',
    skipped: 'warning',
  }
  return map[status] || 'info'
}

function getStatusLabel(status) {
  const map = {
    pending: '等待中',
    running: '运行中',
    passed: '通过',
    success: '成功',
    failed: '失败',
    error: '错误',
    skipped: '跳过',
  }
  return map[status] || status
}
</script>

<style scoped>
.execution-detail {
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  overflow-y: auto;
  height: 100%;
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

.page-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.stat-card {
  border-radius: var(--border-radius-base);
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.timeline-card {
  border-radius: var(--border-radius-base);
}

.steps-result {
  flex: 1;
  background: var(--bg-container);
  border-radius: var(--border-radius-base);
  border: 1px solid var(--border-color);
  padding: var(--spacing-md);
}

.section-header {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--spacing-md);
}

.result-table {
  margin-top: 0;
}

.error-text {
  color: var(--el-color-danger);
  font-size: 13px;
}

.text-muted {
  color: var(--text-disabled);
  font-size: 13px;
}

.code-block {
  background: var(--bg-page);
  border-radius: 4px;
  padding: var(--spacing-sm);
  font-size: 12px;
  overflow-x: auto;
  max-height: 200px;
  overflow-y: auto;
  margin: 0;
}
</style>
