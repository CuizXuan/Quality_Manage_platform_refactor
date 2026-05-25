<template>
  <div class="requirement-management-page">
    <header class="requirement-management-page__header">
      <div>
        <h1>需求管理</h1>
        <p>管理质量测试的需求项，追踪需求覆盖率。</p>
      </div>
      <el-button type="primary" :icon="Plus" class="btn-primary-add" @click="openCreateDialog">新建需求</el-button>
    </header>

    <!-- 覆盖率卡片 -->
    <div class="requirement-management-page__coverage" v-if="store.requirementCoverage">
      <div class="coverage-card">
        <div class="coverage-value">{{ store.requirementCoverage.total }}</div>
        <div class="coverage-label">需求总数</div>
      </div>
      <div class="coverage-card">
        <div class="coverage-value">{{ store.requirementCoverage.with_test_case }}</div>
        <div class="coverage-label">已关联用例</div>
      </div>
      <div class="coverage-card">
        <div class="coverage-value">{{ store.requirementCoverage.with_scenario }}</div>
        <div class="coverage-label">已关联场景</div>
      </div>
      <div class="coverage-card">
        <div class="coverage-value">{{ store.requirementCoverage.executed }}</div>
        <div class="coverage-label">已执行</div>
      </div>
      <div class="coverage-card">
        <div class="coverage-value">{{ store.requirementCoverage.with_defect }}</div>
        <div class="coverage-label">有缺陷</div>
      </div>
    </div>

    <!-- 查询区 -->
    <section class="requirement-management-page__filters">
      <el-form :model="filters" label-position="left" class="filter-form">
        <div class="filter-form__row">
          <el-form-item label="项目：" class="filter-item filter-item--project">
            <el-select v-model="filters.project_id" placeholder="选择项目" clearable class="filter-control" @change="onProjectChange">
              <el-option v-for="p in store.projects" :key="p.id" :label="p.name" :value="p.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="版本：" class="filter-item filter-item--version">
            <el-select v-model="filters.version_id" placeholder="选择版本" clearable class="filter-control" :disabled="!filters.project_id">
              <el-option v-for="v in store.versions" :key="v.id" :label="v.name" :value="v.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="迭代：" class="filter-item filter-item--iteration">
            <el-select v-model="filters.iteration_id" placeholder="选择迭代" clearable class="filter-control" :disabled="!filters.version_id">
              <el-option v-for="i in store.iterations" :key="i.id" :label="i.name" :value="i.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="状态：" class="filter-item filter-item--status">
            <el-select v-model="filters.status" placeholder="状态" clearable class="filter-control">
              <el-option label="打开" value="open" />
              <el-option label="进行中" value="in_progress" />
              <el-option label="已测试" value="tested" />
              <el-option label="已关闭" value="closed" />
            </el-select>
          </el-form-item>
          <div class="filter-actions">
            <el-button type="primary" :icon="Search" @click="fetchRequirements">查询</el-button>
            <el-button :icon="RefreshLeft" @click="resetFilters">重置</el-button>
          </div>
        </div>
      </el-form>
    </section>

    <!-- 数据列表 -->
    <section class="requirement-management-page__table">
      <el-table v-loading="store.loading" :data="store.requirements" height="100%" highlight-current-row>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="title" label="需求标题" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="requirement-title" :title="row.title" @click="editRequirement(row)">{{ row.title }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="source_type" label="来源类型" width="120" align="center">
          <template #default="{ row }">
            <span class="text-secondary">{{ formatSourceType(row.source_type) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="source_key" label="来源编号" width="120" align="center" />
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
        <el-table-column prop="created_at" label="创建时间" width="170" align="center" />
        <el-table-column label="操作" width="180" fixed="right" align="center">
          <template #default="{ row }">
            <div class="actions-cell">
              <el-button type="primary" text size="small" @click="editRequirement(row)">编辑</el-button>
              <el-button type="danger" text size="small" @click="deleteRequirement(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
        <template #empty>
          <span class="empty-text">暂无符合条件的的需求</span>
        </template>
      </el-table>

      <div class="requirement-management-page__pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="store.requirementTotal"
          :page-sizes="[15, 30, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          prev-text="上一页"
          next-text="下一页"
          @current-change="fetchRequirements"
        />
      </div>
    </section>

    <!-- 需求编辑对话框 -->
    <el-dialog v-model="showDialog" :title="editingRequirement ? '编辑需求' : '新建需求'" width="550px">
      <el-form :model="form" label-position="left" class="dialog-form">
        <el-form-item label="所属项目：" required>
          <el-select v-model="form.project_id" placeholder="选择项目" class="filter-control">
            <el-option v-for="p in store.projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="版本：">
          <el-select v-model="form.version_id" placeholder="选择版本" clearable class="filter-control">
            <el-option v-for="v in store.versions" :key="v.id" :label="v.name" :value="v.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="迭代：">
          <el-select v-model="form.iteration_id" placeholder="选择迭代" clearable class="filter-control">
            <el-option v-for="i in store.iterations" :key="i.id" :label="i.name" :value="i.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="需求标题：" required>
          <el-input v-model="form.title" placeholder="请输入需求标题" />
        </el-form-item>
        <el-form-item label="描述：">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="来源类型：">
          <el-select v-model="form.source_type" placeholder="来源类型" clearable class="filter-control">
            <el-option label="用户故事" value="user_story" />
            <el-option label="特性" value="feature" />
            <el-option label="缺陷" value="bug" />
            <el-option label="外部" value="external" />
          </el-select>
        </el-form-item>
        <el-form-item label="来源编号：">
          <el-input v-model="form.source_key" placeholder="如 JIRA-123" />
        </el-form-item>
        <el-form-item label="优先级：">
          <el-select v-model="form.priority" class="filter-control">
            <el-option label="P0" value="P0" />
            <el-option label="P1" value="P1" />
            <el-option label="P2" value="P2" />
            <el-option label="P3" value="P3" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态：">
          <el-select v-model="form.status" class="filter-control">
            <el-option label="打开" value="open" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已测试" value="tested" />
            <el-option label="已关闭" value="closed" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="closeDialog">取消</el-button>
        <el-button type="primary" @click="saveRequirement">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Plus, Search, RefreshLeft } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useQualityFoundationStore } from '@/stores/qualityFoundationStore'

const store = useQualityFoundationStore()

const filters = reactive({ project_id: null, version_id: null, iteration_id: null, status: '' })
const pagination = reactive({ page: 1, pageSize: 20 })

const showDialog = ref(false)
const editingRequirement = ref(null)
const form = reactive({
  project_id: null,
  version_id: null,
  iteration_id: null,
  title: '',
  description: '',
  source_type: '',
  source_key: '',
  priority: 'P2',
  status: 'open',
})

async function fetchRequirements() {
  await store.fetchRequirements(filters)
  if (filters.project_id) {
    await store.fetchRequirementCoverage({ project_id: filters.project_id })
  }
}

async function onProjectChange(projectId) {
  filters.version_id = null
  filters.iteration_id = null
  if (projectId) {
    await store.fetchVersions({ project_id: projectId })
  }
}

function resetFilters() {
  filters.project_id = null
  filters.version_id = null
  filters.iteration_id = null
  filters.status = ''
  store.versions = []
  store.iterations = []
  fetchRequirements()
}

function openCreateDialog() {
  editingRequirement.value = null
  Object.assign(form, { project_id: null, version_id: null, iteration_id: null, title: '', description: '', source_type: '', source_key: '', priority: 'P2', status: 'open' })
  showDialog.value = true
}

function editRequirement(row) {
  editingRequirement.value = row
  Object.assign(form, {
    project_id: row.project_id,
    version_id: row.version_id,
    iteration_id: row.iteration_id,
    title: row.title,
    description: row.description,
    source_type: row.source_type,
    source_key: row.source_key,
    priority: row.priority,
    status: row.status,
  })
  showDialog.value = true
}

async function saveRequirement() {
  if (!form.project_id || !form.title) {
    ElMessage.warning('请填写完整信息')
    return
  }
  if (editingRequirement.value) {
    await store.updateRequirement(editingRequirement.value.id, form)
    ElMessage.success('更新成功')
  } else {
    await store.createRequirement(form)
    ElMessage.success('创建成功')
  }
  closeDialog()
  fetchRequirements()
}

function closeDialog() {
  showDialog.value = false
  editingRequirement.value = null
}

async function deleteRequirement(row) {
  try {
    await ElMessageBox.confirm('确认删除该需求？', '提示', { type: 'warning' })
    await store.deleteRequirement(row.id)
    ElMessage.success('删除成功')
    fetchRequirements()
  } catch (e) {
    if (e !== 'cancel') throw e
  }
}

function formatSourceType(type) {
  const map = { user_story: '用户故事', feature: '特性', bug: '缺陷', external: '外部' }
  return map[type] || type || '-'
}

function getStatusType(status) {
  const map = { open: 'info', in_progress: 'warning', tested: 'success', closed: 'info' }
  return map[status] || 'info'
}

function getStatusLabel(status) {
  const map = { open: '打开', in_progress: '进行中', tested: '已测试', closed: '已关闭' }
  return map[status] || status
}

onMounted(async () => {
  await store.fetchProjects()
  fetchRequirements()
})
</script>

<style scoped>
@keyframes requirement-list-scan {
  from { transform: translateX(-24%); }
  to { transform: translateX(24%); }
}

@keyframes requirement-list-particles {
  from { transform: translate3d(0, 0, 0); }
  to { transform: translate3d(26px, -18px, 0); }
}

.requirement-management-page {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 10px;
  height: 100%;
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

.requirement-management-page::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 24%, rgba(56, 189, 248, 0.16) 44%, transparent 62%),
    repeating-linear-gradient(90deg, transparent 0 92px, rgba(56, 189, 248, 0.075) 92px 93px);
  content: "";
  animation: requirement-list-scan 14s linear infinite;
  z-index: 0;
}

