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
      <el-form :model="draftFilters" label-position="left" class="filter-form">
        <div class="filter-form__row">
          <el-form-item label="项目：" class="filter-item filter-item--project">
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
          <el-form-item label="版本：" class="filter-item filter-item--version">
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
          <el-form-item label="迭代：" class="filter-item filter-item--iteration">
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
          <el-form-item label="状态：" class="filter-item filter-item--status">
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
          </el-form-item>
          <el-form-item label="关键词：" class="filter-item filter-item--keyword">
            <el-input
              v-model="draftFilters.keyword"
              placeholder="搜索场景名称"
              clearable
              class="search-bar__input"
              @keyup.enter="handleSearch"
            />
          </el-form-item>
          <div class="filter-actions">
            <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
            <el-button :icon="RefreshLeft" @click="handleReset">重置</el-button>
          </div>
        </div>
      </el-form>
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
        <el-divider content-position="left">归属信息</el-divider>
        <el-row :gutter="12">
          <el-col :span="8">
            <el-form-item label="项目">
              <el-select v-model="createForm.project_id" placeholder="请选择项目" clearable filterable @change="onCreateProjectChange">
                <el-option v-for="p in foundationProjects" :key="p.id" :label="p.name" :value="p.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="版本">
              <el-select v-model="createForm.version_id" placeholder="请选择版本" clearable filterable :disabled="!createForm.project_id" @change="onCreateVersionChange">
                <el-option v-for="v in foundationVersions" :key="v.id" :label="v.name" :value="v.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="迭代">
              <el-select v-model="createForm.iteration_id" placeholder="请选择迭代" clearable filterable :disabled="!createForm.version_id">
                <el-option v-for="i in foundationIterations" :key="i.id" :label="i.name" :value="i.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
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
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Search, RefreshLeft } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useScenarioStore } from '@/stores/scenarioStore'
import { useQualityFoundationStore } from '@/stores/qualityFoundationStore'

import ScenarioDetailDialog from './ScenarioDetailDialog.vue'

const router = useRouter()
const scenarioStore = useScenarioStore()
const foundationStore = useQualityFoundationStore()
const foundationProjects = computed(() => foundationStore.projects)
const foundationVersions = computed(() => foundationStore.versions)
const foundationIterations = computed(() => foundationStore.iterations)

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
  project_id: null,
  version_id: null,
  iteration_id: null,
})

const draftFilters = ref({
  projectId: null,
  versionId: null,
  iterationId: null,
  keyword: '',
  status: '',
})

const appliedFilters = ref({
  projectId: null,
  versionId: null,
  iterationId: null,
  keyword: '',
  status: '',
})

const pagination = ref({
  page: 1,
  pageSize: 15,
})

onMounted(() => {
  foundationStore.fetchProjects({ page: 1, page_size: 100 })
  scenarioStore.fetchScenarios({ page: 1, page_size: pagination.value.pageSize })
})

function onProjectChange(projectId) {
  draftFilters.value.versionId = null
  draftFilters.value.iterationId = null
  if (projectId) {
    foundationStore.fetchVersions({ project_id: projectId })
  }
}

function onVersionChange(versionId) {
  draftFilters.value.iterationId = null
  if (versionId) {
    foundationStore.fetchIterations({ project_id: draftFilters.value.projectId, version_id: versionId })
  }
}

function onCreateProjectChange(projectId) {
  createForm.value.version_id = null
  createForm.value.iteration_id = null
  if (projectId) {
    foundationStore.fetchVersions(projectId)
  } else {
    foundationStore.clearVersions()
    foundationStore.clearIterations()
  }
}

function onCreateVersionChange(versionId) {
  createForm.value.iteration_id = null
  if (versionId) {
    foundationStore.fetchIterations({ version_id: versionId })
  } else {
    foundationStore.clearIterations()
  }
}

function buildQueryParams() {
  const params = {
    page: pagination.value.page,
    page_size: pagination.value.pageSize,
  }
  if (appliedFilters.value.keyword) params.keyword = appliedFilters.value.keyword
  if (appliedFilters.value.status) params.status = appliedFilters.value.status
  if (appliedFilters.value.projectId) params.project_id = appliedFilters.value.projectId
  if (appliedFilters.value.versionId) params.version_id = appliedFilters.value.versionId
  if (appliedFilters.value.iterationId) params.iteration_id = appliedFilters.value.iterationId
  return params
}

function handleSearch() {
  appliedFilters.value = { ...draftFilters.value }
  pagination.value.page = 1
  scenarioStore.fetchScenarios(buildQueryParams())
}

