<template>
  <div class="execution-history">
    <div class="history-header">
      <el-button :icon="ArrowLeft" text @click="handleBack">返回</el-button>
      <span class="page-title">执行历史</span>
    </div>

    <!-- 筛选条件 -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="场景">
          <el-select
            v-model="filterForm.scenario_id"
            placeholder="全部场景"
            clearable
            style="width: 200px"
          >
            <el-option
              v-for="s in scenarioStore.scenarios"
              :key="s.id"
              :label="s.name"
              :value="s.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="全部状态" clearable style="width: 140px">
            <el-option label="等待中" value="pending" />
            <el-option label="运行中" value="running" />
            <el-option label="成功" value="success" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleFilter">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 执行列表 -->
    <el-table
      v-loading="scenarioStore.loading"
      :data="scenarioStore.executions"
      style="width: 100%"
      @row-click="handleRowClick"
      highlight-current-row
    >
      <el-table-column prop="id" label="Run ID" width="90" />
      <el-table-column prop="scenario_name" label="场景名称" min-width="160">
        <template #default="{ row }">
          <span class="text-ellipsis" :title="row.scenario_name">{{ row.scenario_name }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)" size="small">{{ getStatusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="total_steps" label="步骤数" width="90" align="center" />
      <el-table-column prop="passed_steps" label="成功" width="80" align="center">
        <template #default="{ row }">
          <span style="color: var(--el-color-success)">{{ row.passed_steps }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="failed_steps" label="失败" width="80" align="center">
        <template #default="{ row }">
          <span style="color: var(--el-color-danger)">{{ row.failed_steps }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="duration" label="耗时" width="100" align="center">
        <template #default="{ row }">
          {{ row.duration ? `${row.duration}s` : '—' }}
        </template>
      </el-table-column>
      <el-table-column prop="triggered_by" label="触发者" width="100" align="center" />
      <el-table-column prop="started_at" label="开始时间" width="160" />
      <el-table-column prop="finished_at" label="结束时间" width="160" />
      <el-table-column label="操作" width="100" fixed="right" align="center">
        <template #default="{ row }">
          <el-button type="primary" size="small" text @click.stop="handleViewDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="currentPageSize"
      :total="scenarioStore.executionTotal"
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
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useScenarioStore } from '@/stores/scenarioStore'

const route = useRoute()
const router = useRouter()
const scenarioStore = useScenarioStore()

const currentPage = ref(1)
const currentPageSize = ref(20)
const filterForm = ref({
  scenario_id: route.query.scenario_id ? Number(route.query.scenario_id) : null,
  status: null,
})

onMounted(async () => {
  // 加载场景列表（用于筛选下拉）
  try {
    await scenarioStore.fetchScenarios({ page: 1, page_size: 1000 })
  } catch { /* ignore */ }
  loadExecutions()
})

function loadExecutions() {
  scenarioStore.fetchExecutions({
    page: currentPage.value,
    page_size: currentPageSize.value,
    scenario_id: filterForm.value.scenario_id || undefined,
    status: filterForm.value.status || undefined,
  })
}

function handleFilter() {
  currentPage.value = 1
  loadExecutions()
}

function handleReset() {
  filterForm.value = { scenario_id: null, status: null }
  currentPage.value = 1
  loadExecutions()
}

function handlePageChange(page) {
  currentPage.value = page
  loadExecutions()
}

function handleSizeChange(size) {
  currentPageSize.value = size
  currentPage.value = 1
  loadExecutions()
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

function getStatusType(status) {
  const map = {
    pending: 'info',
    running: 'primary',
    success: 'success',
    failed: 'danger',
  }
  return map[status] || 'info'
}

function getStatusLabel(status) {
  const map = {
    pending: '等待中',
    running: '运行中',
    success: '成功',
    failed: '失败',
  }
  return map[status] || status
}
</script>

<style scoped>
.execution-history {
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.history-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.page-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.filter-card {
  border-radius: var(--border-radius-base);
}
</style>