.requirement-management-page::after {
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
  animation: requirement-list-particles 18s ease-in-out infinite alternate;
  z-index: 0;
}

.requirement-management-page__header {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-height: 56px;
  padding: 12px 16px;
  border: 1px solid rgba(56, 189, 248, 0.22);
  border-radius: var(--border-radius-base);
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.68), rgba(15, 23, 42, 0.42));
  box-shadow: 0 18px 48px rgba(2, 8, 23, 0.24), inset 0 1px 0 rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(18px) saturate(1.25);
}

.requirement-management-page__header h1 {
  margin: 0;
  color: var(--text-strong);
  font-size: 24px;
  line-height: 1.25;
}

.requirement-management-page__header p {
  margin: 4px 0 0;
  color: var(--text-secondary);
  font-size: 13px;
}

.requirement-management-page__coverage {
  position: relative;
  z-index: 1;
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  border: 1px solid rgba(56, 189, 248, 0.15);
  border-radius: var(--border-radius-base);
  background: rgba(15, 23, 42, 0.48);
  backdrop-filter: blur(12px);
}

.coverage-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px;
  border: 1px solid rgba(56, 189, 248, 0.12);
  border-radius: var(--border-radius-base);
  background: rgba(56, 189, 248, 0.06);
}

.coverage-value {
  font-size: 28px;
  font-weight: 700;
  color: #38bdf8;
}

