<template>
  <div class="execution-detail">
    <!-- 页面标题区 -->
    <header class="execution-detail__header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" text @click="router.push('/scenario/executions')">返回</el-button>
        <el-divider direction="vertical" />
        <span class="page-title">执行详情</span>
        <el-tag v-if="execution" :type="getStatusType(execution?.status)" style="margin-left: 8px">
          {{ getStatusLabel(execution?.status) }}
        </el-tag>
      </div>
      <div class="header-right">
        <el-button v-if="execution?.status === 'failed'" type="warning" :icon="MagicStick" :loading="aiAnalyzing" @click="handleAiAnalyze">AI 分析失败</el-button>
        <el-button v-if="execution?.status === 'failed'" type="warning" @click="handleRetry">重试</el-button>
        <el-button type="primary" @click="handleRerun">重新执行</el-button>
      </div>
    </header>

    <!-- 执行概览 -->
    <section v-if="execution" class="execution-detail__stats">
      <el-row :gutter="16">
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
    </section>

    <!-- 时间线信息 -->
    <section v-if="execution" class="execution-detail__timeline">
      <el-card shadow="never">
        <el-descriptions :column="3" border>
          <el-descriptions-item label="Run ID">{{ execution.id }}</el-descriptions-item>
          <el-descriptions-item label="触发者">{{ execution.triggered_by || '—' }}</el-descriptions-item>
          <el-descriptions-item label="开始时间">{{ execution.started_at || '—' }}</el-descriptions-item>
          <el-descriptions-item label="结束时间">{{ execution.finished_at || '—' }}</el-descriptions-item>
          <el-descriptions-item label="失败策略" :span="2">{{ execution.on_error || 'stop' }}</el-descriptions-item>
        </el-descriptions>
      </el-card>
    </section>

    <!-- 步骤结果 -->
    <section class="execution-detail__steps">
      <div class="section-header">步骤结果</div>

      <el-empty v-if="!execution?.step_results?.length" description="暂无步骤结果" />

      <el-table
        v-else
        :data="execution.step_results"
        row-key="id"
        height="100%"
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
          <template #default="{ row }">{{ row.duration != null ? row.duration : '—' }}</template>
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
            <el-button type="primary" size="small" text @click="handleViewStepDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <!-- 步骤详情弹窗 -->
    <el-dialog v-model="stepDetailVisible" title="步骤详情" width="640px" destroy-on-close>
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
        <el-descriptions-item v-if="currentStepResult.error_message" label="错误信息">
          <span style="color: var(--el-color-danger)">{{ currentStepResult.error_message }}</span>
        </el-descriptions-item>
        <el-descriptions-item v-if="currentStepResult.request_data" label="请求数据">
          <pre class="code-block">{{ JSON.stringify(JSON.parse(currentStepResult.request_data), null, 2) }}</pre>
        </el-descriptions-item>
        <el-descriptions-item v-if="currentStepResult.response_data" label="响应数据">
          <pre class="code-block">{{ JSON.stringify(JSON.parse(currentStepResult.response_data), null, 2) }}</pre>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- AI 失败分析结果弹窗 -->
    <el-dialog v-model="aiAnalysisVisible" title="AI 失败分析" width="600px" destroy-on-close>
      <div v-if="aiAnalysisResult" class="ai-analysis-result">
        <el-alert v-if="aiAnalysisResult.root_cause" type="warning" :title="aiAnalysisResult.root_cause" :closable="false" show-icon />
        <div v-if="aiAnalysisResult.suggestions?.length" class="analysis-section">
          <h4>修复建议</h4>
          <ul>
            <li v-for="(s, i) in aiAnalysisResult.suggestions" :key="i">{{ typeof s === 'string' ? s : (s.description || JSON.stringify(s)) }}</li>
          </ul>
        </div>
        <div v-if="aiAnalysisResult.impact_scope" class="analysis-section">
          <h4>影响范围</h4>
          <p>{{ aiAnalysisResult.impact_scope }}</p>
        </div>
      </div>
      <el-empty v-else description="暂无分析结果" />
      <template #footer>
        <el-button @click="aiAnalysisVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleCreateDefectFromAnalysis" :disabled="!aiAnalysisResult?.root_cause">创建缺陷草稿</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, MagicStick } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useScenarioStore } from '@/stores/scenarioStore'
import { useAiStore } from '@/stores/aiStore'
import { useReportStore } from '@/stores/reportStore'

const route = useRoute()
const router = useRouter()
const scenarioStore = useScenarioStore()
const reportStore = useReportStore()

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