function handleReset() {
  draftFilters.value = { projectId: null, versionId: null, iterationId: null, keyword: '', status: '' }
  appliedFilters.value = { projectId: null, versionId: null, iterationId: null, keyword: '', status: '' }
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
/* ── 动画关键帧 ── */
@keyframes scenario-list-scan {
  from { transform: translateX(-24%); }
  to { transform: translateX(24%); }
}

@keyframes scenario-list-particles {
  from { transform: translate3d(0, 0, 0); }
  to { transform: translate3d(26px, -18px, 0); }
}

@keyframes scenario-list-form-scan {
  from { transform: translateY(-8%); }
  to { transform: translateY(108%); }
}

@keyframes scenario-list-table-scan {
  from { transform: translateY(-6%); }
  to { transform: translateY(106%); }
}

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
    linear-gradient(rgba(56, 189, 248, 0.095) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.085) 1px, transparent 1px),
    linear-gradient(145deg, rgba(34, 211, 166, 0.18), transparent 30%),
    linear-gradient(225deg, rgba(56, 189, 248, 0.22), transparent 36%),
    linear-gradient(0deg, rgba(22, 119, 255, 0.12), transparent 50%),
    var(--bg-page);
  background-size: 28px 28px, 28px 28px, auto, auto, auto, auto;
  overflow: hidden;
  position: relative;
}

.scenario-list-page::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 24%, rgba(56, 189, 248, 0.16) 44%, transparent 62%),
    repeating-linear-gradient(90deg, transparent 0 92px, rgba(56, 189, 248, 0.075) 92px 93px);
  content: "";
  animation: scenario-list-scan 14s linear infinite;
}

.scenario-list-page::after {
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
  animation: scenario-list-particles 18s ease-in-out infinite alternate;
}

html:not(.dark) .scenario-list-page {
  background:
    linear-gradient(rgba(56, 189, 248, 0.095) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.085) 1px, transparent 1px),
    linear-gradient(145deg, rgba(34, 211, 166, 0.18), transparent 30%),
    linear-gradient(225deg, rgba(56, 189, 248, 0.22), transparent 36%),
    linear-gradient(0deg, rgba(22, 119, 255, 0.12), transparent 50%),
    var(--bg-page);
}

/* ── 标题区 ── */
.scenario-list-page__header {
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-height: 56px;
  padding: 12px 16px;
  border: 1px solid rgba(56, 189, 248, 0.22);
  border-radius: var(--border-radius-base);
  background:
    linear-gradient(135deg, rgba(15, 23, 42, 0.68), rgba(15, 23, 42, 0.42)),
    rgba(20, 22, 27, 0.48);
  box-shadow: 0 18px 48px rgba(2, 8, 23, 0.24), inset 0 1px 0 rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(18px) saturate(1.25);
  overflow: hidden;
  z-index: 1;
}

.scenario-list-page__header::after {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(90deg, rgba(56, 189, 248, 0.22), transparent 18% 82%, rgba(34, 211, 166, 0.18)),
    repeating-linear-gradient(90deg, transparent 0 42px, rgba(56, 189, 248, 0.06) 42px 43px);
  opacity: 0.65;
  content: "";
}

html:not(.dark) .scenario-list-page__header {
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.86), rgba(245, 250, 255, 0.68)),
    rgba(255, 255, 255, 0.72);
  box-shadow: 0 18px 46px rgba(20, 42, 76, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.82);
  border-color: rgba(22, 119, 255, 0.18);
}

.scenario-list-page__header h1,
.scenario-list-page__header p {
  margin: 0;
  position: relative;
  z-index: 1;
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

/* ── 查询区 ── */
.scenario-list-page__filters {
  position: relative;
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
  padding: 14px;
  border: 1px solid rgba(56, 189, 248, 0.18);
  border-radius: var(--border-radius-base);
  background:
    linear-gradient(rgba(56, 189, 248, 0.055) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.05) 1px, transparent 1px),
    linear-gradient(145deg, rgba(15, 23, 42, 0.54), rgba(15, 23, 42, 0.34)),
    rgba(20, 22, 27, 0.36);
  background-size: 26px 26px, 26px 26px, auto, auto;
  box-shadow: 0 18px 48px rgba(2, 8, 23, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(16px) saturate(1.2);
  overflow: hidden;
  z-index: 1;
}

.scenario-list-page__filters::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(56, 189, 248, 0.1) 50%, transparent 66%);
  opacity: 0.7;
  content: "";
  animation: scenario-list-form-scan 12s linear infinite;
}

html:not(.dark) .scenario-list-page__filters {
  background:
    linear-gradient(rgba(22, 119, 255, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.04) 1px, transparent 1px),
    linear-gradient(145deg, rgba(255, 255, 255, 0.76), rgba(245, 250, 255, 0.58)),
    rgba(255, 255, 255, 0.62);
  background-size: 26px 26px, 26px 26px, auto, auto;
  border-color: rgba(22, 119, 255, 0.14);
}

html:not(.dark) .scenario-list-page__filters::before {
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(22, 119, 255, 0.08) 50%, transparent 66%);
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

