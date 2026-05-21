<template>
  <div class="scenario-list-page">
    <!-- 标题区 -->
    <header class="scenario-list-page__header">
      <div>
        <h1>场景管理</h1>
        <p>统一编排多个测试步骤，支持串联执行与执行历史追踪。</p>
      </div>
      <el-button type="primary" class="btn-primary-add" :icon="Plus" @click="handleCreate">
        新建场景
      </el-button>
    </header>

    <!-- 查询区 -->
    <section class="scenario-list-page__filters">
      <div class="filter-bar">
        <el-select
          v-model="draftFilters.status"
          placeholder="全部状态"
          clearable
          class="filter-control"
        >
          <el-option label="启用" value="active" />
          <el-option label="草稿" value="draft" />
          <el-option label="归档" value="archived" />
        </el-select>
        <el-date-picker
          v-model="draftFilters.date_range"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          class="filter-bar__date-range"
        />
      </div>
      <div class="search-bar">
        <el-input
          v-model="draftFilters.keyword"
          placeholder="搜索场景名称"
          clearable
          class="search-bar__input"
          @keyup.enter="handleSearch"
        />
        <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
        <el-button :icon="RefreshLeft" @click="handleReset">重置</el-button>
      </div>
    </section>

    <!-- 数据列表 -->
    <section class="scenario-list-page__table">
      <el-table
        v-loading="scenarioStore.loading"
        :data="scenarioStore.scenarios"
        height="100%"
        highlight-current-row
        @row-click="handleRowClick"
      >
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="场景名称" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="name-cell">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="scenario_type" label="场景类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getScenarioTypeTag(row.scenario_type)" size="small">
              {{ formatScenarioType(row.scenario_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="90" align="center">
          <template #default="{ row }">
            <span class="priority-cell" :class="`priority-${row.priority}`">
              {{ row.priority }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="version" label="版本" width="80" align="center">
          <template #default="{ row }">
            <span>{{ row.version ?? 1 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="desc-cell">{{ row.description || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="step_count" label="步骤数" width="80" align="center" />
        <el-table-column prop="status" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
              {{ row.status === 'active' ? '启用' : '草稿' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="170" align="center">
          <template #default="{ row }">
            {{ formatDate(row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="210" fixed="right" align="center">
          <template #default="{ row }">
            <div class="actions-cell">
              <el-button type="primary" text size="small" @click.stop="handleRun(row)">执行</el-button>
              <el-button type="primary" text size="small" @click.stop="handleEdit(row)">编辑</el-button>
              <el-button type="primary" text size="small" @click.stop="handleCopy(row)">复制</el-button>
              <el-button type="danger" text size="small" @click.stop="handleDelete(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
        <template #empty>
          <span class="empty-text">暂无符合条件的场景</span>
        </template>
      </el-table>

      <div class="scenario-list-page__pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="scenarioStore.total"
          :page-sizes="[15, 30, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          prev-text="上一页"
          next-text="下一页"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </section>

    <!-- 新建场景弹窗 -->
    <el-dialog
      v-model="createDialogVisible"
      title="新建场景"
      top="4vh"
      width="min(1180px, 92vw)"
      destroy-on-close
      class="scenario-dialog"
    >
      <el-form :model="createForm" label-width="90px" class="scenario-form">
        <el-form-item label="场景名称" required>
          <el-input v-model="createForm.name" placeholder="请输入场景名称" />
        </el-form-item>
        <el-form-item label="场景类型">
          <el-select v-model="createForm.scenario_type" placeholder="请选择类型" style="width: 100%">
            <el-option label="功能测试" value="functional" />
            <el-option label="接口测试" value="api" />
            <el-option label="端到端" value="e2e" />
          </el-select>
        </el-form-item>
        <el-form-item label="版本号">
          <el-input-number v-model="createForm.version" :min="1" :max="999" controls-position="right" style="width: 100%" />
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="createForm.priority" placeholder="请选择优先级" style="width: 100%">
            <el-option label="P0 - 最高" value="P0" />
            <el-option label="P1 - 高" value="P1" />
            <el-option label="P2 - 中" value="P2" />
            <el-option label="P3 - 低" value="P3" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="createForm.status">
            <el-radio value="active">启用</el-radio>
            <el-radio value="draft">草稿</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleCreateSubmit">创建</el-button>
      </template>
    </el-dialog>

    <!-- 场景详情/编辑弹窗 -->
    <ScenarioDetailDialog
      v-model="detailDialogVisible"
      :scenario-id="selectedScenarioId"
      @closed="scenarioStore.fetchScenarios(buildQueryParams())"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Search, RefreshLeft } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useScenarioStore } from '@/stores/scenarioStore'

import ScenarioDetailDialog from './ScenarioDetailDialog.vue'

const router = useRouter()
const scenarioStore = useScenarioStore()

const createDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const selectedScenarioId = ref(null)
const saving = ref(false)

const createForm = ref({
  name: '',
  scenario_type: 'functional',
  version: 1,
  priority: 'P2',
  description: '',
  status: 'draft',
})

const draftFilters = ref({
  keyword: '',
  status: '',
  date_range: null,
})

const appliedFilters = ref({
  keyword: '',
  status: '',
  date_range: null,
})

const pagination = ref({
  page: 1,
  pageSize: 15,
})

onMounted(() => {
  scenarioStore.fetchScenarios({ page: 1, page_size: pagination.value.pageSize })
})

function buildQueryParams() {
  const params = {
    page: pagination.value.page,
    page_size: pagination.value.pageSize,
  }
  if (appliedFilters.value.keyword) params.keyword = appliedFilters.value.keyword
  if (appliedFilters.value.status) params.status = appliedFilters.value.status
  if (appliedFilters.value.date_range && appliedFilters.value.date_range.length === 2) {
    params.start_date = appliedFilters.value.date_range[0]
    params.end_date = appliedFilters.value.date_range[1]
  }
  return params
}

function handleSearch() {
  appliedFilters.value = { ...draftFilters.value, date_range: draftFilters.value.date_range ? [...draftFilters.value.date_range] : null }
  pagination.value.page = 1
  scenarioStore.fetchScenarios(buildQueryParams())
}

function handleReset() {
  draftFilters.value = { keyword: '', status: '', date_range: null }
  appliedFilters.value = { keyword: '', status: '', date_range: null }
  pagination.value.page = 1
  scenarioStore.fetchScenarios({ page: 1, page_size: pagination.value.pageSize })
}

function handlePageChange(page) {
  pagination.value.page = page
  scenarioStore.fetchScenarios(buildQueryParams())
}

function handleSizeChange(size) {
  pagination.value.pageSize = size
  pagination.value.page = 1
  scenarioStore.fetchScenarios({ ...buildQueryParams(), page: 1, page_size: size })
}

function handleRowClick(row) {
  selectedScenarioId.value = row.id
  detailDialogVisible.value = true
}

function handleCreate() {
  createForm.value = { name: '', scenario_type: 'functional', version: 1, priority: 'P2', description: '', status: 'draft' }
  createDialogVisible.value = true
}

async function handleCreateSubmit() {
  if (!createForm.value.name.trim()) {
    ElMessage.warning('请输入场景名称')
    return
  }
  saving.value = true
  try {
    const created = await scenarioStore.createScenario(createForm.value)
    createDialogVisible.value = false
    ElMessage.success('创建成功')
    selectedScenarioId.value = created.id
    detailDialogVisible.value = true
  } catch {
    ElMessage.error('创建失败')
  } finally {
    saving.value = false
  }
}

async function handleRun(row) {
  try {
    await ElMessageBox.confirm(`确定要执行场景「${row.name}」吗？`, '执行确认', {
      confirmButtonText: '执行',
      cancelButtonText: '取消',
      type: 'info',
    })
  } catch {
    return
  }
  try {
    const result = await scenarioStore.startExecution(row.id)
    ElMessage.success(`执行已启动 (run_id: ${result.run_id})`)
    router.push({ name: 'ExecutionDetail', params: { id: result.run_id } })
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || '执行启动失败')
  }
}

function handleEdit(row) {
  selectedScenarioId.value = row.id
  detailDialogVisible.value = true
}

async function handleCopy(row) {
  try {
    const data = await scenarioStore.createScenario({
      name: `${row.name} (副本)`,
      scenario_type: row.scenario_type || 'functional',
      version: 1,
      priority: row.priority || 'P2',
      description: row.description,
      status: row.status === 'active' ? 'active' : 'draft',
    })
    ElMessage.success('复制成功')
    scenarioStore.fetchScenarios(buildQueryParams())
    selectedScenarioId.value = data.id
    detailDialogVisible.value = true
  } catch {
    ElMessage.error('复制失败')
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定要删除场景「${row.name}」吗？`, '删除确认', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await scenarioStore.deleteScenario(row.id)
    ElMessage.success('删除成功')
    scenarioStore.fetchScenarios(buildQueryParams())
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('删除失败')
  }
}

function formatDate(isoStr) {
  if (!isoStr) return '—'
  const d = new Date(isoStr)
  if (isNaN(d.getTime())) return '—'
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function getScenarioTypeTag(type) {
  const map = { functional: 'success', api: 'warning', e2e: 'primary' }
  return map[type] || 'info'
}

function formatScenarioType(type) {
  const map = { functional: '功能', api: '接口', e2e: '端到端' }
  return map[type] || type || '—'
}
</script>

<style scoped>
/* ── 页面容器 ── */
.scenario-list-page {
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
.scenario-list-page__header {
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

html:not(.dark) .scenario-list-page__header {
  background: rgba(255, 255, 255, 0.86);
}

.scenario-list-page__header h1,
.scenario-list-page__header p {
  margin: 0;
}

.scenario-list-page__header h1 {
  color: var(--text-strong);
  font-size: 24px;
  line-height: 1.25;
}

.scenario-list-page__header p {
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 13px;
}

.btn-primary-add {
  border: 0;
  background: var(--brand-gradient);
  font-weight: 700;
  transition: transform 0.2s ease, filter 0.2s ease;
}

.btn-primary-add:hover {
  filter: brightness(1.1);
  transform: translateY(-1px);
}

/* ── 查询区 ── */
.scenario-list-page__filters {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: rgba(20, 22, 27, 0.7);
  box-shadow: var(--box-shadow-light);
  backdrop-filter: blur(10px);
}

html:not(.dark) .scenario-list-page__filters {
  background: rgba(255, 255, 255, 0.86);
}

.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 12px;
  align-items: center;
}

.filter-control {
  width: 160px;
}

.search-bar {
  display: flex;
  gap: 12px;
  align-items: center;
}

.search-bar__input {
  width: 320px;
}

/* Date range control */
.scenario-list-page__filters :deep(.filter-bar__date-range.el-date-editor) {
  flex: 0 0 320px;
  width: 320px !important;
  max-width: 320px;
  min-width: 0;
}

.scenario-list-page__filters :deep(.filter-bar__date-range .el-range-input) {
  width: 96px;
  flex: 0 0 96px;
}

.scenario-list-page__filters :deep(.filter-bar__date-range .el-range-separator) {
  flex: 0 0 24px;
  padding: 0;
}

/* ── 表格区 ── */
.scenario-list-page__table {
  display: flex;
  flex: 1;
  min-height: 0;
  flex-direction: column;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: rgba(20, 22, 27, 0.7);
  box-shadow: var(--box-shadow-light);
  backdrop-filter: blur(10px);
  overflow: hidden;
}

html:not(.dark) .scenario-list-page__table {
  background: rgba(255, 255, 255, 0.86);
}

.scenario-list-page__table :deep(.el-table) {
  flex: 1;
}

.scenario-list-page__table :deep(.el-table__header th) {
  background: var(--bg-container-soft) !important;
  color: var(--text-secondary);
  font-weight: 700;
  font-size: 12px;
}

.scenario-list-page__table :deep(.el-table__row:hover > td) {
  background: rgba(56, 189, 248, 0.1) !important;
}

.scenario-list-page__table :deep(.el-table__body tr) {
  cursor: pointer;
}

.scenario-list-page__table :deep(.el-table__cell) {
  vertical-align: middle;
}

.name-cell {
  font-weight: 600;
  color: var(--text-primary);
}

.desc-cell {
  display: -webkit-box;
  overflow: hidden;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.5;
  color: var(--text-secondary);
}

.priority-cell {
  font-weight: 700;
  font-size: 12px;
}

.priority-P0 { color: var(--color-danger); }
.priority-P1 { color: var(--color-warning); }
.priority-P2 { color: var(--color-primary); }
.priority-P3 { color: var(--text-secondary); }

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
.scenario-list-page__pagination {
  display: flex;
  justify-content: flex-end;
  padding: 10px 16px;
  border-top: 1px solid var(--border-color-lighter, #f0f0f0);
}
</style>
