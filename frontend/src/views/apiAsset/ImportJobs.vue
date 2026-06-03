<template>
  <div class="import-jobs-page">
    <header class="import-jobs-page__header">
      <div>
        <h1>导入任务看板</h1>
        <p>统一查看 OpenAPI、Postman、Apifox 的导入结果、覆盖率和问题分布。</p>
      </div>
      <div class="header-actions">
        <el-button @click="loadJobs">刷新</el-button>
        <el-button type="primary" @click="$router.push('/api-assets')">前往资产中心</el-button>
      </div>
    </header>

    <section class="import-jobs-page__metrics">
      <div class="metric-card">
        <strong>{{ metrics.totalJobs }}</strong>
        <span>导入任务</span>
      </div>
      <div class="metric-card">
        <strong>{{ metrics.totalImported }}</strong>
        <span>已导入接口</span>
      </div>
      <div class="metric-card">
        <strong>{{ metrics.totalIssues }}</strong>
        <span>问题总数</span>
      </div>
      <div class="metric-card">
        <strong>{{ metrics.avgCoverage }}%</strong>
        <span>平均覆盖率</span>
      </div>
    </section>

    <section class="import-jobs-page__board">
      <div class="board-panel">
        <div class="board-panel__title">最近任务</div>
        <div class="job-list">
          <button
            v-for="job in importStore.jobs"
            :key="job.id"
            class="job-card"
            type="button"
            @click="selectedJob = job"
          >
            <div class="job-card__header">
              <strong>#{{ job.id }} {{ job.source_name }}</strong>
              <el-tag size="small">{{ job.source_type }}</el-tag>
            </div>
            <div class="job-card__meta">
              <span>状态：{{ job.status }}</span>
              <span>导入：{{ job.imported_count }}/{{ job.total_count }}</span>
              <span>问题：{{ job.issue_count }}</span>
            </div>
          </button>
        </div>
      </div>

      <div class="board-panel">
        <div class="board-panel__title">任务详情</div>
        <template v-if="selectedJob">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="来源名称">{{ selectedJob.source_name }}</el-descriptions-item>
            <el-descriptions-item label="来源类型">{{ selectedJob.source_type }}</el-descriptions-item>
            <el-descriptions-item label="覆盖率">{{ selectedJob.summary.coverage_rate || 0 }}%</el-descriptions-item>
            <el-descriptions-item label="冲突数">{{ selectedJob.summary.conflict_count || 0 }}</el-descriptions-item>
            <el-descriptions-item label="缺少示例">{{ selectedJob.summary.missing_example_count || 0 }}</el-descriptions-item>
          </el-descriptions>

          <div class="issue-section">
            <div class="board-panel__title">问题清单</div>
            <el-table :data="selectedJob.issues || []" size="small" height="260">
              <el-table-column prop="issue_type" label="类型" width="140" />
              <el-table-column prop="severity" label="等级" width="100" />
              <el-table-column prop="method" label="方法" width="90" />
              <el-table-column prop="endpoint_path" label="路径" min-width="180" />
              <el-table-column prop="message" label="说明" min-width="220" />
            </el-table>
          </div>
        </template>
        <el-empty v-else description="选择左侧任务查看详情" />
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useImportAssetStore } from '@/stores/importAssetStore'

const importStore = useImportAssetStore()
const selectedJob = ref(null)

const metrics = computed(() => {
  const jobs = importStore.jobs || []
  const totalImported = jobs.reduce((sum, item) => sum + (item.imported_count || 0), 0)
  const totalIssues = jobs.reduce((sum, item) => sum + (item.issue_count || 0), 0)
  const avgCoverage = jobs.length
    ? Math.round(jobs.reduce((sum, item) => sum + (item.summary?.coverage_rate || 0), 0) / jobs.length)
    : 0
  return {
    totalJobs: jobs.length,
    totalImported,
    totalIssues,
    avgCoverage,
  }
})

async function loadJobs() {
  await importStore.fetchJobs()
  if (!selectedJob.value && importStore.jobs.length) {
    selectedJob.value = importStore.jobs[0]
  }
}

onMounted(loadJobs)
</script>

<style scoped>
.import-jobs-page {
  display: flex;
  flex-direction: column;
  gap: 10px;
  height: 100%;
  padding: 12px;
  position: relative;
}

.import-jobs-page__header,
.import-jobs-page__metrics,
.board-panel {
  position: relative;
  z-index: 1;
  border: 1px solid rgba(56, 189, 248, 0.18);
  border-radius: var(--border-radius-base);
  background:
    linear-gradient(rgba(56, 189, 248, 0.055) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.05) 1px, transparent 1px),
    linear-gradient(145deg, rgba(15, 23, 42, 0.54), rgba(15, 23, 42, 0.34)),
    rgba(20, 22, 27, 0.36);
  background-size: 26px 26px, 26px 26px, auto, auto;
  box-shadow: 0 18px 48px rgba(2, 8, 23, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(16px) saturate(1.2);
}

html:not(.dark) .import-jobs-page__header,
html:not(.dark) .import-jobs-page__metrics,
html:not(.dark) .board-panel {
  background:
    linear-gradient(rgba(22, 119, 255, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.04) 1px, transparent 1px),
    linear-gradient(145deg, rgba(255, 255, 255, 0.76), rgba(245, 250, 255, 0.58)),
    rgba(255, 255, 255, 0.62);
  background-size: 26px 26px, 26px 26px, auto, auto;
  border-color: rgba(22, 119, 255, 0.14);
  box-shadow: 0 18px 46px rgba(20, 42, 76, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.82);
}

.import-jobs-page__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-height: 56px;
  padding: 12px 16px;
}

.import-jobs-page__header h1,
.import-jobs-page__header p {
  margin: 0;
}

.import-jobs-page__header h1 {
  color: var(--text-strong);
  font-size: 24px;
}

.import-jobs-page__header p {
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 13px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.import-jobs-page__metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  padding: 14px;
}

.metric-card {
  display: grid;
  gap: 4px;
  padding: 12px;
  border-radius: 10px;
  background: rgba(8, 18, 32, 0.28);
}

html:not(.dark) .metric-card {
  background: rgba(255, 255, 255, 0.6);
}

.metric-card strong {
  font-size: 28px;
  color: var(--text-strong);
}

.metric-card span {
  color: var(--text-secondary);
  font-size: 13px;
}

.import-jobs-page__board {
  display: grid;
  grid-template-columns: minmax(320px, 0.9fr) minmax(0, 1.1fr);
  gap: 10px;
  flex: 1;
  min-height: 0;
}

.board-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 14px;
  min-height: 0;
}

.board-panel__title {
  color: var(--text-strong);
  font-size: 15px;
  font-weight: 700;
}

.job-list {
  display: grid;
  gap: 10px;
  overflow: auto;
}

.job-card {
  display: grid;
  gap: 6px;
  padding: 12px;
  border: 1px solid rgba(56, 189, 248, 0.12);
  border-radius: 10px;
  background: rgba(8, 18, 32, 0.26);
  text-align: left;
}

html:not(.dark) .job-card {
  background: rgba(255, 255, 255, 0.58);
  border-color: rgba(22, 119, 255, 0.12);
}

.job-card__header,
.job-card__meta {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
}

.job-card__meta {
  color: var(--text-secondary);
  font-size: 12px;
}

.issue-section {
  display: grid;
  gap: 10px;
  margin-top: 14px;
}
</style>
