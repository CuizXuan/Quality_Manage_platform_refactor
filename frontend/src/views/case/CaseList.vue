<template>
  <div class="case-list-page">
    <!-- 页面标题区 -->
    <header class="case-list-page__header">
      <div>
        <h1>用例列表</h1>
        <p>按名称、类型、优先级和更新时间筛选用例资产。</p>
      </div>
      <el-button type="primary" class="btn-primary-add" :icon="Plus" @click="emit('create-case')">新建用例</el-button>
    </header>

    <!-- 筛选区 -->
    <section class="case-list-page__filters">
      <el-form :inline="false" class="filter-form" @submit.prevent>
        <el-row :gutter="12">
          <el-col :xs="24" :sm="12" :md="8" :lg="6">
            <el-form-item label="关键词：" class="filter-item">
              <el-input
                v-model="draftFilters.keyword"
                placeholder="搜索用例名称或URL"
                clearable
                class="filter-keyword"
                @keyup.enter="handleSearch"
              />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6" :lg="4">
            <el-form-item label="用例类型：" class="filter-item">
              <el-select v-model="draftFilters.case_type" placeholder="全部类型" clearable class="filter-control">
                <el-option label="接口用例" value="api" />
                <el-option label="功能用例" value="functional" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6" :lg="4">
            <el-form-item label="优先级：" class="filter-item">
              <el-select v-model="draftFilters.priority" placeholder="全部优先级" clearable class="filter-control">
                <el-option label="P0" value="P0" />
                <el-option label="P1" value="P1" />
                <el-option label="P2" value="P2" />
                <el-option label="P3" value="P3" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8" :lg="6">
            <el-form-item label="日期范围：" class="filter-item">
              <el-date-picker
                v-model="draftFilters.dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                value-format="YYYY-MM-DD"
                class="filter-range"
                @change="handleDateChange"
              />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6" :lg="4">
            <el-form-item class="filter-item filter-actions">
              <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
              <el-button :icon="RefreshLeft" @click="handleReset">重置</el-button>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </section>

    <!-- 数据列表 -->
    <section class="case-list-page__table">
      <el-table
        v-loading="caseStore.loading"
        :data="cases"
        height="100%"
        highlight-current-row
        @row-click="handleRowClick"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="用例名称" min-width="220">
          <template #default="{ row }">
            <OverflowText :text="row.name" class="name-cell" strong />
          </template>
        </el-table-column>
        <el-table-column prop="case_type" label="用例类型" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="row.case_type === 'api' ? 'success' : 'warning'" size="small">
              {{ row.case_type === 'api' ? '接口' : '功能' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="描述" min-width="240">
          <template #default="{ row }">
            <OverflowText :text="stripHtml(row.description)" placeholder="—" muted />
          </template>
        </el-table-column>
        <el-table-column label="所属分类" min-width="160">
          <template #default="{ row }">
            <OverflowText :text="getFolderName(row.folder_id)" placeholder="—" />
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="getPriorityType(row.priority)" size="small">{{ row.priority }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="180" align="center">
          <template #default="{ row }">{{ formatDate(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right" align="center">
          <template #default="{ row }">
            <div class="actions-cell">
              <el-button type="primary" text size="small" @click.stop="handleCopy(row)">复制</el-button>
              <el-button type="danger" text size="small" @click.stop="handleDelete(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
        <template #empty>
          <span class="empty-text">暂无符合条件的用例</span>
        </template>
      </el-table>

      <div class="case-list-page__pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="caseStore.total"
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
import { ref, computed, onMounted, watch } from 'vue'
import { Search, Plus, RefreshLeft } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useCaseStore } from '@/stores/caseStore'
import { caseApi } from '@/api/case'
import OverflowText from '@/components/common/OverflowText.vue'

const emit = defineEmits(['case-selected', 'create-case'])

const props = defineProps({
  folderId: { type: Number, default: null },
})

const caseStore = useCaseStore()

const folders = ref([])
const pagination = ref({ page: 1, pageSize: 15 })

const draftFilters = ref({ keyword: '', case_type: '', priority: '', dateRange: [] })
const appliedFilters = ref({ keyword: '', case_type: '', priority: '', updated_start: '', updated_end: '' })

const cases = computed(() => caseStore.cases || [])

onMounted(async () => {
  await Promise.all([loadFolders(), loadCases()])
})

watch(() => props.folderId, () => {
  pagination.value.page = 1
  loadCases()
})

function buildQueryParams() {
  return {
    page: pagination.value.page,
    page_size: pagination.value.pageSize,
    ...(props.folderId && { folder_id: props.folderId }),
    ...(appliedFilters.value.keyword && { keyword: appliedFilters.value.keyword }),
    ...(appliedFilters.value.case_type && { case_type: appliedFilters.value.case_type }),
    ...(appliedFilters.value.priority && { priority: appliedFilters.value.priority }),
    ...(appliedFilters.value.updated_start && { updated_start: appliedFilters.value.updated_start }),
    ...(appliedFilters.value.updated_end && { updated_end: appliedFilters.value.updated_end }),
  }
}

async function loadCases() {
  try {
    await caseStore.fetchCases(buildQueryParams())
  } catch {
    ElMessage.error(caseStore.error || '加载用例失败')
  }
}

async function loadFolders() {
  try {
    const res = await caseApi.listFolders({})
    folders.value = res.data?.items || []
  } catch {
    folders.value = []
  }
}

function handleDateChange(val) {
  if (val && val.length === 2) {
    appliedFilters.value.updated_start = val[0]
    appliedFilters.value.updated_end = val[1]
  } else {
    appliedFilters.value.updated_start = ''
    appliedFilters.value.updated_end = ''
  }
}

function handleSearch() {
  appliedFilters.value = {
    keyword: draftFilters.value.keyword,
    case_type: draftFilters.value.case_type,
    priority: draftFilters.value.priority,
    updated_start: appliedFilters.value.updated_start,
    updated_end: appliedFilters.value.updated_end,
  }
  pagination.value.page = 1
  loadCases()
}

function handleReset() {
  draftFilters.value = { keyword: '', case_type: '', priority: '', dateRange: [] }
  appliedFilters.value = { keyword: '', case_type: '', priority: '', updated_start: '', updated_end: '' }
  pagination.value.page = 1
  loadCases()
}

function handlePageChange(p) {
  pagination.value.page = p
  loadCases()
}

function handleSizeChange(s) {
  pagination.value.pageSize = s
  pagination.value.page = 1
  loadCases()
}

function handleRowClick(row) {
  emit('case-selected', row)
}

async function handleCopy(row) {
  try {
    await caseApi.copy(row.id)
    ElMessage.success('复制成功')
    loadCases()
  } catch {
    ElMessage.error('复制失败')
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除用例「${row.name}」？此操作不可恢复。`, '确认删除', { type: 'warning' })
    await caseStore.deleteCase(row.id)
    ElMessage.success('删除成功')
    if (cases.value.length === 0 && pagination.value.page > 1) {
      pagination.value.page--
    }
    loadCases()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error(caseStore.error || '删除失败')
  }
}

function getPriorityType(priority) {
  const map = { P0: 'danger', P1: 'warning', P2: 'success', P3: 'info' }
  return map[priority] || 'info'
}

function formatDate(dateStr) {
  if (!dateStr) return '—'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

function stripHtml(text) {
  return (text || '').replace(/<[^>]+>/g, '').replace(/&nbsp;/g, ' ').trim()
}

function getFolderName(folderId) {
  if (!folderId) return '—'
  return folders.value.find(f => f.id === folderId)?.name || '—'
}

defineExpose({ reload: loadCases })
</script>

<style scoped>
/* ── 页面容器 ── */
.case-list-page {
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
.case-list-page__header {
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

html:not(.dark) .case-list-page__header {
  background: rgba(255, 255, 255, 0.86);
}

.case-list-page__header h1,
.case-list-page__header p {
  margin: 0;
}

.case-list-page__header h1 {
  color: var(--text-strong);
  font-size: 24px;
  line-height: 1.25;
}

.case-list-page__header p {
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 13px;
}

.btn-primary-add {
  border: 0;
  background: var(--brand-gradient);
  font-weight: 700;
  transition: filter 0.2s ease, transform 0.2s ease;
}

.btn-primary-add:hover {
  filter: brightness(1.1);
  transform: translateY(-1px);
}

/* ── 筛选区 ── */
.case-list-page__filters {
  padding: 14px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: rgba(20, 22, 27, 0.7);
  box-shadow: var(--box-shadow-light);
  backdrop-filter: blur(10px);
}

html:not(.dark) .case-list-page__filters {
  background: rgba(255, 255, 255, 0.86);
}

.filter-form :deep(.el-form-item__label) {
  display: flex;
  align-items: center;
}

.filter-form :deep(.el-row) {
  align-items: flex-end;
}

.filter-item {
  margin-bottom: 0;
  width: 100%;
}

.filter-keyword {
  width: 200px;
}

.filter-control {
  width: 100%;
}

.filter-range {
  width: 100%;
}

.filter-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

/* ── 表格区 ── */
.case-list-page__table {
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

html:not(.dark) .case-list-page__table {
  background: rgba(255, 255, 255, 0.86);
}

.case-list-page__table :deep(.el-table) {
  flex: 1;
}

.case-list-page__table :deep(.el-table__header th) {
  background: var(--bg-container-soft) !important;
  color: var(--text-secondary);
  font-weight: 700;
  font-size: 12px;
}

.case-list-page__table :deep(.el-table__row) {
  cursor: pointer;
}

.case-list-page__table :deep(.el-table__row:hover > td) {
  background: var(--color-primary-soft) !important;
}

.case-list-page__table :deep(.el-table__row:hover > td.el-table-fixed-column--left),
.case-list-page__table :deep(.el-table__row:hover > td.el-table-fixed-column--right) {
  background: var(--color-primary-soft) !important;
}

.case-list-page__table :deep(.el-table__cell) {
  vertical-align: middle;
}

/* ── 分页 ── */
.case-list-page__pagination {
  display: flex;
  justify-content: flex-end;
  padding: 10px 16px;
  border-top: 1px solid var(--border-color-lighter, #f0f0f0);
}

/* ── 通用 ── */
.name-cell {
  font-weight: 600;
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
</style>
