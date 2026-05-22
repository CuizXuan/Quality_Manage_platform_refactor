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
      <el-form :model="draftFilters" label-position="left" class="filter-form">
        <div class="filter-form__row">
          <el-form-item label="场景：" class="filter-item filter-item--scenario">
            <el-select
              v-model="draftFilters.scenario_id"
              placeholder="全部场景"
              clearable
              filterable
              class="filter-control filter-control--scenario"
            >
              <el-option
                v-for="s in scenarioStore.scenarios"
                :key="s.id"
                :label="s.name"
                :value="s.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="状态：" class="filter-item filter-item--status">
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
          </el-form-item>
          <el-form-item label="日期：" class="filter-item filter-item--date">
            <el-date-picker
              v-model="draftFilters.date_range"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
              class="filter-bar__date-range"
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
  position: relative;
  display: flex;
  width: 100%;
  height: 100%;
  min-height: 0;
  min-width: 0;
  flex-direction: column;
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
}

.execution-history-page::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 24%, rgba(56, 189, 248, 0.16) 44%, transparent 62%),
    repeating-linear-gradient(90deg, transparent 0 92px, rgba(56, 189, 248, 0.075) 92px 93px);
  content: "";
  animation: execution-history-scan 14s linear infinite;
}

.execution-history-page::after {
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
  animation: execution-history-particles 18s ease-in-out infinite alternate;
}

@keyframes execution-history-scan {
  from { transform: translateX(-24%); }
  to { transform: translateX(24%); }
}

@keyframes execution-history-particles {
  from { transform: translate3d(0, 0, 0); }
  to { transform: translate3d(26px, -18px, 0); }
}

@keyframes execution-history-form-scan {
  from { transform: translateY(-8%); }
  to { transform: translateY(108%); }
}

@keyframes execution-history-table-scan {
  from { transform: translateY(-6%); }
  to { transform: translateY(106%); }
}

@media (prefers-reduced-motion: reduce) {
  .execution-history-page::before,
  .execution-history-page::after {
    animation: none;
  }
}

/* ── 标题区 ── */
.execution-history-page__header {
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

.execution-history-page__header::after {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(90deg, rgba(56, 189, 248, 0.22), transparent 18% 82%, rgba(34, 211, 166, 0.18)),
    repeating-linear-gradient(90deg, transparent 0 42px, rgba(56, 189, 248, 0.06) 42px 43px);
  opacity: 0.65;
  content: "";
}

html:not(.dark) .execution-history-page__header {
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.86), rgba(245, 250, 255, 0.68)),
    rgba(255, 255, 255, 0.72);
  box-shadow: 0 18px 46px rgba(20, 42, 76, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.82);
  border-color: rgba(22, 119, 255, 0.18);
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

.execution-history-page__filters::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(56, 189, 248, 0.1) 50%, transparent 66%);
  opacity: 0.7;
  content: "";
  animation: execution-history-form-scan 12s linear infinite;
}

html:not(.dark) .execution-history-page__filters {
  background:
    linear-gradient(rgba(22, 119, 255, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.04) 1px, transparent 1px),
    linear-gradient(145deg, rgba(255, 255, 255, 0.76), rgba(245, 250, 255, 0.58)),
    rgba(255, 255, 255, 0.62);
  background-size: 26px 26px, 26px 26px, auto, auto;
  border-color: rgba(22, 119, 255, 0.14);
}

html:not(.dark) .execution-history-page__filters::before {
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

.filter-control--scenario {
  width: 260px;
}

.filter-bar__date-range {
  width: 320px;
}

/* Date range control */
.execution-history-page__filters :deep(.filter-bar__date-range.el-date-editor) {
  flex: 0 0 320px;
  width: 320px !important;
  max-width: 320px;
  min-width: 0;
}

.execution-history-page__filters :deep(.filter-bar__date-range .el-range-input) {
  width: 96px;
  flex: 0 0 96px;
}

.execution-history-page__filters :deep(.filter-bar__date-range .el-range-separator) {
  flex: 0 0 24px;
  padding: 0;
}

/* ── 表格区 ── */
.execution-history-page__table {
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

.execution-history-page__table::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(56, 189, 248, 0.12) 50%, transparent 66%),
    radial-gradient(circle at 88% 16%, rgba(34, 211, 166, 0.14), transparent 26%);
  opacity: 0.8;
  content: "";
  animation: execution-history-table-scan 12s linear infinite;
}

