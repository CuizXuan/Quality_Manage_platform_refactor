<template>
  <div class="report-list">
    <div class="page-header">
      <span class="page-title">测试报告</span>
    </div>

    <!-- 筛选栏 -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="关键词">
          <el-input v-model="filterForm.keyword" placeholder="搜索报告名称" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="filterForm.report_type" placeholder="全部" clearable style="width: 140px">
            <el-option label="执行报告" value="execution" />
            <el-option label="场景报告" value="scenario" />
            <el-option label="套件报告" value="suite" />
          </el-select>
        </el-form-item>
        <el-form-item label="环境">
          <el-select v-model="filterForm.environment" placeholder="全部" clearable style="width: 140px">
            <el-option label="开发环境" value="dev" />
            <el-option label="测试环境" value="test" />
            <el-option label="预发环境" value="staging" />
            <el-option label="生产环境" value="prod" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleFilter">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 报告列表 -->
    <el-table
      v-loading="reportStore.loading"
      :data="reportStore.reports"
      style="width: 100%"
      @row-click="handleRowClick"
      highlight-current-row
    >
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="报告名称" min-width="200">
        <template #default="{ row }">
          <span class="text-ellipsis" :title="row.name">{{ row.name }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="report_type" label="类型" width="100" align="center">
        <template #default="{ row }">
          <el-tag size="small">{{ formatType(row.report_type) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="target_name" label="目标" min-width="140">
        <template #default="{ row }">
          <span v-if="row.target_name" class="text-ellipsis" :title="row.target_name">{{ row.target_name }}</span>
          <span v-else class="text-muted">—</span>
        </template>
      </el-table-column>
      <el-table-column prop="environment" label="环境" width="90" align="center">
        <template #default="{ row }">
          <span>{{ row.environment || '—' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="summary.pass_rate" label="通过率" width="100" align="center">
        <template #default="{ row }">
          <span
            :style="{ color: getPassRateColor(row.summary?.pass_rate) }"
          >{{ row.summary?.pass_rate != null ? row.summary.pass_rate + '%' : '—' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="summary" label="通过/失败" width="110" align="center">
        <template #default="{ row }">
          <span style="color: var(--el-color-success)">{{ row.summary?.passed ?? 0 }}</span>
          /
          <span style="color: var(--el-color-danger)">{{ row.summary?.failed ?? 0 }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="duration_ms" label="耗时" width="100" align="center">
        <template #default="{ row }">
          {{ row.duration_ms ? (row.duration_ms / 1000).toFixed(1) + 's' : '—' }}
        </template>
      </el-table-column>
      <el-table-column prop="executed_at" label="执行时间" width="160" />
      <el-table-column label="操作" width="100" fixed="right" align="center">
        <template #default="{ row }">
          <el-button type="danger" size="small" text @click.stop="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="currentPageSize"
      :total="reportStore.reportTotal"
      :page-sizes="[10, 20, 50, 100]"
      layout="total, sizes, prev, pager, next"
      style="margin-top: var(--spacing-md)"
      @current-change="handlePageChange"
      @size-change="handleSizeChange"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useReportStore } from '@/stores/reportStore'

const router = useRouter()
const reportStore = useReportStore()

const currentPage = ref(1)
const currentPageSize = ref(20)
const filterForm = ref({
  keyword: '',
  report_type: null,
  environment: null,
})

onMounted(() => {
  reportStore.fetchReports({ page: currentPage.value, page_size: currentPageSize.value })
})

function handleFilter() {
  currentPage.value = 1
  reportStore.fetchReports({
    page: 1,
    page_size: currentPageSize.value,
    ...filterForm.value,
  })
}

function handleReset() {
  filterForm.value = { keyword: '', report_type: null, environment: null }
  currentPage.value = 1
  reportStore.fetchReports({ page: 1, page_size: currentPageSize.value })
}

function handlePageChange(page) {
  currentPage.value = page
  reportStore.fetchReports({
    page,
    page_size: currentPageSize.value,
    ...filterForm.value,
  })
}

function handleSizeChange(size) {
  currentPageSize.value = size
  currentPage.value = 1
  reportStore.fetchReports({ page: 1, page_size: size, ...filterForm.value })
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
    reportStore.fetchReports({ page: currentPage.value, page_size: currentPageSize.value })
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
  if (rate >= 95) return 'var(--el-color-success)'
  if (rate >= 80) return 'var(--el-color-warning)'
  return 'var(--el-color-danger)'
}
</script>

<style scoped>
.report-list {
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

.filter-card {
  border-radius: var(--border-radius-base);
}

.text-muted {
  color: var(--text-disabled);
  font-size: 13px;
}
</style>
