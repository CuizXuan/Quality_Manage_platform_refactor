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
      <el-form :inline="false" :model="draftFilters" label-position="left" class="filter-form">
        <el-row :gutter="12">
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="项目：" class="filter-item">
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
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="版本：" class="filter-item">
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
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="迭代：" class="filter-item">
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
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="需求：" class="filter-item">
              <el-select
                v-model="draftFilters.requirementId"
                placeholder="选择需求"
                clearable
                class="filter-control"
                :disabled="!draftFilters.projectId"
              >
                <el-option v-for="r in foundationStore.requirements" :key="r.id" :label="r.title" :value="r.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="严重程度：" class="filter-item">
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
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="优先级：" class="filter-item">
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
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="状态：" class="filter-item">
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
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="关键词：" class="filter-item">
              <el-input
                v-model="draftFilters.keyword"
                placeholder="搜索标题"
                clearable
                class="search-bar__input"
                @keyup.enter="handleSearch"
              />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <div class="filter-actions">
              <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
              <el-button :icon="RefreshLeft" @click="handleReset">重置</el-button>
            </div>
          </el-col>
        </el-row>
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
      :initialData="initialDefectData"
      @saved="handleSaved"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Plus, Search, RefreshLeft } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useReportStore } from '@/stores/reportStore'
import { useQualityFoundationStore } from '@/stores/qualityFoundationStore'
import DefectForm from './DefectForm.vue'

const route = useRoute()
const reportStore = useReportStore()
const foundationStore = useQualityFoundationStore()

const draftFilters = ref({
  projectId: null,
  versionId: null,
  iterationId: null,
  requirementId: null,
  keyword: '',
  status: '',
  severity: '',
  priority: '',
})

