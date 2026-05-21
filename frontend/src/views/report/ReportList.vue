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
      <div class="filter-bar">
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
      </div>
      <div class="search-bar">
        <el-input
          v-model="draftFilters.keyword"
          placeholder="搜索报告名称"
          clearable
          class="search-bar__input"
          @keyup.enter="handleSearch"
        />
        <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
        <el-button :icon="RefreshLeft" @click="handleReset">重置</el-button>
      </div>
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

const router = useRouter()
const reportStore = useReportStore()

const draftFilters = ref({
  keyword: '',
  report_type: '',
  environment: '',
})

const appliedFilters = ref({
  keyword: '',
  report_type: '',
  environment: '',
})

const pagination = ref({
  page: 1,
  pageSize: 15,
})

onMounted(() => {
  reportStore.fetchReports({ page: 1, page_size: pagination.value.pageSize })
})

function buildQueryParams() {
  return {
    page: pagination.value.page,
    page_size: pagination.value.pageSize,
    ...(appliedFilters.value.keyword && { keyword: appliedFilters.value.keyword }),
    ...(appliedFilters.value.report_type && { report_type: appliedFilters.value.report_type }),
    ...(appliedFilters.value.environment && { environment: appliedFilters.value.environment }),
  }
}

function handleSearch() {
  appliedFilters.value = { ...draftFilters.value }
  pagination.value.page = 1
  reportStore.fetchReports({ ...buildQueryParams(), page: 1 })
}

function handleReset() {
  draftFilters.value = { keyword: '', report_type: '', environment: '' }
  appliedFilters.value = { keyword: '', report_type: '', environment: '' }
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
    radial-gradient(circle at top right, rgba(56, 189, 248, 0.13), transparent 30%),
    var(--bg-page);
  overflow: hidden;
}

/* ── 标题区 ── */
.report-list-page__header {
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

html:not(.dark) .report-list-page__header {
  background: rgba(255, 255, 255, 0.86);
}

.report-list-page__header h1,
.report-list-page__header p {
  margin: 0;
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
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: rgba(20, 22, 27, 0.7);
  box-shadow: var(--box-shadow-light);
  backdrop-filter: blur(10px);
}

html:not(.dark) .report-list-page__filters {
  background: rgba(255, 255, 255, 0.86);
}

.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 12px;
  align-items: center;
}

.filter-control {
  width: 160px;
}

.search-bar {
  display: flex;
  gap: 12px;
  align-items: center;
}

.search-bar__input {
  width: 320px;
}

/* ── 表格区 ── */
.report-list-page__table {
  display: flex;
  flex: 1;
  min-height: 0;
  flex-direction: column;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: rgba(20, 22, 27, 0.7);
  box-shadow: var(--box-shadow-light);
  backdrop-filter: blur(10px);
  overflow: hidden;
}

html:not(.dark) .report-list-page__table {
  background: rgba(255, 255, 255, 0.86);
}

.report-list-page__table :deep(.el-table) {
  flex: 1;
}

.report-list-page__table :deep(.el-table__header th) {
  background: var(--bg-container-soft) !important;
  color: var(--text-secondary);
  font-weight: 700;
  font-size: 12px;
}

.report-list-page__table :deep(.el-table__row:hover > td) {
  background: rgba(56, 189, 248, 0.1) !important;
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
  border-top: 1px solid var(--border-color-lighter, #f0f0f0);
}
</style>
