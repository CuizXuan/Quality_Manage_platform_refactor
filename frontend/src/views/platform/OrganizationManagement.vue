<template>
  <div class="organization-management">
    <!-- 页面标题区 -->
    <header class="organization-management__header">
      <div>
        <h1>组织管理</h1>
        <p>统一管理多组织架构，支持增删改查与状态控制。</p>
      </div>
      <el-button type="primary" class="btn-primary-add" :icon="Plus" @click="openCreate">新建组织</el-button>
    </header>

    <!-- 查询区 -->
    <section class="organization-management__filters">
      <div class="filter-row">
        <el-input
          v-model="draftFilters.keyword"
          placeholder="搜索组织名称/编码"
          clearable
          class="search-bar__input"
          @keyup.enter="handleSearch"
        />
        <el-select
          v-model="draftFilters.status"
          placeholder="全部状态"
          clearable
          class="filter-control"
        >
          <el-option label="启用" value="active" />
          <el-option label="停用" value="disabled" />
        </el-select>
        <div class="filter-actions">
          <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
          <el-button :icon="RefreshLeft" @click="handleReset">重置</el-button>
        </div>
      </div>
    </section>

    <!-- 数据列表 -->
    <section class="organization-management__table">
      <el-table v-loading="loading" :data="pagedOrgs" border height="100%">
        <el-table-column prop="name" label="组织名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="code" label="组织编码" min-width="140" show-overflow-tooltip />
        <el-table-column label="描述" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">{{ row.description || '—' }}</template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="80" align="center" />
        <el-table-column prop="status" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
              {{ row.status === 'active' ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right" align="center">
          <template #default="{ row }">
            <div class="actions-cell">
              <el-button type="primary" text size="small" @click.stop="openEdit(row)">编辑</el-button>
              <el-button type="danger" text size="small" @click.stop="removeOrg(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
        <template #empty>
          <span class="empty-text">暂无符合条件的组织</span>
        </template>
      </el-table>

      <div class="organization-management__pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="total"
          :page-sizes="[15, 30, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          prev-text="上一页"
          next-text="下一页"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </section>

    <!-- 新建/编辑组织弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="form.id ? '编辑组织' : '新建组织'"
      top="4vh"
      width="min(520px, 92vw)"
      destroy-on-close
      append-to-body
    >
      <el-form :model="form" label-width="90px" class="org-form">
        <el-form-item label="组织名称" required>
          <el-input v-model="form.name" placeholder="请输入组织名称" />
        </el-form-item>
        <el-form-item label="组织编码" required>
          <el-input v-model="form.code" :disabled="!!form.id" placeholder="请输入组织编码" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" class="full-width" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio value="active">启用</el-radio>
            <el-radio value="disabled">停用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveOrg">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { Plus, Search, RefreshLeft } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { systemApi } from '@/api/system'

const loading = ref(false)
const saving = ref(false)
const orgs = ref([])
const dialogVisible = ref(false)

const draftFilters = ref({ keyword: '', status: '' })
const appliedFilters = ref({ keyword: '', status: '' })
const pagination = ref({ page: 1, pageSize: 15 })
const total = ref(0)

const form = reactive(defaultForm())

const pagedOrgs = computed(() => {
  const start = (pagination.value.page - 1) * pagination.value.pageSize
  return orgs.value.slice(start, start + pagination.value.pageSize)
})

function defaultForm() {
  return { id: null, name: '', code: '', description: '', sort_order: 0, status: 'active' }
}

function buildQueryParams() {
  return {
    page: pagination.value.page,
    page_size: pagination.value.pageSize,
    ...(appliedFilters.value.keyword && { keyword: appliedFilters.value.keyword }),
    ...(appliedFilters.value.status && { status: appliedFilters.value.status }),
  }
}

async function fetchOrgs() {
  loading.value = true
  try {
    const res = await systemApi.organizations.list(buildQueryParams())
    orgs.value = res.data.items || res.data || []
    total.value = res.data.total || orgs.value.length
  } catch {
    ElMessage.error('获取组织列表失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  appliedFilters.value = { ...draftFilters.value }
  pagination.value.page = 1
  fetchOrgs()
}

function handleReset() {
  draftFilters.value = { keyword: '', status: '' }
  appliedFilters.value = { keyword: '', status: '' }
  pagination.value.page = 1
  fetchOrgs()
}

function handlePageChange(p) {
  pagination.value.page = p
  fetchOrgs()
}

function handleSizeChange(s) {
  pagination.value.pageSize = s
  pagination.value.page = 1
  fetchOrgs()
}

function openCreate() {
  resetForm()
  dialogVisible.value = true
}

function openEdit(item) {
  resetForm({ ...item })
  dialogVisible.value = true
}

function resetForm(data = {}) {
  Object.keys(form).forEach(key => { form[key] = defaultForm()[key] })
  Object.assign(form, defaultForm(), data)
}

async function saveOrg() {
  if (!form.name || !form.code) {
    ElMessage.warning('请填写组织名称和编码')
    return
  }
  saving.value = true
  try {
    const payload = { ...form }
    if (payload.id) {
      await systemApi.organizations.update(payload.id, payload)
    } else {
      delete payload.id
      await systemApi.organizations.create(payload)
    }
    dialogVisible.value = false
    ElMessage.success('保存成功')
    fetchOrgs()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function removeOrg(item) {
  try {
    await ElMessageBox.confirm(`确定删除组织「${item.name}」？此操作不可恢复。`, '确认删除', { type: 'warning' })
    await systemApi.organizations.delete(item.id)
    ElMessage.success('删除成功')
    fetchOrgs()
  } catch {}
}

onMounted(fetchOrgs)
</script>

<style scoped>
/* ── 页面容器 ── */
.organization-management {
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
.organization-management__header {
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

html:not(.dark) .organization-management__header {
  background: rgba(255, 255, 255, 0.86);
}

.organization-management__header h1,
.organization-management__header p {
  margin: 0;
}

.organization-management__header h1 {
  color: var(--text-strong);
  font-size: 24px;
  line-height: 1.25;
}

.organization-management__header p {
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
.organization-management__filters {
  padding: 14px;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  background: rgba(20, 22, 27, 0.7);
  box-shadow: var(--box-shadow-light);
  backdrop-filter: blur(10px);
}

html:not(.dark) .organization-management__filters {
  background: rgba(255, 255, 255, 0.86);
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.search-bar__input {
  width: 280px;
}

.filter-control {
  width: 140px;
}

.filter-actions {
  display: flex;
  gap: 12px;
}

/* ── 表格区 ── */
.organization-management__table {
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

html:not(.dark) .organization-management__table {
  background: rgba(255, 255, 255, 0.86);
}

.organization-management__table :deep(.el-table) {
  flex: 1;
}

.organization-management__table :deep(.el-table__header th) {
  background: var(--bg-container-soft) !important;
  color: var(--text-secondary);
  font-weight: 700;
  font-size: 12px;
}

.organization-management__table :deep(.el-table__row:hover > td) {
  background: rgba(56, 189, 248, 0.1) !important;
}

.organization-management__table :deep(.el-table__cell) {
  vertical-align: middle;
}

/* ── 分页 ── */
.organization-management__pagination {
  display: flex;
  justify-content: flex-end;
  padding: 10px 16px;
  border-top: 1px solid var(--border-color-lighter, #f0f0f0);
}

/* ── 通用 ── */
.full-width {
  width: 100%;
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

/* ── 弹窗 ── */
.org-form :deep(.el-form-item) {
  margin-bottom: 16px;
}
</style>
