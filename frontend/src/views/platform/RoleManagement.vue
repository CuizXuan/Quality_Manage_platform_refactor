<template>
  <div class="role-management-page">
    <!-- 页面标题区 -->
    <header class="role-management-page__header">
      <div>
        <h1>角色管理</h1>
        <p>统一管理系统角色与权限配置。</p>
      </div>
      <el-button type="primary" class="btn-primary-add" :icon="Plus" @click="openCreate">新建角色</el-button>
    </header>

    <!-- 查询区 -->
    <section class="role-management-page__filters">
      <div class="filter-bar">
        <el-select
          v-model="draftFilters.status"
          placeholder="全部状态"
          clearable
          class="filter-control"
        >
          <el-option label="启用" value="active" />
          <el-option label="停用" value="disabled" />
        </el-select>
      </div>
      <div class="search-bar">
        <el-input
          v-model="draftFilters.keyword"
          placeholder="搜索角色名称/编码"
          clearable
          class="search-bar__input"
          @keyup.enter="handleSearch"
        />
        <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
        <el-button :icon="RefreshLeft" @click="handleReset">重置</el-button>
      </div>
    </section>

    <!-- 数据列表 -->
    <section class="role-management-page__table">
      <el-table
        v-loading="loading"
        :data="pagedRoles"
        height="100%"
        highlight-current-row
      >
        <el-table-column prop="name" label="角色名称" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="name-cell">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="code" label="角色编码" min-width="130" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="text-secondary">{{ row.code }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="text-secondary">{{ row.description || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
              {{ row.status === 'active' ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="权限" width="130" align="center">
          <template #default="{ row }">
            <span class="text-secondary">{{ formatPermissionCount(row.permissions) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right" align="center">
          <template #default="{ row }">
            <div class="actions-cell">
              <el-button type="primary" text size="small" @click.stop="openPermission(row)">授权</el-button>
              <el-button type="primary" text size="small" @click.stop="openEdit(row)">编辑</el-button>
              <el-button type="danger" text size="small" @click.stop="removeRole(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
        <template #empty>
          <span class="empty-text">暂无符合条件的角色</span>
        </template>
      </el-table>

      <div class="role-management-page__pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="total"
          :page-sizes="[15, 30, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          prev-text="上一页"
          next-text="下一页"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </section>

    <!-- 新建/编辑角色弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="form.id ? '编辑角色' : '新建角色'"
      top="4vh"
      width="min(480px, 92vw)"
      destroy-on-close
    >
      <el-form :model="form" label-width="90px" class="role-form">
        <el-form-item label="角色名称" required>
          <el-input v-model="form.name" placeholder="请输入角色名称" />
        </el-form-item>
        <el-form-item label="角色编码" required>
          <el-input v-model="form.code" :disabled="!!form.id" placeholder="请输入角色编码" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入描述" />
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
        <el-button type="primary" :loading="saving" @click="saveRole">保存</el-button>
      </template>
    </el-dialog>

    <!-- 权限配置弹窗 -->
    <el-dialog
      v-model="permissionDialogVisible"
      :title="`配置权限：${permissionRole?.name || ''}`"
      top="4vh"
      width="min(720px, 92vw)"
      destroy-on-close
    >
      <div class="permission-summary">
        <span>已选择 {{ permissionForm.length }} 项</span>
        <span>共 {{ permissionResources.length }} 个菜单</span>
      </div>

      <el-table :data="pagedPermissionResources" border class="permission-table">
        <el-table-column prop="label" label="菜单" min-width="160" />
        <el-table-column
          v-for="action in permissionActions"
          :key="action.key"
          :label="action.label"
          align="center"
        >
          <template #default="{ row }">
            <el-checkbox
              v-if="row.actions.includes(action.key)"
              :model-value="permissionForm.includes(`${row.key}:${action.key}`)"
              @change="togglePermission(`${row.key}:${action.key}`, $event)"
            />
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="permission-pagination-area">
        <el-pagination
          v-model:current-page="permissionPage"
          v-model:page-size="permissionPageSize"
          :total="permissionTotal"
          :page-sizes="[8, 15, 30]"
          layout="total, sizes, prev, pager, next, jumper"
          prev-text="上一页"
          next-text="下一页"
        />
      </div>

      <template #footer>
        <el-button @click="permissionDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingPermission" @click="savePermissions">保存权限</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { Plus, Search, RefreshLeft } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { systemApi } from '@/api/system'
import { permissionActions, permissionResources } from './permissionOptions'

const loading = ref(false)
const saving = ref(false)
const savingPermission = ref(false)
const roles = ref([])
const dialogVisible = ref(false)
const permissionDialogVisible = ref(false)
const permissionRole = ref(null)
const permissionForm = ref([])

const draftFilters = ref({
  keyword: '',
  status: '',
})

const appliedFilters = ref({
  keyword: '',
  status: '',
})

const pagination = ref({
  page: 1,
  pageSize: 15,
})

const total = ref(0)

const form = reactive(defaultForm())

const pagedRoles = computed(() => {
  const start = (pagination.value.page - 1) * pagination.value.pageSize
  return roles.value.slice(start, start + pagination.value.pageSize)
})

const permissionPage = ref(1)
const permissionPageSize = ref(8)
const permissionTotal = computed(() => permissionResources.length)
const pagedPermissionResources = computed(() => {
  const start = (permissionPage.value - 1) * permissionPageSize.value
  return permissionResources.slice(start, start + permissionPageSize.value)
})

function defaultForm() {
  return {
    id: null,
    name: '',
    code: '',
    description: '',
    status: 'active',
  }
}

function formatPermissionCount(value = []) {
  return `已授权 ${value?.length || 0} 项`
}

function buildQueryParams() {
  return {
    page: 1,
    page_size: 1000,
    ...(appliedFilters.value.keyword && { keyword: appliedFilters.value.keyword }),
    ...(appliedFilters.value.status && { status: appliedFilters.value.status }),
  }
}

async function fetchRoles() {
  loading.value = true
  try {
    const res = await systemApi.roles.list(buildQueryParams())
    roles.value = res.data.items || res.data || []
    total.value = res.data.total || roles.value.length
  } catch {
    ElMessage.error('获取角色列表失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  appliedFilters.value = { ...draftFilters.value }
  pagination.value.page = 1
  fetchRoles()
}

function handleReset() {
  draftFilters.value = { keyword: '', status: '' }
  appliedFilters.value = { keyword: '', status: '' }
  pagination.value.page = 1
  fetchRoles()
}

function handlePageChange(page) {
  pagination.value.page = page
  fetchRoles()
}

function handleSizeChange(size) {
  pagination.value.pageSize = size
  pagination.value.page = 1
  fetchRoles()
}

function openCreate() {
  resetForm()
  dialogVisible.value = true
}

function openEdit(item) {
  resetForm({ ...item })
  dialogVisible.value = true
}

function openPermission(item) {
  permissionRole.value = item
  permissionForm.value = [...(item.permissions || [])]
  permissionPage.value = 1
  permissionDialogVisible.value = true
}

function resetForm(data = {}) {
  Object.assign(form, defaultForm(), data)
}

async function saveRole() {
  if (!form.name || !form.code) {
    ElMessage.warning('请填写角色名称和编码')
    return
  }
  saving.value = true
  try {
    const payload = { ...form }
    if (payload.id) {
      await systemApi.roles.update(payload.id, {
        name: payload.name,
        description: payload.description,
        status: payload.status,
      })
    } else {
      await systemApi.roles.create({ ...payload, permissions: [] })
    }
    dialogVisible.value = false
    ElMessage.success('保存成功')
    fetchRoles()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function removeRole(item) {
  try {
    await ElMessageBox.confirm(`确定删除角色「${item.name}」？此操作不可恢复。`, '确认删除', { type: 'warning' })
    await systemApi.roles.delete(item.id)
    ElMessage.success('删除成功')
    fetchRoles()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('删除失败')
  }
}

function togglePermission(value, checked) {
  if (checked) {
    if (!permissionForm.value.includes(value)) permissionForm.value.push(value)
  } else {
    permissionForm.value = permissionForm.value.filter(item => item !== value)
  }
}

async function savePermissions() {
  savingPermission.value = true
  try {
    await systemApi.roles.update(permissionRole.value.id, {
      permissions: permissionForm.value,
    })
    permissionDialogVisible.value = false
    ElMessage.success('权限保存成功')
    fetchRoles()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '权限保存失败')
  } finally {
    savingPermission.value = false
  }
}

onMounted(fetchRoles)
</script>

<style scoped>
/* ── 页面容器 ── */
.role-management-page {
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
.role-management-page__header {
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

html:not(.dark) .role-management-page__header {
  background: rgba(255, 255, 255, 0.86);
}

.role-management-page__header h1,
.role-management-page__header p {
  margin: 0;
}

.role-management-page__header h1 {
  color: var(--text-strong);
  font-size: 24px;
  line-height: 1.25;
}

.role-management-page__header p {
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

/* ── 查询区 ── */
.role-management-page__filters {
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

html:not(.dark) .role-management-page__filters {
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

/* ── 表格区 ── */
.role-management-page__table {
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

html:not(.dark) .role-management-page__table {
  background: rgba(255, 255, 255, 0.86);
}

.role-management-page__table :deep(.el-table) {
  flex: 1;
}

.role-management-page__table :deep(.el-table__header th) {
  background: var(--bg-container-soft) !important;
  color: var(--text-secondary);
  font-weight: 700;
  font-size: 12px;
}

.role-management-page__table :deep(.el-table__row:hover > td) {
  background: rgba(56, 189, 248, 0.1) !important;
}

.role-management-page__table :deep(.el-table__cell) {
  vertical-align: middle;
}

.name-cell {
  font-weight: 600;
  color: var(--text-primary);
}

.text-secondary {
  color: var(--text-secondary);
  font-size: 13px;
}

.text-muted {
  color: var(--text-secondary);
  font-size: 12px;
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

/* ── 分页 ── */
.role-management-page__pagination {
  display: flex;
  justify-content: flex-end;
  padding: 10px 16px;
  border-top: 1px solid var(--border-color-lighter, #f0f0f0);
}

/* ── 权限弹窗 ── */
.permission-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  color: var(--text-secondary);
  font-size: 13px;
}

.permission-table {
  margin-bottom: 12px;
}

.permission-pagination-area {
  display: flex;
  justify-content: flex-end;
}

.role-form :deep(.el-form-item) {
  margin-bottom: 16px;
}
</style>