.search-bar__input {
  width: 280px;
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
  position: relative;
  display: flex;
  flex: 1;
  min-height: 0;
  flex-direction: column;
  border: 1px solid rgba(56, 189, 248, 0.18);
  border-radius: var(--border-radius-base);
  background:
    linear-gradient(rgba(56, 189, 248, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.045) 1px, transparent 1px),
    linear-gradient(145deg, rgba(15, 23, 42, 0.54), rgba(15, 23, 42, 0.34)),
    rgba(20, 22, 27, 0.36);
  background-size: 32px 32px, 32px 32px, auto, auto;
  box-shadow: 0 18px 48px rgba(2, 8, 23, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(16px) saturate(1.2);
  overflow: hidden;
  z-index: 1;
}

.scenario-list-page__table::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(56, 189, 248, 0.12) 50%, transparent 66%),
    radial-gradient(circle at 88% 16%, rgba(34, 211, 166, 0.14), transparent 26%);
  opacity: 0.8;
  content: "";
  animation: scenario-list-table-scan 12s linear infinite;
}

html:not(.dark) .scenario-list-page__table {
  background:
    linear-gradient(rgba(22, 119, 255, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.04) 1px, transparent 1px),
    linear-gradient(145deg, rgba(255, 255, 255, 0.76), rgba(245, 250, 255, 0.58)),
    rgba(255, 255, 255, 0.62);
  background-size: 32px 32px, 32px 32px, auto, auto;
  border-color: rgba(22, 119, 255, 0.14);
}

html:not(.dark) .scenario-list-page__table::before {
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(22, 119, 255, 0.1) 50%, transparent 66%);
}

.scenario-list-page__table :deep(.el-table) {
  flex: 1;
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: rgba(8, 18, 32, 0.34);
  --el-table-header-bg-color: rgba(15, 31, 52, 0.46);
  --el-table-row-hover-bg-color: var(--color-primary-soft);
  --el-table-expanded-cell-bg-color: rgba(8, 18, 32, 0.42);
  position: relative;
  z-index: 1;
  background:
    linear-gradient(rgba(56, 189, 248, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.03) 1px, transparent 1px),
    rgba(8, 18, 32, 0.32);
  background-size: 28px 28px, 28px 28px, auto;
}

html:not(.dark) .scenario-list-page__table :deep(.el-table) {
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

.scenario-list-page__table :deep(.el-table__inner-wrapper::before) {
  background: rgba(56, 189, 248, 0.12);
}

.scenario-list-page__table :deep(.el-table__body-wrapper),
.scenario-list-page__table :deep(.el-table__header-wrapper),
.scenario-list-page__table :deep(.el-scrollbar__view) {
  background: transparent;
}

.scenario-list-page__table :deep(.el-table__header th) {
  height: 44px;
  background: var(--el-table-header-bg-color) !important;
  background-color: var(--el-table-header-bg-color) !important;
  color: var(--text-secondary);
  font-weight: 700;
  font-size: 13px;
}

.scenario-list-page__table :deep(.el-table .cell) {
  padding: 0 10px;
}

.scenario-list-page__table :deep(.el-table__body td) {
  height: 48px;
  background: var(--el-table-tr-bg-color) !important;
  background-color: var(--el-table-tr-bg-color) !important;
}

.scenario-list-page__table :deep(.el-table__body tr:nth-child(even) td.el-table__cell) {
  background: rgba(15, 31, 52, 0.28) !important;
  background-color: rgba(15, 31, 52, 0.28) !important;
}

html:not(.dark) .scenario-list-page__table :deep(.el-table__body tr:nth-child(even) td.el-table__cell) {
  background: rgba(245, 250, 255, 0.5) !important;
  background-color: rgba(245, 250, 255, 0.5) !important;
}

.scenario-list-page__table :deep(.el-table__row:hover > td) {
  background: var(--el-table-row-hover-bg-color) !important;
  background-color: var(--el-table-row-hover-bg-color) !important;
}

.scenario-list-page__table :deep(.el-table__row:hover > td.el-table-fixed-column--right),
.scenario-list-page__table :deep(.el-table__row:hover > td.el-table-fixed-column--left) {
  background: var(--el-table-row-hover-bg-color) !important;
  background-color: var(--el-table-row-hover-bg-color) !important;
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
  border-top: 1px solid rgba(56, 189, 248, 0.12);
}

html:not(.dark) .scenario-list-page__pagination {
  border-top-color: rgba(22, 119, 255, 0.12);
}

@media (prefers-reduced-motion: reduce) {
  .scenario-list-page::before,
  .scenario-list-page::after,
  .scenario-list-page__header::after,
  .scenario-list-page__filters::before,
  .scenario-list-page__table::before {
    animation: none;
  }
}
</style>
