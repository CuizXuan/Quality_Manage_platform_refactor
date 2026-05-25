<template>
  <div class="report-list-page">
    <!-- 页面标题区 -->
    <header class="report-list-page__header">
      <div>
        <h1>测试报告</h1>
        <p>统一管理测试执行报告，支持查看执行详情与趋势分析。</p>
      </div>
    </header>

    <!-- 查询区 -->
    <section class="report-list-page__filters">
      <el-form :model="draftFilters" label-position="left" class="filter-form">
        <div class="filter-form__row">
          <el-form-item label="项目：" class="filter-item filter-item--project">
            <el-select
              v-model="draftFilters.projectId"
              placeholder="选择项目"
              clearable
              class="filter-control"
              @change="onProjectChange"
            >
              <el-option v-for="p in foundationStore.projects" :key="p.id" :label="p.name" :value="p.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="版本：" class="filter-item filter-item--version">
            <el-select
              v-model="draftFilters.versionId"
              placeholder="选择版本"
              clearable
              class="filter-control"
              :disabled="!draftFilters.projectId"
              @change="onVersionChange"
            >
              <el-option v-for="v in foundationStore.versions" :key="v.id" :label="v.name" :value="v.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="迭代：" class="filter-item filter-item--iteration">
            <el-select
              v-model="draftFilters.iterationId"
              placeholder="选择迭代"
              clearable
              class="filter-control"
              :disabled="!draftFilters.versionId"
            >
              <el-option v-for="i in foundationStore.iterations" :key="i.id" :label="i.name" :value="i.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="报告类型：" class="filter-item filter-item--type">
            <el-select
              v-model="draftFilters.report_type"
              placeholder="全部类型"
              clearable
              class="filter-control"
            >
              <el-option label="执行报告" value="execution" />
              <el-option label="场景报告" value="scenario" />
              <el-option label="套件报告" value="suite" />
            </el-select>
          </el-form-item>
          <el-form-item label="环境：" class="filter-item filter-item--env">
            <el-select
              v-model="draftFilters.environment"
              placeholder="全部环境"
              clearable
              class="filter-control"
            >
              <el-option label="开发环境" value="dev" />
              <el-option label="测试环境" value="test" />
              <el-option label="预发环境" value="staging" />
              <el-option label="生产环境" value="prod" />
            </el-select>
          </el-form-item>
          <el-form-item label="关键词：" class="filter-item filter-item--keyword">
            <el-input
              v-model="draftFilters.keyword"
              placeholder="搜索报告名称"
              clearable
              class="search-bar__input"
              @keyup.enter="handleSearch"
            />
          </el-form-item>
          <div class="filter-actions">
            <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
            <el-button :icon="RefreshLeft" @click="handleReset">重置</el-button>
          </div>
        </div>
      </el-form>
    </section>

    <!-- 数据列表 -->
    <section class="report-list-page__table">
      <el-table
        v-loading="reportStore.loading"
        :data="reportStore.reports"
        height="100%"
        highlight-current-row
        @row-click="handleRowClick"
      >
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="报告名称" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="name-cell">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="report_type" label="类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small">{{ formatType(row.report_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="target_name" label="目标" min-width="140">
          <template #default="{ row }">
            <span v-if="row.target_name" class="text-secondary">{{ row.target_name }}</span>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="environment" label="环境" width="90" align="center">
          <template #default="{ row }">
            <span class="text-secondary">{{ row.environment || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="summary.pass_rate" label="通过率" width="100" align="center">
          <template #default="{ row }">
            <span :style="{ color: getPassRateColor(row.summary?.pass_rate) }">
              {{ row.summary?.pass_rate != null ? `${row.summary.pass_rate}%` : '—' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="通过/失败" width="110" align="center">
          <template #default="{ row }">
            <span class="text-success">{{ row.summary?.passed ?? 0 }}</span>
            <span class="text-secondary"> / </span>
            <span class="text-danger">{{ row.summary?.failed ?? 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="duration_ms" label="耗时" width="100" align="center">
          <template #default="{ row }">
            <span class="text-secondary">{{ row.duration_ms ? `${(row.duration_ms / 1000).toFixed(1)}s` : '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="executed_at" label="执行时间" width="170" align="center" />
        <el-table-column label="操作" width="100" fixed="right" align="center">
          <template #default="{ row }">
            <div class="actions-cell">
              <el-button type="danger" text size="small" @click.stop="handleDelete(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
        <template #empty>
          <span class="empty-text">暂无符合条件的报告</span>
        </template>
      </el-table>

      <div class="report-list-page__pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="reportStore.reportTotal"
          :page-sizes="[15, 30, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          prev-text="上一页"
          next-text="下一页"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search, RefreshLeft } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useReportStore } from '@/stores/reportStore'
import { useQualityFoundationStore } from '@/stores/qualityFoundationStore'

const router = useRouter()
const reportStore = useReportStore()
const foundationStore = useQualityFoundationStore()

const draftFilters = ref({
  projectId: null,
  versionId: null,
  iterationId: null,
  keyword: '',
  report_type: '',
  environment: '',
})

const appliedFilters = ref({
  projectId: null,
  versionId: null,
  iterationId: null,
  keyword: '',
  report_type: '',
  environment: '',
})

const pagination = ref({
  page: 1,
  pageSize: 15,
})

onMounted(() => {
  foundationStore.fetchProjects({ page: 1, page_size: 100 })
  reportStore.fetchReports({ page: 1, page_size: pagination.value.pageSize })
})

function onProjectChange(projectId) {
  draftFilters.value.versionId = null
  draftFilters.value.iterationId = null
  if (projectId) {
    foundationStore.fetchVersions({ project_id: projectId })
  }
}

function onVersionChange(versionId) {
  draftFilters.value.iterationId = null
  if (versionId) {
    foundationStore.fetchIterations({ project_id: draftFilters.value.projectId, version_id: versionId })
  }
}

function buildQueryParams() {
  return {
    page: pagination.value.page,
    page_size: pagination.value.pageSize,
    keyword: appliedFilters.value.keyword || undefined,
    report_type: appliedFilters.value.report_type || undefined,
    environment: appliedFilters.value.environment || undefined,
    project_id: appliedFilters.value.projectId || undefined,
    version_id: appliedFilters.value.versionId || undefined,
    iteration_id: appliedFilters.value.iterationId || undefined,
  }
}

function handleSearch() {
  appliedFilters.value = { ...draftFilters.value }
  pagination.value.page = 1
  reportStore.fetchReports({ ...buildQueryParams(), page: 1 })
}

function handleReset() {
  draftFilters.value = { projectId: null, versionId: null, iterationId: null, keyword: '', report_type: '', environment: '' }
  appliedFilters.value = { projectId: null, versionId: null, iterationId: null, keyword: '', report_type: '', environment: '' }
  pagination.value.page = 1
  reportStore.fetchReports({ page: 1, page_size: pagination.value.pageSize })
}

function handlePageChange(page) {
  pagination.value.page = page
  reportStore.fetchReports({ ...buildQueryParams(), page })
}

function handleSizeChange(size) {
  pagination.value.pageSize = size
  pagination.value.page = 1
  reportStore.fetchReports({ ...buildQueryParams(), page: 1, page_size: size })
}

function handleRowClick(row) {
  router.push({ name: 'ReportDetail', params: { id: row.id } })
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定要删除报告「${row.name}」吗？`, '删除确认', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await reportStore.deleteReport(row.id)
    ElMessage.success('删除成功')
    reportStore.fetchReports(buildQueryParams())
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('删除失败')
  }
}

function formatType(type) {
  const map = { execution: '执行', scenario: '场景', suite: '套件' }
  return map[type] || type
}

function getPassRateColor(rate) {
  if (rate == null) return 'var(--text-secondary)'
  if (rate >= 95) return 'var(--color-success)'
  if (rate >= 80) return 'var(--color-warning)'
  return 'var(--color-danger)'
}
</script>

<style scoped>
/* ── 动画关键帧 ── */
@keyframes report-list-scan {
  from { transform: translateX(-24%); }
  to { transform: translateX(24%); }
}

@keyframes report-list-particles {
  from { transform: translate3d(0, 0, 0); }
  to { transform: translate3d(26px, -18px, 0); }
}

@keyframes report-list-form-scan {
  from { transform: translateY(-8%); }
  to { transform: translateY(108%); }
}

@keyframes report-list-table-scan {
  from { transform: translateY(-6%); }
  to { transform: translateY(106%); }
}

/* ── 页面容器 ── */
.report-list-page {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-height: 0;
  min-width: 0;
  gap: 10px;
  padding: 12px;
  background:
    linear-gradient(rgba(56, 189, 248, 0.095) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.085) 1px, transparent 1px),
    linear-gradient(145deg, rgba(34, 211, 166, 0.18), transparent 30%),
    linear-gradient(225deg, rgba(56, 189, 248, 0.22), transparent 36%),
    linear-gradient(0deg, rgba(22, 119, 255, 0.12), transparent 50%),
    var(--bg-page);
  background-size: 28px 28px, 28px 28px, auto, auto, auto, auto;
  overflow: hidden;
  position: relative;
}

.report-list-page::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 24%, rgba(56, 189, 248, 0.16) 44%, transparent 62%),
    repeating-linear-gradient(90deg, transparent 0 92px, rgba(56, 189, 248, 0.075) 92px 93px);
  content: "";
  animation: report-list-scan 14s linear infinite;
}

.report-list-page::after {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background-image:
    radial-gradient(circle, rgba(125, 211, 252, 0.72) 0 1.2px, transparent 1.8px),
    radial-gradient(circle, rgba(45, 212, 191, 0.52) 0 1.1px, transparent 1.7px);
  background-position: 8% 16%, 80% 42%;
  background-size: 180px 160px, 240px 220px;
  opacity: 0.48;
  content: "";
  animation: report-list-particles 18s ease-in-out infinite alternate;
}

html:not(.dark) .report-list-page {
  background:
    linear-gradient(rgba(56, 189, 248, 0.095) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.085) 1px, transparent 1px),
    linear-gradient(145deg, rgba(34, 211, 166, 0.18), transparent 30%),
    linear-gradient(225deg, rgba(56, 189, 248, 0.22), transparent 36%),
    linear-gradient(0deg, rgba(22, 119, 255, 0.12), transparent 50%),
    var(--bg-page);
}

/* ── 标题区 ── */
.report-list-page__header {
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-height: 56px;
  padding: 12px 16px;
  border: 1px solid rgba(56, 189, 248, 0.22);
  border-radius: var(--border-radius-base);
  background:
    linear-gradient(135deg, rgba(15, 23, 42, 0.68), rgba(15, 23, 42, 0.42)),
    rgba(20, 22, 27, 0.48);
  box-shadow: 0 18px 48px rgba(2, 8, 23, 0.24), inset 0 1px 0 rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(18px) saturate(1.25);
  overflow: hidden;
  z-index: 1;
}

.report-list-page__header::after {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(90deg, rgba(56, 189, 248, 0.22), transparent 18% 82%, rgba(34, 211, 166, 0.18)),
    repeating-linear-gradient(90deg, transparent 0 42px, rgba(56, 189, 248, 0.06) 42px 43px);
  opacity: 0.65;
  content: "";
}

html:not(.dark) .report-list-page__header {
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.86), rgba(245, 250, 255, 0.68)),
    rgba(255, 255, 255, 0.72);
  box-shadow: 0 18px 46px rgba(20, 42, 76, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.82);
  border-color: rgba(22, 119, 255, 0.18);
}

.report-list-page__header h1,
.report-list-page__header p {
  margin: 0;
  position: relative;
  z-index: 1;
}

.report-list-page__header h1 {
  color: var(--text-strong);
  font-size: 24px;
  line-height: 1.25;
}

.report-list-page__header p {
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 13px;
}

/* ── 查询区 ── */
.report-list-page__filters {
  position: relative;
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
  padding: 14px;
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
  overflow: hidden;
  z-index: 1;
}

.report-list-page__filters::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(56, 189, 248, 0.1) 50%, transparent 66%);
  opacity: 0.7;
  content: "";
  animation: report-list-form-scan 12s linear infinite;
}

html:not(.dark) .report-list-page__filters {
  background:
    linear-gradient(rgba(22, 119, 255, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.04) 1px, transparent 1px),
    linear-gradient(145deg, rgba(255, 255, 255, 0.76), rgba(245, 250, 255, 0.58)),
    rgba(255, 255, 255, 0.62);
  background-size: 26px 26px, 26px 26px, auto, auto;
  border-color: rgba(22, 119, 255, 0.14);
}

html:not(.dark) .report-list-page__filters::before {
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(22, 119, 255, 0.08) 50%, transparent 66%);
}

.filter-form {
  position: relative;
  z-index: 1;
  width: 100%;
}

.filter-form__row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: flex-end;
  width: 100%;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.filter-form :deep(.el-form-item__label) {
  display: flex;
  align-items: center;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 700;
  line-height: 34px;
}

.filter-item {
  display: flex;
  flex: 0 0 auto;
  align-items: flex-end;
}

.filter-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: flex-end;
  margin-left: auto;
}

.filter-actions :deep(.el-button),
.filter-actions .el-button {
  min-width: 76px;
  height: 34px;
  margin-left: 0;
}

.filter-control {
  width: 180px;
}

.search-bar__input {
  width: 280px;
}

/* ── 表格区 ── */
.report-list-page__table {
  position: relative;
  display: flex;
  flex: 1;
  min-height: 0;
  flex-direction: column;
  border: 1px solid rgba(56, 189, 248, 0.18);
  border-radius: var(--border-radius-base);
  background:
    linear-gradient(rgba(56, 189, 248, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.045) 1px, transparent 1px),
    linear-gradient(145deg, rgba(15, 23, 42, 0.54), rgba(15, 23, 42, 0.34)),
    rgba(20, 22, 27, 0.36);
  background-size: 32px 32px, 32px 32px, auto, auto;
  box-shadow: 0 18px 48px rgba(2, 8, 23, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(16px) saturate(1.2);
  overflow: hidden;
  z-index: 1;
}

.report-list-page__table::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(56, 189, 248, 0.12) 50%, transparent 66%),
    radial-gradient(circle at 88% 16%, rgba(34, 211, 166, 0.14), transparent 26%);
  opacity: 0.8;
  content: "";
  animation: report-list-table-scan 12s linear infinite;
}

html:not(.dark) .report-list-page__table {
  background:
    linear-gradient(rgba(22, 119, 255, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.04) 1px, transparent 1px),
    linear-gradient(145deg, rgba(255, 255, 255, 0.76), rgba(245, 250, 255, 0.58)),
    rgba(255, 255, 255, 0.62);
  background-size: 32px 32px, 32px 32px, auto, auto;
  border-color: rgba(22, 119, 255, 0.14);
}

html:not(.dark) .report-list-page__table::before {
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(22, 119, 255, 0.1) 50%, transparent 66%);
}

.report-list-page__table :deep(.el-table) {
  flex: 1;
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: rgba(8, 18, 32, 0.34);
  --el-table-header-bg-color: rgba(15, 31, 52, 0.46);
  --el-table-row-hover-bg-color: var(--color-primary-soft);
  --el-table-expanded-cell-bg-color: rgba(8, 18, 32, 0.42);
  background:
    linear-gradient(rgba(56, 189, 248, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.03) 1px, transparent 1px),
    rgba(8, 18, 32, 0.32);
  background-size: 28px 28px, 28px 28px, auto;
}

html:not(.dark) .report-list-page__table :deep(.el-table) {
  --el-table-tr-bg-color: rgba(255, 255, 255, 0.54);
  --el-table-header-bg-color: rgba(240, 247, 255, 0.68);
  --el-table-expanded-cell-bg-color: rgba(255, 255, 255, 0.64);
  --el-table-row-hover-bg-color: var(--color-primary-soft);
  background:
    linear-gradient(rgba(22, 119, 255, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.03) 1px, transparent 1px),
    rgba(255, 255, 255, 0.44);
  background-size: 28px 28px, 28px 28px, auto;
}

.report-list-page__table :deep(.el-table__header th) {
  height: 44px;
  background: var(--el-table-header-bg-color) !important;
  background-color: var(--el-table-header-bg-color) !important;
  color: var(--text-secondary);
  font-weight: 700;
  font-size: 13px;
}

.report-list-page__table :deep(.el-table .cell) {
  padding: 0 10px;
}

.report-list-page__table :deep(.el-table__body td) {
  height: 48px;
  background: var(--el-table-tr-bg-color) !important;
  background-color: var(--el-table-tr-bg-color) !important;
}

.report-list-page__table :deep(.el-table__body tr:nth-child(even) td.el-table__cell) {
  background: rgba(15, 31, 52, 0.28) !important;
  background-color: rgba(15, 31, 52, 0.28) !important;
}

html:not(.dark) .report-list-page__table :deep(.el-table__body tr:nth-child(even) td.el-table__cell) {
  background: rgba(245, 250, 255, 0.5) !important;
  background-color: rgba(245, 250, 255, 0.5) !important;
}

.report-list-page__table :deep(.el-table__row:hover > td) {
  background: var(--el-table-row-hover-bg-color) !important;
  background-color: var(--el-table-row-hover-bg-color) !important;
}

.report-list-page__table :deep(.el-table__row:hover > td.el-table-fixed-column--right),
.report-list-page__table :deep(.el-table__row:hover > td.el-table-fixed-column--left) {
  background: var(--el-table-row-hover-bg-color) !important;
  background-color: var(--el-table-row-hover-bg-color) !important;
}

.report-list-page__table :deep(.el-table__cell) {
  vertical-align: middle;
}

.name-cell {
  font-weight: 600;
  color: var(--text-primary);
}

.text-secondary {
  color: var(--text-secondary);
  font-size: 13px;
}

.text-muted {
  color: var(--text-secondary);
  font-size: 13px;
}

.text-success {
  color: var(--color-success);
  font-weight: 600;
}

.text-danger {
  color: var(--color-danger);
  font-weight: 600;
}

.actions-cell {
  display: inline-flex;
  flex-wrap: nowrap;
  justify-content: center;
  gap: 4px;
  white-space: nowrap;
}

.actions-cell :deep(.el-button) {
  margin-left: 0;
  padding: 0 3px;
  font-size: 12px;
}

.empty-text {
  color: var(--text-secondary);
  font-size: 13px;
}

/* ── 分页 ── */
.report-list-page__pagination {
  display: flex;
  justify-content: flex-end;
  padding: 10px 16px;
  border-top: 1px solid rgba(56, 189, 248, 0.12);
}

html:not(.dark) .report-list-page__pagination {
  border-top-color: rgba(22, 119, 255, 0.12);
}

@media (prefers-reduced-motion: reduce) {
  .report-list-page::before,
  .report-list-page::after,
  .report-list-page__header::after,
  .report-list-page__filters::before,
  .report-list-page__table::before {
    animation: none;
  }
}
</style>
