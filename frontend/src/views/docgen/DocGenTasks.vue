<template>
  <div class="docgen-tasks-page page-shell page-shell--tech-grid">
    <!-- 页面标题区 -->
    <header class="docgen-tasks-page__header">
      <div>
        <h1>任务中心</h1>
        <p>查看和管理所有文档生成任务</p>
      </div>
      <el-button type="primary" :icon="Refresh" @click="loadTasks">刷新</el-button>
    </header>

    <!-- 查询区 -->
    <section class="docgen-tasks-page__filters">
      <el-form :inline="false" :model="draftFilters" label-position="left" class="filter-form">
        <el-row :gutter="12">
          <el-col :xs="24" :sm="12" :md="6" :lg="5">
            <el-form-item label="任务类型：" class="filter-item">
              <el-select v-model="draftFilters.task_type" placeholder="任务类型" clearable class="filter-control">
                <el-option label="需求设计" value="requirement_design" />
                <el-option label="数据库设计" value="database_design" />
                <el-option label="接口设计" value="api_design" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6" :lg="5">
            <el-form-item label="状态：" class="filter-item">
              <el-select v-model="draftFilters.status" placeholder="状态" clearable class="filter-control">
                <el-option label="进行中" value="running" />
                <el-option label="成功" value="success" />
                <el-option label="失败" value="failed" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6" :lg="5">
            <el-form-item label="关键词：" class="filter-item filter-item--keyword">
              <el-input v-model="draftFilters.keyword" placeholder="搜索名称/源文件" clearable class="search-bar__input" @keyup.enter="handleSearch" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6" :lg="5">
            <div class="filter-actions">
              <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
              <el-button :icon="RefreshLeft" @click="handleReset">重置</el-button>
            </div>
          </el-col>
        </el-row>
      </el-form>
    </section>

    <!-- 数据列表 -->
    <section class="docgen-tasks-page__table">
      <el-table v-loading="docgenStore.loading" :data="docgenStore.tasks" height="100%" highlight-current-row>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="任务名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="task_type" label="类型" width="120" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.task_type === 'requirement_design'" type="primary" size="small">需求设计</el-tag>
            <el-tag v-else-if="row.task_type === 'database_design'" type="success" size="small">数据库设计</el-tag>
            <el-tag v-else-if="row.task_type === 'api_design'" type="warning" size="small">接口设计</el-tag>
            <el-tag v-else size="small">{{ row.task_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'running'" type="warning" size="small">进行中</el-tag>
            <el-tag v-else-if="row.status === 'success'" type="success" size="small">成功</el-tag>
            <el-tag v-else-if="row.status === 'failed'" type="danger" size="small">失败</el-tag>
            <el-tag v-else size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="source_filename" label="源文件" min-width="150" show-overflow-tooltip />
        <el-table-column prop="output_filename" label="输出文件" min-width="150" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="170" align="center">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right" align="center">
          <template #default="{ row }">
            <el-button v-if="row.output_path && row.status === 'success'" type="primary" size="small" link @click="handleDownload(row)">下载</el-button>
            <el-button v-if="row.status === 'running'" type="warning" size="small" link @click="pollTaskStatus(row.id)">刷新状态</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <span class="empty-text">暂无符合条件的任务</span>
        </template>
      </el-table>

      <div class="docgen-tasks-page__pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="docgenStore.taskTotal"
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
import { Refresh, Search, RefreshLeft } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useDocgenStore } from '@/stores/docgenStore'

const docgenStore = useDocgenStore()

const draftFilters = ref({
  task_type: '',
  status: '',
  keyword: '',
})

const appliedFilters = ref({
  task_type: '',
  status: '',
  keyword: '',
})

const pagination = ref({
  page: 1,
  pageSize: 15,
})

onMounted(() => {
  loadTasks()
})


function loadTasks() {
  docgenStore.fetchTasks({
    page: pagination.value.page,
    page_size: pagination.value.pageSize,
    task_type: appliedFilters.value.task_type || undefined,
    status: appliedFilters.value.status || undefined,
    keyword: appliedFilters.value.keyword || undefined,
  })
}

function handleSearch() {
  appliedFilters.value = { ...draftFilters.value }
  pagination.value.page = 1
  loadTasks()
}

function handleReset() {
  draftFilters.value = { task_type: '', status: '', keyword: '' }
  appliedFilters.value = { task_type: '', status: '', keyword: '' }
  pagination.value.page = 1
  loadTasks()
}

function handlePageChange() {
  loadTasks()
}

function handleSizeChange() {
  pagination.value.page = 1
  loadTasks()
}

function formatTime(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}

async function handleDownload(task) {
  await docgenStore.downloadTaskFile(task.id, task.output_filename)
  ElMessage.success('下载已开始')
}

async function pollTaskStatus(taskId) {
  try {
    const task = await docgenStore.pollTaskUntilDone(taskId)
    const idx = docgenStore.tasks.findIndex(t => t.id === taskId)
    if (idx !== -1) docgenStore.tasks[idx] = task
    ElMessage.success(`任务已完成：${task.status}`)
  } catch (err) {
    ElMessage.error(err.message)
  }
}
</script>

<style scoped>
.docgen-tasks-page {
  height: 100%;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 12px;
  gap: 10px;
}

.docgen-tasks-page__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
  padding: 14px 16px;
  border-radius: var(--border-radius-base);
  background: var(--bg-container);
  border: 1px solid var(--border-color);
}

