<template>
  <div class="defect-list-page">
    <!-- 页面标题区 -->
    <header class="defect-list-page__header">
      <div>
        <h1>缺陷管理</h1>
        <p>统一管理测试缺陷全生命周期，支持状态流转追踪。</p>
      </div>
      <el-button type="primary" :icon="Plus" class="btn-primary-add" @click="handleCreate">新建缺陷</el-button>
    </header>

    <!-- 统计卡片行 -->
    <div class="defect-list-page__stats" v-if="reportStore.defectStats">
      <div class="stat-card">
        <div class="stat-value">{{ reportStore.defectStats.total }}</div>
        <div class="stat-label">全部</div>
      </div>
      <div class="stat-card" v-for="(count, status) in reportStore.defectStats.by_status" :key="status">
        <div class="stat-value" :style="{ color: getStatusColor(status) }">{{ count }}</div>
        <div class="stat-label">{{ getStatusLabel(status) }}</div>
      </div>
    </div>

    <!-- 查询区 -->
    <section class="defect-list-page__filters">
      <el-form :model="draftFilters" inline label-position="left" class="filter-form">
        <el-form-item label="严重程度" class="filter-item">
          <el-select
            v-model="draftFilters.severity"
            placeholder="严重程度"
            clearable
            class="filter-control"
          >
            <el-option label="Critical" value="critical" />
            <el-option label="High" value="high" />
            <el-option label="Medium" value="medium" />
            <el-option label="Low" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级" class="filter-item">
          <el-select
            v-model="draftFilters.priority"
            placeholder="优先级"
            clearable
            class="filter-control"
          >
            <el-option label="P0" value="P0" />
            <el-option label="P1" value="P1" />
            <el-option label="P2" value="P2" />
            <el-option label="P3" value="P3" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" class="filter-item">
          <el-select
            v-model="draftFilters.status"
            placeholder="全部状态"
            clearable
            class="filter-control"
          >
            <el-option label="打开" value="open" />
            <el-option label="已确认" value="confirmed" />
            <el-option label="已修复" value="fixed" />
            <el-option label="已验证" value="verified" />
            <el-option label="已关闭" value="closed" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词" class="filter-item">
          <el-input
            v-model="draftFilters.keyword"
            placeholder="搜索标题"
            clearable
            class="search-bar__input"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item class="filter-item filter-actions">
          <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
          <el-button :icon="RefreshLeft" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </section>

    <!-- 数据列表 -->
    <section class="defect-list-page__table">
      <el-table
        v-loading="reportStore.loading"
        :data="reportStore.defects"
        height="100%"
        highlight-current-row
      >
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="title" label="缺陷标题" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="defect-title" :title="row.title" @click="handleEdit(row)">{{ row.title }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="severity" label="严重程度" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="getSeverityType(row.severity)" size="small">{{ row.severity }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="80" align="center">
          <template #default="{ row }">
            <span class="priority-cell" :class="`priority-${row.priority}`">{{ row.priority }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="defect_type" label="类型" width="100" align="center">
          <template #default="{ row }">
            <span class="text-secondary">{{ formatDefectType(row.defect_type) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="opened_at" label="创建时间" width="170" align="center" />
        <el-table-column label="操作" width="200" fixed="right" align="center">
          <template #default="{ row }">
            <div class="actions-cell">
              <el-button
                v-for="action in getAvailableActions(row.status)"
                :key="action.status"
                type="primary"
                text
                size="small"
                @click.stop="handleTransition(row, action.status, action.label)"
              >{{ action.label }}</el-button>
              <el-button type="primary" text size="small" @click.stop="handleEdit(row)">编辑</el-button>
              <el-button type="danger" text size="small" @click.stop="handleDelete(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
        <template #empty>
          <span class="empty-text">暂无符合条件的缺陷</span>
        </template>
      </el-table>

      <div class="defect-list-page__pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="reportStore.defectTotal"
          :page-sizes="[15, 30, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          prev-text="上一页"
          next-text="下一页"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </section>

    <!-- 缺陷表单抽屉 -->
    <DefectForm
      v-model="formVisible"
      :defect="currentDefect"
      @saved="handleSaved"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Plus, Search, RefreshLeft } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useReportStore } from '@/stores/reportStore'
import DefectForm from './DefectForm.vue'

const reportStore = useReportStore()

const draftFilters = ref({
  keyword: '',
  status: '',
  severity: '',
  priority: '',
})

const appliedFilters = ref({
  keyword: '',
  status: '',
  severity: '',
  priority: '',
})

const pagination = ref({
  page: 1,
  pageSize: 15,
})

const formVisible = ref(false)
const currentDefect = ref(null)

onMounted(() => {
  reportStore.fetchDefects({ page: 1, page_size: pagination.value.pageSize })
  reportStore.fetchDefectStats()
})

function buildQueryParams() {
  return {
    page: pagination.value.page,
    page_size: pagination.value.pageSize,
    ...(appliedFilters.value.keyword && { keyword: appliedFilters.value.keyword }),
    ...(appliedFilters.value.status && { status: appliedFilters.value.status }),
    ...(appliedFilters.value.severity && { severity: appliedFilters.value.severity }),
    ...(appliedFilters.value.priority && { priority: appliedFilters.value.priority }),
  }
}

function handleSearch() {
  appliedFilters.value = { ...draftFilters.value }
  pagination.value.page = 1
  reportStore.fetchDefects({ ...buildQueryParams(), page: 1 })
}

function handleReset() {
  draftFilters.value = { keyword: '', status: '', severity: '', priority: '' }
  appliedFilters.value = { keyword: '', status: '', severity: '', priority: '' }
  pagination.value.page = 1
  reportStore.fetchDefects({ page: 1, page_size: pagination.value.pageSize })
}

function handlePageChange(page) {
  pagination.value.page = page
  reportStore.fetchDefects({ ...buildQueryParams(), page })
}

function handleSizeChange(size) {
  pagination.value.pageSize = size
  pagination.value.page = 1
  reportStore.fetchDefects({ ...buildQueryParams(), page: 1, page_size: size })
}

function handleCreate() {
  currentDefect.value = null
  formVisible.value = true
}

function handleEdit(row) {
  currentDefect.value = { ...row }
  formVisible.value = true
}

function handleSaved() {
  formVisible.value = false
  currentDefect.value = null
  reportStore.fetchDefects(buildQueryParams())
  reportStore.fetchDefectStats()
}

async function handleTransition(row, targetStatus, label) {
  try {
    await ElMessageBox.confirm(`确定要将缺陷「${row.title}」状态变更为「${label}」吗？`, '状态流转', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info',
    })
    await reportStore.transitionDefect(row.id, targetStatus)
    ElMessage.success('状态变更成功')
    reportStore.fetchDefects(buildQueryParams())
    reportStore.fetchDefectStats()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error(err.message || '状态流转失败')
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定要删除缺陷「${row.title}」吗？`, '删除确认', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await reportStore.deleteDefect(row.id)
    ElMessage.success('删除成功')
    reportStore.fetchDefects(buildQueryParams())
    reportStore.fetchDefectStats()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('删除失败')
  }
}

function getAvailableActions(status) {
  const transitions = {
    open: [{ status: 'confirmed', label: '确认' }],
    confirmed: [{ status: 'fixed', label: '修复' }, { status: 'open', label: '退回' }],
    fixed: [{ status: 'verified', label: '验证' }],
    verified: [{ status: 'closed', label: '关闭' }],
    closed: [{ status: 'open', label: '重新打开' }],
  }
  return transitions[status] || []
}

function getStatusLabel(status) {
  const map = { open: '打开', confirmed: '已确认', fixed: '已修复', verified: '已验证', closed: '已关闭' }
  return map[status] || status
}

function getStatusType(status) {
  const map = { open: 'danger', confirmed: 'warning', fixed: 'primary', verified: 'success', closed: 'info' }
  return map[status] || 'info'
}

function getStatusColor(status) {
  const map = {
    open: 'var(--color-danger)',
    confirmed: 'var(--color-warning)',
    fixed: 'var(--color-primary)',
    verified: 'var(--color-success)',
    closed: 'var(--text-secondary)',
  }
  return map[status] || 'var(--text-secondary)'
}

function getSeverityType(severity) {
  const map = { critical: 'danger', high: 'warning', medium: '', low: 'info' }
  return map[severity] || 'info'
}

function formatDefectType(type) {
  const map = { functional: '功能', api: '接口', performance: '性能', security: '安全' }
  return map[type] || type || '—'
}
</script>

<style scoped>
/* ── 动画关键帧 ── */
@keyframes case-scan {
  from { transform: translateX(-24%); }
  to { transform: translateX(24%); }
}

@keyframes case-particles {
  from { transform: translate3d(0, 0, 0); }
  to { transform: translate3d(26px, -18px, 0); }
}

@keyframes case-form-scan {
  from { transform: translateY(-8%); }
  to { transform: translateY(108%); }
}

@keyframes case-table-scan {
  from { transform: translateY(-6%); }
  to { transform: translateY(106%); }
}

/* ── 页面容器 ── */
.defect-list-page {
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

.defect-list-page::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 24%, rgba(56, 189, 248, 0.16) 44%, transparent 62%),
    repeating-linear-gradient(90deg, transparent 0 92px, rgba(56, 189, 248, 0.075) 92px 93px);
  content: "";
  animation: case-scan 14s linear infinite;
}

.defect-list-page::after {
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

html:not(.dark) .defect-list-page {
  background:
    linear-gradient(rgba(22, 119, 255, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.04) 1px, transparent 1px),
    linear-gradient(145deg, rgba(14, 116, 144, 0.12), transparent 30%),
    linear-gradient(225deg, rgba(22, 119, 255, 0.16), transparent 36%),
    linear-gradient(0deg, rgba(56, 189, 248, 0.08), transparent 50%),
    var(--bg-page);
}

/* ── 标题区 ── */
.defect-list-page__header {
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

.defect-list-page__header::after {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(90deg, rgba(56, 189, 248, 0.22), transparent 18% 82%, rgba(34, 211, 166, 0.18)),
    repeating-linear-gradient(90deg, transparent 0 42px, rgba(56, 189, 248, 0.06) 42px 43px);
  opacity: 0.65;
  content: "";
}

html:not(.dark) .defect-list-page__header {
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.86), rgba(245, 250, 255, 0.68)),
    rgba(255, 255, 255, 0.72);
  box-shadow: 0 18px 46px rgba(20, 42, 76, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.82);
  border-color: rgba(22, 119, 255, 0.18);
}

.defect-list-page__header h1,
.defect-list-page__header p {
  margin: 0;
  position: relative;
  z-index: 1;
}

.defect-list-page__header h1 {
  color: var(--text-strong);
  font-size: 24px;
  line-height: 1.25;
}

.defect-list-page__header p {
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 13px;
}

.btn-primary-add {
  position: relative;
  z-index: 1;
  border: 0;
  background: var(--brand-gradient);
  font-weight: 700;
  transition: filter 0.2s ease, transform 0.2s ease;
}

.btn-primary-add:hover {
  filter: brightness(1.1);
  transform: translateY(-1px);
}

/* ── 统计卡片行 ── */
.defect-list-page__stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 10px;
  position: relative;
  z-index: 1;
}

.stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 14px 8px;
  border: 1px solid rgba(56, 189, 248, 0.18);
  border-radius: var(--border-radius-base);
  background:
    linear-gradient(rgba(56, 189, 248, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.045) 1px, transparent 1px),
    rgba(20, 22, 27, 0.58);
  background-size: 28px 28px, 28px 28px;
  box-shadow: 0 18px 48px rgba(2, 8, 23, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(16px) saturate(1.2);
  gap: 4px;
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(56, 189, 248, 0.08) 50%, transparent 66%);
  opacity: 0.7;
  content: "";
  animation: case-form-scan 14s linear infinite;
}

html:not(.dark) .stat-card {
  background:
    linear-gradient(rgba(22, 119, 255, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.035) 1px, transparent 1px),
    rgba(255, 255, 255, 0.72);
  background-size: 28px 28px, 28px 28px;
  border-color: rgba(22, 119, 255, 0.14);
}

html:not(.dark) .stat-card::before {
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(22, 119, 255, 0.06) 50%, transparent 66%);
}

.stat-value {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
  position: relative;
  z-index: 1;
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
  position: relative;
  z-index: 1;
}

/* ── 查询区 ── */
.defect-list-page__filters {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px;
  border: 1px solid rgba(56, 189, 248, 0.18);
  border-radius: var(--border-radius-base);
  background:
    linear-gradient(rgba(56, 189, 248, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.045) 1px, transparent 1px),
    rgba(20, 22, 27, 0.58);
  background-size: 28px 28px, 28px 28px;
  box-shadow: 0 18px 48px rgba(2, 8, 23, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(16px) saturate(1.2);
  overflow: hidden;
  z-index: 1;
}

.defect-list-page__filters::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(56, 189, 248, 0.1) 50%, transparent 66%);
  opacity: 0.7;
  content: "";
  animation: case-form-scan 12s linear infinite;
}

html:not(.dark) .defect-list-page__filters {
  background:
    linear-gradient(rgba(22, 119, 255, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.035) 1px, transparent 1px),
    rgba(255, 255, 255, 0.72);
  background-size: 28px 28px, 28px 28px;
  border-color: rgba(22, 119, 255, 0.14);
}

html:not(.dark) .defect-list-page__filters::before {
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(22, 119, 255, 0.08) 50%, transparent 66%);
}

.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 12px;
  align-items: center;
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
  margin-left: auto;
}

.filter-control {
  width: 140px;
}

.search-bar {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: flex-end;
}

.search-bar__input {
  width: 320px;
}

/* ── 表格区 ── */
.defect-list-page__table {
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
    rgba(20, 22, 27, 0.48);
  background-size: 32px 32px, 32px 32px;
  box-shadow: 0 18px 48px rgba(2, 8, 23, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(16px) saturate(1.2);
  overflow: hidden;
  z-index: 1;
}

.defect-list-page__table::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(56, 189, 248, 0.12) 50%, transparent 66%),
    radial-gradient(circle at 88% 16%, rgba(34, 211, 166, 0.14), transparent 26%);
  opacity: 0.8;
  content: "";
  animation: case-table-scan 12s linear infinite;
}

html:not(.dark) .defect-list-page__table {
  background:
    linear-gradient(rgba(22, 119, 255, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.035) 1px, transparent 1px),
    rgba(255, 255, 255, 0.64);
  background-size: 32px 32px, 32px 32px;
  border-color: rgba(22, 119, 255, 0.14);
}

html:not(.dark) .defect-list-page__table::before {
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(22, 119, 255, 0.1) 50%, transparent 66%);
}

.defect-list-page__table :deep(.el-table) {
  flex: 1;
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: rgba(8, 18, 32, 0.34);
  --el-table-header-bg-color: rgba(15, 31, 52, 0.46);
  --el-table-row-hover-bg-color: rgba(56, 189, 248, 0.1);
  --el-table-expanded-cell-bg-color: rgba(8, 18, 32, 0.42);
  background:
    linear-gradient(rgba(56, 189, 248, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.03) 1px, transparent 1px),
    rgba(8, 18, 32, 0.32);
  background-size: 28px 28px, 28px 28px, auto;
}

html:not(.dark) .defect-list-page__table :deep(.el-table) {
  --el-table-tr-bg-color: rgba(255, 255, 255, 0.54);
  --el-table-header-bg-color: rgba(240, 247, 255, 0.68);
  --el-table-expanded-cell-bg-color: rgba(255, 255, 255, 0.64);
  background:
    linear-gradient(rgba(22, 119, 255, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.03) 1px, transparent 1px),
    rgba(255, 255, 255, 0.44);
  background-size: 28px 28px, 28px 28px, auto;
}

.defect-list-page__table :deep(.el-table__header th) {
  background: var(--bg-container-soft) !important;
  color: var(--text-secondary);
  font-weight: 700;
  font-size: 12px;
}

.defect-list-page__table :deep(.el-table__row:hover > td) {
  background: rgba(56, 189, 248, 0.1) !important;
}

.defect-list-page__table :deep(.el-table__cell) {
  vertical-align: middle;
}

.defect-title {
  color: var(--color-primary);
  cursor: pointer;
  font-weight: 500;
}

.defect-title:hover {
  text-decoration: underline;
}

.priority-cell {
  font-weight: 700;
  font-size: 12px;
}

.priority-P0 { color: var(--color-danger); }
.priority-P1 { color: var(--color-warning); }
.priority-P2 { color: var(--color-primary); }
.priority-P3 { color: var(--text-secondary); }

.text-secondary {
  color: var(--text-secondary);
  font-size: 13px;
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
.defect-list-page__pagination {
  display: flex;
  justify-content: flex-end;
  padding: 10px 16px;
  border-top: 1px solid rgba(56, 189, 248, 0.12);
}

html:not(.dark) .defect-list-page__pagination {
  border-top-color: rgba(22, 119, 255, 0.12);
}

@media (prefers-reduced-motion: reduce) {
  .defect-list-page::before,
  .defect-list-page::after,
  .defect-list-page__header::after,
  .stat-card::before,
  .defect-list-page__filters::before,
  .defect-list-page__table::before {
    animation: none;
  }
}
</style>
