<template>
  <div class="test-plan-page">
    <!-- 标题区 -->
    <header class="page-header">
      <div>
        <h1>测试计划</h1>
        <p>管理测试计划、套件和批量执行</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" :icon="Plus" class="btn-primary-add" @click="openCreateDialog">新建计划</el-button>
      </div>
    </header>

    <!-- 主体 -->
    <div class="page-body">
      <!-- 查询栏 -->
      <div class="filter-bar">
        <el-form :model="filters" label-position="left" class="filter-form">
          <div class="filter-form__row">
            <el-form-item label="关键词：" class="filter-item filter-item--keyword">
              <el-input v-model="filters.keyword" placeholder="搜索计划名称" clearable class="filter-control" @keyup.enter="handleSearch" />
            </el-form-item>
            <el-form-item label="状态：" class="filter-item filter-item--status">
              <el-select v-model="filters.status" placeholder="全部" clearable class="filter-control">
                <el-option label="草稿" value="draft" />
                <el-option label="激活" value="active" />
                <el-option label="归档" value="archived" />
              </el-select>
            </el-form-item>
            <el-form-item label="项目：" class="filter-item filter-item--status">
              <el-select v-model="filters.project_id" placeholder="全部项目" clearable filterable class="filter-control" @change="onProjectFilterChange">
                <el-option v-for="p in foundationStore.projects" :key="p.id" :label="p.name" :value="p.id" />
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
        <el-table v-loading="store.loading" :data="store.plans" height="100%" highlight-current-row>
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="name" label="计划名称" min-width="160" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="plan-name" @click="openDetail(row)">{{ row.name }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
          <el-table-column prop="status" label="状态" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)" size="small">
                {{ getStatusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="suites" label="套件数" width="80" align="center">
            <template #default="{ row }">
              <span>{{ row.suites?.length || 0 }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right" align="center">
            <template #default="{ row }">
              <div class="actions-cell">
                <el-button type="primary" text size="small" @click="openDetail(row)">详情</el-button>
                <el-button type="primary" text size="small" @click="handleRun(row)">执行</el-button>
                <el-button type="danger" text size="small" @click="handleDelete(row)">删除</el-button>
              </div>
            </template>
          </el-table-column>
          <template #empty>
            <span class="empty-text">暂无测试计划</span>
          </template>
        </el-table>

        <div class="pagination-bar">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.pageSize"
            :total="store.total"
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

    <!-- 新建/编辑弹窗 -->
    <el-dialog v-model="showDialog" :title="editingPlan ? '编辑计划' : '新建测试计划'" width="500px" destroy-on-close>
      <el-form :model="planForm" label-width="80px">
        <el-form-item label="计划名称" required>
          <el-input v-model="planForm.name" placeholder="请输入计划名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="planForm.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="项目">
          <el-select v-model="planForm.project_id" placeholder="请选择项目" clearable filterable class="filter-control" @change="onFormProjectChange">
            <el-option v-for="p in foundationStore.projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="版本">
          <el-select v-model="planForm.version_id" placeholder="请选择版本" clearable filterable class="filter-control" :disabled="!planForm.project_id" @change="onFormVersionChange">
            <el-option v-for="v in foundationStore.versions" :key="v.id" :label="v.name" :value="v.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="迭代">
          <el-select v-model="planForm.iteration_id" placeholder="请选择迭代" clearable filterable class="filter-control" :disabled="!planForm.version_id">
            <el-option v-for="i in foundationStore.iterations" :key="i.id" :label="i.name" :value="i.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="planForm.status" class="filter-control">
            <el-option label="草稿" value="draft" />
            <el-option label="激活" value="active" />
            <el-option label="归档" value="archived" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { Plus, Search, RefreshLeft } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { useTestPlanStore } from '@/stores/testPlanStore'
import { useQualityFoundationStore } from '@/stores/qualityFoundationStore'

const router = useRouter()
const store = useTestPlanStore()
const foundationStore = useQualityFoundationStore()

const filters = reactive({ keyword: '', status: '', project_id: null })
const pagination = reactive({ page: 1, pageSize: 15 })
const showDialog = ref(false)
const editingPlan = ref(null)
const saving = ref(false)
const planForm = reactive({ name: '', description: '', status: 'draft', project_id: null, version_id: null, iteration_id: null })

function getStatusType(status) {
  const map = { draft: 'info', active: 'success', archived: 'warning' }
  return map[status] || 'info'
}

function getStatusLabel(status) {
  const map = { draft: '草稿', active: '激活', archived: '归档' }
  return map[status] || status
}

function onFormProjectChange(projectId) {
  planForm.version_id = null
  planForm.iteration_id = null
  if (projectId) {
    foundationStore.fetchVersions({ project_id: projectId })
  } else {
    foundationStore.clearVersions()
    foundationStore.clearIterations()
  }
}

function onFormVersionChange(versionId) {
  planForm.iteration_id = null
  if (versionId) {
    foundationStore.fetchIterations({ version_id: versionId })
  } else {
    foundationStore.clearIterations()
  }
}

async function fetchPlans() {
  await store.fetchPlans({
    page: pagination.page,
    page_size: pagination.pageSize,
    keyword: filters.keyword || undefined,
    status: filters.status || undefined,
    project_id: filters.project_id || undefined,
  })
}

function onProjectFilterChange() {
  pagination.page = 1
  fetchPlans()
}

function handleSearch() {
  pagination.page = 1
  fetchPlans()
}

function handleReset() {
  filters.keyword = ''
  filters.status = ''
  filters.project_id = null
  pagination.page = 1
  fetchPlans()
}

function handlePageChange() {
  fetchPlans()
}

function handleSizeChange(size) {
  pagination.pageSize = size
  fetchPlans()
}

function openCreateDialog() {
  editingPlan.value = null
  Object.assign(planForm, { name: '', description: '', status: 'draft', project_id: null, version_id: null, iteration_id: null })
  if (!foundationStore.projects.length) foundationStore.fetchProjects()
  showDialog.value = true
}

function openDetail(plan) {
  router.push({ name: 'TestPlanDetail', params: { id: plan.id } })
}

async function handleSave() {
  if (!planForm.name) {
    ElMessage.warning('请输入计划名称')
    return
  }
  saving.value = true
  try {
    if (editingPlan.value) {
      await store.updatePlan(editingPlan.value.id, { ...planForm })
      ElMessage.success('更新成功')
    } else {
      await store.createPlan({ ...planForm })
      ElMessage.success('创建成功')
    }
    showDialog.value = false
    fetchPlans()
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function handleRun(plan) {
  try {
    const result = await store.runPlan(plan.id)
    ElMessage.success(`执行已开始: ${result.id}`)
    router.push({ name: 'TestPlanRuns' })
  } catch (e) {
    ElMessage.error('执行失败')
  }
}

async function handleDelete(plan) {
  try {
    await ElMessageBox.confirm(`确定要删除计划「${plan.name}」吗？`, '删除确认', { type: 'warning' })
    await store.deletePlan(plan.id)
    ElMessage.success('删除成功')
    fetchPlans()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

onMounted(() => {
  foundationStore.fetchProjects()
  fetchPlans()
})
</script>

<style scoped>
.test-plan-page {
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

.filter-item--keyword {
  flex: 0 0 280px;
}

.filter-item--status {
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

.plan-name {
  cursor: pointer;
  color: var(--el-color-primary);
  font-weight: 600;
}

.plan-name:hover {
  text-decoration: underline;
}

.actions-cell {
  display: inline-flex;
  gap: 4px;
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
</style>