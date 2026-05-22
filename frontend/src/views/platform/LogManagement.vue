<template>
  <div class="log-management">
    <!-- 页面标题区 -->
    <header class="log-management__header">
      <div>
        <h1>操作日志</h1>
        <p>完整记录用户操作行为，支持多维查询与追溯。</p>
      </div>
    </header>

    <!-- 查询区 -->
    <section class="log-management__filters">
      <el-form :model="draftFilters" inline label-position="left" class="filter-form">
        <el-form-item label="关键词" class="filter-item">
          <el-input
            v-model="draftFilters.keyword"
            placeholder="搜索用户名/操作/模块/详情"
            clearable
            class="search-bar__input"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="模块" class="filter-item">
          <el-select v-model="draftFilters.module" placeholder="全部模块" clearable class="filter-control">
            <el-option label="用户" value="user" />
            <el-option label="角色" value="role" />
            <el-option label="组织" value="organization" />
            <el-option label="菜单" value="menu" />
            <el-option label="字典" value="dictionary" />
            <el-option label="用例" value="case" />
            <el-option label="场景" value="scenario" />
            <el-option label="执行" value="execution" />
            <el-option label="报告" value="report" />
            <el-option label="缺陷" value="defect" />
            <el-option label="AI" value="ai" />
          </el-select>
        </el-form-item>
        <el-form-item label="操作" class="filter-item">
          <el-select v-model="draftFilters.action" placeholder="全部操作" clearable class="filter-control">
            <el-option label="创建" value="create" />
            <el-option label="更新" value="update" />
            <el-option label="删除" value="delete" />
            <el-option label="登录" value="login" />
            <el-option label="登出" value="logout" />
            <el-option label="执行" value="run" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期范围" class="filter-item">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            class="filter-range"
            @change="handleDateChange"
          />
        </el-form-item>
        <el-form-item class="filter-item filter-actions">
          <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
          <el-button :icon="RefreshLeft" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </section>

    <!-- 数据列表 -->
    <section class="log-management__table">
      <el-table v-loading="loading" :data="logList" border height="100%">
        <el-table-column prop="username" label="用户名" width="120" show-overflow-tooltip />
        <el-table-column prop="action" label="操作" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="actionType(row.action)" size="small">{{ row.action }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="module" label="模块" width="100" show-overflow-tooltip />
        <el-table-column prop="detail" label="详情" min-width="260" show-overflow-tooltip />
        <el-table-column prop="ip" label="IP地址" width="130" show-overflow-tooltip />
        <el-table-column prop="created_at" label="操作时间" width="170" align="center">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <template #empty>
          <span class="empty-text">暂无日志数据</span>
        </template>
      </el-table>

      <div class="log-management__pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="total"
          :page-sizes="[20, 50, 100]"
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
import { ref, reactive, onMounted } from 'vue'
import { Search, RefreshLeft } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { logApi } from '@/api/log'

const loading = ref(false)
const logList = ref([])
const total = ref(0)
const dateRange = ref(null)

const draftFilters = ref({ keyword: '', module: '', action: '' })
const appliedFilters = ref({ keyword: '', module: '', action: '', start_date: null, end_date: null })
const pagination = ref({ page: 1, pageSize: 20 })

onMounted(fetchLogs)

function buildQueryParams() {
  return {
    page: pagination.value.page,
    page_size: pagination.value.pageSize,
    ...(appliedFilters.value.keyword && { keyword: appliedFilters.value.keyword }),
    ...(appliedFilters.value.module && { module: appliedFilters.value.module }),
    ...(appliedFilters.value.action && { action: appliedFilters.value.action }),
    ...(appliedFilters.value.start_date && { start_date: appliedFilters.value.start_date }),
    ...(appliedFilters.value.end_date && { end_date: appliedFilters.value.end_date }),
  }
}

async function fetchLogs() {
  loading.value = true
  try {
    const res = await logApi.list(buildQueryParams())
    logList.value = res.data?.items || res.items || []
    total.value = res.data?.total || res.total || 0
  } catch {
    ElMessage.error('获取日志列表失败')
  } finally {
    loading.value = false
  }
}

function handleDateChange(val) {
  if (val && val.length === 2) {
    appliedFilters.value.start_date = val[0]
    appliedFilters.value.end_date = val[1]
  } else {
    appliedFilters.value.start_date = null
    appliedFilters.value.end_date = null
  }
  handleSearch()
}

function handleSearch() {
  appliedFilters.value = { ...draftFilters.value, start_date: appliedFilters.value.start_date, end_date: appliedFilters.value.end_date }
  pagination.value.page = 1
  fetchLogs()
}

function handleReset() {
  draftFilters.value = { keyword: '', module: '', action: '' }
  appliedFilters.value = { keyword: '', module: '', action: '', start_date: null, end_date: null }
  dateRange.value = null
  pagination.value.page = 1
  fetchLogs()
}

function handlePageChange(p) {
  pagination.value.page = p
  fetchLogs()
}

function handleSizeChange(s) {
  pagination.value.pageSize = s
  pagination.value.page = 1
  fetchLogs()
}

function actionType(action) {
  const map = { create: 'success', update: 'warning', delete: 'danger', login: 'info', logout: 'info', run: 'primary' }
  return map[action] || 'info'
}

function formatTime(timeStr) {
  if (!timeStr) return '—'
  const d = new Date(timeStr)
  if (isNaN(d.getTime())) return timeStr
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}
</script>

<style scoped>
/* ── 页面容器 ── */
.log-management {
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

.log-management::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 24%, rgba(56, 189, 248, 0.16) 44%, transparent 62%),
    repeating-linear-gradient(90deg, transparent 0 92px, rgba(56, 189, 248, 0.075) 92px 93px);
  content: "";
  animation: case-scan 14s linear infinite;
}

