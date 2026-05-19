<template>
  <div class="defect-list">
    <div class="page-header">
      <span class="page-title">缺陷管理</span>
      <el-button type="primary" :icon="Plus" @click="handleCreate">新建缺陷</el-button>
    </div>

    <!-- 统计概览 -->
    <el-row :gutter="12" class="stats-row" v-if="reportStore.defectStats">
      <el-col :span="4">
        <el-card class="stat-card" shadow="never">
          <div class="stat-value">{{ reportStore.defectStats.total }}</div>
          <div class="stat-label">全部</div>
        </el-card>
      </el-col>
      <el-col :span="4" v-for="(count, status) in reportStore.defectStats.by_status" :key="status">
        <el-card class="stat-card" shadow="never">
          <div class="stat-value" :style="{ color: getStatusColor(status) }">{{ count }}</div>
          <div class="stat-label">{{ getStatusLabel(status) }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 筛选栏 -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="关键词">
          <el-input v-model="filterForm.keyword" placeholder="搜索标题" clearable style="width: 180px" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="全部" clearable style="width: 120px">
            <el-option label="打开" value="open" />
            <el-option label="已确认" value="confirmed" />
            <el-option label="已修复" value="fixed" />
            <el-option label="已验证" value="verified" />
            <el-option label="已关闭" value="closed" />
          </el-select>
        </el-form-item>
        <el-form-item label="严重程度">
          <el-select v-model="filterForm.severity" placeholder="全部" clearable style="width: 120px">
            <el-option label="Critical" value="critical" />
            <el-option label="High" value="high" />
            <el-option label="Medium" value="medium" />
            <el-option label="Low" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="filterForm.priority" placeholder="全部" clearable style="width: 100px">
            <el-option label="P0" value="P0" />
            <el-option label="P1" value="P1" />
            <el-option label="P2" value="P2" />
            <el-option label="P3" value="P3" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleFilter">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 缺陷列表 -->
    <el-table
      v-loading="reportStore.loading"
      :data="reportStore.defects"
      style="width: 100%"
      highlight-current-row
    >
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="title" label="缺陷标题" min-width="200">
        <template #default="{ row }">
          <span class="text-ellipsis defect-title" :title="row.title" @click="handleEdit(row)">{{ row.title }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="severity" label="严重程度" width="110" align="center">
        <template #default="{ row }">
          <el-tag :type="getSeverityType(row.severity)" size="small">{{ row.severity }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="priority" label="优先级" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="getPriorityType(row.priority)" size="small">{{ row.priority }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)" size="small">{{ getStatusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="defect_type" label="类型" width="100" align="center">
        <template #default="{ row }">
          {{ formatDefectType(row.defect_type) }}
        </template>
      </el-table-column>
      <el-table-column prop="opened_at" label="创建时间" width="160" />
      <el-table-column label="操作" width="200" fixed="right" align="center">
        <template #default="{ row }">
          <el-button
            v-for="action in getAvailableActions(row.status)"
            :key="action.status"
            type="primary"
            size="small"
            text
            @click.stop="handleTransition(row, action.status, action.label)"
          >{{ action.label }}</el-button>
          <el-button type="primary" size="small" text @click.stop="handleEdit(row)">编辑</el-button>
          <el-button type="danger" size="small" text @click.stop="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="currentPageSize"
      :total="reportStore.defectTotal"
      :page-sizes="[10, 20, 50, 100]"
      layout="total, sizes, prev, pager, next"
      style="margin-top: var(--spacing-md)"
      @current-change="handlePageChange"
      @size-change="handleSizeChange"
    />

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
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useReportStore } from '@/stores/reportStore'
import DefectForm from './DefectForm.vue'

const reportStore = useReportStore()

const currentPage = ref(1)
const currentPageSize = ref(20)
const filterForm = ref({
  keyword: '',
  status: null,
  severity: null,
  priority: null,
})

const formVisible = ref(false)
const currentDefect = ref(null)

onMounted(() => {
  reportStore.fetchDefects({ page: currentPage.value, page_size: currentPageSize.value })
  reportStore.fetchDefectStats()
})

function handleFilter() {
  currentPage.value = 1
  reportStore.fetchDefects({ page: 1, page_size: currentPageSize.value, ...filterForm.value })
}

function handleReset() {
  filterForm.value = { keyword: '', status: null, severity: null, priority: null }
  currentPage.value = 1
  reportStore.fetchDefects({ page: 1, page_size: currentPageSize.value })
}

function handlePageChange(page) {
  currentPage.value = page
  reportStore.fetchDefects({ page, page_size: currentPageSize.value, ...filterForm.value })
}

function handleSizeChange(size) {
  currentPageSize.value = size
  currentPage.value = 1
  reportStore.fetchDefects({ page: 1, page_size: size, ...filterForm.value })
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
  reportStore.fetchDefects({ page: currentPage.value, page_size: currentPageSize.value, ...filterForm.value })
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
    reportStore.fetchDefectStats()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '状态流转失败')
    }
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
    reportStore.fetchDefectStats()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('删除失败')
  }
}

function getAvailableActions(status) {
  const transitions = {
    open: [{ status: 'confirmed', label: '确认' }],
    confirmed: [
      { status: 'fixed', label: '修复' },
      { status: 'open', label: '退回' },
    ],
    fixed: [{ status: 'verified', label: '验证' }],
    verified: [{ status: 'closed', label: '关闭' }],
    closed: [{ status: 'open', label: '重新打开' }],
  }
  return transitions[status] || []
}

function getStatusLabel(status) {
  const map = {
    open: '打开',
    confirmed: '已确认',
    fixed: '已修复',
    verified: '已验证',
    closed: '已关闭',
  }
  return map[status] || status
}

function getStatusType(status) {
  const map = {
    open: 'danger',
    confirmed: 'warning',
    fixed: 'primary',
    verified: 'success',
    closed: 'info',
  }
  return map[status] || 'info'
}

function getStatusColor(status) {
  const map = {
    open: 'var(--el-color-danger)',
    confirmed: 'var(--el-color-warning)',
    fixed: 'var(--el-color-primary)',
    verified: 'var(--el-color-success)',
    closed: 'var(--text-secondary)',
  }
  return map[status] || 'var(--text-secondary)'
}

function getSeverityType(severity) {
  const map = { critical: 'danger', high: 'warning', medium: '', low: 'info' }
  return map[severity] || 'info'
}

function getPriorityType(priority) {
  const map = { P0: 'danger', P1: 'warning', P2: '', P3: 'info' }
  return map[priority] || 'info'
}

function formatDefectType(type) {
  const map = { functional: '功能', api: '接口', performance: '性能', security: '安全' }
  return map[type] || type
}
</script>

<style scoped>
.defect-list {
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.stats-row {
  margin-bottom: 0;
}

.stat-card {
  border-radius: var(--border-radius-base);
  text-align: center;
}

.stat-value {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.filter-card {
  border-radius: var(--border-radius-base);
}

.defect-title {
  color: var(--el-color-primary);
  cursor: pointer;
}

.defect-title:hover {
  text-decoration: underline;
}
</style>
