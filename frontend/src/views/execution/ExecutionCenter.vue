<template>
  <div class="execution-center-page scenario-workbench-page">
    <header class="execution-center-page__header scenario-workbench-page__header">
      <div>
        <h1>执行中心</h1>
        <p>统一查看场景执行、计划执行、回归运行与队列状态。</p>
      </div>
    </header>

    <section class="execution-center-page__filters scenario-workbench-page__panel">
      <el-form label-position="left" class="filter-form">
        <div class="filter-form__row">
          <el-form-item label="执行对象" class="filter-item">
            <el-select v-model="filters.target_type" clearable class="filter-control" placeholder="全部">
              <el-option label="场景" value="scenario" />
              <el-option label="计划" value="plan" />
            </el-select>
          </el-form-item>
          <el-form-item label="状态" class="filter-item">
            <el-select v-model="filters.status" clearable class="filter-control" placeholder="全部">
              <el-option label="排队中" value="queued" />
              <el-option label="运行中" value="running" />
              <el-option label="成功" value="passed" />
              <el-option label="失败" value="failed" />
              <el-option label="停止" value="stopped" />
            </el-select>
          </el-form-item>
          <div class="filter-actions">
            <el-button type="primary" @click="loadRuns">查询</el-button>
            <el-button @click="resetFilters">重置</el-button>
          </div>
        </div>
      </el-form>
    </section>

    <section class="execution-center-page__table scenario-workbench-page__panel">
      <el-table v-loading="executionStore.loading" :data="executionStore.runs" height="100%">
        <el-table-column prop="id" label="Run ID" width="90" />
        <el-table-column prop="target_type" label="对象类型" width="100" />
        <el-table-column prop="target_id" label="对象 ID" width="100" />
        <el-table-column prop="status" label="状态" width="100" />
        <el-table-column prop="queue_status" label="队列状态" width="100" />
        <el-table-column prop="duration_ms" label="耗时(ms)" width="120" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <div class="actions-cell">
              <el-button text type="primary" size="small" @click="openRun(row.id)">详情</el-button>
              <el-button text type="warning" size="small" @click="cancelRun(row.id)">停止</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>

<script setup>
import { onMounted, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { useExecutionStore } from '@/stores/executionStore'

const router = useRouter()
const executionStore = useExecutionStore()
const filters = reactive({
  target_type: '',
  status: '',
})

async function loadRuns() {
  await executionStore.fetchRuns({
    target_type: filters.target_type || undefined,
    status: filters.status || undefined,
  })
}

function resetFilters() {
  filters.target_type = ''
  filters.status = ''
  loadRuns()
}

async function cancelRun(id) {
  await executionStore.cancelRun(id)
  ElMessage.success('执行已停止')
  await loadRuns()
}

function openRun(id) {
  router.push({ name: 'ExecutionDetailView', params: { id } })
}

onMounted(loadRuns)
</script>

<style scoped>
.execution-center-page {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 10px;
  height: 100%;
  padding: 12px;
}

.execution-center-page__header {
  min-height: 56px;
  padding: 12px 16px;
}

.execution-center-page__header h1,
.execution-center-page__header p {
  margin: 0;
}

.execution-center-page__header h1 {
  color: var(--text-strong);
  font-size: 24px;
}

.execution-center-page__header p {
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 13px;
}

.execution-center-page__filters {
  padding: 14px;
}

.filter-form__row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: flex-end;
}

.filter-item {
  display: flex;
  align-items: flex-end;
}

.filter-control {
  width: 180px;
}

.filter-actions {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.execution-center-page__table {
  flex: 1;
  min-height: 0;
  padding: 12px 16px;
}

.actions-cell {
  display: inline-flex;
  gap: 4px;
}
</style>