.log-management::after {
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
  animation: case-particles 18s ease-in-out infinite alternate;
}

/* ── 标题区 ── */
.log-management__header {
  position: relative;
  z-index: 1;
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
}

.log-management__header::after {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(90deg, rgba(56, 189, 248, 0.22), transparent 18% 82%, rgba(34, 211, 166, 0.18)),
    repeating-linear-gradient(90deg, transparent 0 42px, rgba(56, 189, 248, 0.06) 42px 43px);
  opacity: 0.65;
  content: "";
}

html:not(.dark) .log-management__header {
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.86), rgba(245, 250, 255, 0.68)),
    rgba(255, 255, 255, 0.72);
  box-shadow: 0 18px 46px rgba(20, 42, 76, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.82);
}

.log-management__header h1,
.log-management__header p {
  margin: 0;
}

.log-management__header h1 {
  position: relative;
  z-index: 1;
  color: var(--text-strong);
  font-size: 24px;
  line-height: 1.25;
}

.log-management__header p {
  position: relative;
  z-index: 1;
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 13px;
}

/* ── 筛选区 ── */
.log-management__filters {
  position: relative;
  z-index: 1;
  padding: 14px;
  border: 1px solid rgba(56, 189, 248, 0.18);
  border-radius: var(--border-radius-base);
  background:
    linear-gradient(135deg, rgba(15, 23, 42, 0.54), rgba(15, 23, 42, 0.34)),
    rgba(20, 22, 27, 0.48);
  box-shadow: 0 14px 36px rgba(2, 8, 23, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(16px) saturate(1.2);
  overflow: hidden;
}

.log-management__filters::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(56, 189, 248, 0.1) 50%, transparent 66%),
    radial-gradient(circle at 88% 16%, rgba(34, 211, 166, 0.12), transparent 26%);
  opacity: 0.8;
  content: "";
  animation: case-form-scan 12s linear infinite;
}

html:not(.dark) .log-management__filters {
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.76), rgba(245, 250, 255, 0.58)),
    rgba(255, 255, 255, 0.72);
  box-shadow: 0 14px 34px rgba(20, 42, 76, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.86);
}

html:not(.dark) .log-management__filters::before {
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(22, 119, 255, 0.08) 50%, transparent 66%),
    radial-gradient(circle at 88% 16%, rgba(22, 119, 255, 0.1), transparent 26%);
}

