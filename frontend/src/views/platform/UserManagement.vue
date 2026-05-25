<template>
  <div class="user-management">
    <!-- 页面标题区 -->
    <header class="user-management__header">
      <div>
        <h1>用户管理</h1>
        <p>管理系统用户，分配角色与权限。</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="openCreate">新建用户</el-button>
    </header>

    <!-- 查询区 -->
    <section class="user-management__filters">
      <el-form :model="draftFilters" label-position="left" class="filter-form">
        <div class="filter-form__row">
          <el-form-item label="状态：" class="filter-item filter-item--status">
            <el-select
              v-model="draftFilters.status"
              placeholder="全部状态"
              clearable
              class="filter-control"
            >
              <el-option label="启用" value="active" />
              <el-option label="停用" value="disabled" />
            </el-select>
          </el-form-item>
          <el-form-item label="创建日期：" class="filter-item filter-item--date">
            <el-date-picker
              v-model="draftFilters.date_range"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
              class="filter-bar__date-range"
            />
          </el-form-item>
          <el-form-item label="关键词：" class="filter-item filter-item--keyword">
            <el-input
              v-model="draftFilters.keyword"
              placeholder="搜索用户名/姓名/邮箱"
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
    <section class="user-management__table">
      <el-table v-loading="loading" :data="pagedUsers" border>
        <el-table-column prop="username" label="用户名" min-width="130" show-overflow-tooltip />
        <el-table-column prop="display_name" label="姓名" min-width="120" show-overflow-tooltip>
          <template #default="{ row }">{{ row.display_name || '-' }}</template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" min-width="180" show-overflow-tooltip />
        <el-table-column prop="organization_name" label="组织" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">{{ row.organization_name || '-' }}</template>
        </el-table-column>
        <el-table-column label="角色" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">{{ row.roles?.join('，') || '-' }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
              {{ row.status === 'active' ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right" align="center">
          <template #default="{ row }">
            <div class="row-actions">
              <el-button size="small" text type="primary" @click.stop="openEdit(row)">编辑</el-button>
              <el-button size="small" text type="danger" @click.stop="removeUser(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 — 右下角固定 -->
      <div class="pagination-area">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
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

    <!-- 新建/编辑用户弹窗 -->
    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑用户' : '新建用户'" top="4vh" width="min(480px, 92vw)" destroy-on-close>
      <el-form :model="form" label-width="90px">
        <el-form-item label="用户名" required>
          <el-input v-model="form.username" :disabled="!!form.id" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="form.display_name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="邮箱" required>
          <el-input v-model="form.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item v-if="!form.id" label="密码" required>
          <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="form.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="组织">
          <el-select v-model="form.organization_id" placeholder="请选择组织" class="full-width">
            <el-option :value="null" label="未分配" />
            <el-option v-for="org in organizations" :key="org.id" :label="org.name" :value="org.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="角色">
          <el-checkbox-group v-model="form.role_ids" class="check-group">
            <el-checkbox v-for="role in roles" :key="role.id" :label="role.id">
              {{ role.name }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio label="active">启用</el-radio>
            <el-radio label="disabled">停用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveUser">保存</el-button>
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
const users = ref([])
const roles = ref([])
const organizations = ref([])
const dialogVisible = ref(false)

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
const page = ref(1)
const pageSize = ref(15)
const total = ref(0)

const form = reactive(defaultForm())

const pagedUsers = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return users.value.slice(start, start + pageSize.value)
})

function defaultForm() {
  return {
    id: null,
    username: '',
    display_name: '',
    email: '',
    password: '',
    phone: '',
    organization_id: null,
    status: 'active',
    role_ids: [],
  }
}

function buildQueryParams() {
  const params = {
    page: page.value,
    page_size: pageSize.value,
  }
  if (draftFilters.value.keyword) params.keyword = draftFilters.value.keyword
  if (draftFilters.value.status) params.status = draftFilters.value.status
  return params
}

async function fetchUsers() {
  loading.value = true
  try {
    const params = buildQueryParams()
    const res = await systemApi.users.list(params)
    users.value = res.data.items || res.data || []
    total.value = res.data.total || users.value.length
  } catch (e) {
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

async function fetchRoles() {
  try {
    const res = await systemApi.roles.list()
    roles.value = res.data.items || res.data || []
  } catch {}
}

async function fetchOrganizations() {
  try {
    const res = await systemApi.organizations.list()
    organizations.value = res.data.items || res.data || []
  } catch {}
}

function handleSearch() {
  page.value = 1
  fetchUsers()
}

function handleReset() {
  draftFilters.value.keyword = ''
  draftFilters.value.status = ''
  page.value = 1
  fetchUsers()
}

function handlePageChange(p) {
  page.value = p
  fetchUsers()
}

function handleSizeChange(s) {
  pageSize.value = s
  page.value = 1
  fetchUsers()
}

function openCreate() {
  resetForm()
  dialogVisible.value = true
}

function openEdit(user) {
  resetForm({ ...user, password: '', role_ids: [...(user.role_ids || [])] })
  dialogVisible.value = true
}

function resetForm(data = {}) {
  Object.keys(form).forEach(key => { form[key] = defaultForm()[key] })
  Object.assign(form, defaultForm(), data)
}

async function saveUser() {
  if (!form.username || !form.email) {
    ElMessage.warning('请填写用户名和邮箱')
    return
  }
  saving.value = true
  try {
    const payload = { ...form }
    if (payload.id) {
      delete payload.username
      delete payload.password
      await systemApi.users.update(payload.id, payload)
    } else {
      await systemApi.users.create(payload)
    }
    dialogVisible.value = false
    ElMessage.success('保存成功')
    fetchUsers()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function removeUser(user) {
  try {
    await ElMessageBox.confirm(`确定删除用户「${user.username}」？此操作不可恢复。`, '确认删除', { type: 'warning' })
    await systemApi.users.delete(user.id)
    ElMessage.success('删除成功')
    fetchUsers()
  } catch {}
}

onMounted(() => {
  fetchUsers()
  fetchRoles()
  fetchOrganizations()
})
</script>

<style scoped>
/* ── 页面容器 ── */
.user-management {
  position: relative;
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
}

.user-management::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 24%, rgba(56, 189, 248, 0.16) 44%, transparent 62%),
    repeating-linear-gradient(90deg, transparent 0 92px, rgba(56, 189, 248, 0.075) 92px 93px);
  content: "";
  animation: user-management-scan 14s linear infinite;
}

.user-management::after {
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
  animation: user-management-particles 18s ease-in-out infinite alternate;
}

@keyframes user-management-scan {
  from { transform: translateX(-24%); }
  to { transform: translateX(24%); }
}

@keyframes user-management-particles {
  from { transform: translate3d(0, 0, 0); }
  to { transform: translate3d(26px, -18px, 0); }
}

@keyframes user-management-form-scan {
  from { transform: translateY(-8%); }
  to { transform: translateY(108%); }
}

@keyframes user-management-table-scan {
  from { transform: translateY(-6%); }
  to { transform: translateY(106%); }
}

@media (prefers-reduced-motion: reduce) {
  .user-management::before,
  .user-management::after {
    animation: none;
  }
}

/* ── 标题区 ── */
.user-management__header {
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

.user-management__header::after {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(90deg, rgba(56, 189, 248, 0.22), transparent 18% 82%, rgba(34, 211, 166, 0.18)),
    repeating-linear-gradient(90deg, transparent 0 42px, rgba(56, 189, 248, 0.06) 42px 43px);
  opacity: 0.65;
  content: "";
}

html:not(.dark) .user-management__header {
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.86), rgba(245, 250, 255, 0.68)),
    rgba(255, 255, 255, 0.72);
  box-shadow: 0 18px 46px rgba(20, 42, 76, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.82);
  border-color: rgba(22, 119, 255, 0.18);
}

.user-management__header h1,
.user-management__header p {
  margin: 0;
  position: relative;
  z-index: 1;
}

.user-management__header .el-button {
  position: relative;
  z-index: 1;
}

.user-management__header h1 {
  color: var(--text-strong);
  font-size: 24px;
  line-height: 1.25;
}

.user-management__header p {
  margin-top: 4px;
  color: var(--text-secondary);
  font-size: 13px;
}

/* ── 查询区 ── */
.user-management__filters {
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

.user-management__filters::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(56, 189, 248, 0.1) 50%, transparent 66%);
  opacity: 0.7;
  content: "";
  animation: user-management-form-scan 12s linear infinite;
}

html:not(.dark) .user-management__filters {
  background:
    linear-gradient(rgba(22, 119, 255, 0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.04) 1px, transparent 1px),
    linear-gradient(145deg, rgba(255, 255, 255, 0.76), rgba(245, 250, 255, 0.58)),
    rgba(255, 255, 255, 0.62);
  background-size: 26px 26px, 26px 26px, auto, auto;
  border-color: rgba(22, 119, 255, 0.14);
}

html:not(.dark) .user-management__filters::before {
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
  flex-wrap: wrap;
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
.user-management__filters :deep(.filter-bar__date-range.el-date-editor) {
  flex: 0 0 320px;
  width: 320px !important;
  max-width: 320px;
  min-width: 0;
}

.user-management__filters :deep(.filter-bar__date-range .el-range-input) {
  width: 96px;
  flex: 0 0 96px;
}

.user-management__filters :deep(.filter-bar__date-range .el-range-separator) {
  flex: 0 0 24px;
  padding: 0;
}

/* ── 表格区 ── */
.user-management__table {
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
}

.user-management__table::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 36%, rgba(56, 189, 248, 0.12) 50%, transparent 66%),
    radial-gradient(circle at 88% 16%, rgba(34, 211, 166, 0.14), transparent 26%);
  opacity: 0.8;
  content: "";
  animation: user-management-table-scan 12s linear infinite;
}

