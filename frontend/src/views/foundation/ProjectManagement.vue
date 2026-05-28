<template>
  <div class="foundation-projects-page">
    <div class="foundation-projects-page__ambient" aria-hidden="true">
      <div class="circuit-a"><span>PROJ</span><i></i><span>VER</span><i></i><span>ITER</span></div>
      <div class="circuit-b"><span>REQ</span><i></i><span>TEST</span></div>
    </div>
    <header class="foundation-projects-page__header">
      <div>
        <h1>项目版本管理</h1>
        <p>管理质量测试的项目、版本和迭代结构。</p>
      </div>
      <el-button type="primary" :icon="Plus" class="btn-primary-add" @click="showProjectDialog = true">新建项目</el-button>
    </header>

    <!-- 查询区 -->
    <section class="foundation-projects-page__filters">
      <el-form :inline="false" :model="filters" label-position="left" class="filter-form">
        <el-row :gutter="12">
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="项目名称：" class="filter-item">
              <el-input v-model="filters.name" placeholder="项目名称" clearable class="search-bar__input" @keyup.enter="fetchProjects" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="状态：" class="filter-item">
              <el-select v-model="filters.status" placeholder="状态" clearable class="filter-control">
                <el-option label="激活" value="active" />
                <el-option label="归档" value="archived" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="10">
            <div class="filter-actions">
              <el-button type="primary" :icon="Search" @click="fetchProjects">查询</el-button>
              <el-button :icon="RefreshLeft" @click="resetFilters">重置</el-button>
            </div>
          </el-col>
        </el-row>
      </el-form>
    </section>

    <!-- 数据列表 -->
    <section class="foundation-projects-page__table">
      <el-table v-loading="store.loading" :data="store.projects" height="100%" highlight-current-row>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="项目名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="code" label="项目代码" width="150" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">{{ row.status === 'active' ? '激活' : '归档' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" align="center" />
        <el-table-column label="操作" width="320" fixed="right" align="center">
          <template #default="{ row }">
            <div class="actions-cell">
              <el-button type="primary" text size="small" @click="openVersionDialog(row)">版本</el-button>
              <el-button type="primary" text size="small" @click="editProject(row)">编辑</el-button>
              <el-button type="danger" text size="small" @click="deleteProject(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
        <template #empty>
          <span class="empty-text">暂无符合条件的项目</span>
        </template>
      </el-table>

      <div class="foundation-projects-page__pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="store.projectTotal"
          :page-sizes="[15, 30, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          prev-text="上一页"
          next-text="下一页"
          @current-change="fetchProjects"
          @size-change="fetchProjects"
        />
      </div>
    </section>

    <!-- 项目编辑对话框 -->
    <el-dialog v-model="showProjectDialog" :title="editingProject ? '编辑项目' : '新建项目'" width="500px">
      <el-form :model="projectForm" label-position="left" class="dialog-form">
        <el-form-item label="项目名称：" required>
          <el-input v-model="projectForm.name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="项目代码：" required>
          <el-input v-model="projectForm.code" placeholder="请输入项目代码" :disabled="!!editingProject" />
        </el-form-item>
        <el-form-item label="描述：">
          <el-input v-model="projectForm.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="状态：">
          <el-select v-model="projectForm.status" class="filter-control">
            <el-option label="激活" value="active" />
            <el-option label="归档" value="archived" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="closeProjectDialog">取消</el-button>
        <el-button type="primary" @click="saveProject">保存</el-button>
      </template>
    </el-dialog>

    <!-- 版本对话框 -->
    <el-dialog v-model="showVersionDialog" :title="`版本管理 - ${currentProject?.name}`" width="650px">
      <div class="version-section">
        <div class="version-section__header">
          <span>版本列表</span>
          <el-button type="primary" size="small" @click="showVersionForm = true">新建版本</el-button>
        </div>
        <el-form v-if="showVersionForm" :model="versionForm" inline class="version-form">
          <el-form-item label="版本名称：">
            <el-input v-model="versionForm.name" placeholder="版本名称" />
          </el-form-item>
          <el-form-item label="版本代码：">
            <el-input v-model="versionForm.code" placeholder="版本代码" />
          </el-form-item>
          <el-form-item label="状态：">
            <el-select v-model="versionForm.status" class="filter-control">
              <el-option label="规划中" value="planning" />
              <el-option label="开发中" value="development" />
              <el-option label="测试中" value="testing" />
              <el-option label="已发布" value="released" />
              <el-option label="归档" value="archived" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" size="small" @click="saveVersion">保存</el-button>
            <el-button size="small" @click="cancelVersionForm">取消</el-button>
          </el-form-item>
        </el-form>
        <el-table :data="store.versions" height="200" size="small">
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="name" label="版本名称" min-width="120" />
          <el-table-column prop="code" label="版本代码" width="120" />
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag size="small">{{ formatVersionStatus(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180" align="center">
            <template #default="{ row }">
              <div class="actions-cell">
                <el-button type="primary" text size="small" @click="openIterationDialog(row)">迭代</el-button>
                <el-button type="danger" text size="small" @click="deleteVersion(row)">删除</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>

    <!-- 迭代对话框 -->
    <el-dialog v-model="showIterationDialog" :title="`迭代管理 - ${currentVersion?.name}`" width="600px">
      <div class="iteration-section">
        <div class="iteration-section__header">
          <span>迭代列表</span>
          <el-button type="primary" size="small" @click="showIterationForm = true">新建迭代</el-button>
        </div>
        <el-form v-if="showIterationForm" :model="iterationForm" inline class="version-form">
          <el-form-item label="迭代名称：">
            <el-input v-model="iterationForm.name" placeholder="迭代名称" />
          </el-form-item>
          <el-form-item label="状态：">
            <el-select v-model="iterationForm.status" class="filter-control">
              <el-option label="规划中" value="planning" />
              <el-option label="进行中" value="running" />
              <el-option label="已完成" value="completed" />
              <el-option label="已取消" value="cancelled" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" size="small" @click="saveIteration">保存</el-button>
            <el-button size="small" @click="cancelIterationForm">取消</el-button>
          </el-form-item>
        </el-form>
        <el-table :data="store.iterations" height="200" size="small">
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="name" label="迭代名称" min-width="140" />
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag size="small">{{ formatIterationStatus(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" align="center">
            <template #default="{ row }">
              <el-button type="danger" text size="small" @click="deleteIteration(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { Plus, Search, RefreshLeft } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useQualityFoundationStore } from '@/stores/qualityFoundationStore'

const store = useQualityFoundationStore()

const filters = reactive({ name: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 15 })

const showProjectDialog = ref(false)
const editingProject = ref(null)
const projectForm = reactive({ name: '', code: '', description: '', status: 'active' })

const showVersionDialog = ref(false)
const currentProject = ref(null)
const showVersionForm = ref(false)
const versionForm = reactive({ name: '', code: '', status: 'planning' })

const showIterationDialog = ref(false)
const currentVersion = ref(null)
const showIterationForm = ref(false)
const iterationForm = reactive({ name: '', status: 'planning' })

async function fetchProjects() {
  await store.fetchProjects({ page: pagination.page, page_size: pagination.pageSize, keyword: filters.name, status: filters.status })
}

function resetFilters() {
  filters.name = ''
  filters.status = ''
  pagination.page = 1
  fetchProjects()
}

function editProject(row) {
  editingProject.value = row
  Object.assign(projectForm, { name: row.name, code: row.code, description: row.description, status: row.status })
  showProjectDialog.value = true
}

async function saveProject() {
  if (!projectForm.name || !projectForm.code) {
    ElMessage.warning('请填写完整信息')
    return
  }
  if (editingProject.value) {
    await store.updateProject(editingProject.value.id, projectForm)
    ElMessage.success('更新成功')
  } else {
    await store.createProject(projectForm)
    ElMessage.success('创建成功')
  }
  closeProjectDialog()
  fetchProjects()
}

function closeProjectDialog() {
  showProjectDialog.value = false
  editingProject.value = null
  Object.assign(projectForm, { name: '', code: '', description: '', status: 'active' })
}

async function deleteProject(row) {
  try {
    await ElMessageBox.confirm('确认删除该项目？', '提示', { type: 'warning' })
    await store.deleteProject(row.id)
    ElMessage.success('删除成功')
    fetchProjects()
  } catch (e) {
    if (e !== 'cancel') {
      if (e.response?.data?.detail) ElMessage.error(e.response.data.detail)
      else throw e
    }
  }
}

async function openVersionDialog(row) {
  currentProject.value = row
  showVersionDialog.value = true
  showVersionForm.value = false
  await store.fetchVersions({ project_id: row.id })
}

async function saveVersion() {
  if (!versionForm.name || !versionForm.code) {
    ElMessage.warning('请填写完整信息')
    return
  }
  await store.createVersion({ project_id: currentProject.value.id, ...versionForm })
  ElMessage.success('创建成功')
  cancelVersionForm()
  await store.fetchVersions({ project_id: currentProject.value.id })
}

function cancelVersionForm() {
  showVersionForm.value = false
  Object.assign(versionForm, { name: '', code: '', status: 'planning' })
}

async function deleteVersion(row) {
  try {
    await ElMessageBox.confirm('确认删除该版本？', '提示', { type: 'warning' })
    await store.deleteVersion(row.id)
    ElMessage.success('删除成功')
    await store.fetchVersions({ project_id: currentProject.value.id })
  } catch (e) {
    if (e !== 'cancel') {
      if (e.response?.data?.detail) ElMessage.error(e.response.data.detail)
      else throw e
    }
  }
}

async function openIterationDialog(row) {
  currentVersion.value = row
  showIterationDialog.value = true
  showIterationForm.value = false
  await store.fetchIterations({ project_id: currentProject.value.id, version_id: row.id })
}

async function saveIteration() {
  if (!iterationForm.name) {
    ElMessage.warning('请填写迭代名称')
    return
  }
  await store.createIteration({ project_id: currentProject.value.id, version_id: currentVersion.value.id, ...iterationForm })
  ElMessage.success('创建成功')
  cancelIterationForm()
  await store.fetchIterations({ project_id: currentProject.value.id, version_id: currentVersion.value.id })
}

function cancelIterationForm() {
  showIterationForm.value = false
  Object.assign(iterationForm, { name: '', status: 'planning' })
}

async function deleteIteration(row) {
  try {
    await ElMessageBox.confirm('确认删除该迭代？', '提示', { type: 'warning' })
    await store.deleteIteration(row.id)
    ElMessage.success('删除成功')
    await store.fetchIterations({ project_id: currentProject.value.id, version_id: currentVersion.value.id })
  } catch (e) {
    if (e !== 'cancel') {
      if (e.response?.data?.detail) ElMessage.error(e.response.data.detail)
      else throw e
    }
  }
}

function formatVersionStatus(status) {
  const map = { planning: '规划中', development: '开发中', testing: '测试中', released: '已发布', archived: '归档' }
  return map[status] || status
}

function formatIterationStatus(status) {
  const map = { planning: '规划中', running: '进行中', completed: '已完成', cancelled: '已取消' }
  return map[status] || status
}

fetchProjects()
</script>

<style scoped>
@keyframes flow-a {
  0%, 100% { transform: translate3d(0, 0, 0); opacity: 0.3; }
  50% { transform: translate3d(-24px, 8px, 0); opacity: 0.46; }
}

@keyframes flow-b {
  0%, 100% { transform: translate3d(0, 0, 0) scale(0.9); opacity: 0.2; }
  50% { transform: translate3d(28px, -8px, 0) scale(0.9); opacity: 0.32; }
}

.foundation-projects-page {
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

.foundation-projects-page__ambient {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}

.circuit-a, .circuit-b {
  position: absolute;
  display: inline-grid;
  grid-auto-flow: column;
  gap: 12px;
  align-items: center;
  padding: 8px 12px;
  border: 1px solid rgba(56, 189, 248, 0.2);
  border-radius: var(--border-radius-base);
  color: rgba(125, 211, 252, 0.68);
  background: rgba(15, 23, 42, 0.28);
  box-shadow: 0 0 24px rgba(56, 189, 248, 0.08);
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

.circuit-a { top: 80px; right: 6%; animation: flow-a 16s ease-in-out infinite; }
.circuit-b { bottom: 12%; left: 6%; opacity: 0.46; animation: flow-b 20s ease-in-out infinite; }

.circuit-a span::before, .circuit-b span::before {
  width: 6px; height: 6px; margin-right: 6px; border-radius: 50%;
  background: currentColor; box-shadow: 0 0 12px currentColor; content: "";
}

.circuit-a i, .circuit-b i {
  position: relative; width: 54px; height: 1px;
  background: linear-gradient(90deg, currentColor, transparent);
}

.foundation-projects-page__header {
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

.foundation-projects-page__filters {
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

.filter-form :deep(.el-row) {
  align-items: flex-end;
  row-gap: 8px;
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
  align-items: flex-end;
  margin-bottom: 0;
  width: 100%;
}

.filter-control {
  width: 100%;
}

.search-bar__input :deep(.el-input) {
  width: 280px;
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

.foundation-projects-page__table {
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

.foundation-projects-page__table :deep(.el-table) {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(56, 189, 248, 0.08);
}

.foundation-projects-page__pagination {
  display: flex;
  justify-content: flex-end;
  padding: 10px 16px;
  border-top: 1px solid var(--border-color-lighter);
}

.foundation-projects-page__header h1 {
  margin: 0;
  color: var(--text-strong);
  font-size: 24px;
  line-height: 1.25;
}

.foundation-projects-page__header p {
  margin: 4px 0 0;
  color: var(--text-secondary);
  font-size: 13px;
}

.dialog-form :deep(.el-form-item__label) { min-width: 90px; }

.version-section__header, .iteration-section__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-weight: 600;
  color: var(--text-strong);
}

.version-form, .iteration-form {
  margin-bottom: 12px;
  padding: 12px;
  border: 1px solid rgba(56, 189, 248, 0.15);
  border-radius: var(--border-radius-base);
  background: rgba(15, 23, 42, 0.32);
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

.btn-primary-add {
  position: relative;
  z-index: 1;
  border: 0;
  background: var(--brand-gradient);
  color: var(--text-inverse);
  font-weight: 700;
  transition: transform 0.2s ease, filter 0.2s ease;
}

.btn-primary-add:hover {
  filter: brightness(1.1);
  transform: translateY(-1px);
}

/* ── 浅色主题 ── */
html:not(.dark) .foundation-projects-page__ambient .circuit-a,
html:not(.dark) .foundation-projects-page__ambient .circuit-b {
  border-color: rgba(22, 119, 255, 0.18);
  color: rgba(22, 119, 255, 0.55);
  background: rgba(255, 255, 255, 0.72);
  box-shadow: 0 0 24px rgba(22, 119, 255, 0.08);
}

html:not(.dark) .foundation-projects-page__header {
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.86), rgba(245, 250, 255, 0.68)),
    rgba(255, 255, 255, 0.72);
  box-shadow: 0 18px 46px rgba(20, 42, 76, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.82);
  border-color: rgba(22, 119, 255, 0.18);
}

html:not(.dark) .foundation-projects-page__filters {
  background:
    linear-gradient(rgba(22, 119, 255, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.04) 1px, transparent 1px),
    linear-gradient(145deg, rgba(255, 255, 255, 0.76), rgba(245, 250, 255, 0.58)),
    rgba(255, 255, 255, 0.62);
  background-size: 26px 26px, 26px 26px, auto, auto;
  border-color: rgba(22, 119, 255, 0.14);
}

html:not(.dark) .foundation-projects-page__table {
  background:
    linear-gradient(rgba(22, 119, 255, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.04) 1px, transparent 1px),
    linear-gradient(145deg, rgba(255, 255, 255, 0.76), rgba(245, 250, 255, 0.58)),
    rgba(255, 255, 255, 0.62);
  background-size: 32px 32px, 32px 32px, auto, auto;
  border-color: rgba(22, 119, 255, 0.14);
}

html:not(.dark) .foundation-projects-page__table :deep(.el-table) {
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

html:not(.dark) .foundation-projects-page__table :deep(.el-table__header th) {
  background: var(--el-table-header-bg-color) !important;
  background-color: var(--el-table-header-bg-color) !important;
  color: var(--text-secondary);
  font-weight: 700;
  font-size: 13px;
}

html:not(.dark) .foundation-projects-page__table :deep(.el-table__body td) {
  background: var(--el-table-tr-bg-color) !important;
  background-color: var(--el-table-tr-bg-color) !important;
}

html:not(.dark) .foundation-projects-page__table :deep(.el-table__body tr:nth-child(even) td.el-table__cell) {
  background: rgba(245, 250, 255, 0.5) !important;
  background-color: rgba(245, 250, 255, 0.5) !important;
}

html:not(.dark) .foundation-projects-page__table :deep(.el-table__row:hover > td) {
  background: var(--el-table-row-hover-bg-color) !important;
  background-color: var(--el-table-row-hover-bg-color) !important;
}

html:not(.dark) .foundation-projects-page__pagination {
  border-top-color: rgba(22, 119, 255, 0.12);
}

html:not(.dark) .version-form,
html:not(.dark) .iteration-form {
  background: rgba(255, 255, 255, 0.6);
  border-color: rgba(22, 119, 255, 0.14);
}
</style>