.docgen-tasks-page__header h1 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 4px;
}

.docgen-tasks-page__header p {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0;
}

.docgen-tasks-page__filters {
  flex-shrink: 0;
  padding: 12px 16px;
  border-radius: var(--border-radius-base);
  background: var(--bg-container);
  border: 1px solid var(--border-color);
}

.filter-form {
  width: 100%;
}

.filter-form :deep(.el-row) {
  align-items: flex-end;
  row-gap: 8px;
}

.filter-item {
  margin-bottom: 0;
  width: 100%;
}

.filter-item :deep(.el-form-item__label) {
  display: flex;
  align-items: center;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 700;
  line-height: 34px;
}

.filter-item--keyword {
  width: 200px;
}

.filter-control {
  width: 100%;
}

.search-bar__input {
  width: 280px;
}

.filter-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.filter-actions .el-button {
  min-width: 76px;
  height: 34px;
}

.docgen-tasks-page__table {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  border-radius: var(--border-radius-base);
  background: var(--bg-container);
  border: 1px solid var(--border-color);
  padding: 12px 16px;
  overflow: hidden;
}

.docgen-tasks-page__table .el-table {
  flex: 1;
  min-height: 0;
}

.docgen-tasks-page__table :deep(.el-table__body tr:nth-child(even) td.el-table__cell) {
  background: rgba(245, 250, 255, 0.5) !important;
  background-color: rgba(245, 250, 255, 0.5) !important;
}

.docgen-tasks-page__pagination {
  flex-shrink: 0;
  display: flex;
  justify-content: flex-end;
  padding-top: 8px;
}

.empty-text {
  color: var(--text-secondary);
  font-size: 14px;
}

.btn-primary-add {
  position: relative;
  z-index: 1;
  border: 0;
  background: var(--brand-gradient);
  font-weight: 700;
  transition: transform 0.2s ease, filter 0.2s ease;
}

.btn-primary-add:hover {
  filter: brightness(1.1);
  transform: translateY(-1px);
}

/* ── Light Theme ── */
html:not(.dark) .docgen-tasks-page__header {
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.86), rgba(245, 250, 255, 0.68)),
    rgba(255, 255, 255, 0.72);
  box-shadow: 0 18px 46px rgba(20, 42, 76, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.82);
  border-color: rgba(22, 119, 255, 0.18);
}

html:not(.dark) .docgen-tasks-page__filters {
  background:
    linear-gradient(rgba(22, 119, 255, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.04) 1px, transparent 1px),
    linear-gradient(145deg, rgba(255, 255, 255, 0.76), rgba(245, 250, 255, 0.58)),
    rgba(255, 255, 255, 0.62);
  background-size: 26px 26px, 26px 26px, auto, auto;
  border-color: rgba(22, 119, 255, 0.14);
}

html:not(.dark) .docgen-tasks-page__table {
  background:
    linear-gradient(rgba(22, 119, 255, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.04) 1px, transparent 1px),
    linear-gradient(145deg, rgba(255, 255, 255, 0.76), rgba(245, 250, 255, 0.58)),
    rgba(255, 255, 255, 0.62);
  background-size: 32px 32px, 32px 32px, auto, auto;
  border-color: rgba(22, 119, 255, 0.14);
}

html:not(.dark) .docgen-tasks-page__table :deep(.el-table) {
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

html:not(.dark) .docgen-tasks-page__table :deep(.el-table__body tr:nth-child(even) td.el-table__cell) {
  background: rgba(245, 250, 255, 0.5) !important;
  background-color: rgba(245, 250, 255, 0.5) !important;
}

html:not(.dark) .docgen-tasks-page__pagination {
  border-top-color: rgba(22, 119, 255, 0.12);
}
</style>