html:not(.dark) .execution-history-page__table {
  background:
    linear-gradient(rgba(22, 119, 255, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.04) 1px, transparent 1px),
    linear-gradient(145deg, rgba(255, 255, 255, 0.76), rgba(245, 250, 255, 0.58)),
    rgba(255, 255, 255, 0.62);
  background-size: 32px 32px, 32px 32px, auto, auto;
  border-color: rgba(22, 119, 255, 0.14);
}

html:not(.dark) .execution-history-page__table::before {
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(22, 119, 255, 0.1) 50%, transparent 66%);
}

.execution-history-page__table :deep(.el-table) {
  flex: 1;
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: rgba(8, 18, 32, 0.34);
  --el-table-header-bg-color: rgba(15, 31, 52, 0.46);
  --el-table-expanded-cell-bg-color: rgba(8, 18, 32, 0.42);
  --el-table-row-hover-bg-color: var(--color-primary-soft);
  position: relative;
  z-index: 1;
  background:
    linear-gradient(rgba(56, 189, 248, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.03) 1px, transparent 1px),
    rgba(8, 18, 32, 0.32);
  background-size: 28px 28px, 28px 28px, auto;
}

html:not(.dark) .execution-history-page__table :deep(.el-table) {
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

.execution-history-page__table :deep(.el-table__inner-wrapper::before) {
  background: rgba(56, 189, 248, 0.12);
}

.execution-history-page__table :deep(.el-table__body-wrapper),
.execution-history-page__table :deep(.el-table__header-wrapper),
.execution-history-page__table :deep(.el-scrollbar__view) {
  background: transparent;
}

.execution-history-page__table :deep(.el-table__header th) {
  height: 44px;
  color: var(--text-secondary);
  background: var(--el-table-header-bg-color) !important;
  background-color: var(--el-table-header-bg-color) !important;
  font-weight: 700;
  font-size: 13px;
}

.execution-history-page__table :deep(.el-table__body td) {
  height: 48px;
  background: var(--el-table-tr-bg-color) !important;
  background-color: var(--el-table-tr-bg-color) !important;
}

.execution-history-page__table :deep(.el-table__body tr:nth-child(even) td.el-table__cell) {
  background: rgba(15, 31, 52, 0.28) !important;
  background-color: rgba(15, 31, 52, 0.28) !important;
}

html:not(.dark) .execution-history-page__table :deep(.el-table__body tr:nth-child(even) td.el-table__cell) {
  background: rgba(245, 250, 255, 0.5) !important;
  background-color: rgba(245, 250, 255, 0.5) !important;
}

.execution-history-page__table :deep(.el-table__row:hover > td) {
  background: var(--el-table-row-hover-bg-color) !important;
  background-color: var(--el-table-row-hover-bg-color) !important;
}

.execution-history-page__table :deep(.el-table__row:hover > td.el-table-fixed-column--right),
.execution-history-page__table :deep(.el-table__row:hover > td.el-table-fixed-column--left) {
  background: var(--el-table-row-hover-bg-color) !important;
  background-color: var(--el-table-row-hover-bg-color) !important;
}

.execution-history-page__table :deep(.el-table .cell) {
  padding: 0 10px;
}

.execution-history-page__table :deep(.el-table__cell) {
  vertical-align: middle;
}

@media (prefers-reduced-motion: reduce) {
  .execution-history-page__table::before {
    animation: none;
  }
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
  border-top: 1px solid rgba(56, 189, 248, 0.12);
}

html:not(.dark) .execution-history-page__pagination {
  border-top-color: rgba(22, 119, 255, 0.12);
}
</style>