.filter-row {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 16px;
  align-items: center;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.filter-form :deep(.el-form-item__label) {
  color: var(--text-secondary);
  font-size: 13px;
}

.filter-item {
  display: inline-flex;
  align-items: center;
}

.filter-actions {
  display: flex;
  gap: 12px;
  margin-left: auto;
}

.search-bar__input {
  width: 240px;
}

.filter-control {
  width: 140px;
}

.filter-range {
  width: 240px;
}

/* ── 表格区 ── */
.log-management__table {
  position: relative;
  z-index: 1;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  border: 1px solid rgba(56, 189, 248, 0.18);
  border-radius: var(--border-radius-base);
  background:
    linear-gradient(rgba(56, 189, 248, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.045) 1px, transparent 1px),
    rgba(20, 22, 27, 0.48);
  background-size: 32px 32px;
  box-shadow: 0 14px 36px rgba(2, 8, 23, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(16px) saturate(1.2);
  overflow: hidden;
}

.log-management__table::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(56, 189, 248, 0.1) 50%, transparent 66%),
    radial-gradient(circle at 88% 16%, rgba(34, 211, 166, 0.12), transparent 26%);
  opacity: 0.8;
  content: "";
  animation: case-form-scan 12s linear infinite;
}

html:not(.dark) .log-management__table {
  background:
    linear-gradient(rgba(22, 119, 255, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.035) 1px, transparent 1px),
    rgba(255, 255, 255, 0.64);
  background-size: 32px 32px;
  box-shadow: 0 14px 34px rgba(20, 42, 76, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.86);
}

html:not(.dark) .log-management__table::before {
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(22, 119, 255, 0.08) 50%, transparent 66%),
    radial-gradient(circle at 88% 16%, rgba(22, 119, 255, 0.1), transparent 26%);
}

.log-management__table :deep(.el-table) {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: rgba(8, 18, 32, 0.34);
  --el-table-header-bg-color: rgba(15, 31, 52, 0.46);
  --el-table-expanded-cell-bg-color: rgba(8, 18, 32, 0.42);
  flex: 1;
  background:
    linear-gradient(rgba(56, 189, 248, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.03) 1px, transparent 1px),
    rgba(8, 18, 32, 0.32);
  background-size: 28px 28px, 28px 28px, auto;
}

html:not(.dark) .log-management__table :deep(.el-table) {
  --el-table-tr-bg-color: rgba(255, 255, 255, 0.54);
  --el-table-header-bg-color: rgba(240, 247, 255, 0.68);
  --el-table-expanded-cell-bg-color: rgba(255, 255, 255, 0.64);
  background:
    linear-gradient(rgba(22, 119, 255, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.03) 1px, transparent 1px),
    rgba(255, 255, 255, 0.44);
  background-size: 28px 28px, 28px 28px, auto;
}

.log-management__table :deep(.el-table__header th) {
  background: var(--bg-container-soft) !important;
  color: var(--text-secondary);
  font-weight: 700;
  font-size: 12px;
}

.log-management__table :deep(.el-table__row:hover > td) {
  background: rgba(56, 189, 248, 0.1) !important;
}

html:not(.dark) .log-management__table :deep(.el-table__row:hover > td) {
  background: rgba(22, 119, 255, 0.08) !important;
}

.log-management__table :deep(.el-table__cell) {
  vertical-align: middle;
}

/* ── 分页 ── */
.log-management__pagination {
  display: flex;
  justify-content: flex-end;
  padding: 10px 16px;
  border-top: 1px solid rgba(56, 189, 248, 0.1);
}

html:not(.dark) .log-management__pagination {
  border-top-color: rgba(22, 119, 255, 0.1);
}

/* ── 通用 ── */
.empty-text {
  color: var(--text-secondary);
  font-size: 13px;
}

@keyframes case-scan {
  from { transform: translateX(-24%); }
  to { transform: translateX(24%); }
}

@keyframes case-particles {
  from { transform: translate3d(0, 0, 0); }
  to { transform: translate3d(26px, -18px, 0); }
}

@keyframes case-form-scan {
  from { transform: translateX(-20%); }
  to { transform: translateX(20%); }
}

@media (prefers-reduced-motion: reduce) {
  .log-management::before,
  .log-management::after,
  .log-management__filters::before,
  .log-management__table::before {
    animation: none;
  }
}
</style>
