<template>
  <div class="test-plan-runs-page">
    <!-- 标题区 -->
    <header class="page-header">
      <div>
        <h1>执行历史</h1>
        <p>查看测试计划的执行记录</p>
      </div>
    </header>

    <!-- 主体 -->
    <div class="page-body">
      <!-- 查询栏 -->
      <div class="filter-bar">
        <el-form :model="filters" label-position="left" class="filter-form">
          <div class="filter-form__row">
            <el-form-item label="状态：" class="filter-item">
              <el-select v-model="filters.status" placeholder="全部" clearable class="filter-control">
                <el-option label="等待中" value="pending" />
                <el-option label="运行中" value="running" />
                <el-option label="成功" value="passed" />
                <el-option label="失败" value="failed" />
              </el-select>
            </el-form-item>
            <div class="filter-actions">
              <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
              <el-button :icon="RefreshLeft" @click="handleReset">重置</el-button>
            </div>
          </div>
        </el-form>
      </div>

      <!-- 数据列表 -->
      <div class="data-table">
        <el-table v-loading="store.loading" :data="store.runs" height="100%" highlight-current-row>
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="plan_id" label="计划ID" width="80" />
          <el-table-column prop="status" label="状态" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)" size="small">
                {{ getStatusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="total" label="总数" width="60" align="center" />
          <el-table-column prop="passed" label="通过" width="60" align="center">
            <template #default="{ row }">
              <span class="passed-count">{{ row.passed }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="failed" label="失败" width="60" align="center">
            <template #default="{ row }">
              <span class="failed-count">{{ row.failed }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="skipped" label="跳过" width="60" align="center">
            <template #default="{ row }">
              <span class="skipped-count">{{ row.skipped }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="duration_ms" label="耗时" width="80">
            <template #default="{ row }">
              <span>{{ row.duration_ms ? `${row.duration_ms}ms` : '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="started_at" label="开始时间" width="160">
            <template #default="{ row }">
              <span>{{ formatTime(row.started_at) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80" fixed="right" align="center">
            <template #default="{ row }">
              <el-button type="primary" text size="small" @click="viewDetail(row)">详情</el-button>
            </template>
          </el-table-column>
          <template #empty>
            <span class="empty-text">暂无执行记录</span>
          </template>
        </el-table>

        <div class="pagination-bar">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.pageSize"
            :total="store.runsTotal"
            :page-sizes="[15, 30, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            prev-text="上一页"
            next-text="下一页"
            @current-change="handlePageChange"
            @size-change="handleSizeChange"
          />
        </div>
      </div>
    </div>

    <!-- 详情弹窗 -->
    <el-dialog v-model="showDetailDialog" title="执行详情" width="700px" destroy-on-close>
      <div v-if="detailRun" class="run-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="计划ID">{{ detailRun.plan_id }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(detailRun.status)" size="small">
              {{ getStatusLabel(detailRun.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="总数">{{ detailRun.total }}</el-descriptions-item>
          <el-descriptions-item label="通过数">{{ detailRun.passed }}</el-descriptions-item>
          <el-descriptions-item label="失败数">{{ detailRun.failed }}</el-descriptions-item>
          <el-descriptions-item label="跳过数">{{ detailRun.skipped }}</el-descriptions-item>
          <el-descriptions-item label="开始时间">{{ formatTime(detailRun.started_at) }}</el-descriptions-item>
          <el-descriptions-item label="结束时间">{{ formatTime(detailRun.finished_at) }}</el-descriptions-item>
          <el-descriptions-item label="耗时">{{ detailRun.duration_ms ? `${detailRun.duration_ms}ms` : '-' }}</el-descriptions-item>
        </el-descriptions>

        <div v-if="detailRun.summary?.items?.length" class="run-items">
          <h4>执行明细</h4>
          <el-table :data="detailRun.summary.items" size="small">
            <el-table-column prop="item_type" label="类型" width="80">
              <template #default="{ row }">
                <el-tag size="small" :type="row.item_type === 'case' ? 'primary' : 'success'">
                  {{ row.item_type === 'case' ? '用例' : '场景' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="item_id_ref" label="ID" width="60" />
            <el-table-column prop="status" label="状态" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="getItemStatusType(row.status)" size="small">
                  {{ row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="error" label="错误信息" show-overflow-tooltip />
          </el-table>
        </div>
      </div>
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Search, RefreshLeft } from '@element-plus/icons-vue'
import { useTestPlanStore } from '@/stores/testPlanStore'

const store = useTestPlanStore()

const filters = reactive({ status: '' })
const pagination = reactive({ page: 1, pageSize: 15 })
const showDetailDialog = ref(false)
const detailRun = ref(null)

function getStatusType(status) {
  const map = { pending: 'info', running: 'primary', passed: 'success', failed: 'danger', stopped: 'warning' }
  return map[status] || 'info'
}

function getStatusLabel(status) {
  const map = { pending: '等待中', running: '运行中', passed: '成功', failed: '失败', stopped: '已停止' }
  return map[status] || status
}

function getItemStatusType(status) {
  const map = { passed: 'success', failed: 'danger', skipped: 'info' }
  return map[status] || 'info'
}

function formatTime(timeStr) {
  if (!timeStr) return '-'
  return timeStr.replace('T', ' ').slice(0, 19)
}

async function fetchRuns() {
  await store.fetchRuns({
    page: pagination.page,
    page_size: pagination.pageSize,
    status: filters.status || undefined,
  })
}

function handleSearch() {
  pagination.page = 1
  fetchRuns()
}

function handleReset() {
  filters.status = ''
  pagination.page = 1
  fetchRuns()
}

function handlePageChange() {
  fetchRuns()
}

function handleSizeChange(size) {
  pagination.pageSize = size
  fetchRuns()
}

async function viewDetail(run) {
  detailRun.value = await store.fetchRun(run.id)
  showDetailDialog.value = true
}

onMounted(() => {
  fetchRuns()
})
</script>

<style scoped>
.test-plan-runs-page {
  display: flex;
  flex-direction: column;
  gap: 10px;
  height: 100%;
  padding: 12px;
  background: var(--bg-page);
  overflow: hidden;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-height: 56px;
  padding: 12px 16px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: var(--bg-header);
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  color: var(--text-strong);
}

.page-header p {
  margin: 4px 0 0;
  color: var(--text-secondary);
  font-size: 13px;
}

.page-body {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  gap: 10px;
}

.filter-bar {
  padding: 12px 16px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: var(--bg-header);
}

.filter-form__row {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.filter-item {
  flex: 0 0 160px;
}

.filter-control {
  width: 100%;
}

.filter-actions {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.data-table {
  flex: 1;
  min-height: 0;
  padding: 12px 16px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: var(--bg-header);
}

.pagination-bar {
  display: flex;
  justify-content: flex-end;
  padding: 10px 0 0;
  border-top: 1px solid var(--border-color);
}

.passed-count {
  color: var(--el-color-success);
}

.failed-count {
  color: var(--el-color-danger);
}

.skipped-count {
  color: var(--el-color-info);
}

.run-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.run-items h4 {
  margin: 0 0 8px;
  color: var(--text-secondary);
}

.empty-text {
  color: var(--text-secondary);
  font-size: 13px;
}
</style>