const appliedFilters = ref({
  projectId: null,
  versionId: null,
  iterationId: null,
  requirementId: null,
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
const initialDefectData = ref(null)

onMounted(() => {
  foundationStore.fetchProjects({ page: 1, page_size: 100 })
  reportStore.fetchDefects({ page: 1, page_size: pagination.value.pageSize })
  reportStore.fetchDefectStats()

  // 处理 query params 跳转自动打开新建缺陷表单
  const { open, action, title, description, severity, priority, defect_type, tags, project_id, version_id, iteration_id, requirement_id } = route.query

  const shouldOpenCreate = open === 'create' || action === 'create'
  if (shouldOpenCreate) {
    const initialDefect = {}

    if (title) initialDefect.title = String(title)
    if (description) initialDefect.description = String(description)
    if (severity && ['critical', 'high', 'medium', 'low'].includes(String(severity).toLowerCase())) {
      initialDefect.severity = String(severity).toLowerCase()
    }
    if (priority && /^P[0-3]$/.test(String(priority))) {
      initialDefect.priority = String(priority)
    }
    if (defect_type && ['functional', 'api', 'performance', 'security'].includes(String(defect_type))) {
      initialDefect.defect_type = String(defect_type)
    }

    // 处理 tags：支持逗号分隔字符串或 JSON 数组字符串
    if (tags) {
      const rawTags = String(tags)
      try {
        initialDefect.tags = JSON.parse(rawTags)
      } catch {
        initialDefect.tags = rawTags.split(',').map(t => t.trim()).filter(Boolean)
      }
    }

    // 数字字段
    if (project_id) initialDefect.project_id = Number(project_id) || null
    if (version_id) initialDefect.version_id = Number(version_id) || null
    if (iteration_id) initialDefect.iteration_id = Number(iteration_id) || null
    if (requirement_id) initialDefect.requirement_id = Number(requirement_id) || null

    // 加载级联数据
    if (initialDefect.project_id) {
      foundationStore.fetchVersions({ project_id: initialDefect.project_id })
    }
    if (initialDefect.project_id && initialDefect.version_id) {
      foundationStore.fetchIterations({ project_id: initialDefect.project_id, version_id: initialDefect.version_id })
    }

    currentDefect.value = null
    initialDefectData.value = Object.keys(initialDefect).length > 0 ? initialDefect : null
    formVisible.value = true
  }
})

function onProjectChange(projectId) {
  draftFilters.value.versionId = null
  draftFilters.value.iterationId = null
  draftFilters.value.requirementId = null
  if (projectId) {
    foundationStore.fetchVersions({ project_id: projectId })
    foundationStore.fetchRequirements({ project_id: projectId, page: 1, page_size: 100 })
    reportStore.fetchDefectStats(projectId)
  } else {
    reportStore.fetchDefectStats()
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
    status: appliedFilters.value.status || undefined,
    severity: appliedFilters.value.severity || undefined,
    priority: appliedFilters.value.priority || undefined,
    project_id: appliedFilters.value.projectId || undefined,
    version_id: appliedFilters.value.versionId || undefined,
    iteration_id: appliedFilters.value.iterationId || undefined,
    requirement_id: appliedFilters.value.requirementId || undefined,
  }
}

function handleSearch() {
  appliedFilters.value = { ...draftFilters.value }
  pagination.value.page = 1
  reportStore.fetchDefects({ ...buildQueryParams(), page: 1 })
}

function handleReset() {
  draftFilters.value = { projectId: null, versionId: null, iterationId: null, requirementId: null, keyword: '', status: '', severity: '', priority: '' }
  appliedFilters.value = { projectId: null, versionId: null, iterationId: null, requirementId: null, keyword: '', status: '', severity: '', priority: '' }
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
/* ── 页面容器 ── */
.defect-list-page {
  position: relative;
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

/* ── 标题区 ── */
.defect-list-page__header {
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
  overflow: hidden;
}

html:not(.dark) .defect-list-page__header {
  background: rgba(255, 255, 255, 0.86);
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
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: rgba(20, 22, 27, 0.7);
  box-shadow: var(--box-shadow-light);
  backdrop-filter: blur(10px);
  gap: 4px;
  position: relative;
  overflow: hidden;
}

html:not(.dark) .stat-card {
  background: rgba(255, 255, 255, 0.86);
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
  z-index: 1;
  padding: 14px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: rgba(20, 22, 27, 0.7);
  box-shadow: var(--box-shadow-light);
  backdrop-filter: blur(10px);
  overflow: hidden;
}

html:not(.dark) .defect-list-page__filters {
  background: rgba(255, 255, 255, 0.86);
}

.filter-form {
  position: relative;
  z-index: 1;
  width: 100%;
}

.filter-form :deep(.el-row) {
  align-items: flex-end;
  row-gap: 8px;
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
  align-items: flex-end;
  margin-bottom: 0;
  width: 100%;
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
  width: 100%;
}

.search-bar__input :deep(.el-input) {
  width: 280px;
}

/* ── 表格区 ── */
.defect-list-page__table {
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
  z-index: 1;
}

html:not(.dark) .defect-list-page__table {
  background: rgba(255, 255, 255, 0.86);
}

.defect-list-page__table :deep(.el-table) {
  flex: 1;
}

html:not(.dark) .defect-list-page__table {
  background:
    linear-gradient(rgba(22, 119, 255, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.04) 1px, transparent 1px),
    rgba(255, 255, 255, 0.64);
  background-size: 32px 32px;
  box-shadow: 0 14px 34px rgba(20, 42, 76, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.86);
  border-color: rgba(22, 119, 255, 0.14);
}

html:not(.dark) .defect-list-page__table :deep(.el-table) {
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

html:not(.dark) .defect-list-page__table :deep(.el-table__header th) {
  background: var(--el-table-header-bg-color) !important;
  background-color: var(--el-table-header-bg-color) !important;
  color: var(--text-secondary);
  font-weight: 700;
  font-size: 12px;
}

html:not(.dark) .defect-list-page__table :deep(.el-table__body td) {
  background: var(--el-table-tr-bg-color) !important;
  background-color: var(--el-table-tr-bg-color) !important;
}

html:not(.dark) .defect-list-page__table :deep(.el-table__body tr:nth-child(even) td.el-table__cell) {
  background: rgba(245, 250, 255, 0.5) !important;
  background-color: rgba(245, 250, 255, 0.5) !important;
}

html:not(.dark) .defect-list-page__table :deep(.el-table__row:hover > td) {
  background: var(--el-table-row-hover-bg-color) !important;
  background-color: var(--el-table-row-hover-bg-color) !important;
}

html:not(.dark) .defect-list-page__pagination {
  border-top-color: rgba(22, 119, 255, 0.12);
}

.defect-list-page__table :deep(.el-table__header th) {
  background: var(--bg-container-soft) !important;
  color: var(--text-secondary);
  font-weight: 700;
  font-size: 12px;
}

.defect-list-page__table :deep(.el-table__row:hover > td) {
  background: var(--color-primary-soft) !important;
}

.defect-list-page__table :deep(.el-table__row:hover > td.el-table-fixed-column--left),
.defect-list-page__table :deep(.el-table__row:hover > td.el-table-fixed-column--right) {
  background: var(--color-primary-soft) !important;
}

.defect-list-page__table :deep(.el-table__cell) {
  vertical-align: middle;
}

.defect-list-page__table :deep(.el-table__body tr:nth-child(even) td.el-table__cell) {
  background: rgba(245, 250, 255, 0.5) !important;
  background-color: rgba(245, 250, 255, 0.5) !important;
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
  border-top: 1px solid var(--border-color-lighter);
}
</style>
