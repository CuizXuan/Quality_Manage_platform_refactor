<template>
  <div class="execution-history-page">
    <!-- 页面标题区 -->
    <header class="execution-history-page__header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" text @click="handleBack">返回</el-button>
        <el-divider direction="vertical" />
        <h1>执行历史</h1>
      </div>
      <el-button :icon="RefreshRight" @click="handleRefresh">刷新</el-button>
    </header>

    <!-- 查询区 -->
    <section class="execution-history-page__filters">
      <div class="filter-bar">
        <el-select
          v-model="draftFilters.scenario_id"
          placeholder="全部场景"
          clearable
          filterable
          class="filter-control"
        >
          <el-option
            v-for="s in scenarioStore.scenarios"
            :key="s.id"
            :label="s.name"
            :value="s.id"
          />
        </el-select>
        <el-select
          v-model="draftFilters.status"
          placeholder="全部状态"
          clearable
          class="filter-control"
        >
          <el-option label="等待中" value="pending" />
          <el-option label="运行中" value="running" />
          <el-option label="成功" value="success" />
          <el-option label="失败" value="failed" />
        </el-select>
      </div>
      <div class="search-bar">
        <el-date-picker
          v-model="draftFilters.date_range"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          class="search-bar__date-range"
        />
        <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
        <el-button :icon="RefreshLeft" @click="handleReset">重置</el-button>
      </div>
    </section>

    <!-- 数据列表 -->
    <section class="execution-history-page__table">
      <el-table
        v-loading="scenarioStore.loading"
        :data="scenarioStore.executions"
        height="100%"
        highlight-current-row
        @row-click="handleRowClick"
      >
        <el-table-column prop="id" label="Run ID" width="80" />
        <el-table-column prop="scenario_name" label="场景名称" min-width="180">
          <template #default="{ row }">
            <span class="text-ellipsis" :title="row.scenario_name">{{ row.scenario_name || `场景#${row.target_id}` }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_steps" label="总步骤" width="90" align="center" />
        <el-table-column prop="passed_steps" label="成功" width="80" align="center">
          <template #default="{ row }">
            <span class="text-success">{{ row.passed_steps ?? 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="failed_steps" label="失败" width="80" align="center">
          <template #default="{ row }">
            <span class="text-danger">{{ row.failed_steps ?? 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="耗时" width="100" align="center">
          <template #default="{ row }">
            {{ row.duration != null ? `${row.duration}s` : '—' }}
          </template>
        </el-table-column>
        <el-table-column prop="started_at" label="开始时间" width="170" align="center" />
        <el-table-column label="操作" width="100" fixed="right" align="center">
          <template #default="{ row }">
            <el-button type="primary" text size="small" @click.stop="handleViewDetail(row)">详情</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <span class="empty-text">暂无执行记录</span>
        </template>
      </el-table>

      <div class="execution-history-page__pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="scenarioStore.executionTotal"
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
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Search, RefreshLeft, RefreshRight } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useScenarioStore } from '@/stores/scenarioStore'

const route = useRoute()
const router = useRouter()
const scenarioStore = useScenarioStore()

const draftFilters = ref({
  scenario_id: route.query.scenario_id ? Number(route.query.scenario_id) : null,
  status: '',
  date_range: null,
})

const appliedFilters = ref({
  scenario_id: route.query.scenario_id ? Number(route.query.scenario_id) : null,
  status: '',
  date_range: null,
})

const pagination = ref({
  page: 1,
  pageSize: 15,
})

onMounted(async () => {
  try {
    await scenarioStore.fetchScenarios({ page: 1, page_size: 1000 })
  } catch { /* ignore */ }
  scenarioStore.fetchExecutions(buildQueryParams())
})

function buildQueryParams() {
  return {
    page: pagination.value.page,
    page_size: pagination.value.pageSize,
    ...(appliedFilters.value.scenario_id && { scenario_id: appliedFilters.value.scenario_id }),
    ...(appliedFilters.value.status && { status: appliedFilters.value.status }),
    ...(appliedFilters.value.date_range && appliedFilters.value.date_range.length === 2 && {
      start_date: appliedFilters.value.date_range[0],
      end_date: appliedFilters.value.date_range[1],
    }),
  }
}

function handleSearch() {
  appliedFilters.value = {
    scenario_id: draftFilters.value.scenario_id,
    status: draftFilters.value.status,
    date_range: draftFilters.value.date_range
      ? [...draftFilters.value.date_range]
      : null,
  }
  pagination.value.page = 1
  scenarioStore.fetchExecutions({ ...buildQueryParams(), page: 1 })
}

function handleReset() {
  draftFilters.value = { scenario_id: null, status: '', date_range: null }
  appliedFilters.value = { scenario_id: null, status: '', date_range: null }
  pagination.value.page = 1
  scenarioStore.fetchExecutions({ page: 1, page_size: pagination.value.pageSize })
}

function handlePageChange(page) {
  pagination.value.page = page
  scenarioStore.fetchExecutions({ ...buildQueryParams(), page })
}

function handleSizeChange(size) {
  pagination.value.pageSize = size
  pagination.value.page = 1
  scenarioStore.fetchExecutions({ ...buildQueryParams(), page: 1, page_size: size })
}

function handleRowClick(row) {
  router.push({ name: 'ExecutionDetail', params: { id: row.id } })
}

function handleViewDetail(row) {
  router.push({ name: 'ExecutionDetail', params: { id: row.id } })
}

function handleBack() {
  router.back()
}

function handleRefresh() {
  scenarioStore.fetchExecutions(buildQueryParams())
  ElMessage.success('已刷新')
}

function getStatusType(status) {
  const map = { pending: 'info', running: 'primary', success: 'success', failed: 'danger' }
  return map[status] || 'info'
}

function getStatusLabel(status) {
  const map = { pending: '等待中', running: '运行中', success: '成功', failed: '失败' }
  return map[status] || status
}
</script>

<style scoped>
/* ── 页面容器 ── */
.execution-history-page {
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
.execution-history-page__header {
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
}

html:not(.dark) .execution-history-page__header {
  background: rgba(255, 255, 255, 0.86);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-left h1 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

/* ── 查询区 ── */
.execution-history-page__filters {
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

html:not(.dark) .execution-history-page__filters {
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
  flex-wrap: wrap;
  gap: 10px 12px;
  align-items: center;
}

.search-bar__date-range {
  width: 320px;
}

/* Date range control */
.execution-history-page__filters :deep(.search-bar__date-range.el-date-editor) {
  flex: 0 0 320px;
  width: 320px !important;
  max-width: 320px;
  min-width: 0;
}

.execution-history-page__filters :deep(.search-bar__date-range .el-range-input) {
  width: 96px;
  flex: 0 0 96px;
}

.execution-history-page__filters :deep(.search-bar__date-range .el-range-separator) {
  flex: 0 0 24px;
  padding: 0;
}

/* ── 表格区 ── */
.execution-history-page__table {
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

html:not(.dark) .execution-history-page__table {
  background: rgba(255, 255, 255, 0.86);
}

.execution-history-page__table :deep(.el-table) {
  flex: 1;
}

.execution-history-page__table :deep(.el-table__header th) {
  background: var(--bg-container-soft) !important;
  color: var(--text-secondary);
  font-weight: 700;
  font-size: 12px;
}

.execution-history-page__table :deep(.el-table__row:hover > td) {
  background: rgba(56, 189, 248, 0.1) !important;
}

.execution-history-page__table :deep(.el-table__cell) {
  vertical-align: middle;
}

.text-ellipsis {
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.text-success {
  color: var(--color-success);
  font-weight: 600;
}

.text-danger {
  color: var(--color-danger);
  font-weight: 600;
}

.empty-text {
  color: var(--text-secondary);
  font-size: 13px;
}

/* ── 分页 ── */
.execution-history-page__pagination {
  display: flex;
  justify-content: flex-end;
  padding: 10px 16px;
  border-top: 1px solid var(--border-color-lighter, #f0f0f0);
}
</style>