// ── AI 失败分析 ────────────────────────────────────────────

const aiStore = useAiStore()
const aiAnalyzing = ref(false)
const aiAnalysisResult = ref(null)
const aiAnalysisVisible = ref(false)

async function handleAiAnalyze() {
  aiAnalyzing.value = true
  aiAnalysisResult.value = null
  try {
    const result = await aiStore.analyzeFailure({
      execution_step_id: runId.value,
      case_data: {
        scenario_name: execution.value?.scenario_name,
        step_results: execution.value?.step_results,
      },
    })
    aiAnalysisResult.value = result
    aiAnalysisVisible.value = true
    if (result?.root_cause) {
      ElMessage.success('分析完成')
    }
  } catch (e) {
    ElMessage.error('AI 分析失败: ' + (e.response?.data?.detail || e.message || '请检查 AI 配置'))
  } finally {
    aiAnalyzing.value = false
  }
}

function handleCreateDefectFromAnalysis() {
  if (!aiAnalysisResult.value?.root_cause) return
  const rootCause = aiAnalysisResult.value.root_cause
  const suggestions = (aiAnalysisResult.value.suggestions || [])
    .map(s => typeof s === 'string' ? s : s.description)
    .filter(Boolean)
    .join('; ')
  const defectData = {
    title: `[缺陷草稿] ${rootCause}`,
    description: `场景：${execution.value?.scenario_name || ''}\n根因：${rootCause}\n修复建议：${suggestions}`,
    severity: 'medium',
    priority: 'P2',
    defect_type: 'functional',
    tags: ['AI分析'],
  }
  reportStore.createDefect(defectData).then(() => {
    ElMessage.success('缺陷草稿已创建')
  }).catch(() => {
    ElMessage.error('创建缺陷失败')
  })
  aiAnalysisVisible.value = false
}

function getStatusType(status) {
  const map = {
    pending: 'info', running: 'primary', passed: 'success', success: 'success',
    failed: 'danger', error: 'danger', skipped: 'warning',
  }
  return map[status] || 'info'
}

function getStatusLabel(status) {
  const map = {
    pending: '等待中', running: '运行中', passed: '通过', success: '成功',
    failed: '失败', error: '错误', skipped: '跳过',
  }
  return map[status] || status
}
</script>

<style scoped>
/* ── 页面容器 ── */
.execution-detail {
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

/* ── 标题区 ── */
.execution-detail__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-height: 56px;
  padding: 12px 16px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: rgba(20, 22, 27, 0.7);
  box-shadow: var(--box-shadow-light);
  backdrop-filter: blur(10px);
}

html:not(.dark) .execution-detail__header {
  background: rgba(255, 255, 255, 0.86);
}

.header-left {
  display: flex;
  align-items: center;
}

.header-right {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}

.page-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-strong);
}

/* ── 统计卡片 ── */
.execution-detail__stats :deep(.el-card) {
  border-radius: var(--border-radius-base);
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
  color: var(--text-strong);
}

/* ── 时间线 ── */
.execution-detail__timeline :deep(.el-card) {
  border-radius: var(--border-radius-base);
}

/* ── 步骤结果 ── */
.execution-detail__steps {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: rgba(20, 22, 27, 0.7);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  box-shadow: var(--box-shadow-light);
  backdrop-filter: blur(10px);
  overflow: hidden;
}

html:not(.dark) .execution-detail__steps {
  background: rgba(255, 255, 255, 0.86);
}

.section-header {
  padding: 12px 16px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-strong);
  border-bottom: 1px solid var(--border-color);
}

.execution-detail__steps :deep(.el-table) {
  flex: 1;
}

.execution-detail__steps :deep(.el-table__header th) {
  background: var(--bg-container-soft) !important;
  color: var(--text-secondary);
  font-weight: 700;
  font-size: 12px;
}

.execution-detail__steps :deep(.el-table__row:hover > td) {
  background: rgba(56, 189, 248, 0.1) !important;
}

.execution-detail__steps :deep(.el-table__cell) {
  vertical-align: middle;
}

/* ── 通用 ── */
.text-ellipsis {
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
  padding: 8px;
  font-size: 12px;
  overflow-x: auto;
  max-height: 200px;
  overflow-y: auto;
  margin: 0;
}

.ai-analysis-result {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ai-analysis-result .analysis-section h4 {
  margin: 0 0 8px;
  color: var(--text-secondary);
  font-size: 13px;
}

.ai-analysis-result .analysis-section ul {
  margin: 0;
  padding-left: 20px;
  color: var(--text-primary);
}
</style>