html:not(.dark) .user-management__table {
  background:
    linear-gradient(rgba(22, 119, 255, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(22, 119, 255, 0.03) 1px, transparent 1px),
    linear-gradient(145deg, rgba(255, 255, 255, 0.76), rgba(245, 250, 255, 0.58)),
    rgba(255, 255, 255, 0.62);
  background-size: 32px 32px, 32px 32px, auto, auto;
  border-color: rgba(22, 119, 255, 0.14);
}

.user-management__table :deep(.el-table) {
  flex: 1;
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: rgba(8, 18, 32, 0.34);
  --el-table-header-bg-color: rgba(15, 31, 52, 0.46);
  --el-table-expanded-cell-bg-color: rgba(8, 18, 32, 0.42);
  --el-table-row-hover-bg-color: var(--color-primary-soft);
  position: relative;
  z-index: 1;
}

html:not(.dark) .user-management__table :deep(.el-table) {
  --el-table-tr-bg-color: rgba(255, 255, 255, 0.54);
  --el-table-header-bg-color: rgba(240, 247, 255, 0.68);
  --el-table-expanded-cell-bg-color: rgba(255, 255, 255, 0.64);
  --el-table-row-hover-bg-color: var(--color-primary-soft);
}

.user-management__table :deep(.el-table__inner-wrapper::before) {
  background: rgba(56, 189, 248, 0.12);
}

.user-management__table :deep(.el-table__body-wrapper),
.user-management__table :deep(.el-table__header-wrapper),
.user-management__table :deep(.el-scrollbar__view) {
  background: transparent;
}

.user-management__table :deep(.el-table__header th) {
  height: 44px;
  color: var(--text-secondary);
  background: var(--el-table-header-bg-color) !important;
  background-color: var(--el-table-header-bg-color) !important;
  font-weight: 700;
  font-size: 13px;
}

.user-management__table :deep(.el-table__body td) {
  height: 48px;
  background: var(--el-table-tr-bg-color) !important;
  background-color: var(--el-table-tr-bg-color) !important;
}

.user-management__table :deep(.el-table__body tr:nth-child(even) td.el-table__cell) {
  background: rgba(15, 31, 52, 0.28) !important;
  background-color: rgba(15, 31, 52, 0.28) !important;
}

html:not(.dark) .user-management__table :deep(.el-table__body tr:nth-child(even) td.el-table__cell) {
  background: rgba(245, 250, 255, 0.5) !important;
  background-color: rgba(245, 250, 255, 0.5) !important;
}

.user-management__table :deep(.el-table__row:hover > td) {
  background: var(--el-table-row-hover-bg-color) !important;
  background-color: var(--el-table-row-hover-bg-color) !important;
}

.user-management__table :deep(.el-table__row:hover > td.el-table-fixed-column--right),
.user-management__table :deep(.el-table__row:hover > td.el-table-fixed-column--left) {
  background: var(--el-table-row-hover-bg-color) !important;
  background-color: var(--el-table-row-hover-bg-color) !important;
}

.user-management__table :deep(.el-table .cell) {
  padding: 0 10px;
}

.user-management__table :deep(.el-table__cell) {
  vertical-align: middle;
}

@media (prefers-reduced-motion: reduce) {
  .user-management__table::before {
    animation: none;
  }
}

.pagination-area {
  display: flex;
  justify-content: flex-end;
  padding: 10px 16px;
  border-top: 1px solid rgba(56, 189, 248, 0.12);
}

html:not(.dark) .pagination-area {
  border-top-color: rgba(22, 119, 255, 0.12);
}

.full-width {
  width: 100%;
}

.check-group {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-sm);
}

.row-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}
</style>
