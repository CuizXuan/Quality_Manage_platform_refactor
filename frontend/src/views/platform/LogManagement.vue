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
      <div class="filter-row">
        <el-input
          v-model="draftFilters.keyword"
          placeholder="搜索用户名/操作/模块/详情"
          clearable
          class="search-bar__input"
          @keyup.enter="handleSearch"
        />
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
        <el-select v-model="draftFilters.action" placeholder="全部操作" clearable class="filter-control">
          <el-option label="创建" value="create" />
          <el-option label="更新" value="update" />
          <el-option label="删除" value="delete" />
          <el-option label="登录" value="login" />
          <el-option label="登出" value="logout" />
          <el-option label="执行" value="run" />
        </el-select>
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
        <div class="filter-actions">
          <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
          <el-button :icon="RefreshLeft" @click="handleReset">重置</el-button>
        </div>
      </div>
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
.log-management__header {
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

html:not(.dark) .log-management__header {
  background: rgba(255, 255, 255, 0.86);
}

.log-management__header h1,
.log-management__header p {
  margin: 0;
}

.log-management__header h1 {
  color: var(--text-strong);
  font-size: 24px;
  line-height: 1.25;
}

.log-management__header p {
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 13px;
}

/* ── 筛选区 ── */
.log-management__filters {
  padding: 14px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: rgba(20, 22, 27, 0.7);
  box-shadow: var(--box-shadow-light);
  backdrop-filter: blur(10px);
}

html:not(.dark) .log-management__filters {
  background: rgba(255, 255, 255, 0.86);
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
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

.filter-actions {
  display: flex;
  gap: 12px;
}

/* ── 表格区 ── */
.log-management__table {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: rgba(20, 22, 27, 0.7);
  box-shadow: var(--box-shadow-light);
  backdrop-filter: blur(10px);
  overflow: hidden;
}

html:not(.dark) .log-management__table {
  background: rgba(255, 255, 255, 0.86);
}

.log-management__table :deep(.el-table) {
  flex: 1;
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

.log-management__table :deep(.el-table__cell) {
  vertical-align: middle;
}

/* ── 分页 ── */
.log-management__pagination {
  display: flex;
  justify-content: flex-end;
  padding: 10px 16px;
  border-top: 1px solid var(--border-color-lighter, #f0f0f0);
}

/* ── 通用 ── */
.empty-text {
  color: var(--text-secondary);
  font-size: 13px;
}
</style>
