<template>
  <div class="report-detail">
    <div class="detail-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" text @click="router.push('/report')">返回列表</el-button>
        <el-divider direction="vertical" />
        <span class="detail-title">{{ report?.name || '加载中…' }}</span>
      </div>
    </div>

    <!-- 概览统计 -->
    <el-row :gutter="16" v-if="report">
      <el-col :span="6">
        <el-card class="stat-card" shadow="never">
          <div class="stat-label">通过率</div>
          <div class="stat-value" :style="{ color: getPassRateColor(report.summary?.pass_rate) }">
            {{ report.summary?.pass_rate != null ? report.summary.pass_rate + '%' : '—' }}
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="never">
          <div class="stat-label">用例总数</div>
          <div class="stat-value">{{ report.summary?.total ?? '—' }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="never">
          <div class="stat-label">通过 / 失败</div>
          <div class="stat-value">
            <span style="color: var(--el-color-success)">{{ report.summary?.passed ?? 0 }}</span>
            /
            <span style="color: var(--el-color-danger)">{{ report.summary?.failed ?? 0 }}</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="never">
          <div class="stat-label">执行耗时</div>
          <div class="stat-value">{{ report.duration_ms ? (report.duration_ms / 1000).toFixed(1) + 's' : '—' }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 基本信息 -->
    <el-card v-if="report" class="info-card" shadow="never">
      <el-descriptions :column="3" border>
        <el-descriptions-item label="报告ID">{{ report.id }}</el-descriptions-item>
        <el-descriptions-item label="报告类型">{{ formatType(report.report_type) }}</el-descriptions-item>
        <el-descriptions-item label="执行环境">{{ report.environment || '—' }}</el-descriptions-item>
        <el-descriptions-item label="目标名称">{{ report.target_name || '—' }}</el-descriptions-item>
        <el-descriptions-item label="触发者">{{ report.triggered_by || '—' }}</el-descriptions-item>
        <el-descriptions-item label="执行时间">{{ report.executed_at || '—' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 指标详情 -->
    <el-card v-if="report?.metrics && Object.keys(report.metrics).length > 0" class="metrics-card" shadow="never">
      <template #header>
        <span class="card-title">详细指标</span>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item
          v-for="(value, key) in report.metrics"
          :key="key"
          :label="key"
        >
          {{ formatMetricValue(value) }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 加载状态 -->
    <el-empty v-if="!report && !reportStore.loading" description="报告不存在或已删除" />
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { useReportStore } from '@/stores/reportStore'

const route = useRoute()
const router = useRouter()
const reportStore = useReportStore()

const report = computed(() => reportStore.currentReport)

onMounted(async () => {
  const id = Number(route.params.id)
  try {
    await reportStore.fetchReport(id)
  } catch {
    /* error handled in store */
  }
})

function formatType(type) {
  const map = { execution: '执行报告', scenario: '场景报告', suite: '套件报告' }
  return map[type] || type
}

function getPassRateColor(rate) {
  if (rate == null) return 'var(--text-secondary)'
  if (rate >= 95) return 'var(--el-color-success)'
  if (rate >= 80) return 'var(--el-color-warning)'
  return 'var(--el-color-danger)'
}

function formatMetricValue(value) {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}
</script>

<style scoped>
.report-detail {
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
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

.detail-title {
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
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}

.info-card,
.metrics-card {
  border-radius: var(--border-radius-base);
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}
</style>