.coverage-label {
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-secondary);
}

.requirement-management-page__filters {
  position: relative;
  z-index: 1;
  padding: 12px 16px;
  border: 1px solid rgba(56, 189, 248, 0.15);
  border-radius: var(--border-radius-base);
  background: rgba(15, 23, 42, 0.48);
  backdrop-filter: blur(12px);
}

.filter-form {
  position: relative;
  z-index: 1;
  width: 100%;
}

.filter-form__row {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  width: 100%;
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
  flex: 0 0 auto;
  align-items: flex-end;
}

.filter-item--project,
.filter-item--version,
.filter-item--iteration,
.filter-item--status {
  flex: 0 0 auto;
}

.filter-control {
  width: 180px;
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

.requirement-management-page__table {
  position: relative;
  z-index: 1;
  flex: 1;
  min-height: 0;
  padding: 12px 16px;
  border: 1px solid rgba(56, 189, 248, 0.15);
  border-radius: var(--border-radius-base);
  background: rgba(15, 23, 42, 0.48);
  backdrop-filter: blur(12px);
}

.requirement-management-page__table :deep(.el-table) {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(56, 189, 248, 0.08);
}

.requirement-management-page__pagination {
  display: flex;
  justify-content: flex-end;
  padding: 12px 0 0;
}

.dialog-form :deep(.el-form-item__label) {
  min-width: 90px;
}

.actions-cell {
  display: flex;
  justify-content: center;
  gap: 4px;
}

.empty-text {
  color: var(--text-secondary);
  font-size: 14px;
}

.requirement-title {
  cursor: pointer;
  color: #38bdf8;
}

.requirement-title:hover {
  text-decoration: underline;
}

.btn-primary-add {
  color: var(--text-inverse);
}

.priority-cell {
  font-weight: 600;
}

.priority-P0 { color: #ef4444; }
.priority-P1 { color: #f97316; }
.priority-P2 { color: #eab308; }
.priority-P3 { color: #22c55e; }

.text-secondary {
  color: var(--text-secondary);
}

/* ── 浅色主题 ── */
html:not(.dark) .requirement-management-page {
  background:
    linear-gradient(rgba(56, 189, 248, 0.095) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.085) 1px, transparent 1px),
    linear-gradient(145deg, rgba(34, 211, 166, 0.18), transparent 30%),
    linear-gradient(225deg, rgba(56, 189, 248, 0.22), transparent 36%),
    linear-gradient(0deg, rgba(22, 119, 255, 0.12), transparent 50%),
    var(--bg-page);
}

html:not(.dark) .requirement-management-page__header {
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.86), rgba(245, 250, 255, 0.68)),
    rgba(255, 255, 255, 0.72);
  box-shadow: 0 18px 46px rgba(20, 42, 76, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.82);
  border-color: rgba(22, 119, 255, 0.18);
}

html:not(.dark) .requirement-management-page__coverage {
  background:
    linear-gradient(rgba(22, 119, 255, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.04) 1px, transparent 1px),
    linear-gradient(145deg, rgba(255, 255, 255, 0.76), rgba(245, 250, 255, 0.58)),
    rgba(255, 255, 255, 0.62);
  background-size: 26px 26px, 26px 26px, auto, auto;
  border-color: rgba(22, 119, 255, 0.14);
}

html:not(.dark) .coverage-card {
  background: rgba(255, 255, 255, 0.6);
  border-color: rgba(22, 119, 255, 0.1);
}

html:not(.dark) .coverage-value {
  color: var(--color-primary);
}

html:not(.dark) .requirement-management-page__filters {
  background:
    linear-gradient(rgba(22, 119, 255, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.04) 1px, transparent 1px),
    linear-gradient(145deg, rgba(255, 255, 255, 0.76), rgba(245, 250, 255, 0.58)),
    rgba(255, 255, 255, 0.62);
  background-size: 26px 26px, 26px 26px, auto, auto;
  border-color: rgba(22, 119, 255, 0.14);
}

html:not(.dark) .requirement-management-page__table {
  background:
    linear-gradient(rgba(22, 119, 255, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.04) 1px, transparent 1px),
    linear-gradient(145deg, rgba(255, 255, 255, 0.76), rgba(245, 250, 255, 0.58)),
    rgba(255, 255, 255, 0.62);
  background-size: 32px 32px, 32px 32px, auto, auto;
  border-color: rgba(22, 119, 255, 0.14);
}

html:not(.dark) .requirement-management-page__table :deep(.el-table) {
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

html:not(.dark) .requirement-management-page__table :deep(.el-table__header th) {
  background: var(--el-table-header-bg-color) !important;
  background-color: var(--el-table-header-bg-color) !important;
  color: var(--text-secondary);
  font-weight: 700;
  font-size: 13px;
}

html:not(.dark) .requirement-management-page__table :deep(.el-table__body td) {
  background: var(--el-table-tr-bg-color) !important;
  background-color: var(--el-table-tr-bg-color) !important;
}

html:not(.dark) .requirement-management-page__table :deep(.el-table__body tr:nth-child(even) td.el-table__cell) {
  background: rgba(245, 250, 255, 0.5) !important;
  background-color: rgba(245, 250, 255, 0.5) !important;
}

html:not(.dark) .requirement-management-page__table :deep(.el-table__row:hover > td) {
  background: var(--el-table-row-hover-bg-color) !important;
  background-color: var(--el-table-row-hover-bg-color) !important;
}

html:not(.dark) .requirement-management-page__pagination {
  border-top-color: rgba(22, 119, 255, 0.12);
}

@media (prefers-reduced-motion: reduce) {
  .requirement-management-page::before,
  .requirement-management-page::after {
    animation: none;
  }
}
</style>
