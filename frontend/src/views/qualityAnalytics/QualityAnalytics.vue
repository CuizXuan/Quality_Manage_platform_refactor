<template>
  <div class="quality-analytics-page">
    <!-- 页面标题区 -->
    <header class="page-header">
      <div>
        <h1>质量看板</h1>
        <p>版本能不能发，风险在哪里，通过率和缺陷趋势如何。</p>
      </div>
    </header>

    <!-- 筛选栏 -->
    <section class="filter-bar">
      <el-form :model="filters" inline class="filter-form">
        <el-form-item label="项目">
          <el-select
            v-model="filters.project_id"
            placeholder="全部项目"
            clearable
            filterable
            @change="onProjectChange"
          >
            <el-option
              v-for="p in foundationStore.projects"
              :key="p.id"
              :label="p.name"
              :value="p.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="版本">
          <el-select
            v-model="filters.version_id"
            placeholder="全部版本"
            clearable
            filterable
            :disabled="!filters.project_id"
            @change="onVersionChange"
          >
            <el-option
              v-for="v in foundationStore.versions"
              :key="v.id"
              :label="v.name"
              :value="v.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="迭代">
          <el-select
            v-model="filters.iteration_id"
            placeholder="全部迭代"
            clearable
            filterable
            :disabled="!filters.version_id"
          >
            <el-option
              v-for="i in foundationStore.iterations"
              :key="i.id"
              :label="i.name"
              :value="i.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="时间范围">
          <el-select v-model="filters.days" @change="loadAll">
            <el-option label="最近 7 天" :value="7" />
            <el-option label="最近 30 天" :value="30" />
            <el-option label="最近 90 天" :value="90" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadAll">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
      <div v-if="scopeNote" class="scope-note">
        <el-alert :title="scopeNote" type="info" :closable="false" show-icon />
      </div>
    </section>

    <!-- 质量概览卡片 -->
    <section class="metrics-cards">
      <div class="metric-card metric-card--score">
        <div class="metric-card__value">{{ overview?.quality_score ?? 0 }}</div>
        <div class="metric-card__label">质量评分</div>
        <div class="metric-card__hint">0-100</div>
      </div>
      <div class="metric-card metric-card--pass">
        <div class="metric-card__value">{{ overview?.average_pass_rate ?? 0 }}%</div>
        <div class="metric-card__label">平均通过率</div>
        <div class="metric-card__sub">{{ overview?.passed_cases ?? 0 }} / {{ overview?.total_cases ?? 0 }}</div>
      </div>
      <div class="metric-card metric-card--execution">
        <div class="metric-card__value">{{ overview?.execution_count ?? 0 }}</div>
        <div class="metric-card__label">执行次数</div>
        <div class="metric-card__sub">{{ overview?.report_count ?? 0 }} 份报告</div>
      </div>
      <div class="metric-card metric-card--defect">
        <div class="metric-card__value">{{ overview?.defect_total ?? 0 }}</div>
        <div class="metric-card__label">缺陷总数</div>
        <div class="metric-card__sub">
          <span class="text-danger">P0/P1: {{ overview?.defect_p0p1 ?? 0 }}</span>
          &nbsp; 未关闭: {{ overview?.defect_open ?? 0 }}
        </div>
      </div>
      <div class="metric-card metric-card--coverage">
        <div class="metric-card__value">{{ coverageRate ?? 0 }}%</div>
        <div class="metric-card__label">需求覆盖率</div>
        <div class="metric-card__sub">
          {{ overview?.requirement_covered ?? 0 }} / {{ overview?.requirement_total ?? 0 }}
        </div>
      </div>
    </section>

    <!-- 发布门禁结论 -->
    <section class="gate-result" :class="releaseGate?.overall_pass ? 'gate-result--pass' : 'gate-result--fail'">
      <div class="gate-result__icon">
        <el-icon :size="32"><CircleCheck v-if="releaseGate?.overall_pass" /><CloseBold v-else /></el-icon>
      </div>
      <div class="gate-result__content">
        <div class="gate-result__title">
          {{ releaseGate?.overall_pass ? '✓ 发布门禁通过' : '✗ 发布门禁未通过' }}
        </div>
        <div class="gate-result__level">
          门禁等级：<el-tag size="small" :type="gateLevelType">{{ releaseGate?.gate_level ?? 'warning' }}</el-tag>
          &nbsp; 检查门禁 {{ gatesChecked ?? 0 }} 个
          &nbsp; 通过 {{ releaseGate?.conditions_passed ?? 0 }} / 失败 {{ releaseGate?.conditions_failed ?? 0 }}
        </div>
        <div v-if="releaseGate?.blockers?.length" class="gate-result__blockers">
          <div class="blocker-item" v-for="(b, i) in releaseGate.blockers" :key="i">
            <el-icon><Warning /></el-icon> {{ b }}
          </div>
        </div>
      </div>
    </section>

    <!-- 趋势图区域（表格形式） -->
    <section class="trend-table">
      <div class="section-title">通过率趋势</div>
      <el-table :data="trends" height="200" size="small">
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column prop="pass_rate" label="通过率" width="100">
          <template #default="{ row }">
            <span :class="passRateClass(row.pass_rate)">{{ row.pass_rate }}%</span>
          </template>
        </el-table-column>
        <el-table-column prop="execution_count" label="执行次数" width="100" />
        <el-table-column prop="defect_count" label="新增缺陷" width="100" />
      </el-table>
    </section>

    <!-- 缺陷分布 + 需求覆盖 -->
    <section class="two-column">
      <div class="panel">
        <div class="section-title">缺陷分布</div>
        <el-table :data="defectDistribution" height="200" size="small">
          <el-table-column prop="severity" label="严重程度" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="severityType(row.severity)">{{ row.severity }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="count" label="数量" width="80" />
          <el-table-column prop="open_count" label="未关闭" width="80" />
        </el-table>
      </div>
      <div class="panel">
        <div class="section-title">需求覆盖 ({{ coverageRate ?? 0 }}%)</div>
        <el-table :data="requirementCoverage.slice(0, 20)" height="200" size="small">
          <el-table-column prop="title" label="需求" min-width="160">
            <template #default="{ row }">
              <span :class="row.covered ? 'text-success' : 'text-muted'">
                {{ row.covered ? '✓ ' : '✗ ' }}{{ row.title || '(无标题)' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="80" />
        </el-table>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useQualityAnalyticsStore } from '@/stores/qualityAnalyticsStore'
import { useQualityFoundationStore } from '@/stores/qualityFoundationStore'
import { useReportStore } from '@/stores/reportStore'
import { TrendCharts, CircleCheck, CloseBold, Warning } from '@element-plus/icons-vue'

const analyticsStore = useQualityAnalyticsStore()
const foundationStore = useQualityFoundationStore()
const reportStore = useReportStore()

const filters = ref({
  project_id: null,
  version_id: null,
  iteration_id: null,
  days: 30,
})

const overview = computed(() => analyticsStore.overview)
const trends = computed(() => analyticsStore.trends)
const defectDistribution = computed(() => analyticsStore.defectDistribution)
const requirementCoverage = computed(() => analyticsStore.requirementCoverage)
const releaseGate = computed(() => analyticsStore.releaseGate)
const coverageRate = computed(() => analyticsStore.coverageRate ?? 0)
const gatesChecked = computed(() => analyticsStore.gatesChecked ?? 0)
const scopeNote = computed(() => analyticsStore.scopeNote || '')

const gateLevelType = computed(() => {
  const level = releaseGate.value?.gate_level
  if (level === 'blocking') return 'danger'
  if (level === 'warning') return 'warning'
  return 'info'
})

function severityType(sev) {
  const map = { critical: 'danger', high: 'warning', medium: 'info', low: 'success' }
  return map[sev] || 'info'
}

function passRateClass(rate) {
  if (rate >= 90) return 'text-success'
  if (rate >= 70) return 'text-warning'
  return 'text-danger'
}

function onProjectChange() {
  filters.value.version_id = null
  filters.value.iteration_id = null
  foundationStore.clearVersions()
  foundationStore.clearIterations()
  if (filters.value.project_id) {
    foundationStore.fetchVersions({ project_id: filters.value.project_id })
  }
}

function onVersionChange() {
  filters.value.iteration_id = null
  foundationStore.clearIterations()
  if (filters.value.version_id) {
    foundationStore.fetchIterations({ version_id: filters.value.version_id })
  }
}

async function loadAll() {
  analyticsStore.setFilters(filters.value)
  const [overview, trends, defects, coverage, gate] = await Promise.all([
    analyticsStore.fetchOverview().then(() => analyticsStore.overview),
    analyticsStore.fetchTrends().then(() => analyticsStore.trends),
    analyticsStore.fetchDefectDistribution().then(() => analyticsStore.defectDistribution),
    analyticsStore.fetchRequirementCoverage().then(() => analyticsStore.requirementCoverage),
    analyticsStore.fetchReleaseGate().then(() => analyticsStore.releaseGate),
  ])

  // Extract extra fields from API responses
  if (analyticsStore.overview) {
    // already set
  }
}

function resetFilters() {
  filters.value = { project_id: null, version_id: null, iteration_id: null, days: 30 }
  analyticsStore.resetFilters()
  loadAll()
}

onMounted(async () => {
  // Load projects for filter dropdown
  if (!foundationStore.projects?.length) {
    foundationStore.fetchProjects()
  }

  // Load all analytics data
  analyticsStore.setFilters(filters.value)
  await analyticsStore.loadAll()
})
</script>

<style scoped>
@import '@/styles/element-override.css';

.quality-analytics-page {
  padding: 20px 24px;
  min-height: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}
.page-header h1 {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 4px;
}
.page-header p {
  color: var(--text-secondary, #909399);
  font-size: 13px;
  margin: 0;
}

.filter-bar {
  background: var(--card-bg, #fff);
  border-radius: 8px;
  padding: 16px;
}
.filter-form {
  flex-wrap: wrap;
  gap: 8px;
}
.scope-note {
  margin-top: 8px;
}

.metrics-cards {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
}
.metric-card {
  background: var(--card-bg, #fff);
  border-radius: 8px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.metric-card__value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
}
.metric-card__label {
  font-size: 13px;
  color: var(--text-secondary, #909399);
}
.metric-card__sub {
  font-size: 12px;
  color: var(--text-secondary, #909399);
}
.metric-card--score .metric-card__value { color: #409eff; }
.metric-card--pass .metric-card__value { color: #67c23a; }
.metric-card--defect .metric-card__value { color: #f56c6c; }
.metric-card--coverage .metric-card__value { color: #e6a23c; }

.gate-result {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  background: var(--card-bg, #fff);
  border-radius: 8px;
  padding: 16px 20px;
  border-left: 4px solid;
}
.gate-result--pass { border-color: #67c23a; }
.gate-result--fail { border-color: #f56c6c; }
.gate-result__icon {
  flex-shrink: 0;
  line-height: 1;
}
.gate-result--pass .gate-result__icon { color: #67c23a; }
.gate-result--fail .gate-result__icon { color: #f56c6c; }
.gate-result__title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 6px;
}
.gate-result__level {
  font-size: 13px;
  color: var(--text-secondary, #909399);
}
.gate-result__blockers {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.blocker-item {
  font-size: 12px;
  color: #f56c6c;
  display: flex;
  align-items: center;
  gap: 4px;
}

.trend-table {
  background: var(--card-bg, #fff);
  border-radius: 8px;
  padding: 16px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--text-primary, #303133);
}

.two-column {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.panel {
  background: var(--card-bg, #fff);
  border-radius: 8px;
  padding: 16px;
}

.text-success { color: #67c23a; }
.text-warning { color: #e6a23c; }
.text-danger { color: #f56c6c; }
.text-muted { color: #909399; }
</style>